# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin # Import the core octoprint plugin components
import logging          # Import logging to allow for easier debugging
import threading        # Import threading. This is used to process the temps asynchronously so that we don't block octoprints communications with the printer
import time             # Import time. This is so that we can add delays to parts of the code

_logger = logging.getLogger('octoprint.plugins.ThermalRunaway')

class ThermalRunawayPlugin(octoprint.plugin.StartupPlugin,
                           octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.TemplatePlugin):
    def on_after_startup(self):

        # create global variables for storing bed temps and thermal warnings
        global bHighTemp
        global bLowTemp
        global bThermalHighWarning
        global bThermalHighAlert
        global bThermalLowWarning
        global bThermalLowAlert

        # create global variables for storing tool temps and thermal warnings
        global tHighTemp
        global tLowTemp
        global tThermalHighWarning
        global tThermalHighAlert
        global tThermalLowWarning
        global tThermalLowAlert

        # set initial values of bed variables
        bHighTemp = 0.0
        bLowTemp = 0.0
        bThermalHighWarning = False
        bThermalHighAlert = False
        bThermalLowWarning = False
        bThermalLowAlert = False

        # set initial values of tool variables
        tHighTemp = 0.0
        tLowTemp = 0.0
        tThermalHighWarning = False
        tThermalHighAlert = False
        tThermalLowWarning = False
        tThermalLowAlert = False

        # log that we have completed this function successfully.
        _logger.debug('reached end of on_after_startup')
        
        return
    
    ##~~ SettingsPlugin mixin
    
    def get_settings_defaults(self):
        # Define default settings for this plugin
        return dict(
            emergencyGcode="M112",
            bMaxDiff="10",
            bMaxOffTemp="30",
            tMaxDiff="20",
            tMaxOffTemp="30",
            tDelay="25",
            bDelay="20"
        )

    ##~~ TemplatePlugin mixin

    def get_template_configs(self):
        # Tell octoprint that we have a settings page
        return [
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ Temperatures received hook

    def check_temps(self, temps):
        _logger.debug('Spawned new thread.') # Log that we spawned the new thread
        _logger.debug('Reached start of check_temps') # Log that we have reached the start of check_temps

        # set the necessary variables to be global
        global bHighTemp
        global bLowTemp
        global bThermalHighWarning
        global bThermalHighAlert
        global bThermalLowWarning
        global bThermalLowAlert
        global tHighTemp
        global tLowTemp
        global tThermalHighWarning
        global tThermalHighAlert
        global tThermalLowWarning
        global tThermalLowAlert

        # Get all settings values
        emergencyGCode = self._settings.get(["emergencyGcode"])
        tMaxOffTempStr = self._settings.get(["tMaxOffTemp"])
        bMaxOffTempStr = self._settings.get(["bMaxOffTemp"])
        bDelayStr = self._settings.get(["bDelay"])
        tDelayStr = self._settings.get(["tDelay"])
        tMaxDiffStr = self._settings.get(["tMaxDiff"])
        bMaxDiffStr = self._settings.get(["bMaxDiff"])
        _logger.debug('got all values from settings.')
        bMaxDiff = float(bMaxDiffStr)
        tMaxDiff = float(tMaxDiffStr)
        bMaxOffTemp = float(bMaxOffTempStr)
        tMaxOffTemp = float(tMaxOffTempStr)
        _logger.debug('bMaxDiff = %s, tMaxDiff = %s, bMaxOffTemp = %s, tMaxOffTemp = %s' % (bMaxDiff, tMaxDiff, bMaxOffTemp, tMaxOffTemp)) # Log values to aid in debugging
        
        bDelay = int(bDelayStr)
        tDelay = int(tDelayStr)
        
        bTemps = temps["B"]
        _logger.debug('bTemps: %s' % bTemps)
        tTemps = temps["T0"]
        _logger.debug('tTemps: %s' % tTemps)
        
        bCurrentTemp = bTemps[0]
        tCurrentTemp = tTemps[0]
        
        bSetTemp = bTemps[1]
        tSetTemp = tTemps[1]

        _logger.debug("Got all values. Beginning to run through if statements...")


        ## Check if tThermalHighAlert = True
        if (tThermalHighAlert == True):
            _logger.debug('tThermalHighAlert = True')
            if (tCurrentTemp > tHighTemp):
                self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to tool OverTemp")
                self._printer.commands(emergencyGCode)
                _logger.debug('tCurrentTemp > tHighTemp. Sent emergencyGCode to printer')
            else:
                tHighTemp = tCurrentTemp
            tThermalHighAlert = False
            _logger.debug('set tThermalHighAlert to False')

        ## Check if bThermalHighAlert = True
        if (bThermalHighAlert == True):
            _logger.debug('bThermalHighAlert = True')
            if (bCurrentTemp > bHighTemp):
                self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to bed OverTemp")
                self._printer.commands(emergencyGCode)
                _logger.debug('bCurrentTemp > bHighTemp. Sent emergencyGCode to printer')
            else:
                bHighTemp = bCurrentTemp
            bThermalHighAlert = False
            _logger.debug('set bThermalHighAlert to False')



        ## Check if tThermalLowAlert = True
        if (tThermalLowAlert == True):
            _logger.debug('tThermalLowAlert = True')
            if (tCurrentTemp < tLowTemp):
                self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to tool UnderTemp")
                self._printer.commands(emergencyGCode)
                _logger.debug('tCurrentTemp < tLowTemp. Sent emergencyGCode to printer')
            else:
                tLowTemp = tCurrentTemp
            tThermalLowAlert = False
            _logger.debug('set tThermalLowAlert to False')

        ## Check if bThermalLowAlert = True
        if (bThermalLowAlert == True):
            _logger.debug('bThermalLowAlert = True')
            if (bCurrentTemp < bLowTemp):
                self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to bed UnderTemp")
                self._printer.commands(emergencyGCode)
                _logger.debug('bCurrentTemp < bLowTemp. Sent emergencyGCode to printer')
            else:
                bLowTemp = bCurrentTemp
            bThermalLowAlert = False
            _logger.debug('set bThermalLowAlert to False')

            

        ## Check if bThermalHighWarning is set to True
        if (bThermalHighWarning == True):
            _logger.debug('bThermalHighWarning = True')
            if (bCurrentTemp > bHighTemp):
                _logger.debug('setting bThermalHighAlert to True...')
                time.sleep(bDelay)
                bThermalHighAlert = True
                _logger.debug('set tThermalHighAlert to True')
            else:
                bHighTemp = bCurrentTemp
            bThermalHighWarning = False
            _logger.debug('set bThermalHighWarning to False')

        ## Check if tThermalHighWarning is set to True
        if (tThermalHighWarning == True):
            _logger.debug('tThermalHighWarning = True')
            if (tCurrentTemp > tHighTemp):
                _logger.debug('setting tThermalHighAlert to True...')
                time.sleep(tDelay)
                tThermalHighAlert = True
                _logger.debug('set tThermalHighAlert to True')
            else:
                tHighTemp = tCurrentTemp
            tThermalHighWarning = False
            _logger.debug('set tThermalHighWarning to False')



        ## Check if bThermalLowWarning is set to True
        if (bThermalLowWarning == True):
            _logger.debug('bThermalLowWarning = True')
            if (bCurrentTemp < bLowTemp):
                _logger.debug('setting bThermalLowAlert to True...')
                time.sleep(bDelay)
                bThermalLowAlert = True
                _logger.debug('set tThermalLowAlert to True')
            else:
                bLowTemp = bCurrentTemp
            bThermalLowWarning = False
            _logger.debug('set bThermalLowWarning to False')

        ## Check if tThermalLowWarning is set to True
        if (tThermalLowWarning == True):
            _logger.debug('tThermalLowWarning = True')
            if (tCurrentTemp < tLowTemp):
                _logger.debug('setting tThermalLowAlert to True...')
                time.sleep(tDelay)
                tThermalLowAlert = True
                _logger.debug('set tThermalLowAlert to True')
            else:
                tLowTemp = tCurrentTemp
            tThermalLowWarning = False
            _logger.debug('set tThermalLowWarning to False')



        ## If the bed is turned on then set bMaxTemp and bMinTemp
        if (bSetTemp > 0.0):
            bMaxTemp = bSetTemp + bMaxDiff
            _logger.debug('bMaxTemp = %s' % bMaxTemp)
            bMinTemp = bSetTemp - bMaxDiff
            _logger.debug('bMinTemp = %s' % bMinTemp)

            ## If the current temp of the bed is lower than the max allowed temp then set bThermalHighWarning to True
            if (bCurrentTemp < bMinTemp):
                bLowTemp = bCurrentTemp
                _logger.debug('bCurrentTemp < bLowTemp, set bLowTemp to bCurrentTemp. New bLowTemp = %s' % bLowTemp)
                bThermalLowWarning = True
                _logger.debug('set bThermalLowWarning to True')

        ## If the bed is turned off then set bMaxTemp to bMaxOffTemp
        if (bSetTemp <= 0.0):
            bMaxTemp = bMaxOffTemp
            bMinTemp = 0.0

        ## If the hotend is turned on then set tMaxTemp and tMinTemp
        if (tSetTemp > 0.0):
            tMaxTemp = tSetTemp + tMaxDiff
            _logger.debug('tMaxTemp = %s' % tMaxTemp)
            tMinTemp = tSetTemp - tMaxDiff
            _logger.debug('tMinTemp = %s' % tMinTemp)

            ## If the current temp of the hotend is lower than the max allowed temp then set bThermalHighWarning to True
            if (tCurrentTemp < tMinTemp):
                tLowTemp = tCurrentTemp
                _logger.debug('tCurrentTemp < tLowTemp, set tLowTemp to tCurrentTemp. New tLowTemp = %s' % tLowTemp)
                tThermalLowWarning = True
                _logger.debug('set tThermalLowWarning to True')

        ## If the hotend is turned off then set tMaxTemp to tMaxOffTemp
        if (tSetTemp <= 0.0):
            tMaxTemp = tMaxOffTemp
            tMinTemp = 0.0

        ## If the current temp of the bed is higher than the max allowed temp then set bThermalHighWarning to True
        if (bCurrentTemp > bMaxTemp):
            bHighTemp = bCurrentTemp
            _logger.debug('bCurrentTemp > bMaxTemp, set bHighTemp to bCurrentTemp. New bHighTemp = %s' % bHighTemp)
            bThermalHighWarning = True
            _logger.debug('set bThermalHighWarning to True')

        ## If the current temp of the hotend is higher than the max allowed temp then set tThermalHighWarning to True
        if (tCurrentTemp > tMaxTemp):
            tHighTemp = tCurrentTemp
            _logger.debug('tCurrentTemp > tMaxTemp, set tHighTemp to tCurrentTemp. New tHighTemp = %s' % tHighTemp)
            tThermalHighWarning = True
            _logger.debug('set tThermalHighWarning to True')



        ## Log that we have reached the end of check_temps
        _logger.debug('Reached end of check_temps')
        return


    ##~~ Temperatures hook

    def get_temps(self, comm, parsed_temps):
        _logger.debug('Temps received') # Log that temps have been received
        temps = parsed_temps
        if (temps == parsed_temps):
            _logger.debug('Spawning new thread...') # Log that we are attempting to spawn a new thread to process the received temps in
            t = threading.Timer(0,self.check_temps,[temps]) # Create a threading Timer object
            t.start() # Start the threading Timer object
        return parsed_temps # return the temps to octoprint

    
    ##~~ Softwareupdate hook

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


__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ThermalRunawayPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.get_temps
    }
