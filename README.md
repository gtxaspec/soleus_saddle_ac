# Soleus Saddle AC - ESPHome Custom Component

Control your Soleus WS3-08E-201 Saddle Window Air Conditioner (and compatible models) with ESPHome and Home Assistant.

## Features

- Full climate control via IR transmitter
- Temperature control: 62-86°F (17-30°C)
- Multiple operating modes: Cool, Auto, Fan Only, Dry
- Fan speed control: Low, Medium, High
- Power presets: Eco, Sleep
- IR receiver support for learning from physical remote
- Home Assistant integration

## Supported Models

<img width="360" height="480" alt="image" src="https://github.com/user-attachments/assets/0aa390c6-4476-4556-9766-6e26ba386042" />

This component supports the Soleus WS3-08E-201 and potentially other models from the same OEM manufacturer (Nantong Ningpu Electrical Appliance Co., Ltd.), including various rebranded units. See the [protocol documentation](AC_IR_Protocol_Documentation.md) for a comprehensive list of potentially compatible models and brands.

## Installation

### Method 1: GitHub (Recommended)

Add this to your ESPHome YAML configuration:

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/gtxaspec/soleus_saddle_ac
      ref: master
    components: [soleus]
    refresh: 0s
```

### Method 2: Local Installation

1. Clone this repository
2. Copy the `components/soleus` folder to your ESPHome configuration directory
3. Reference it as a local component:

```yaml
external_components:
  - source:
      type: local
      path: components
    components: [soleus]
```

## Configuration

### Basic Configuration

```yaml
# IR Transmitter (required)
remote_transmitter:
  pin: GPIO32  # Adjust to your IR LED pin
  carrier_duty_percent: 50%

# IR Receiver (optional, for learning from remote)
remote_receiver:
  pin: GPIO33  # Adjust to your IR receiver pin
  dump: all

# Climate component
climate:
  - platform: soleus
    name: "AC"
    supports_heat: false  # Set to true if your model has heating (untested - we need community feedback)
```

### Full Example

See [example_config.yaml](components/soleus/example_config.yaml) for a complete configuration including optional buttons for common presets.

## Usage

Once configured and connected to Home Assistant, you can:

- Set target temperature (62-86°F / 17-30°C)
- Change operating modes (Off, Cool, Fan Only, Auto, Dry)
- Adjust fan speed (Low, Medium, High)
- Apply presets (None, Eco, Sleep)

### Operating Modes

- **Cool**: Normal cooling mode with full temperature and fan control
- **Auto**: Automatic temperature control
- **Fan Only**: Circulate air without cooling
- **Dry**: Dehumidification mode (fan locked to Low)
- **Off**: Turn off the unit

### Presets

- **Eco**: Energy-saving mode
- **Sleep**: Quiet operation for nighttime comfort

## Technical Details

This component implements the IR protocol for Soleus saddle window air conditioners. The protocol uses:
- 38kHz carrier frequency
- 72-bit data packets
- Pulse distance encoding

For detailed protocol information, see [AC_IR_Protocol_Documentation.md](AC_IR_Protocol_Documentation.md).

## Tools Included

- `ac_ir_code_generator.py`: Generate Pronto IR codes for any temperature/fan combination
- `ir_esp_capture.py`: Capture IR codes from your physical remote
- `captured_ir_buttons.json`: Database of validated IR codes

## Contributing

Contributions are welcome! Especially needed:
- **Heating mode testing**: The component includes heating support (`supports_heat: true`) but this is untested as we don't have access to models with heating capability
- IR captures for heating mode (available on WS5-xxHW-301 series)
- Testing with other compatible models
- Bug reports and feature requests

Please open an issue or submit a pull request on GitHub.

## License

This project is open source and available under the MIT License.

## Acknowledgments

Special thanks to the ESPHome community for providing the framework that makes this integration possible.
