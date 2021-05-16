[![Donate](https://img.shields.io/badge/Donate%3A-Buy%20Me%20A%20Coffee-brightgreen)](https://www.buymeacoffee.com/AlexVerrico)

# Thermal Runaway

#### An Octoprint plugin to provide some basic thermal runaway protection.
__What this plugin does:__ <br/>
Sends the configured GCode command when a heater on the printer is outside of configured maximum/minimum temperatures and not heading towards the set temperature<br/>
Calls any plugins registered for the hooks provided (see below)<br/><br/>

__What this plugin _does not_ do:__<br/>
This plugin does not stop a thermal runaway, it just sends a GCode command and calls a couple plugin hooks, and it is up to you to find a way to handle that GCode command or plugin hook(s) appropriately. As such, *I strongly recommend that you __watch your printer at all times__*


## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/AlexVerrico/Octoprint-ThermalRunaway/archive/master.zip


## Configuration
This plugin has the following configuration options:

![](extras/img/ThermalRunaway-config.png)

### Disclaimer:
I, the plugin author, strongly recommend that you __NEVER__ leave you printer unattended while powered. This plugin is not a replacement for [firmware thermal runaway detection](https://3dprinting.stackexchange.com/a/8467). I, the plugin author, __cannot__ be held responsible for any damage to equipment or injuries that may arise from leaving your 3D Printer unattended. I, the plugin author, make no guarantees that this plugin will work or continue to work.

## Hooks
This plugin provides the following three hooks:  
- `octoprint.plugin.ThermalRunaway.runaway_triggered`: Called when any thermal runaway is triggered  
- `octoprint.plugin.ThermalRunaway.over_runaway_triggered`: Called when an over temperature thermal runaway is triggered  
- `octoprint.plugin.ThermalRunaway.under_runaway_triggered`: Called when an under temperature thermal runaway is triggered  

All three of these hooks are called with the following parameters:  
`heater_id, set_temp, current_temp`  
heater_id is the id of the heater (usually something like T0 or B)  
set_temp is the target temperature for the heater  
current_temp is the reported temperature of the heater  

My plugin [Octoprint-TR_test](https://github.com/AlexVerrico/Octoprint-TR_Test) provides an example of how to register for a hook.

## Contributing

All Pull Requests **<u>MUST</u>** be made to the devel branch, otherwise they will be ignored.<br/>
Please ensure that you follow the style of the code (eg. use spaces not tabs, etc)<br/>
Please open an issue to discuss what features you want to add / bugs you want to fix _before_ working on them, as this avoids 2 people submitting a PR for the same feature/bug.

**If you find this plugin useful, please consider supporting my work through [Buy Me A Coffee](https://www.buymeacoffee.com/AlexVerrico)**
