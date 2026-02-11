#pragma once

#include "esphome/components/climate_ir/climate_ir.h"

namespace esphome {
namespace soleus {

// Soleus WS3-08E-201 Climate Control
// OEM: Nantong Ningpu Electrical Appliance Co., Ltd.
// May be compatible with other brands using the same OEM

// Temperature range for Soleus WS3-08E-201
const uint8_t SOLEUS_TEMP_MIN = 62;  // Fahrenheit
const uint8_t SOLEUS_TEMP_MAX = 86;  // Fahrenheit
const float SOLEUS_TEMP_MIN_C = 17.0f;  // Celsius (62°F)
const float SOLEUS_TEMP_MAX_C = 30.0f;  // Celsius (86°F)

// Protocol timing constants (based on Pronto analysis)
const uint32_t SOLEUS_HEADER_MARK = 8000;
const uint32_t SOLEUS_HEADER_SPACE = 4000;
const uint32_t SOLEUS_BIT_MARK = 600;
const uint32_t SOLEUS_ONE_SPACE = 1600;
const uint32_t SOLEUS_ZERO_SPACE = 550;

// Protocol byte definitions
const uint8_t SOLEUS_BYTE1_DEVICE = 0x19;  // Device ID

// Byte 2 values
const uint8_t SOLEUS_BYTE2_NORMAL = 0x80;
const uint8_t SOLEUS_BYTE2_SLEEP = 0x81;
const uint8_t SOLEUS_BYTE2_POWER_OFF = 0x00;

// Byte 3 fan speed values (lower nibble identifies mode)
const uint8_t SOLEUS_FAN_TEMP_LOW = 0x11;
const uint8_t SOLEUS_FAN_TEMP_MED = 0x21;
const uint8_t SOLEUS_FAN_TEMP_HIGH = 0x31;

const uint8_t SOLEUS_FAN_AUTO_LOW = 0x10;
const uint8_t SOLEUS_FAN_AUTO_MED = 0x20;
const uint8_t SOLEUS_FAN_AUTO_HIGH = 0x30;

const uint8_t SOLEUS_FAN_ONLY_LOW = 0x13;
const uint8_t SOLEUS_FAN_ONLY_MED = 0x23;
const uint8_t SOLEUS_FAN_ONLY_HIGH = 0x33;

const uint8_t SOLEUS_FAN_ECO_LOW = 0x15;
const uint8_t SOLEUS_FAN_ECO_MED = 0x25;
const uint8_t SOLEUS_FAN_ECO_HIGH = 0x35;

const uint8_t SOLEUS_FAN_SLEEP_LOW = 0x16;
const uint8_t SOLEUS_FAN_SLEEP_MED = 0x26;
const uint8_t SOLEUS_FAN_SLEEP_HIGH = 0x36;

const uint8_t SOLEUS_FAN_DRY_LOW = 0x12;

const uint8_t SOLEUS_BYTE3_POWER_OFF = 0x13;

// Byte 5 special values
const uint8_t SOLEUS_BYTE5_AUTO = 0x48;
const uint8_t SOLEUS_BYTE5_FAN_ONLY = 0x4F;
const uint8_t SOLEUS_BYTE5_POWER_OFF = 0x4F;
const uint8_t SOLEUS_BYTE5_DRY = 0x4F;
const uint8_t SOLEUS_TEMP_BASE = 0x3E;  // Base value for 62°F

class SoleusClimate : public climate_ir::ClimateIR {
 public:
  SoleusClimate()
      : climate_ir::ClimateIR(SOLEUS_TEMP_MIN_C, SOLEUS_TEMP_MAX_C, 0.5f, true, false,
                              {climate::CLIMATE_FAN_LOW, climate::CLIMATE_FAN_MEDIUM, climate::CLIMATE_FAN_HIGH},
                              {},
                              {climate::CLIMATE_PRESET_NONE, climate::CLIMATE_PRESET_ECO, climate::CLIMATE_PRESET_SLEEP}) {}

  void set_supports_heat(bool supports_heat) { this->supports_heat_ = supports_heat; }

 protected:
  climate::ClimateTraits traits() override;
  void transmit_state() override;
  bool on_receive(remote_base::RemoteReceiveData data) override;
  bool parse_state_frame_(const uint8_t frame[]);
  
 private:
  bool supports_heat_{false};

  void transmit_pronto_(const std::vector<uint16_t> &data);
  uint8_t temp_to_protocol_(float temp_c) const;
  float protocol_to_temp_(uint8_t value) const;
  uint8_t calculate_checksum_(uint8_t byte2, uint8_t byte3, uint8_t byte5) const;
};

}  // namespace soleus
}  // namespace esphome
