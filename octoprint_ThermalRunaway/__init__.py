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

_logger = logging.getLogger('octoprint.plugins.ThermalRunaway')

class ThermalRunawayPlugin(octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.AssetPlugin,
                           octoprint.plugin.TemplatePlugin):

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
        )

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/ThermalRunaway.js"],
            css=["css/ThermalRunaway.css"],
            less=["less/ThermalRunaway.less"]
        )

    ##~~ Temperatures received hook

    def check_temps(self, temps):
        _logger.debug('reached start of check_temps')
        
        BMaxAbove = "10"
        T0MaxAbove = "25"

        BMaxOffTemp = "50"
        T0MaxOffTemp = "250"
        
        BTemps = temps["B"]
        BSetTemp = BTemps[1]
        BSetTempInt = round(BSetTemp)
        BCurrentTemp = BTemps[0]
        BCurrentTempInt = round(BCurrentTemp)

        if (BSetTemp > "0"):
            BMaxTemp = BSetTemp + BMaxAbove
        else:
            BMaxTemp = BMaxOffTemp

        T0Temps = temps["T0"]
        T0SetTemp = T0Temps[1]
        T0CurrentTemp = T0Temps[0]
##        if (T0SetTemp > "0"):
##            T0MaxTemp = T0SetTemp + T0MaxAbove
##        else:
##            T0MaxTemp = T0MaxOffTemp
        _logger.debug('BSetTemp:')
        _logger.debug(BSetTemp)
        _logger.debug('BCurrentTemp:')
        _logger.debug(BCurrentTemp)
        _logger.debug('Current Temp rounded:')
        _logger.debug(BCurrentTempInt)
        _logger.debug('BMaxTemp:')
        _logger.debug(BMaxTemp)
        if (BCurrentTemp > BMaxTemp):
            _logger.debug('Bed above MaxTemp ------------------------------------------------------------------------------------')
##        if (T0CurrentTemp > T0MaxTemp):
##            _logger.debug('T0 above MaxTemp ------------------------------------------------------------------------------------')
        

    def get_temps(self, comm, parsed_temps):
        temps = parsed_temps
        if (temps == parsed_temps):
            _logger.debug('Spawning new thread...')
            t = threading.Timer(0,self.check_temps,[temps])
            t.start()
            _logger.debug('Spawned new thread.')
        return parsed_temps
    
##                BTemp = parsed_temps["B"]
##                _logger.debug('B tuple = ');
##                _logger.debug(BTemp)
##                BCurrentTemp = BTemp[0]
##                _logger.debug('B Current Temp = ')
##                _logger.debug(BCurrentTemp)
##                BSetTemp = BTemp[1]
##                _logger.debug('B Set Temp = ')
##                _logger.debug(BSetTemp)

    
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
