#!/usr/bin/env python3
"""
AC IR Code Generator for Soleus Saddle Window A/C (Model: WS3-08E-201)
OEM: Nantong Ningpu Electrical Appliance Co., Ltd.
Generates Pronto codes for AC control (62-86°F, LOW/MED/HIGH fan speeds)

This protocol may be compatible with other models from the same OEM sold under
various brands including: AIR CHOICE, KONWIN, TRUSTECH, CLIMATE CHOICE, ECOTRONIC,
KOOLWOOM, PATIO BOSS, SUNDAY LIVING, PRO CHOICE, LIFEPLUS, ZAFRO, R.W.FLAME, 
COWSAR, Joy Pebble, Costway, and others.
"""

import argparse
import sys

class ACIRCodeGenerator:
    """Generate Pronto IR codes for Soleus WS3-08E-201 AC control"""
    
    # Constants
    TEMP_MIN = 62
    TEMP_MAX = 86
    TEMP_BASE = 0x3E  # Base value for 62°F
    
    # Fan speed bytes for temperature control mode
    FAN_SPEEDS = {
        'LOW': 0x11,
        'MED': 0x21,
        'HIGH': 0x31
    }
    
    # Fan speed bytes for AUTO mode
    AUTO_FAN_SPEEDS = {
        'LOW': 0x10,
        'MED': 0x20,
        'HIGH': 0x30
    }
    
    # Fan speed bytes for FAN only mode
    FAN_ONLY_SPEEDS = {
        'LOW': 0x13,
        'MED': 0x23,
        'HIGH': 0x33
    }
    
    # Fan speed bytes for ECO mode
    ECO_SPEEDS = {
        'LOW': 0x15,
        'MED': 0x25,
        'HIGH': 0x35
    }
    
    # Fan speed bytes for SLEEP mode
    SLEEP_SPEEDS = {
        'LOW': 0x16,
        'MED': 0x26,
        'HIGH': 0x36
    }
    
    # Special mode values
    AUTO_TEMP_BYTE = 0x48
    FAN_ONLY_BYTE5 = 0x4F
    SLEEP_BYTE2 = 0x81
    POWER_OFF_BYTE2 = 0x00
    POWER_OFF_BYTE3 = 0x13
    POWER_OFF_BYTE5 = 0x4F
    
    # DRY mode constants
    DRY_FAN_SPEED = {
        'LOW': 0x12  # DRY mode only supports LOW fan
    }
    DRY_BYTE5 = 0x4F  # Same as FAN only mode
    
    # Pronto format constants
    PRONTO_HEADER = ['0000', '006D', '004A', '0000']
    PRONTO_CARRIER = ['0153', '00AE']
    PRONTO_END = ['0014', '0181']
    
    # Pulse/space values for binary encoding
    BIT_0 = ['0013', '0018']  # Short pulse, short space
    BIT_1 = ['0013', '0043']  # Short pulse, long space
    
    def __init__(self):
        """Initialize the generator"""
        pass
    
    def validate_inputs(self, temperature, fan_speed):
        """Validate temperature and fan speed inputs"""
        if temperature < self.TEMP_MIN or temperature > self.TEMP_MAX:
            raise ValueError(f"Temperature must be between {self.TEMP_MIN} and {self.TEMP_MAX}°F")
        
        fan_speed_upper = fan_speed.upper()
        if fan_speed_upper not in self.FAN_SPEEDS:
            raise ValueError(f"Fan speed must be one of: {', '.join(self.FAN_SPEEDS.keys())}")
        
        return fan_speed_upper
    
    def calculate_temperature_byte(self, temperature):
        """Calculate the temperature byte value"""
        return self.TEMP_BASE + (temperature - self.TEMP_MIN)
    
    def calculate_checksum(self, fan_byte, temp_byte):
        """Calculate the checksum byte"""
        return (0x80 + fan_byte + temp_byte) & 0xFF
    
    def build_binary_data(self, temperature, fan_speed):
        """Build the 72-bit binary data string"""
        # Get byte values
        fan_byte = self.FAN_SPEEDS[fan_speed]
        temp_byte = self.calculate_temperature_byte(temperature)
        checksum = self.calculate_checksum(fan_byte, temp_byte)
        
        # Build binary string
        binary = (
            f"{0x19:08b}" +      # Byte 1: Device ID (0x19)
            f"{0x80:08b}" +      # Byte 2: Protocol (0x80)
            f"{fan_byte:08b}" +  # Byte 3: Fan speed
            f"{0x00:08b}" +      # Byte 4: Reserved (0x00)
            f"{temp_byte:08b}" + # Byte 5: Temperature
            f"{0x00:08b}" +      # Byte 6: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 7: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 8: Reserved (0x00)
            f"{checksum:08b}"    # Byte 9: Checksum
        )
        
        return binary, fan_byte, temp_byte, checksum
    
    def binary_to_pronto(self, binary_string):
        """Convert binary string to Pronto format"""
        pronto_data = []
        
        for bit in binary_string:
            if bit == '0':
                pronto_data.extend(self.BIT_0)
            else:  # bit == '1'
                pronto_data.extend(self.BIT_1)
        
        return pronto_data
    
    def generate_power_off(self):
        """Generate POWER OFF code"""
        # Power OFF uses special values
        byte2 = self.POWER_OFF_BYTE2
        byte3 = self.POWER_OFF_BYTE3
        byte5 = self.POWER_OFF_BYTE5
        checksum = 0x62  # Fixed checksum for power off
        
        binary = (
            f"{0x19:08b}" +      # Byte 1: Device ID (0x19)
            f"{byte2:08b}" +     # Byte 2: 0x00 for power off
            f"{byte3:08b}" +     # Byte 3: 0x13 for power off
            f"{0x00:08b}" +      # Byte 4: Reserved (0x00)
            f"{byte5:08b}" +     # Byte 5: 0x4F for power off
            f"{0x00:08b}" +      # Byte 6: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 7: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 8: Reserved (0x00)
            f"{checksum:08b}"    # Byte 9: Checksum
        )
        
        pronto_data = self.binary_to_pronto(binary)
        pronto_code = (
            self.PRONTO_HEADER +
            self.PRONTO_CARRIER +
            pronto_data +
            self.PRONTO_END
        )
        
        return {
            'pronto_code': ' '.join(pronto_code),
            'mode': 'POWER OFF',
            'binary': binary
        }
    
    def generate_auto_mode(self, fan_speed):
        """Generate AUTO mode code"""
        fan_speed = fan_speed.upper()
        if fan_speed not in self.AUTO_FAN_SPEEDS:
            raise ValueError(f"Fan speed must be one of: {', '.join(self.AUTO_FAN_SPEEDS.keys())}")
        
        # AUTO mode uses special fan speed bytes and fixed temp byte
        fan_byte = self.AUTO_FAN_SPEEDS[fan_speed]
        temp_byte = self.AUTO_TEMP_BYTE
        checksum = (0x80 + fan_byte + temp_byte) & 0xFF
        
        binary = (
            f"{0x19:08b}" +      # Byte 1: Device ID (0x19)
            f"{0x80:08b}" +      # Byte 2: Protocol (0x80)
            f"{fan_byte:08b}" +  # Byte 3: AUTO fan speed
            f"{0x00:08b}" +      # Byte 4: Reserved (0x00)
            f"{temp_byte:08b}" + # Byte 5: AUTO temp (0x48)
            f"{0x00:08b}" +      # Byte 6: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 7: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 8: Reserved (0x00)
            f"{checksum:08b}"    # Byte 9: Checksum
        )
        
        pronto_data = self.binary_to_pronto(binary)
        pronto_code = (
            self.PRONTO_HEADER +
            self.PRONTO_CARRIER +
            pronto_data +
            self.PRONTO_END
        )
        
        return {
            'pronto_code': ' '.join(pronto_code),
            'mode': 'AUTO',
            'fan_speed': fan_speed,
            'fan_byte': fan_byte,
            'checksum': checksum,
            'binary': binary
        }
    
    def generate_fan_only_mode(self, fan_speed):
        """Generate FAN only mode code"""
        fan_speed = fan_speed.upper()
        if fan_speed not in self.FAN_ONLY_SPEEDS:
            raise ValueError(f"Fan speed must be one of: {', '.join(self.FAN_ONLY_SPEEDS.keys())}")
        
        # FAN only mode uses special fan speed bytes and fixed byte5
        fan_byte = self.FAN_ONLY_SPEEDS[fan_speed]
        temp_byte = self.FAN_ONLY_BYTE5
        checksum = (0x80 + fan_byte + temp_byte) & 0xFF
        
        binary = (
            f"{0x19:08b}" +      # Byte 1: Device ID (0x19)
            f"{0x80:08b}" +      # Byte 2: Protocol (0x80)
            f"{fan_byte:08b}" +  # Byte 3: FAN only speed
            f"{0x00:08b}" +      # Byte 4: Reserved (0x00)
            f"{temp_byte:08b}" + # Byte 5: FAN mode (0x4F)
            f"{0x00:08b}" +      # Byte 6: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 7: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 8: Reserved (0x00)
            f"{checksum:08b}"    # Byte 9: Checksum
        )
        
        pronto_data = self.binary_to_pronto(binary)
        pronto_code = (
            self.PRONTO_HEADER +
            self.PRONTO_CARRIER +
            pronto_data +
            self.PRONTO_END
        )
        
        return {
            'pronto_code': ' '.join(pronto_code),
            'mode': 'FAN',
            'fan_speed': fan_speed,
            'fan_byte': fan_byte,
            'checksum': checksum,
            'binary': binary
        }
    
    def generate_eco_mode(self, temperature, fan_speed):
        """Generate ECO mode code"""
        # Validate inputs
        fan_speed = self.validate_inputs(temperature, fan_speed)
        
        # ECO mode uses special fan speed bytes with temperature
        fan_byte = self.ECO_SPEEDS[fan_speed]
        temp_byte = self.calculate_temperature_byte(temperature)
        checksum = (0x80 + fan_byte + temp_byte) & 0xFF
        
        binary = (
            f"{0x19:08b}" +      # Byte 1: Device ID (0x19)
            f"{0x80:08b}" +      # Byte 2: Protocol (0x80)
            f"{fan_byte:08b}" +  # Byte 3: ECO fan speed
            f"{0x00:08b}" +      # Byte 4: Reserved (0x00)
            f"{temp_byte:08b}" + # Byte 5: Temperature
            f"{0x00:08b}" +      # Byte 6: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 7: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 8: Reserved (0x00)
            f"{checksum:08b}"    # Byte 9: Checksum
        )
        
        pronto_data = self.binary_to_pronto(binary)
        pronto_code = (
            self.PRONTO_HEADER +
            self.PRONTO_CARRIER +
            pronto_data +
            self.PRONTO_END
        )
        
        return {
            'pronto_code': ' '.join(pronto_code),
            'mode': 'ECO',
            'temperature': temperature,
            'fan_speed': fan_speed,
            'fan_byte': fan_byte,
            'temp_byte': temp_byte,
            'checksum': checksum,
            'binary': binary
        }
    
    def generate_sleep_mode(self, temperature, fan_speed):
        """Generate SLEEP mode code"""
        # Validate inputs
        fan_speed = self.validate_inputs(temperature, fan_speed)
        
        # SLEEP mode uses special byte2 and fan speed bytes
        byte2 = self.SLEEP_BYTE2
        fan_byte = self.SLEEP_SPEEDS[fan_speed]
        temp_byte = self.calculate_temperature_byte(temperature)
        checksum = (byte2 + fan_byte + temp_byte) & 0xFF
        
        binary = (
            f"{0x19:08b}" +      # Byte 1: Device ID (0x19)
            f"{byte2:08b}" +     # Byte 2: SLEEP mode (0x81)
            f"{fan_byte:08b}" +  # Byte 3: SLEEP fan speed
            f"{0x00:08b}" +      # Byte 4: Reserved (0x00)
            f"{temp_byte:08b}" + # Byte 5: Temperature
            f"{0x00:08b}" +      # Byte 6: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 7: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 8: Reserved (0x00)
            f"{checksum:08b}"    # Byte 9: Checksum
        )
        
        pronto_data = self.binary_to_pronto(binary)
        pronto_code = (
            self.PRONTO_HEADER +
            self.PRONTO_CARRIER +
            pronto_data +
            self.PRONTO_END
        )
        
        return {
            'pronto_code': ' '.join(pronto_code),
            'mode': 'SLEEP',
            'temperature': temperature,
            'fan_speed': fan_speed,
            'byte2': byte2,
            'fan_byte': fan_byte,
            'temp_byte': temp_byte,
            'checksum': checksum,
            'binary': binary
        }
    
    def generate_dry_mode(self):
        """Generate DRY mode code"""
        # DRY mode uses LOW fan speed only
        fan_byte = self.DRY_FAN_SPEED['LOW']
        temp_byte = self.DRY_BYTE5
        checksum = (0x80 + fan_byte + temp_byte) & 0xFF
        
        binary = (
            f"{0x19:08b}" +      # Byte 1: Device ID (0x19)
            f"{0x80:08b}" +      # Byte 2: Protocol (0x80)
            f"{fan_byte:08b}" +  # Byte 3: DRY fan speed (0x12)
            f"{0x00:08b}" +      # Byte 4: Reserved (0x00)
            f"{temp_byte:08b}" + # Byte 5: DRY mode (0x4F)
            f"{0x00:08b}" +      # Byte 6: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 7: Reserved (0x00)
            f"{0x00:08b}" +      # Byte 8: Reserved (0x00)
            f"{checksum:08b}"    # Byte 9: Checksum
        )
        
        pronto_data = self.binary_to_pronto(binary)
        pronto_code = (
            self.PRONTO_HEADER +
            self.PRONTO_CARRIER +
            pronto_data +
            self.PRONTO_END
        )
        
        return {
            'pronto_code': ' '.join(pronto_code),
            'mode': 'DRY',
            'fan_speed': 'LOW',
            'fan_byte': fan_byte,
            'checksum': checksum,
            'binary': binary
        }
    
    def generate_pronto_code(self, temperature, fan_speed):
        """Generate complete Pronto code for given temperature and fan speed"""
        # Validate inputs
        fan_speed = self.validate_inputs(temperature, fan_speed)
        
        # Build binary data
        binary, fan_byte, temp_byte, checksum = self.build_binary_data(temperature, fan_speed)
        
        # Convert to Pronto format
        pronto_data = self.binary_to_pronto(binary)
        
        # Build complete Pronto code
        pronto_code = (
            self.PRONTO_HEADER +
            self.PRONTO_CARRIER +
            pronto_data +
            self.PRONTO_END
        )
        
        # Return code and debug info
        return {
            'pronto_code': ' '.join(pronto_code),
            'temperature': temperature,
            'fan_speed': fan_speed,
            'fan_byte': fan_byte,
            'temp_byte': temp_byte,
            'checksum': checksum,
            'binary': binary
        }
    
    def generate_all_codes(self, output_file=None):
        """Generate all possible AC codes"""
        all_codes = []
        
        # Temperature control codes
        for temp in range(self.TEMP_MIN, self.TEMP_MAX + 1):
            for speed in self.FAN_SPEEDS.keys():
                result = self.generate_pronto_code(temp, speed)
                all_codes.append({
                    'button_name': f"AC,{temp},{speed}",
                    'pronto_data': result['pronto_code']
                })
        
        # AUTO mode codes
        for speed in self.AUTO_FAN_SPEEDS.keys():
            result = self.generate_auto_mode(speed)
            all_codes.append({
                'button_name': f"AUTO,{speed}",
                'pronto_data': result['pronto_code']
            })
        
        # ECO mode codes
        for temp in range(self.TEMP_MIN, self.TEMP_MAX + 1):
            for speed in self.ECO_SPEEDS.keys():
                result = self.generate_eco_mode(temp, speed)
                all_codes.append({
                    'button_name': f"ECO, {temp}, {speed}",
                    'pronto_data': result['pronto_code']
                })
        
        # SLEEP mode codes
        for temp in range(self.TEMP_MIN, self.TEMP_MAX + 1):
            for speed in self.SLEEP_SPEEDS.keys():
                result = self.generate_sleep_mode(temp, speed)
                all_codes.append({
                    'button_name': f"SLEEP, {temp}, {speed}",
                    'pronto_data': result['pronto_code']
                })
        
        # FAN only mode codes
        for speed in self.FAN_ONLY_SPEEDS.keys():
            result = self.generate_fan_only_mode(speed)
            all_codes.append({
                'button_name': f"FAN, {speed}",
                'pronto_data': result['pronto_code']
            })
        
        # DRY mode code
        result = self.generate_dry_mode()
        all_codes.append({
            'button_name': "DRY, AUTO",
            'pronto_data': result['pronto_code']
        })
        
        # POWER OFF code
        result = self.generate_power_off()
        all_codes.append({
            'button_name': "POWER OFF",
            'pronto_data': result['pronto_code']
        })
        
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(all_codes, f, indent=2)
        
        return all_codes


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Generate Pronto IR codes for Soleus WS3-08E-201 AC control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t 79 -f HIGH
  %(prog)s --temperature 72 --fan LOW
  %(prog)s -m eco -t 75 -f MED
  %(prog)s -m sleep -t 68 -f LOW
  %(prog)s -m auto -f MED
  %(prog)s -m fan -f HIGH
  %(prog)s -m dry
  %(prog)s --mode off
  %(prog)s --all --output all_codes.json
  %(prog)s --info
        """
    )
    
    parser.add_argument('-t', '--temperature', type=int, 
                        help=f'Temperature in Fahrenheit ({ACIRCodeGenerator.TEMP_MIN}-{ACIRCodeGenerator.TEMP_MAX})')
    parser.add_argument('-f', '--fan', type=str, choices=['LOW', 'MED', 'HIGH', 'low', 'med', 'high'],
                        help='Fan speed setting')
    parser.add_argument('-m', '--mode', type=str, choices=['temp', 'eco', 'sleep', 'auto', 'fan', 'dry', 'off'],
                        default='temp', help='Operating mode (default: temp)')
    parser.add_argument('--all', action='store_true',
                        help='Generate all possible codes')
    parser.add_argument('-o', '--output', type=str,
                        help='Output file for --all option (JSON format)')
    parser.add_argument('--info', action='store_true',
                        help='Show protocol information')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed information')
    
    args = parser.parse_args()
    
    generator = ACIRCodeGenerator()
    
    # Show protocol info
    if args.info:
        print("Soleus WS3-08E-201 AC IR Protocol Information")
        print("=" * 50)
        print("Model: Soleus Saddle Window A/C (WS3-08E-201)")
        print(f"Temperature range: {generator.TEMP_MIN}-{generator.TEMP_MAX}°F")
        print(f"Fan speeds: {', '.join(generator.FAN_SPEEDS.keys())}")
        print("\nProtocol structure (9 bytes):")
        print("  Byte 1: Device ID (0x19)")
        print("  Byte 2: Protocol (0x80 normal, 0x81 sleep, 0x00 power off)")
        print("  Byte 3: Fan speed")
        print("    - Temperature mode: LOW=0x11, MED=0x21, HIGH=0x31")
        print("    - ECO mode: LOW=0x15, MED=0x25, HIGH=0x35")
        print("    - SLEEP mode: LOW=0x16, MED=0x26, HIGH=0x36")
        print("    - AUTO mode: LOW=0x10, MED=0x20, HIGH=0x30")
        print("    - FAN only mode: LOW=0x13, MED=0x23, HIGH=0x33")
        print("    - DRY mode: LOW=0x12 (LOW fan only)")
        print("    - Power OFF: 0x13")
        print("  Byte 4: Reserved (0x00)")
        print("  Byte 5: Mode/Temperature")
        print("    - Temperature/ECO/SLEEP mode: 0x3E + (temp - 62)")
        print("    - AUTO mode: 0x48")
        print("    - FAN only mode: 0x4F")
        print("    - DRY mode: 0x4F")
        print("    - Power OFF: 0x4F")
        print("  Byte 6-8: Reserved (0x00)")
        print("  Byte 9: Checksum ((byte2 + byte3 + byte5) & 0xFF)")
        print("\nModes:")
        print("  - Temperature control: Set specific temperature with fan speed")
        print("  - ECO: Energy-saving mode with temperature and fan speed")
        print("  - SLEEP: Sleep comfort mode with temperature and fan speed")
        print("  - AUTO: Automatic temperature control with fan speed")
        print("  - FAN: Fan only mode (no cooling) with fan speed")
        print("  - DRY: Dehumidification mode (LOW fan only)")
        print("  - Power OFF: Turn off the AC unit")
        return
    
    # Generate all codes
    if args.all:
        print("Generating all AC codes...")
        codes = generator.generate_all_codes(args.output)
        print(f"Generated {len(codes)} codes")
        if args.output:
            print(f"Saved to: {args.output}")
        else:
            for code in codes[:5]:  # Show first 5 as example
                print(f"{code['button_name']}: {code['pronto_data'][:50]}...")
            print(f"... and {len(codes) - 5} more")
        return
    
    # Generate single code based on mode
    if args.mode == 'off':
        result = generator.generate_power_off()
        if args.verbose:
            print("AC Code Generator - POWER OFF")
            print("=" * 70)
            print(f"Binary (72 bits): {result['binary']}")
            print("\nPronto Code:")
        print(result['pronto_code'])
    
    elif args.mode == 'auto':
        if args.fan is None:
            parser.error("--fan is required for AUTO mode")
        result = generator.generate_auto_mode(args.fan)
        if args.verbose:
            print(f"AC Code Generator - AUTO Mode, {result['fan_speed']} Speed")
            print("=" * 70)
            print(f"Fan speed byte: 0x{result['fan_byte']:02X}")
            print(f"Checksum byte: 0x{result['checksum']:02X}")
            print(f"Binary (72 bits): {result['binary']}")
            print("\nPronto Code:")
        print(result['pronto_code'])
    
    elif args.mode == 'eco':
        if args.temperature is None or args.fan is None:
            parser.error("Both --temperature and --fan are required for ECO mode")
        try:
            result = generator.generate_eco_mode(args.temperature, args.fan)
            if args.verbose:
                print(f"AC Code Generator - ECO Mode, {result['temperature']}°F, {result['fan_speed']} Speed")
                print("=" * 70)
                print(f"Temperature byte: 0x{result['temp_byte']:02X}")
                print(f"Fan speed byte: 0x{result['fan_byte']:02X}")
                print(f"Checksum byte: 0x{result['checksum']:02X}")
                print(f"Binary (72 bits): {result['binary']}")
                print("\nPronto Code:")
            print(result['pronto_code'])
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.mode == 'sleep':
        if args.temperature is None or args.fan is None:
            parser.error("Both --temperature and --fan are required for SLEEP mode")
        try:
            result = generator.generate_sleep_mode(args.temperature, args.fan)
            if args.verbose:
                print(f"AC Code Generator - SLEEP Mode, {result['temperature']}°F, {result['fan_speed']} Speed")
                print("=" * 70)
                print(f"Byte 2: 0x{result['byte2']:02X}")
                print(f"Temperature byte: 0x{result['temp_byte']:02X}")
                print(f"Fan speed byte: 0x{result['fan_byte']:02X}")
                print(f"Checksum byte: 0x{result['checksum']:02X}")
                print(f"Binary (72 bits): {result['binary']}")
                print("\nPronto Code:")
            print(result['pronto_code'])
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.mode == 'fan':
        if args.fan is None:
            parser.error("--fan is required for FAN only mode")
        result = generator.generate_fan_only_mode(args.fan)
        if args.verbose:
            print(f"AC Code Generator - FAN Only Mode, {result['fan_speed']} Speed")
            print("=" * 70)
            print(f"Fan speed byte: 0x{result['fan_byte']:02X}")
            print(f"Checksum byte: 0x{result['checksum']:02X}")
            print(f"Binary (72 bits): {result['binary']}")
            print("\nPronto Code:")
        print(result['pronto_code'])
    
    elif args.mode == 'dry':
        result = generator.generate_dry_mode()
        if args.verbose:
            print("AC Code Generator - DRY Mode (Dehumidification)")
            print("=" * 70)
            print(f"Binary (72 bits): {result['binary']}")
            print("\nPronto Code:")
        print(result['pronto_code'])
    
    else:  # temp mode
        if args.temperature is None or args.fan is None:
            parser.error("Both --temperature and --fan are required for temperature mode")
        
        try:
            result = generator.generate_pronto_code(args.temperature, args.fan)
            
            if args.verbose:
                print(f"AC Code Generator - {result['temperature']}°F, {result['fan_speed']} Speed")
                print("=" * 70)
                print(f"Temperature byte: 0x{result['temp_byte']:02X}")
                print(f"Fan speed byte: 0x{result['fan_byte']:02X}")
                print(f"Checksum byte: 0x{result['checksum']:02X}")
                print(f"Binary (72 bits): {result['binary']}")
                print("\nPronto Code:")
            
            print(result['pronto_code'])
            
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()