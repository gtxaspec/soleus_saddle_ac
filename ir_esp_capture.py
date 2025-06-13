#!/usr/bin/env python3
"""
Log-Based IR Code Capture
Monitors ESPHome logs via API to capture Pronto codes from dump output
"""

import asyncio
import json
import re
from datetime import datetime
from collections import deque
import logging
import time

try:
    import aioesphomeapi
    from aioesphomeapi import LogLevel
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

# Configuration
ESP32_IP = "x.x.x.x"
LOG_FILE = "captured_ir_buttons.json"
MATCH_THRESHOLD = 10  # Need 3 matching codes to identify a button
BUFFER_SIZE = 40     # Collect up to 20 codes before analyzing

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LogBasedIRCapture:
    def __init__(self):
        self.recent_codes = deque(maxlen=BUFFER_SIZE)
        self.captured_buttons = []
        self.already_captured = set()  # Track codes we've already saved
        self.client = None
        self.pronto_buffer = []
        self.collecting_pronto = False
        self.current_pronto_lines = []
        self.last_code_time = 0
        self.last_code = ""
        self.debounce_time = 0.2  # Ignore repeated codes within 1 second
        self.load_existing_captures()
        
    def load_existing_captures(self):
        try:
            with open(LOG_FILE, 'r') as f:
                self.captured_buttons = json.load(f)
            print(f"📚 Loaded {len(self.captured_buttons)} existing captures")
        except (FileNotFoundError, json.JSONDecodeError):
            print("📚 Starting with empty capture log")
            
    def save_capture(self, pronto_data, button_name=None):
        if not button_name:
            button_name = f"button_{len(self.captured_buttons) + 1}"
            
        capture = {
            "timestamp": datetime.now().isoformat(),
            "button_name": button_name,
            "pronto_data": pronto_data,
            "matches_found": MATCH_THRESHOLD
        }
        
        self.captured_buttons.append(capture)
        
        try:
            with open(LOG_FILE, 'w') as f:
                json.dump(self.captured_buttons, f, indent=2)
                
            print(f"\n🎯 BUTTON CAPTURED!")
            print(f"Name: {button_name}")
            print(f"Data: {pronto_data[:80]}...")
            print("Ready for next button...\n")
            
        except Exception as e:
            print(f"❌ Failed to save: {e}")
            
    def process_pronto_code(self, pronto_data):
        if not pronto_data:
            return
            
        # Clean up the Pronto data
        cleaned_data = ' '.join(pronto_data.split())
        
        # Check if this is a repeat of the last code within debounce time
        current_time = datetime.now().timestamp()
        if (cleaned_data == self.last_code and 
            current_time - self.last_code_time < self.debounce_time):
            print(f"📡 Ignoring repeat within {self.debounce_time}s")
            return
            
        self.last_code = cleaned_data
        self.last_code_time = current_time
        
        # Skip if we've already captured this code
        if cleaned_data in self.already_captured:
            print(f"📡 Already captured this code, skipping...")
            return
        
        print(f"📡 Pronto received: {cleaned_data[:60]}...")
        
        self.recent_codes.append(cleaned_data)
        
        # Count occurrences of each unique code in the buffer
        from collections import Counter
        code_counts = Counter(self.recent_codes)
        
        print(f"   Buffer: {len(self.recent_codes)}/{BUFFER_SIZE} codes")
        
        # Check if any code has appeared at least MATCH_THRESHOLD times
        for code, count in code_counts.items():
            if count >= MATCH_THRESHOLD and code not in self.already_captured:
                print(f"\n🔥 Found a code that appeared {count} times!")
                print(f"   Code: {code[:60]}...")
                button_name = input("Enter button name (or press Enter for auto-name): ").strip()
                self.save_capture(code, button_name)
                self.already_captured.add(code)
                
        # Show status of codes in buffer
        if len(code_counts) > 0:
            status_parts = []
            for code, count in code_counts.most_common(5):  # Show top 5
                preview = code[:20] + "..."
                status_parts.append(f"{count}x {preview}")
            print(f"   Top codes: {' | '.join(status_parts)}")
            
    def parse_log_message(self, message):
        """Parse log messages for Pronto data"""
        # Debug: print all messages to see what we're receiving
        if "remote" in message.lower() or "pronto" in message.lower():
            print(f"[DEBUG] IR-related message: {message}")
        
        # Check if this is the start of a Pronto dump
        if "[I][remote.pronto:231]: Received Pronto: data=" in message:
            # Start new collection
            self.collecting_pronto = True
            self.current_pronto_lines = []
            print("[DEBUG] Started collecting multi-line Pronto code")
            return
                    
        # Check if this is a data line with hex data
        if "[I][remote.pronto:233]:" in message:
            # Extract the hex data part after the tag
            parts = message.split("[I][remote.pronto:233]:", 1)
            if len(parts) > 1:
                hex_data = parts[1].strip()
                
                # If we're collecting multi-line, add to buffer
                if self.collecting_pronto:
                    self.current_pronto_lines.append(hex_data)
                    # Check if this looks like the end
                    if "0181" in hex_data or (len(hex_data.split()) < 5 and len(self.current_pronto_lines) > 1):
                        # Complete multi-line Pronto code received
                        complete_pronto = ' '.join(self.current_pronto_lines)
                        print(f"[DEBUG] Complete multi-line Pronto: {complete_pronto[:60]}...")
                        self.process_pronto_code(complete_pronto)
                        self.collecting_pronto = False
                        self.current_pronto_lines = []
                # Only check for single-line format if NOT collecting multi-line
                elif hex_data.startswith("0000") and "0181" in hex_data:
                    # This is a complete single-line code
                    # Fix any missing spaces between 4-digit hex values
                    import re
                    fixed_hex = re.sub(r'([0-9A-Fa-f]{4})([0-9A-Fa-f]{4})', r'\1 \2', hex_data)
                    print(f"[DEBUG] Complete single-line Pronto: {fixed_hex[:60]}...")
                    self.process_pronto_code(fixed_hex)
                    
        # Any other message type ends the collection if we have data
        elif self.collecting_pronto and "[I][remote.pronto:" not in message:
            if self.current_pronto_lines:
                complete_pronto = ' '.join(self.current_pronto_lines)
                print(f"[DEBUG] Ended collection, complete Pronto: {complete_pronto[:60]}...")
                self.process_pronto_code(complete_pronto)
            self.collecting_pronto = False
            self.current_pronto_lines = []
                
    async def monitor_logs(self):
        """Monitor ESPHome logs for IR codes"""
        try:
            print(f"🔗 Connecting to ESPHome at {ESP32_IP}:6053...")
            
            self.client = aioesphomeapi.APIClient(ESP32_IP, 6053, "")
            await self.client.connect(login=True)
            
            print("✅ Connected to ESPHome API!")
            
            # Get device info
            device_info = await self.client.device_info()
            print(f"📱 Device: {device_info.name}")
            print(f"📝 ESPHome: {device_info.esphome_version}")
            
            print(f"\n🎯 Monitoring logs for Pronto IR codes...")
            print(f"📋 Press any button at least {MATCH_THRESHOLD} times within {BUFFER_SIZE} presses")
            print(f"💡 Mix different buttons - the script will identify each one!")
            print("🔄 Press Ctrl+C to stop\n")
            
            # Define log callback
            def log_callback(log_entry):
                # Debug: show what we're receiving
                try:
                    # The log_entry is a protobuf message, extract the message field directly
                    message = log_entry.message
                    
                    # Check if message is bytes and decode it
                    if isinstance(message, bytes):
                        message = message.decode('utf-8', errors='ignore')
                    
                    # Strip ANSI color codes
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    clean_message = ansi_escape.sub('', message)
                    
                    # Debug print for all messages (comment out once working)
                    # print(f"[DEBUG] Clean message: {clean_message}")
                    
                    # Process IR-related messages
                    if 'remote' in clean_message.lower() or 'pronto' in clean_message.lower():
                        self.parse_log_message(clean_message)
                        
                except Exception as e:
                    print(f"[DEBUG] Error processing log entry: {e}")
                    # Try to process the raw string representation
                    try:
                        raw_str = str(log_entry)
                        if 'remote.pronto' in raw_str:
                            # Extract the message part
                            if 'message: "' in raw_str:
                                msg_start = raw_str.find('message: "') + 10
                                msg_end = raw_str.find('"', msg_start)
                                if msg_end > msg_start:
                                    raw_message = raw_str[msg_start:msg_end]
                                    # Strip ANSI codes from escaped format
                                    raw_message = raw_message.replace('\\033[0;32m', '')
                                    raw_message = raw_message.replace('\\033[0m', '')
                                    raw_message = raw_message.replace('\\033[0;36m', '')
                                    self.parse_log_message(raw_message)
                    except Exception as e2:
                        print(f"[DEBUG] Secondary error: {e2}")
                
            # Subscribe to logs with verbose level to catch all messages
            # LogLevel values: NONE=0, ERROR=1, WARN=2, INFO=3, DEBUG=4, VERBOSE=5, VERY_VERBOSE=6
            # Try with level 5 (VERBOSE) or 6 (VERY_VERBOSE)
            self.client.subscribe_logs(log_callback, log_level=6)  # VERY_VERBOSE
            
            print("📡 Subscribed to logs successfully with VERY_VERBOSE level!")
            print("[DEBUG] Waiting for IR messages... (press a remote button)")
            
            # Keep the connection alive
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
                    
        except Exception as e:
            print(f"❌ Connection error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.client:
                await self.client.disconnect()
            
    def run(self):
        """Run the log monitor"""
        print("🚀 Log-Based IR Code Capture")
        print("=" * 50)
        
        if not API_AVAILABLE:
            print("❌ Please install: pip install aioesphomeapi")
            return
            
        try:
            asyncio.run(self.monitor_logs())
        except KeyboardInterrupt:
            print(f"\n👋 Stopped. Captured {len(self.captured_buttons)} buttons.")
            
    def list_captures(self):
        """List all captured buttons"""
        if not self.captured_buttons:
            print("No buttons captured yet")
            return
            
        print(f"\n📋 Captured Buttons ({len(self.captured_buttons)}):")
        print("=" * 60)
        
        for i, button in enumerate(self.captured_buttons, 1):
            print(f"{i:2d}. {button['button_name']}")
            print(f"    Time: {button['timestamp']}")
            print(f"    Data: {button['pronto_data'][:80]}...")
            print()

    def export_for_esphome(self):
        """Export captured buttons in ESPHome YAML format"""
        if not self.captured_buttons:
            print("No buttons to export")
            return
            
        print("\n# ESPHome Remote Transmitter Configuration")
        print("# Add this to your ESPHome YAML file\n")
        print("remote_transmitter:")
        print("  pin: GPIO32  # Change to your IR LED pin")
        print("  carrier_duty_percent: 50%\n")
        print("button:")
        
        for button in self.captured_buttons:
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', button['button_name'].lower())
            print(f"  - platform: template")
            print(f"    name: \"{button['button_name']}\"")
            print(f"    id: {safe_name}")
            print(f"    on_press:")
            print(f"      - remote_transmitter.transmit_pronto:")
            print(f"          data: \"{button['pronto_data']}\"")
            print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            LogBasedIRCapture().list_captures()
        elif sys.argv[1] == "export":
            LogBasedIRCapture().export_for_esphome()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  ./test.py         - Start capturing IR codes")
            print("  ./test.py list    - List all captured buttons")
            print("  ./test.py export  - Export buttons for ESPHome YAML")
    else:
        LogBasedIRCapture().run()
