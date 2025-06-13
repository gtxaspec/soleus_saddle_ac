# AC IR Remote Protocol Documentation

## Overview
This document describes the IR protocol used by the **Soleus Saddle Window A/C (Model: WS3-08E-201)**, based on analysis of captured Pronto codes. The protocol allows control of temperature (62-86°F) and fan speed (LOW, MED, HIGH).

## Capture Methodology
The IR codes were captured using `iresp.py` with an ESP32 equipped with an IR receiver. To ensure accuracy and account for environmental variances:

1. **Multiple Captures**: Each button press on the AC remote was captured multiple times
2. **Validation Threshold**: The capture process continued until 10 identical matches were recorded for each button
3. **Environmental Compensation**: This approach filtered out noise, timing variations, and other environmental factors that could affect IR signal reception
4. **Data Storage**: All validated captures were stored in `captured_ir_buttons.json` with:
   - Timestamp of capture
   - Button name/function
   - Pronto-formatted IR code
   - Number of matches found (always 10 for validated data)

This methodology ensured that only consistent, reliable IR codes were used for protocol analysis.

### Example Capture Entry
```json
{
  "timestamp": "2025-06-10T18:15:32.457821",
  "button_name": "AC, 79, HIGH",
  "pronto_data": "0000 006D 004A 0000 0154 00AE 0013 0018 0013 0018 0013 0018 0013 0043 ...",
  "matches_found": 10
}
```

## Pronto Code Format
The IR codes use the standard Pronto format with the following structure:
- **Header**: `0000 006D 004A 0000` (standard Pronto header)
- **Carrier**: `0153 00AE` or `0154 00AE` (38kHz carrier frequency, minor variation acceptable)
- **Data**: 144 transitions (72 bits of data)
- **End**: `0014 0181` (end marker and repeat gap)

## Device Information
- **Brand**: Soleus
- **Model**: WS3-08E-201 (Saddle Window A/C)
- **OEM Manufacturer**: Nantong Ningpu Electrical Appliance Co., Ltd. (per Intertek Control Number: 4010450)
- **Remote Type**: IR (Infrared)
- **Carrier Frequency**: 38kHz

### Compatible Models and Brands
This IR protocol may be compatible with various models from the same OEM, including:

**Model Patterns:**
- NPL followed by A-Z or blank; followed by 1-100 or blank; followed by A-Z or blank; followed by -05C, -05H, -06C or -06H; followed by /X1E; may be followed by -W
- Specific models: A5405-8K, A5405-10K, A5406-8K-CH, A5406-8K-JP, A5406-10K-CH, A5406-10K-JP, A5407-8K, A5407-10K, A5413-8K-RW, A5413-8K-WAL-AU, A5413-10K-RW, A5413-10K-WAL-AU, A5406-8K-CS, A5406-10K-CS, A5411-8K-RW, A5411-8K-ZA, A5411-10K-RW, A5411-10K-ZA, A5412-8K-JP, A5412-8K-CS, A5412-8K-WAL-KD, A5412-10K-JP, A5412-10K-CS, A5412-10K-WAL-KD, FP10233CA-WH, FP10233US-WH, FP10270CA-WH, FP10270US-WH, 823-041V80BK, 823-041V80CW, 823-041V81BK, 823-041V81CW

**Known Compatible Brands:**
Ningpu, AIR CHOICE, KONWIN, TRUSTECH, CLIMATE CHOICE, ECOTRONIC, KOOLWOOM, PATIO BOSS, SUNDAY LIVING, PRO CHOICE, LIFEPLUS, CHOICE PLUS, IQTRONIC, DOOYAOPLUS, ZAFRO, R.W.FLAME, COWSAR, Joy Pepple, Rintuf, Auseo, Joy Pebble, Fornido, Xbeauty, Kndko, Costway

*Note: While these models share the same OEM, IR protocol compatibility should be verified for each specific model.*

### Models with Heating Mode

Some newer models from the same OEM include heating functionality. Due to lack of hardware, heating mode captures are not yet included in this protocol documentation. **Contributions of heating mode IR captures via issues or pull requests are welcome!**

**Known models with heating capability:**
- WS5-08HW-301 (8,000 BTU)
- WS5-10HW-301 (10,000 BTU)  
- WS5-12HW-301 (12,000 BTU)
- WS4-10EHW-301 (10,000 BTU)
- WS4-10EH7W-301 (10,000 BTU)

If you have one of these models, please consider capturing the heating mode IR codes using the same methodology described in the Capture Methodology section and submitting them to help complete the protocol documentation.

## Binary Encoding
The protocol uses pulse distance encoding:
- **Binary 0**: Short pulse (0x0013) + Short space (0x0018)
- **Binary 1**: Short pulse (0x0013) + Long space (0x0043)
- **Bit Order**: MSB first (most significant bit transmitted first)

## Data Structure (9 bytes / 72 bits)

### Byte 1: Device Header
- **Value**: `0x19` (00011001)
- **Purpose**: Fixed device/model identifier

### Byte 2: Protocol Identifier  
- **Normal operation**: `0x80` (10000000)
- **SLEEP mode**: `0x81` (10000001)
- **Power OFF**: `0x00` (00000000)
- **Purpose**: Protocol/power state identifier

### Byte 3: Fan Speed and Mode Control
The upper nibble of byte 3 encodes the fan speed (1=LOW, 2=MED, 3=HIGH), while the lower nibble identifies the mode:
- `0x1`: Temperature control mode
- `0x0`: AUTO mode
- `0x2`: DRY mode
- `0x3`: FAN only mode or Power OFF
- `0x5`: ECO mode
- `0x6`: SLEEP mode

#### Detailed Byte 3 Values
- **Temperature Control Mode**:
  - **LOW**: `0x11` (00010001)
  - **MED**: `0x21` (00100001)
  - **HIGH**: `0x31` (00110001)
- **AUTO Mode**:
  - **LOW**: `0x10` (00010000)
  - **MED**: `0x20` (00100000)
  - **HIGH**: `0x30` (00110000)
- **FAN Only Mode**:
  - **LOW**: `0x13` (00010011)
  - **MED**: `0x23` (00100011)
  - **HIGH**: `0x33` (00110011)
- **ECO Mode**:
  - **LOW**: `0x15` (00010101)
  - **MED**: `0x25` (00100101)
  - **HIGH**: `0x35` (00110101)
- **SLEEP Mode**:
  - **LOW**: `0x16` (00010110)
  - **MED**: `0x26` (00100110)
  - **HIGH**: `0x36` (00110110)
- **DRY Mode**:
  - **LOW**: `0x12` (00010010) - DRY mode appears to only use LOW fan
- **Power OFF**: `0x13` (00010011)

### Byte 4: Reserved
- **Value**: `0x00` (00000000)
- **Purpose**: Fixed/reserved byte

### Byte 5: Temperature/Mode Encoding
- **Temperature Control, ECO, SLEEP Modes**: `temperature_byte = 0x3E + (temperature_F - 62)`
  - Temperature range: 62°F to 86°F (0x3E to 0x56)
  - Examples:
    - 62°F = 0x3E (00111110) = 62 decimal
    - 70°F = 0x46 (01000110) = 70 decimal
    - 79°F = 0x4F (01001111) = 79 decimal
    - 86°F = 0x56 (01010110) = 86 decimal
  - Note: The byte value equals the temperature in Fahrenheit
- **AUTO Mode**: `0x48` (01001000) - Fixed value
- **FAN Only Mode**: `0x4F` (01001111) - Fixed value
- **DRY Mode**: `0x4F` (01001111) - Fixed value (same as FAN only)
- **Power OFF**: `0x4F` (01001111) - Fixed value

### Bytes 6-8: Reserved
- **All modes**: `0x00` (00000000) for all three bytes
- **Purpose**: Fixed/reserved bytes

### Byte 9: Checksum
- **Formula for most modes**: `checksum = (0x80 + byte3 + byte5) & 0xFF`
- **Formula for SLEEP mode**: `checksum = (0x81 + byte3 + byte5) & 0xFF`
- **Formula for Power OFF**: `checksum = (0x00 + byte3 + byte5) & 0xFF = 0x62`
- **Purpose**: Error detection/validation
- **Note**: The checksum uses the actual byte2 value (0x80, 0x81, or 0x00)

## Checksum Calculation Examples

For 79°F HIGH:
- Byte 3 (HIGH) = 0x31
- Byte 5 (79°F) = 0x4F
- Checksum = (0x80 + 0x31 + 0x4F) & 0xFF = 0x00

For 83°F HIGH:
- Byte 3 (HIGH) = 0x31
- Byte 5 (83°F) = 0x53
- Checksum = (0x80 + 0x31 + 0x53) & 0xFF = 0x04

For DRY mode:
- Byte 3 (LOW) = 0x12
- Byte 5 (DRY) = 0x4F
- Checksum = (0x80 + 0x12 + 0x4F) & 0xFF = 0xE1

## Mode Summary Table

| Mode | Byte 2 | Byte 3 (LOW/MED/HIGH) | Byte 5 | Notes |
|------|--------|------------------------|--------|-------|
| Temperature Control | 0x80 | 0x11/0x21/0x31 | 0x3E-0x56 | Temperature encoded |
| ECO | 0x80 | 0x15/0x25/0x35 | 0x3E-0x56 | Temperature encoded |
| SLEEP | 0x81 | 0x16/0x26/0x36 | 0x3E-0x56 | Temperature encoded, special byte 2 |
| AUTO | 0x80 | 0x10/0x20/0x30 | 0x48 | Fixed byte 5 |
| FAN Only | 0x80 | 0x13/0x23/0x33 | 0x4F | Fixed byte 5 |
| DRY | 0x80 | 0x12 only | 0x4F | LOW fan only |
| Power OFF | 0x00 | 0x13 | 0x4F | Special byte 2 |
| HEAT* | Unknown | Unknown | Unknown | *Not yet captured |

*HEAT mode is available on some models but IR codes have not been captured yet.

## Complete Binary Pattern

The 72-bit pattern follows this structure:

```
[Device ID][Protocol][Fan Speed][Reserved][Temperature][Reserved][Reserved][Reserved][Checksum]
[0x19     ][0x80/81 ][Speed    ][0x00    ][Temp      ][0x00    ][0x00    ][0x00    ][Check   ]
```


## Generating Pronto Codes

To generate a Pronto code:

1. Calculate the temperature byte: `temp_byte = 0x3E + (temp_F - 62)`
2. Select fan speed byte: 0x11 (LOW), 0x21 (MED), or 0x31 (HIGH)
3. Calculate checksum: `(0x80 + fan_speed_byte + temp_byte) & 0xFF`
4. Build 72-bit binary string from the 9 bytes
5. Convert each bit to Pronto format:
   - Bit 0 → `0013 0018`
   - Bit 1 → `0013 0043`
6. Add Pronto header, carrier, and end sequences

## Valid Modes and Ranges
- **Temperature Control**: 62°F to 86°F with fan speeds LOW, MED, HIGH
- **ECO Mode**: Energy-saving mode, 62°F to 86°F with fan speeds LOW, MED, HIGH
- **SLEEP Mode**: Sleep comfort mode, 62°F to 86°F with fan speeds LOW, MED, HIGH
- **AUTO Mode**: Automatic temperature with fan speeds LOW, MED, HIGH
- **FAN Only Mode**: Fan only (no cooling) with speeds LOW, MED, HIGH
- **DRY Mode**: Dehumidification mode with LOW fan only
- **HEAT Mode**: Available on select models (WS5-xxHW-301, WS4-10EHW-301, WS4-10EH7W-301) - *IR codes not yet captured*
- **Power OFF**: Turns off the AC unit
- **Total Combinations**: 158 (25 temperatures × 3 speeds × 3 modes [normal, ECO, SLEEP] + 3 AUTO modes + 3 FAN modes + 1 DRY mode + 1 Power OFF)
- **Note**: Additional combinations would be available with HEAT mode once captured

## Using the AC IR Code Generator Script

The `ac_ir_code_generator.py` script provides an easy way to generate Pronto codes for controlling the AC unit.

### Installation and Basic Usage

```bash
# Make the script executable
chmod +x ac_ir_code_generator.py

# Show help
./ac_ir_code_generator.py --help

# Show protocol information
./ac_ir_code_generator.py --info
```

### Command-Line Options

| Option | Short | Description | Values |
|--------|-------|-------------|---------|
| `--temperature` | `-t` | Set temperature in Fahrenheit | 62-86 |
| `--fan` | `-f` | Set fan speed | LOW, MED, HIGH |
| `--mode` | `-m` | Operating mode | temp, eco, sleep, auto, fan, dry, off |
| `--all` | | Generate all possible codes | |
| `--output` | `-o` | Output file for --all option | filename.json |
| `--verbose` | `-v` | Show detailed information | |
| `--info` | | Show protocol information | |

### Temperature Control Examples

```bash
# Set AC to 72°F with LOW fan speed
./ac_ir_code_generator.py -t 72 -f LOW

# Set AC to 79°F with HIGH fan speed
./ac_ir_code_generator.py --temperature 79 --fan HIGH

# Set AC to 75°F with MEDIUM fan speed (verbose output)
./ac_ir_code_generator.py -t 75 -f MED -v
```

### Special Modes

```bash
# ECO mode at 75°F with MEDIUM fan
./ac_ir_code_generator.py -m eco -t 75 -f MED

# SLEEP mode at 68°F with LOW fan
./ac_ir_code_generator.py -m sleep -t 68 -f LOW

# AUTO mode with MEDIUM fan (temperature automatic)
./ac_ir_code_generator.py -m auto -f MED

# FAN only mode with HIGH fan (no cooling)
./ac_ir_code_generator.py -m fan -f HIGH

# DRY mode (dehumidification - uses LOW fan automatically)
./ac_ir_code_generator.py -m dry

# Power OFF
./ac_ir_code_generator.py --mode off
```

### Batch Generation

```bash
# Generate all possible codes and display summary
./ac_ir_code_generator.py --all

# Generate all codes and save to JSON file
./ac_ir_code_generator.py --all --output all_ac_codes.json

# Generate all codes for a specific integration
./ac_ir_code_generator.py --all -o home_assistant_codes.json
```

### Integration Examples

```bash
# Generate code and send via ESP32 (example using mosquitto)
CODE=$(./ac_ir_code_generator.py -t 72 -f LOW)
mosquitto_pub -t "esp32/ir/send" -m "$CODE"

# Generate code and save to file
./ac_ir_code_generator.py -t 75 -f MED > ac_75f_med.txt

# Use in a bash script for temperature scheduling
#!/bin/bash
# Morning: 72°F LOW
./ac_ir_code_generator.py -t 72 -f LOW | send_ir_command
sleep 28800  # 8 hours
# Afternoon: 75°F MED
./ac_ir_code_generator.py -t 75 -f MED | send_ir_command
```

### Verbose Output Example

When using the `-v` flag, you get detailed information:

```bash
$ ./ac_ir_code_generator.py -t 75 -f MED -v
AC Code Generator - 75°F, MED Speed
======================================================================
Temperature byte: 0x4B
Fan speed byte: 0x21
Checksum byte: 0xEC
Binary (72 bits): 000110011000000000100001000000000100101100000000000000000000000011101100

Pronto Code:
0000 006D 004A 0000 0153 00AE 0013 0018 0013 0018 0013 0018 0013 0043 ...
```

### Error Handling

The script validates inputs and provides helpful error messages:

```bash
# Temperature out of range
$ ./ac_ir_code_generator.py -t 90 -f HIGH
Error: Temperature must be between 62 and 86°F

# Missing required parameters
$ ./ac_ir_code_generator.py -m eco -t 75
Error: Both --temperature and --fan are required for ECO mode
```

### Using Generated Codes with Different Platforms

#### ESPHome
```yaml
# In your ESPHome configuration
button:
  - platform: template
    name: "AC 72°F Low"
    on_press:
      - remote_transmitter.transmit_pronto:
          data: "0000 006D 004A 0000 0153 00AE ..."  # paste generated code here
```

#### Home Assistant (via Shell Command)
```yaml
# In configuration.yaml
shell_command:
  ac_cool_72: 'python3 /path/to/ac_ir_code_generator.py -t 72 -f LOW | /path/to/ir_send'
  ac_eco_75: 'python3 /path/to/ac_ir_code_generator.py -m eco -t 75 -f MED | /path/to/ir_send'
```

#### Python Script Integration
```python
import subprocess
import json

# Generate a specific code
result = subprocess.run(['./ac_ir_code_generator.py', '-t', '75', '-f', 'MED'], 
                       capture_output=True, text=True)
pronto_code = result.stdout.strip()

# Generate all codes for lookup table
subprocess.run(['./ac_ir_code_generator.py', '--all', '-o', 'codes.json'])
with open('codes.json') as f:
    all_codes = json.load(f)
```

## Manual Protocol Example

To manually generate a code for 75°F with MEDIUM fan speed:
1. Temperature byte: 0x3E + (75 - 62) = 0x4B
2. Fan speed byte: 0x21 (MED)
3. Checksum: (0x80 + 0x21 + 0x4B) & 0xFF = 0xEC
4. Binary: 00011001 10000000 00100001 00000000 01001011 00000000 00000000 00000000 11101100
5. Convert to Pronto format as described above

## Contributing

### Heating Mode Captures Needed

If you have a model with heating capability (WS5-xxHW-301 or WS4-10EHW-301 series), we need your help to complete the protocol documentation! 

To contribute heating mode captures:

1. **Equipment needed**: ESP32 with IR receiver, running `iresp.py`
2. **Capture process**: 
   - Set your AC to various heating temperatures (62-86°F)
   - Capture each temperature at LOW, MED, and HIGH fan speeds
   - Ensure 10 matching captures for each setting
3. **Submission**: Submit captured data via:
   - GitHub issue with the JSON capture file
   - Pull request adding to `captured_ir_buttons.json`
   - Include your model number and any observations

### Other Contributions

We also welcome:
- Captures from other compatible models to verify protocol consistency
- Bug reports or corrections to the documentation
- Improvements to the code generator script
- ESPHome component enhancements
- Integration examples for other platforms

Your contributions help make this resource more complete and useful for the entire community!