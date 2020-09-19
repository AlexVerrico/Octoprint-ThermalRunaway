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

        global heaterList
        heaterDict = dict()
        heaterDict['B'] = {'highTemp': 0.0, 'lowTemp': 0.0, 'thermalHighWarning': False, 'thermalLowWarning': False, 'thermalHighAlert': False, 'thermalLowAlert': False}
        heaterDict['T0'] = {'highTemp': 0.0, 'lowTemp': 0.0, 'thermalHighWarning': False, 'thermalLowWarning': False, 'thermalHighAlert': False, 'thermalLowAlert': False}
##        # create global variables for storing bed temps and thermal warnings
##        global bHighTemp
##        global bLowTemp
##        global bThermalHighWarning
##        global bThermalHighAlert
##        global bThermalLowWarning
##        global bThermalLowAlert
##
##        # create global variables for storing tool temps and thermal warnings
##        global tHighTemp
##        global tLowTemp
##        global tThermalHighWarning
##        global tThermalHighAlert
##        global tThermalLowWarning
##        global tThermalLowAlert

##        # set initial values of bed variables
##        bHighTemp = 0.0
##        bLowTemp = 0.0
##        bThermalHighWarning = False
##        bThermalHighAlert = False
##        bThermalLowWarning = False
##        bThermalLowAlert = False
##
##        # set initial values of tool variables
##        tHighTemp = 0.0
##        tLowTemp = 0.0
##        tThermalHighWarning = False
##        tThermalHighAlert = False
##        tThermalLowWarning = False
##        tThermalLowAlert = False

        # log that we have completed this function successfully.
        _logger.debug('reached end of on_after_startup')
        
        return
    
    ##~~ SettingsPlugin mixin
    
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

##        # set the necessary variables to be global
##        global bHighTemp
##        global bLowTemp
##        global bThermalHighWarning
##        global bThermalHighAlert
##        global bThermalLowWarning
##        global bThermalLowAlert
##        global tHighTemp
##        global tLowTemp
##        global tThermalHighWarning
##        global tThermalHighAlert
##        global tThermalLowWarning
##        global tThermalLowAlert
        global heaterDict
        heaterList = ('B', 'T0')
##        B = heaterList['B']
##        T0 = heaterList['T0']
        
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

        delaysDict = dict()
        delaysDict['B'] = int(bDelayStr)
        delaysDict['T0'] = int(tDelayStr)
        
        bTemps = temps['B']
        _logger.debug('bTemps: %s' % bTemps)
        tTemps = temps['T0']
        _logger.debug('tTemps: %s' % tTemps)
        tempsDict = dict()
        tempsDict['B']['current'] = bTemps[0]
        #bCurrentTemp = bTemps[0]
        tempsDict['T0']['current'] = tTemps[0]
        #tCurrentTemp = tTemps[0]
        tempsDict['B']['set'] = bTemps[1]
        tempsDict['T0']['set'] = tTemps[1]
        tempsDict['B']['diff'] = bMaxDiff
        tempsDict['T0']['diff'] = tMaxDiff
        tempsDict['B']['maxOff'] = bmaxOffTemp
        tempsDict['T0']['maxOff'] = tmaxOffTemp
        #bSetTemp = bTemps[1]
        #tSetTemp = tTemps[1]

        _logger.debug("Got all values. Beginning to run through if statements...")


        ## Check if thermalHighAlert = True
        for i in heaterList:
            if (heaterDict[i]['thermalHighAlert'] == True):
                _logger.debug('%s thermalHighAlert = True' % i)
                if (tempsDict[i]['current'] > heaterDict[i]['highTemp']):
                    self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to %s OverTemp" % i)
                    self._printer.commands(emergencyGCode)
                    _logger.debug('%s currentTemp > %s highTemp. Sent emergencyGCode to printer' % (i, i))
                else:
                    heaterDict[i]['highTemp'] = tempsDict[i]['current']
                heaterDict[i]['thermalHighAlert'] = False
                _logger.debug('set %s thermalHighAlert to False' % i)

            ## Check if thermalLowAlert = True
            if (heaterDict[i]['thermalLowAlert'] == True):
                _logger.debug('%s thermalLowAlert = True' % i)
                if (tempsDict[i]['current'] < heaterDict[i]['lowTemp']):
                    self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to %s UnderTemp" %s)
                    self._printer.commands(emergencyGCode)
                    _logger.debug('%s currentTemp < %s lowTemp. Sent emergencyGCode to printer' % (i, i))
                else:
                    heaterDict[i]['lowTemp'] = tempsDict[i]['current']
                heaterDict[i]['thermalLowAlert'] = False
                _logger.debug('set %s thermalLowAlert to False' % i)

            ## Check if thermalHighWarning is set to True
            if (heaterDict[i]['thermalHighWarning'] == True):
                _logger.debug('%s thermalHighWarning = True' % i)
                if (tempsDict[i]['current'] > heaterDict[i]['highTemp']):
                    _logger.debug('setting %s ThermalHighAlert to True...' % i)
                    time.sleep(delaysDict[i])
                    heaterDict[i]['thermalHighAlert'] = True
                    _logger.debug('set %s thermalHighAlert to True' % i)
                else:
                    heaterDict[i]['highTemp'] = tempsDict[i]['current']
                heaterDict[i]['thermalHighWarning'] = False
                _logger.debug('set %s thermalHighWarning to False' % i)
                
            ## Check if thermalLowWarning is set to True    
            if (heaterDict[i]['thermalLowWarning'] == True):
                _logger.debug('%s thermalLowWarning = True' % i)
                if (tempsDict[i]['current'] < heaterDict[i]['lowTemp']):
                    _logger.debug('setting %s thermalLowAlert to True...' % i)
                    time.sleep(delaysDict[i])
                    heaterDict[i]['thermalLowAlert'] = True
                    _logger.debug('set %s thermalLowAlert to True' % i)
                else:
                    heaterDict[i]['lowTemp'] = tempsDict[i]['current']
                heaterDict[i]['thermalLowWarning'] = False
                _logger.debug('set %s thermalLowWarning to False' % i)

            ## If the heater is turned on then set maxTemp and minTemp
            if (tempsDict[i]['set'] > 0.0):
                tempsDict[i]['max'] = tempsDict[i]['set'] + tempsDict[i]['diff']
                _logger.debug('%s maxTemp = %s' % (i, tempsDict[i]['max']))
                tempsDict[i]['min'] = tempsDict[i]['set'] - tempsDict[i]['diff']
                _logger.debug('%s minTemp = %s' % (i, tempsDict[i]['min']))

                ## If the current temp of the heater is lower than the min allowed temp then set thermalLowWarning to True
                if (tempsDict[i]['current'] < tempsDict[i]['min']):
                    heaterDict[i]['lowTemp'] = tempsDcit[i]['current']
                    _logger.debug('%s currentTemp < %s lowTemp, set %s lowTemp to %s currentTemp. New %s lowTemp = %s' % (i, i, i, i, i, heaterDict[i]['lowTemp'])
                    heaterDict[i]['thermalLowWarning'] = True
                    _logger.debug('set %s thermalLowWarning to True' % i)

            ## If the bed is turned off then set bMaxTemp to bMaxOffTemp
            if (tempsDict[i]['set'] <= 0.0):
                tempsDict[i]['max'] = tempsDict[i]['maxOff']
                tempsDict[i]['min'] = 0.0

            ## If the current temp of the heater is higher than the max allowed temp then set thermalHighWarning to True
            if (tempsDict[i]['current'] > tempsDict[i]['max']):
                heaterDict[i]['highTemp'] = tempsDict[i]['current']
                _logger.debug('%s currentTemp > %s maxTemp, set %s highTemp to %s currentTemp. New %s highTemp = %s' % (i, i, i, i, i, bHighTemp))
                heaterDict[i]['thermalHighWarning'] = True
                _logger.debug('set %s thermalHighWarning to True' % i)
        
##        ## Check if bThermalHighAlert = True
##        if (bThermalHighAlert == True):
##            _logger.debug('bThermalHighAlert = True')
##            if (bCurrentTemp > bHighTemp):
##                self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to bed OverTemp")
##                self._printer.commands(emergencyGCode)
##                _logger.debug('bCurrentTemp > bHighTemp. Sent emergencyGCode to printer')
##            else:
##                bHighTemp = bCurrentTemp
##            bThermalHighAlert = False
##            _logger.debug('set bThermalHighAlert to False')



        

##        ## Check if bThermalLowAlert = True
##        if (bThermalLowAlert == True):
##            _logger.debug('bThermalLowAlert = True')
##            if (bCurrentTemp < bLowTemp):
##                self._printer.commands("M117 plugin.ThermalRunaway sent emergencyGCode due to bed UnderTemp")
##                self._printer.commands(emergencyGCode)
##                _logger.debug('bCurrentTemp < bLowTemp. Sent emergencyGCode to printer')
##            else:
##                bLowTemp = bCurrentTemp
##            bThermalLowAlert = False
##            _logger.debug('set bThermalLowAlert to False')

            

        

##        ## Check if tThermalHighWarning is set to True
##        if (tThermalHighWarning == True):
##            _logger.debug('tThermalHighWarning = True')
##            if (tCurrentTemp > tHighTemp):
##                _logger.debug('setting tThermalHighAlert to True...')
##                time.sleep(tDelay)
##                tThermalHighAlert = True
##                _logger.debug('set tThermalHighAlert to True')
##            else:
##                tHighTemp = tCurrentTemp
##            tThermalHighWarning = False
##            _logger.debug('set tThermalHighWarning to False')





##        ## Check if tThermalLowWarning is set to True
##        if (tThermalLowWarning == True):
##            _logger.debug('tThermalLowWarning = True')
##            if (tCurrentTemp < tLowTemp):
##                _logger.debug('setting tThermalLowAlert to True...')
##                time.sleep(tDelay)
##                tThermalLowAlert = True
##                _logger.debug('set tThermalLowAlert to True')
##            else:
##                tLowTemp = tCurrentTemp
##            tThermalLowWarning = False
##            _logger.debug('set tThermalLowWarning to False')



        



##        ## If the hotend is turned on then set tMaxTemp and tMinTemp
##        if (tSetTemp > 0.0):
##            tMaxTemp = tSetTemp + tMaxDiff
##            _logger.debug('tMaxTemp = %s' % tMaxTemp)
##            tMinTemp = tSetTemp - tMaxDiff
##            _logger.debug('tMinTemp = %s' % tMinTemp)
##
##            ## If the current temp of the hotend is lower than the max allowed temp then set bThermalHighWarning to True
##            if (tCurrentTemp < tMinTemp):
##                tLowTemp = tCurrentTemp
##                _logger.debug('tCurrentTemp < tLowTemp, set tLowTemp to tCurrentTemp. New tLowTemp = %s' % tLowTemp)
##                tThermalLowWarning = True
##                _logger.debug('set tThermalLowWarning to True')

##        ## If the hotend is turned off then set tMaxTemp to tMaxOffTemp
##        if (tSetTemp <= 0.0):
##            tMaxTemp = tMaxOffTemp
##            tMinTemp = 0.0

        

##        ## If the current temp of the hotend is higher than the max allowed temp then set tThermalHighWarning to True
##        if (tCurrentTemp > tMaxTemp):
##            tHighTemp = tCurrentTemp
##            _logger.debug('tCurrentTemp > tMaxTemp, set tHighTemp to tCurrentTemp. New tHighTemp = %s' % tHighTemp)
##            tThermalHighWarning = True
##            _logger.debug('set tThermalHighWarning to True')



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
