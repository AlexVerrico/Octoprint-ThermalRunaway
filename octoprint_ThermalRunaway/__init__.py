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
        global bThermalWarning
        bHighTemp = 0.0
        bThermalWarning = False
        _logger.debug('bHighTemp = ')
        _logger.debug(bHighTemp)
        _logger.debug('reached end of on_after_startup')
        return
    
    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            emergencyGcode="M112"
        )

    ##~~ TemplatePlugin mixin

##    def get_template_configs(self):
##        return [
##            dict(type="settings", custom_bindings=False)
##        ]

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
        global bHighTemp
        global bThermalWarning
        theEmergencyGcode = _self.settings.get(["emergencyGcode"])
        _logger.debug('emergencyGcode: ')
        _logger.debug(theEmergencyGcode)
        _logger.debug('reached start of check_temps')
        emergencyGCode = "M112"
        TMaxOffTemp = 250.0
        bMaxOffTemp = 60
        TMaxDiff = 25.0
        bMaxDiff = 10
        bTemps = temps["B"]
        TTemps = temps["T0"]
        bCurrentTemp = bTemps[0]
        _logger.debug('bCurrentTemp = ')
        _logger.debug(bCurrentTemp)
        TCurrentTemp = TTemps[0]
        bSetTemp = bTemps[1]
        _logger.debug('bSetTemp = ')
        _logger.debug(bSetTemp)
        TSetTemp = TTemps[1]
        _logger.debug('old bHighTemp = ')
        _logger.debug(bHighTemp)
        if (bThermalWarning == True):
            _logger.debug('bThermalWarning = True')
            if (bCurrentTemp > bHighTemp):
                self._printer.commands(emergencyGCode)
                _logger.debug('bCurrentTemp > bHighTemp. Called killPrint')
            else:
                bHighTemp = bCurrentTemp
            bThermalWarning = False
            _logger.debug('set bThermalWarning to False')
        if (bSetTemp > 0.0):
            bMaxTemp = bSetTemp + bMaxDiff
            _logger.debug('bMaxTemp = ')
            _logger.debug(bMaxTemp)
        if (TSetTemp > 0.0):
            TMaxTemp = TSetTemp + TMaxDiff
            _logger.debug('TMaxTemp = ')
            _logger.debug(TMaxTemp)
        if (bCurrentTemp > bMaxTemp):
            bHighTemp = bCurrentTemp
            _logger.debug('bCurrentTemp > bMaxTemp, set bHighTemp to bCurrentTemp. New bHighTemp = ')
            _logger.debug(bHighTemp)
            bThermalWarning = True
            _logger.debug('set bThermalWarning to True')
        if (TCurrentTemp > TMaxTemp):
            _logger.debug('KillPrint()')
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
                displayName="Thermalrunaway Plugin",
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
