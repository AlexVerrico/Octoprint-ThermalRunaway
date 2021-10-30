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
                'thermalHighWarning': False,  # Variable to store whether
                'thermalLowWarning': False,  #
                'thermalHighAlert': False,  #
                'thermalLowAlert': False,  #
                'thermalHighCount': 0,
                'thermalLowCount': 0,
                'temps': {
                    'current': 0.0,
                    'set': 0.0,
                    'high': 0.0,
                    'low': 0.0,
                    'maxOff': self._settings.get(['bMaxOffTemp']),
                    'max': 0.0,
                    'min': 0.0
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
                'thermalHighWarning': False,
                'thermalLowWarning': False,
                'thermalHighAlert': False,
                'thermalLowAlert': False,
                'thermalHighCount': 0,
                'thermalLowCount': 0,
                'temps': {
                    'current': 0.0,
                    'set': 0.0,
                    'high': 0.0,
                    'low': 0.0,
                    'maxOff': self._settings.get(['tMaxOffTemp']),
                    'max': 0.0,
                    'min': 0.0
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
    # Function to process temperatures received from the printer and check for a thermal runaway
    def check_temps(self, temps):
        # Log that we have reached the start of check_temps
        self.logger.debug('Reached start of check_temps')

        # Check what GCode the user has specified to send in the event of a thermal runaway
        self.emergencyGCode = self._settings.get(["emergencyGcode"])

        # Store received temperatures and settings values for the bed
        self.heaterDict['B']['delay'] = float(self._settings.get(["bDelay"]))
        self.heaterDict['B']['maxDiff'] = float(self._settings.get(["bMaxDiff"]))
        self.heaterDict['B']['temps']['set'] = float(temps['B'][1])
        self.heaterDict['B']['temps']['current'] = float(temps['B'][0])
        self.heaterDict['B']['temps']['maxOff'] = float(self._settings.get(["bMaxOffTemp"]))

        # Store received temperatures and settings values for the extruder(s)
        for extruder in range(0, int(self.extruderCount)):
            self.heaterDict['T{}'.format(extruder)]['delay'] = float(self._settings.get(["tDelay"]))
            self.heaterDict['T{}'.format(extruder)]['maxDiff'] = float(self._settings.get(["tMaxDiff"]))
            self.heaterDict['T{}'.format(extruder)]['temps']['set'] = float(temps['T{}'.format(extruder)][1])
            self.heaterDict['T{}'.format(extruder)]['temps']['current'] = float(temps['T{}'.format(extruder)][0])
            self.heaterDict['T{}'.format(extruder)]['temps']['maxOff'] = float(self._settings.get(["tMaxOffTemp"]))

        # Loop through dictionary of heaters
        for heater, values in self.heaterDict.items():

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

            # Check if the current temp is lower than the minTemp
            if float(self.heaterDict[heater]['temps']['current']) < float(self.heaterDict[heater]['temps']['min']):
                # Check if thermalLowCount is equal to 0:
                if int(self.heaterDict[heater]['thermalLowCount']) == 0:
                    # Set thermalLowCount to 1 (warning level)
                    self.heaterDict[heater]['thermalLowCount'] = 1
                    # Set the lowTemp to the current temp
                    self.heaterDict[heater]['temps']['low'] = float(self.heaterDict[heater]['temps']['current'])
            else:
                # Set thermalLowCount to 0 (all clear)
                self.heaterDict[heater]['thermalLowCount'] = 0

            # Check if the current temp is higher than the maxTemp
            if float(self.heaterDict[heater]['temps']['current']) > float(self.heaterDict[heater]['temps']['max']):
                # Check if the thermalHighCount is equal to 0:
                if int(self.heaterDict[heater]['thermalHighCount']) == 0:
                    # Set thermalHighCount to 1 (warning level)
                    self.heaterDict[heater]['thermalHighCount'] = 1
                    # Set the highTemp to the current temp
                    self.heaterDict[heater]['temps']['high'] = float(self.heaterDict[heater]['temps']['current'])
            else:
                # Set thermalHighCount to 0 (all clear)
                self.heaterDict[heater]['thermalHighCount'] = 0

            # Check if thermalHighCount is greater than 2 (alert level)
            if int(self.heaterDict[heater]['thermalHighCount']) >= 2:
                # Log that a thermalHighAlert has been triggered
                self.logger.warning('thermalHighCount > 2 for {h}'.format(h=heater))
                # Check whether the thermalAlert should be triggered if the current temperature
                # is equal to the high temp and set the test variable accordingly
                if self._settings.get(['triggerOnEqual']) is True:
                    test = float(self.heaterDict[heater]['temps']['current']) >= float(self.heaterDict[heater]['temps']['high'])
                else:
                    test = float(self.heaterDict[heater]['temps']['current']) > float(self.heaterDict[heater]['temps']['high'])
                # Check if the current temp is higher than the stored highTemp
                if test is True:
                    # Call self.runaway_triggered and pass the required details
                    self.runaway_triggered(heater,
                                           self.heaterDict[heater]['temps']['set'],
                                           self.heaterDict[heater]['temps']['current'],
                                           'over')
                    # Log that we caught a thermal runaway
                    self.logger.critical(self.runaway_message.format(h=heater,
                                                                     c=self.heaterDict[heater]['temps']['current'],
                                                                     s=self.heaterDict[heater]['temps']['set'],
                                                                     t="over"))
                    self.heaterDict[heater]['thermalHighCount'] = 0
                else:
                    # Set stored highTemp to current temp
                    self.heaterDict[heater]['temps']['high'] = float(self.heaterDict[heater]['temps']['current'])
                    # Set thermalHighCount to 1 (warning level)
                    self.heaterDict[heater]['thermalHighCount'] = 1

            # Check if thermalLowCount is greater than 2 (alert level)
            if int(self.heaterDict[heater]['thermalLowCount']) >= 2:
                # Log that a thermalLowAlert has been triggered
                self.logger.warning('thermalLowCount > 2 for {h}'.format(h=heater))
                # Check whether the thermalAlert should be triggered if the current temperature
                # is equal to the low temp and set the test variable accordingly
                if self._settings.get(['triggerOnEqual']) is True:
                    test = float(self.heaterDict[heater]['temps']['current']) <= float(self.heaterDict[heater]['temps']['low'])
                else:
                    test = float(self.heaterDict[heater]['temps']['current']) < float(self.heaterDict[heater]['temps']['low'])
                # Check if the current temp is lower than the stored lowTemp
                if test is True:
                    # Call self.runaway_triggered and pass the required details
                    self.runaway_triggered(heater,
                                           self.heaterDict[heater]['temps']['set'],
                                           self.heaterDict[heater]['temps']['current'],
                                           'under')
                    # Log that we caught a thermal runaway
                    self.logger.critical(self.runaway_message.format(h=heater,
                                                                     c=self.heaterDict[heater]['temps']['current'],
                                                                     s=self.heaterDict[heater]['temps']['set'],
                                                                     t="under"))
                    self.heaterDict[heater]['thermalLowCount'] = 0
                else:
                    # Set stored lowTemp to current temp
                    self.heaterDict[heater]['temps']['low'] = float(self.heaterDict[heater]['temps']['current'])
                    # Set thermalLowCount to 1 (warning level)
                    self.heaterDict[heater]['thermalLowCount'] = 1

            # Check if thermalHighCount is equal to 1 (warning level)
            if int(self.heaterDict[heater]['thermalHighCount']) == 1:
                # Log that a thermalHighWarning has been triggered
                self.logger.warning('thermalHighCount == 1 for {h}'.format(h=heater))
                # Check whether the thermalAlert should be triggered if the current temperature
                # is equal to the high temp and set the test variable accordingly
                if self._settings.get(['triggerOnEqual']) is True:
                    test = float(self.heaterDict[heater]['temps']['current']) >= float(self.heaterDict[heater]['temps']['high'])
                else:
                    test = float(self.heaterDict[heater]['temps']['current']) > float(self.heaterDict[heater]['temps']['high'])
                # Check if the current temp is greater than or equal to the stored highTemp
                if test is True:
                    # Delay to avoid immediately triggering a thermal runaway alert
                    time.sleep(int(self.heaterDict[heater]['delay']))
                    # Set thermalHighCount to 2 (alert level)
                    self.heaterDict[heater]['thermalHighCount'] = 2
                else:
                    # Set stored highTemp to current temp
                    self.heaterDict[heater]['temps']['high'] = float(self.heaterDict[heater]['temps']['current'])
                    # Set thermalHighCount to 0
                    self.heaterDict[heater]['thermalHighCount'] = 0

            # Check if thermalLowCount is equal to 1 (warning level)
            if int(self.heaterDict[heater]['thermalLowCount']) == 1:
                # Log that a thermalLowWarning has been triggered
                self.logger.warning('thermalLowCount == 1 for {h}'.format(h=heater))
                # Check whether the thermalAlert should be triggered if the current temperature
                # is equal to the low temp and set the test variable accordingly
                if self._settings.get(['triggerOnEqual']) is True:
                    test = float(self.heaterDict[heater]['temps']['current']) <= float(self.heaterDict[heater]['temps']['low'])
                else:
                    test = float(self.heaterDict[heater]['temps']['current']) < float(self.heaterDict[heater]['temps']['low'])
                # Check if the current temp is less than or equal to the stored lowTemp
                if test is True:
                    # Delay to avoid immediately triggering a thermal runaway alert
                    time.sleep(int(self.heaterDict[heater]['delay']))
                    # Set thermalLowCount to 2 (alert level)
                    self.heaterDict[heater]['thermalLowCount'] = 2
                else:
                    # Set stored lowTemp to current temp
                    self.heaterDict[heater]['temps']['low'] = float(self.heaterDict[heater]['temps']['current'])
                    # Set thermalLowCount to 0
                    self.heaterDict[heater]['thermalLowCount'] = 0

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
