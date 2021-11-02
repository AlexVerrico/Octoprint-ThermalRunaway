# coding=utf-8
from __future__ import absolute_import

# Import the core OctoPrint plugin components
import octoprint.plugin
# Import logging to allow for easier debugging
import logging
# Import threading. This is used to process the temps asynchronously so
# that we don't block OctoPrints communications with the printer
import threading
# Import time. This is so that we can add delays to parts of the code
import time


class ThermalRunawayPlugin(octoprint.plugin.StartupPlugin,
                           octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.TemplatePlugin,
                           octoprint.plugin.RestartNeedingPlugin):

    def __init__(self):
        # This allows us to store and display our logs with the rest of the OctoPrint logs
        self.logger = logging.getLogger('octoprint.plugins.ThermalRunaway')

        self.runaway_message = "Thermal Runaway ({t} temp) caught on heater {h}. Reported temp is {c}, set temp is {s} "
        return

    #######################
    # StartupPlugin Mixin #
    #######################
    # Function to run after OctoPrint starts, used to initialise variables
    def on_after_startup(self):
        # Create a dictionary to store the data about the bed heater
        self.heaterDict = {
            'B': {
                'delay': self._settings.get(['bDelay']),  # Delay before setting a thermal warning
                'maxDiff': self._settings.get(['bMaxDiff']),  # Maximum allowed deviation from set temperature
                'warningTimes': {
                    'low': 0,
                    'high': 0
                },
                'temps': {
                    'current': float('NaN'),
                    'set': float('NaN'),
                    'high': float('NaN'),
                    'low': float('NaN'),
                    'maxOff': self._settings.get(['bMaxOffTemp']),
                    'max': float('NaN'),
                    'min': float('NaN')
                }
            }
        }

        # Check how many extruders we should be monitoring
        self.extruderCount = self._settings.get(['numberExtruders'])

        # Loop through the number of extruders and create a dictionary for each one to store the data for it
        for extruder in range(0, int(self.extruderCount)):
            self.heaterDict['T{}'.format(extruder)] = {
                'delay': self._settings.get(['tDelay']),
                'maxDiff': self._settings.get(['tMaxDiff']),
                'warningTimes': {
                    'low': 0,
                    'high': 0
                },
                'temps': {
                    'current': float('NaN'),
                    'set': float('NaN'),
                    'high': float('NaN'),
                    'low': float('NaN'),
                    'maxOff': self._settings.get(['tMaxOffTemp']),
                    'max': float('NaN'),
                    'min': float('NaN')
                }
            }

        # Check what GCode the user has specified to send in the event of a thermal runaway
        self.emergencyGCode = self._settings.get(['emergencyGcode'])

        # log that we have reached the end of this function
        self.logger.debug('reached end of on_after_startup')
        return

    ########################
    # SettingsPlugin Mixin #
    ########################
    # Function to return the default values for all settings for this plugin
    def get_settings_defaults(self):
        # Define default settings for this plugin
        return dict(
            numberExtruders=1,
            emergencyGcode="M112",
            bMaxDiff="10",
            bMaxOffTemp="30",
            tMaxDiff="20",
            tMaxOffTemp="30",
            tDelay="25",
            bDelay="20",
            triggerOnEqual=True
        )

    ########################
    # TemplatePlugin Mixin #
    ########################
    # Function to inform OctoPrint what parts of the UI we will be binding to
    def get_template_configs(self):
        # Tell OctoPrint that we have a settings page
        return [
            dict(type="settings", custom_bindings=False)
        ]

    ##############################
    # Temperatures Received Hook #
    ##############################
    # Temperatures hook
    def get_temps(self, comm, parsed_temps):
        # Wrap everything in a try-except-finally statement to ensure that we always pass the temps to OctoPrint
        try:
            # Create a thread to process the received temps to ensure that we don't block communications to the printer
            t = threading.Thread(target=self.check_temps, args=(parsed_temps,))
            t.start()  # Start the thread
        except Exception as e:
            # Log that something went wrong
            self.logger.error("Exception in get_temps: {}".format(e))
        finally:
            # log that we have reached the end of this function
            self.logger.debug('Reached end of get_temps')
            return parsed_temps  # return the temps to OctoPrint

    ####################
    # Custom functions #
    ####################
    # update the target range that heaters are expected to be in
    def update_target_temp_range(self, heater, newSetTemp):
        if self.heaterDict[heater]['temps']['set'] == newSetTemp:
            # hasn't changed, no need to update
            return

        # rest only runs if set temp has changed

        # store new set temp
        self.heaterDict[heater]['temps']['set'] = newSetTemp

        # reset high/low to current
        self.heaterDict[heater]['temps']['low'] = self.heaterDict[heater]['temps']['current']
        self.heaterDict[heater]['temps']['high'] = self.heaterDict[heater]['temps']['current']

        # reset warnings when setpoint changes
        self.heaterDict[heater]['warningTimes'] = {
            'low': 0,
            'high': 0
        }

        # Check if the heater is turned on
        if float(self.heaterDict[heater]['temps']['set']) > 0.0:
            # Set the heater max temp to setTemp + maxDiff
            self.heaterDict[heater]['temps']['max'] = float(self.heaterDict[heater]['temps']['set']) + \
                                                        float(self.heaterDict[heater]['maxDiff'])
            # Set the heater min temp to setTemp - maxDiff
            self.heaterDict[heater]['temps']['min'] = float(self.heaterDict[heater]['temps']['set']) - \
                                                        float(self.heaterDict[heater]['maxDiff'])
            # Log what we set the max and min temps to
            self.logger.debug("Heater {h} is set to {s}. Max temp set to {ma}, Min temp set to {mi}"
                                .format(h=heater,
                                        s=self.heaterDict[heater]['temps']['set'],
                                        ma=self.heaterDict[heater]['temps']['max'],
                                        mi=self.heaterDict[heater]['temps']['min']))

        # If the heater is turned off:
        else:
            # Set the max temp to maxOffTemp
            self.heaterDict[heater]['temps']['max'] = float(self.heaterDict[heater]['temps']['maxOff'])
            # Set the min temp to 0
            self.heaterDict[heater]['temps']['min'] = 0.0
            # Log what we set the max and min temps to
            self.logger.debug("Heater {h} is set to less than 0.0. Max temp set to {ma}, Min temp set to {mi}"
                                .format(h=heater,
                                        ma=self.heaterDict[heater]['temps']['max'],
                                        mi=self.heaterDict[heater]['temps']['min']))
    
    # unify high/low checks
    # direction = high/low
    def check_threshold_direction(self, heater, direction):
        # comparisons where true is a good state, false is bad
        goodComparisonMap = {
            'low': lambda current, low: current > low,
            'high': lambda current, high: current < high 
        }

        currentTime = time.time()

        # check if we're currently within the threshold
        if goodComparisonMap[direction](float(self.heaterDict[heater]['temps']['current']), float(self.heaterDict[heater]['temps'][direction])):
            # we're within threshold, nothing to worry about
            # reset any warnings
            self.heaterDict[heater]['warningTimes'][direction] = 0

            return

        # we're not within threshold, start processing warnings

        # check if we've been on the wrong side of the threshold for longer than the specified delay
        # if so, we're in runaway
        if self.heaterDict[heater]['warningTimes'][direction] + int(self.heaterDict[heater]['delay']) > currentTime:
            directionRunawayMap = {
                'low': 'under',
                'high': 'over'
            }
            # Call self.runaway_triggered and pass the required details
            self.runaway_triggered(heater,
                                    self.heaterDict[heater]['temps']['set'],
                                    self.heaterDict[heater]['temps']['current'],
                                    directionRunawayMap[direction])
            # Log that we caught a thermal runaway
            self.logger.critical(self.runaway_message.format(h=heater,
                                                                c=self.heaterDict[heater]['temps']['current'],
                                                                s=self.heaterDict[heater]['temps']['set'],
                                                                t=directionRunawayMap[direction]))
            
            return
        
        # check if we're already in warning
        if self.heaterDict[heater]['warningTimes'][direction] == 0:
            # we were not, let's set it now
            self.heaterDict[heater]['warningTimes'][direction] = currentTime
            self.logger.warning('{h} temperature is now {d}'.format(h=heater, d=direction))
        else:
            # we were, let's log it
            self.logger.warning('{h} temperature has been {d} for {s} seconds'.format(h=heater, d=direction, s=(currentTime - self.heaterDict[heater]['warningTimes'][direction])))


    def check_heater_thresholds(self, heater):
        aboveMin = float(self.heaterDict[heater]['temps']['current']) >= float(self.heaterDict[heater]['temps']['min'])
        belowMax = float(self.heaterDict[heater]['temps']['current']) <= float(self.heaterDict[heater]['temps']['max'])

        if aboveMin and belowMax:
            # temperature is within target range, skip
            return

        if not aboveMin:
            # temp below target range
            self.check_threshold_direction(heater, 'low')
        
        if not belowMax:
            # temp above target range
            self.check_threshold_direction(heater, 'high')
        
    
    # update thresholds to current temp (only if they're moving in the right direction)
    def update_stored_temps(self, heater):
        # only update low if we're higher than previous low
        if float(self.heaterDict[heater]['temps']['current']) > float(self.heaterDict[heater]['temps']['low']):
            # Set the lowTemp to the current temp
            self.heaterDict[heater]['temps']['low'] = float(self.heaterDict[heater]['temps']['current'])

        # only update high if we're lower than previous high
        if float(self.heaterDict[heater]['temps']['current']) < float(self.heaterDict[heater]['temps']['high']):
            # Set the highTemp to the current temp
            self.heaterDict[heater]['temps']['high'] = float(self.heaterDict[heater]['temps']['current'])

    # Function to process temperatures received from the printer and check for a thermal runaway
    def check_temps(self, temps):
        # Log that we have reached the start of check_temps
        self.logger.debug('Reached start of check_temps')

        # Check what GCode the user has specified to send in the event of a thermal runaway
        self.emergencyGCode = self._settings.get(["emergencyGcode"])

        # Store received temperatures and settings values for the bed
        self.heaterDict['B']['delay'] = float(self._settings.get(["bDelay"]))
        self.heaterDict['B']['maxDiff'] = float(self._settings.get(["bMaxDiff"]))
        self.heaterDict['B']['temps']['current'] = float(temps['B'][0])
        self.heaterDict['B']['temps']['maxOff'] = float(self._settings.get(["bMaxOffTemp"]))
        self.update_target_temp_range('B', float(temps['B'][1]))


        # Store received temperatures and settings values for the extruder(s)
        for extruder in range(0, int(self.extruderCount)):
            self.heaterDict['T{}'.format(extruder)]['delay'] = float(self._settings.get(["tDelay"]))
            self.heaterDict['T{}'.format(extruder)]['maxDiff'] = float(self._settings.get(["tMaxDiff"]))
            self.heaterDict['T{}'.format(extruder)]['temps']['current'] = float(temps['T{}'.format(extruder)][0])
            self.heaterDict['T{}'.format(extruder)]['temps']['maxOff'] = float(self._settings.get(["tMaxOffTemp"]))
            self.update_target_temp_range('T{}'.format(extruder), float(temps['T{}'.format(extruder)][1]))

        # Loop through dictionary of heaters
        for heater, values in self.heaterDict.items():
            self.check_heater_thresholds(heater)

            # Update high/low temps at end of loop
            self.update_stored_temps(heater)

        # log that we have reached the end of this function
        self.logger.debug('Reached end of check_temps')
        return

    # Function that is used to call all plugins that have registered handlers for this plugins hooks
    def runaway_triggered(self, heater_id: str, set_temp: float, current_temp: float, runaway_type: str):
        # Wrap everything in a try-except to catch any errors
        try:
            # Send the emergency GCode
            self._printer.commands(self.emergencyGCode)

            # Generate a list of plugins that have registered handlers for the hook runaway_triggered
            registered_plugins = self._plugin_manager.get_hooks(
                "octoprint.plugin.ThermalRunaway.runaway_triggered"
            )
            # Iterate through the list of registered hooks
            for name, hook in registered_plugins.items():
                try:
                    # Attempt to call the hook in a new thread
                    t = threading.Thread(target=hook, args=(heater_id, set_temp, current_temp))
                    t.start()
                except Exception as e:
                    # Log that something went wrong
                    self.logger.exception("Exception in runway_triggered: {}".format(e))

            if runaway_type == 'over':
                # Generate a list of plugins that have registered handlers for the hook over_runaway_triggered
                registered_plugins = self._plugin_manager.get_hooks(
                    "octoprint.plugin.ThermalRunaway.over_runaway_triggered"
                )
                # Iterate through the list of registered hooks
                for name, hook in registered_plugins.items():
                    try:
                        # Attempt to call the hook in a new thread
                        t = threading.Thread(target=hook, args=(heater_id, set_temp, current_temp))
                        t.start()
                    except Exception as e:
                        # Log that something went wrong
                        self.logger.exception("Exception in runaway_triggered: {}".format(e))

            if runaway_type == 'under':
                # Generate a list of plugins that have registered handlers for the hook under_runaway_triggered
                registered_plugins = self._plugin_manager.get_hooks(
                    "octoprint.plugin.ThermalRunaway.under_runaway_triggered"
                )
                # Iterate through the list of registered hooks
                for name, hook in registered_plugins.items():
                    try:
                        # Attempt to call the hook in a new thread
                        t = threading.Thread(target=hook, args=(heater_id, set_temp, current_temp))
                        t.start()
                    except Exception as e:
                        # Log that something went wrong
                        self.logger.exception("Exception in runaway_triggered: {}".format(e))

        except Exception as e:
            # Log that something went wrong
            self.logger.exception("Exception in runaway_triggered: {}".format(e))
        finally:
            return

    ########################
    # Software Update Hook #
    ########################
    # Function to tell OctoPrint how to update the plugin
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            ThermalRunaway=dict(
                displayName="Thermal Runaway Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="AlexVerrico",
                repo="Octoprint-ThermalRunaway",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/AlexVerrico/Octoprint-ThermalRunaway/archive/{target_version}.zip"
            )
        )


__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ThermalRunawayPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.get_temps
    }
