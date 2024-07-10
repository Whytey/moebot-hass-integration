# MoeBot Home Assistant Integration

Provides the following:

- A [Lawn Mower](https://www.home-assistant.io/integrations/lawn_mower/) component for control of your MoeBot.
- Further controls to manage whether the MoeBot continues to mow during rain and how long to mow for.
- Ability to alter the multi-zone configuration of the mower (these entities are disabled by default). 
- Sensors to monitor the working state, errors and battery level of the MoeBot
- A [Vacuum](https://www.home-assistant.io/integrations/vacuum/) component is also provided for legacy users, but will be removed in a future update.

<img src="https://raw.githubusercontent.com/WhyTey/pymoebot-hass-integration/master/images/device-settings.png">

## Installation

Easiest install is via [HACS](https://hacs.xyz/) 

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Whytey&repository=https%3A%2F%2Fgithub.com%2FWhytey%2Fmoebot-hass-integration&category=integration)


1. Add the repository to your HACS install by clicking the button below:
1. Restart HA
1. Open the Home Assistant web interface.
1. Navigate to "Configuration" > "Integrations".
1. Click on the "+" button in the bottom right corner to add a new integration.
1. Search for "MoeBot" and select it from the list.
1. Enter the required details; Device ID, IP address and [Local Key](https://github.com/make-all/tuya-local?tab=readme-ov-file#finding-your-device-id-and-local-key)
1. Click on "Submit" to complete the integration setup.



For manual installation for advanced users, copy `custom_components/moebot` to your `custom_components` folder in Home Assistant then continue from step 2 above.

## Documentation

Additional documentation is provided in the `pymoebot` [repository](https://github.com/Whytey/pymoebot).
