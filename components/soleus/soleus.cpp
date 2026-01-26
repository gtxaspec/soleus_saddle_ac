#include "soleus.h"
#include "esphome/core/log.h"

namespace esphome {
namespace soleus {

static const char *const TAG = "soleus.climate";

climate::ClimateTraits SoleusClimate::traits() {
  auto traits = climate::ClimateTraits();
  
  traits.set_supports_current_temperature(false);
  traits.set_visual_min_temperature(SOLEUS_TEMP_MIN_C);
  traits.set_visual_max_temperature(SOLEUS_TEMP_MAX_C);
  traits.set_visual_temperature_step(1.0f);
  
  // Base modes - always supported
  traits.set_supported_modes({
    climate::CLIMATE_MODE_OFF,
    climate::CLIMATE_MODE_COOL,
    climate::CLIMATE_MODE_FAN_ONLY,
    climate::CLIMATE_MODE_DRY,
    climate::CLIMATE_MODE_AUTO,
  });
  
  // Only add heat modes if supports_heat is true
  if (this->supports_heat_) {
    traits.add_supported_mode(climate::CLIMATE_MODE_HEAT);
    traits.add_supported_mode(climate::CLIMATE_MODE_HEAT_COOL);
  }
  
  traits.set_supported_fan_modes({
    climate::CLIMATE_FAN_LOW,
    climate::CLIMATE_FAN_MEDIUM,
    climate::CLIMATE_FAN_HIGH,
  });
  
  traits.set_supported_presets({
    climate::CLIMATE_PRESET_NONE,
    climate::CLIMATE_PRESET_ECO,
    climate::CLIMATE_PRESET_SLEEP,
  });
  
  return traits;
}

void SoleusClimate::transmit_state() {
  uint8_t frame[9] = {0};
  
  // Byte 1: Device ID
  frame[0] = SOLEUS_BYTE1_DEVICE;
  
  // Determine mode and set appropriate bytes
  if (this->mode == climate::CLIMATE_MODE_OFF) {
    // Power OFF
    frame[1] = SOLEUS_BYTE2_POWER_OFF;
    frame[2] = SOLEUS_BYTE3_POWER_OFF;
    frame[4] = SOLEUS_BYTE5_POWER_OFF;
  } else {
    // Determine if we're in SLEEP preset
    bool is_sleep = (this->preset.value_or(climate::CLIMATE_PRESET_NONE) == climate::CLIMATE_PRESET_SLEEP);
    bool is_eco = (this->preset.value_or(climate::CLIMATE_PRESET_NONE) == climate::CLIMATE_PRESET_ECO);
    
    // Byte 2: Protocol identifier
    frame[1] = is_sleep ? SOLEUS_BYTE2_SLEEP : SOLEUS_BYTE2_NORMAL;
    
    // Byte 3: Fan speed and mode
    uint8_t fan_speed_base = 0;
    switch (this->fan_mode.value_or(climate::CLIMATE_FAN_MEDIUM)) {
      case climate::CLIMATE_FAN_LOW:
        fan_speed_base = 0x10;
        break;
      case climate::CLIMATE_FAN_MEDIUM:
        fan_speed_base = 0x20;
        break;
      case climate::CLIMATE_FAN_HIGH:
        fan_speed_base = 0x30;
        break;
      default:
        fan_speed_base = 0x20;
        break;
    }
    
    // Determine mode nibble based on current mode and preset
    if (this->mode == climate::CLIMATE_MODE_FAN_ONLY) {
      frame[2] = fan_speed_base | 0x03;  // FAN only mode
      frame[4] = SOLEUS_BYTE5_FAN_ONLY;
    } else if (this->mode == climate::CLIMATE_MODE_AUTO) {
      frame[2] = fan_speed_base | 0x00;  // AUTO mode
      frame[4] = SOLEUS_BYTE5_AUTO;
    } else if (this->mode == climate::CLIMATE_MODE_DRY) {
      frame[2] = SOLEUS_FAN_DRY_LOW;  // DRY mode only supports LOW fan
      frame[4] = SOLEUS_BYTE5_DRY;
      // Force LOW fan mode for DRY
      this->fan_mode = climate::CLIMATE_FAN_LOW;
    } else if (this->mode == climate::CLIMATE_MODE_HEAT) {
      // HEAT mode - only available if supports_heat_ is true
      frame[2] = fan_speed_base | 0x01;  // Temperature control mode
      frame[4] = temp_to_protocol_(this->target_temperature);
      // TODO: Add heat-specific protocol bytes if different from cool
    } else if (is_sleep) {
      frame[2] = fan_speed_base | 0x06;  // SLEEP mode
      frame[4] = temp_to_protocol_(this->target_temperature);
    } else if (is_eco) {
      frame[2] = fan_speed_base | 0x05;  // ECO mode
      frame[4] = temp_to_protocol_(this->target_temperature);
    } else {
      // Normal temperature control mode (COOL)
      frame[2] = fan_speed_base | 0x01;  // Temperature control mode
      frame[4] = temp_to_protocol_(this->target_temperature);
    }
  }
  
  // Byte 4: Reserved (always 0x00)
  frame[3] = 0x00;
  
  // Bytes 6-8: Reserved (always 0x00)
  frame[5] = 0x00;
  frame[6] = 0x00;
  frame[7] = 0x00;
  
  // Byte 9: Checksum
  frame[8] = calculate_checksum_(frame[1], frame[2], frame[4]);
  
  // Convert to Pronto format and transmit
  std::vector<uint16_t> pronto_data;
  
  // Add header
  pronto_data.push_back(SOLEUS_HEADER_MARK);
  pronto_data.push_back(SOLEUS_HEADER_SPACE);
  
  // Convert bytes to IR pulses
  for (int i = 0; i < 9; i++) {
    for (int bit = 7; bit >= 0; bit--) {
      pronto_data.push_back(SOLEUS_BIT_MARK);
      if (frame[i] & (1 << bit)) {
        pronto_data.push_back(SOLEUS_ONE_SPACE);
      } else {
        pronto_data.push_back(SOLEUS_ZERO_SPACE);
      }
    }
  }
  
  // Add trailing mark
  pronto_data.push_back(SOLEUS_BIT_MARK);
  
  ESP_LOGD(TAG, "Sending Soleus code: %02X %02X %02X %02X %02X %02X %02X %02X %02X", 
           frame[0], frame[1], frame[2], frame[3], frame[4], frame[5], frame[6], frame[7], frame[8]);
  
  transmit_pronto_(pronto_data);
}

bool SoleusClimate::on_receive(remote_base::RemoteReceiveData data) {
  uint8_t frame[9] = {0};
  int byte_index = 0;
  int bit_index = 7;
  
  // Check header
  if (!data.expect_item(SOLEUS_HEADER_MARK, SOLEUS_HEADER_SPACE))
    return false;
  
  // Decode 72 bits (9 bytes)
  for (int i = 0; i < 72; i++) {
    if (data.expect_item(SOLEUS_BIT_MARK, SOLEUS_ONE_SPACE)) {
      frame[byte_index] |= (1 << bit_index);
    } else if (data.expect_item(SOLEUS_BIT_MARK, SOLEUS_ZERO_SPACE)) {
      // Bit is already 0
    } else {
      return false;
    }
    
    bit_index--;
    if (bit_index < 0) {
      bit_index = 7;
      byte_index++;
    }
  }
  
  // Verify it's a Soleus protocol frame
  if (frame[0] != SOLEUS_BYTE1_DEVICE)
    return false;
  
  // Verify checksum
  uint8_t expected_checksum = calculate_checksum_(frame[1], frame[2], frame[4]);
  
  if (frame[8] != expected_checksum) {
    ESP_LOGW(TAG, "Invalid checksum: expected %02X, got %02X", expected_checksum, frame[8]);
    return false;
  }
  
  ESP_LOGD(TAG, "Received Soleus code: %02X %02X %02X %02X %02X %02X %02X %02X %02X", 
           frame[0], frame[1], frame[2], frame[3], frame[4], frame[5], frame[6], frame[7], frame[8]);
  
  return parse_state_frame_(frame);
}

bool SoleusClimate::parse_state_frame_(const uint8_t frame[]) {
  // Check for power off
  if (frame[1] == SOLEUS_BYTE2_POWER_OFF) {
    this->mode = climate::CLIMATE_MODE_OFF;
    this->publish_state();
    return true;
  }
  
  // Parse fan speed (upper nibble of byte 3)
  uint8_t fan_speed = frame[2] & 0xF0;
  switch (fan_speed) {
    case 0x10:
      this->fan_mode = climate::CLIMATE_FAN_LOW;
      break;
    case 0x20:
      this->fan_mode = climate::CLIMATE_FAN_MEDIUM;
      break;
    case 0x30:
      this->fan_mode = climate::CLIMATE_FAN_HIGH;
      break;
  }
  
  // Parse mode (lower nibble of byte 3)
  uint8_t mode_nibble = frame[2] & 0x0F;
  
  // Check if SLEEP mode (byte 2 = 0x81)
  bool is_sleep = (frame[1] == SOLEUS_BYTE2_SLEEP);
  
  switch (mode_nibble) {
    case 0x0:  // AUTO mode
      this->mode = climate::CLIMATE_MODE_AUTO;
      this->preset = climate::CLIMATE_PRESET_NONE;
      break;
      
    case 0x1:  // Temperature control mode (COOL or HEAT depending on unit)
      this->mode = climate::CLIMATE_MODE_COOL;  // Default to COOL
      this->preset = climate::CLIMATE_PRESET_NONE;
      this->target_temperature = protocol_to_temp_(frame[4]);
      break;
      
    case 0x2:  // DRY mode
      this->mode = climate::CLIMATE_MODE_DRY;
      this->preset = climate::CLIMATE_PRESET_NONE;
      this->fan_mode = climate::CLIMATE_FAN_LOW;
      break;
      
    case 0x3:  // FAN only mode
      this->mode = climate::CLIMATE_MODE_FAN_ONLY;
      this->preset = climate::CLIMATE_PRESET_NONE;
      break;
      
    case 0x5:  // ECO mode
      this->mode = climate::CLIMATE_MODE_COOL;
      this->preset = climate::CLIMATE_PRESET_ECO;
      this->target_temperature = protocol_to_temp_(frame[4]);
      break;
      
    case 0x6:  // SLEEP mode
      this->mode = climate::CLIMATE_MODE_COOL;
      this->preset = climate::CLIMATE_PRESET_SLEEP;
      this->target_temperature = protocol_to_temp_(frame[4]);
      break;
  }
  
  this->publish_state();
  return true;
}

void SoleusClimate::transmit_pronto_(const std::vector<uint16_t> &data) {
  auto transmit = this->transmitter_->transmit();
  auto *transmit_data = transmit.get_data();
  
  transmit_data->set_carrier_frequency(38000);
  transmit_data->reserve(data.size());
  
  for (size_t i = 0; i < data.size(); i += 2) {
    if (i + 1 < data.size()) {
      transmit_data->item(data[i], data[i + 1]);
    } else {
      transmit_data->mark(data[i]);
    }
  }
  
  transmit.perform();
}

uint8_t SoleusClimate::temp_to_protocol_(float temp_c) const {
  float temp_f = (temp_c * 9.0f / 5.0f) + 32.0f;
  temp_f = std::max(static_cast<float>(SOLEUS_TEMP_MIN), std::min(static_cast<float>(SOLEUS_TEMP_MAX), temp_f));
  return SOLEUS_TEMP_BASE + static_cast<uint8_t>(temp_f - SOLEUS_TEMP_MIN);
}

float SoleusClimate::protocol_to_temp_(uint8_t value) const {
  float temp_f = static_cast<float>(value - SOLEUS_TEMP_BASE + SOLEUS_TEMP_MIN);
  return (temp_f - 32.0f) * 5.0f / 9.0f;
}

uint8_t SoleusClimate::calculate_checksum_(uint8_t byte2, uint8_t byte3, uint8_t byte5) const {
  return (byte2 + byte3 + byte5) & 0xFF;
}

}  // namespace soleus
}  // namespace esphome
