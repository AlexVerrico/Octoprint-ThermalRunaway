# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import logging
import threading
import time

_logger = logging.getLogger('octoprint.plugins.ThermalRunaway')

class ThermalRunawayPlugin(octoprint.plugin.StartupPlugin,
                           octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.TemplatePlugin):
    def on_after_startup(self):
        global bHighTemp
        global bThermalHighWarning
        global tHighTemp
        global tThermalHighWarning
        bHighTemp = 0.0
        bThermalHighWarning = False
        tHighTemp = 0.0
        tThermalHighWarning = False
##        _logger.debug('bHighTemp = ')
##        _logger.debug(bHighTemp)
        _logger.debug('reached end of on_after_startup')
        return
    
    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            emergencyGcode="M112",
            bMaxDiff="10",
            bMaxOffTemp="20",
            tMaxDiff="20",
            tMaxOffTemp="20"
        )

    ##~~ TemplatePlugin mixin

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ AssetPlugin mixin

##    def get_assets(self):
##        # Define your plugin's asset files to automatically include in the
##        # core UI here.
##        return dict(
##            js=["js/ThermalRunaway.js"],
##            css=["css/ThermalRunaway.css"],
##            less=["less/ThermalRunaway.less"]
##        )


    ##~~ Temperatures received hook

    def check_temps(self, temps):
        _logger.debug('Reached start of check_temps')
        
        global bHighTemp
        global bThermalHighWarning
        global tHighTemp
        global tThermalHighWarning
        
        emergencyGCode = self._settings.get(["emergencyGcode"])
        
        tMaxOffTempStr = self._settings.get(["tMaxOffTemp"])
        bMaxOffTempStr = self._settings.get(["bMaxOffTemp"])
        
        tMaxDiffStr = self._settings.get(["tMaxDiff"])
        bMaxDiffStr = self._settings.get(["bMaxDiff"])

        bMaxDiff = float(bMaxDiffStr)
        tMaxDiff = float(tMaxDiffStr)
        bMaxOffTemp = float(bMaxOffTempStr)
        tMaxOffTemp = float(btMaxOffTempStr)
        
        bTemps = temps["B"]
##        tTemps = temps["T0"]
        tTemps = bTemps
        
        bCurrentTemp = bTemps[0]
##        _logger.debug('bCurrentTemp = ')
##        _logger.debug(bCurrentTemp)
        tCurrentTemp = tTemps[0]
        
        bSetTemp = bTemps[1]
##        _logger.debug('bSetTemp = ')
##        _logger.debug(bSetTemp)
        tSetTemp = tTemps[1]

        _logger.debug("Got all values. Beginning to run through if statements...")

        ## Check if bThermalWarning is set to True
        if (bThermalHighWarning == True):
            _logger.debug('bThermalHighWarning = True')
            if (bCurrentTemp > bHighTemp):
                self._printer.commands(emergencyGCode)
                _logger.debug('bCurrentTemp > bHighTemp. Sent emergencyGCode to printer')
            else:
                bHighTemp = bCurrentTemp
            bThermalHighWarning = False
            _logger.debug('set bThermalHighWarning to False')

        ## Check if tThermalWarning is set to True
        if (tThermalHighWarning == True):
            _logger.debug('tThermalHighWarning = True')
            if (tCurrentTemp > tHighTemp):
                self._printer.commands(emergencyGCode)
                _logger.debug('tCurrentTemp > tHighTemp. Sent emergencyGCode to printer')
            else:
                tHighTemp = tCurrentTemp
            tThermalHighWarning = False
            _logger.debug('set tThermalHighWarning to False')

        ## Check if the bed target temp is set to something greater than 0
        if (bSetTemp > 0.0):
            bMaxTemp = bSetTemp + bMaxDiff
            _logger.debug('bMaxTemp = ')
            _logger.debug(bMaxTemp)
            bMinTemp = bSetTemp - bMaxDiff
            _logger.debug('bMinTemp = ')
            _logger.debug(bMinTemp)
            
        ## Check if the tool target temp is set to something greater than 0
        if (tSetTemp > 0.0):
            tMaxTemp = tSetTemp + tMaxDiff
            _logger.debug('tMaxTemp = ')
            _logger.debug(tMaxTemp)
            tMinTemp = tSetTemp - tMaxDiff
            _logger.debug('tMinTemp = ')
            _logger.debug(tMinTemp)

        ##
        if (bCurrentTemp > bMaxTemp):
            bHighTemp = bCurrentTemp
            _logger.debug('bCurrentTemp > bMaxTemp, set bHighTemp to bCurrentTemp. New bHighTemp = ')
            _logger.debug(bHighTemp)
            bThermalHighWarning = True
            _logger.debug('set bThermalHighWarning to True')

        ##
        if (tCurrentTemp > tMaxTemp):
            tHighTemp = tCurrentTemp
            _logger.debug('tCurrentTemp > tMaxTemp, set tHighTemp to tCurrentTemp. New tHighTemp = ')
            _logger.debug(tHighTemp)
            tThermalHighWarning = True
            _logger.debug('set tThermalHighWarning to True')
            
        ##
        _logger.debug('Reached end of check_temps')
        return

    def get_temps(self, comm, parsed_temps):
        temps = parsed_temps
        if (temps == parsed_temps):
            _logger.debug('Spawning new thread...')
            t = threading.Timer(0,self.check_temps,[temps])
            t.start()
            _logger.debug('Spawned new thread.')
        return parsed_temps

    
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


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
##__plugin_name__ = "Thermalrunaway Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
__plugin_pythoncompat__ = ">=3,<4" # only python 3
#__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ThermalRunawayPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.get_temps
    }
