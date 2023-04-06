# MoeBot Home Assistant Integration

Provides the following:

- Presents a Vacuum component for control of your MoeBot (actual control not yet implemented).
- Further controls to manage whether the MoeBot continues to mow during rain
- Sensors to monitor the working state, errors and battery level of the MoeBot

<img src="https://raw.githubusercontent.com/WhyTey/pymoebot-hass-integration/master/images/device-settings.png">

## Installation

Easiest install is via [HACS](https://hacs.xyz/):

`HACS -> Explore & Add Repositories -> MoeBot`

Notes:

- HACS does not "configure" the integration for you. You must go to `Configuration > Integrations` and add MoeBot after installing via HACS.


For manual installation for advanced users, copy `custom_components/moebot` to
your `custom_components` folder in Home Assistant.

## Documentation

Additional documentation is provided in the `pymoebot` [repository](https://github.com/Whytey/pymoebot).
