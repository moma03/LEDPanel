#include "config_loader.h"

#include <fstream>
#include <cstring>

#include <json.hpp>

using json = nlohmann::json;
using namespace rgb_matrix;

bool LoadMatrixOptionsFromConfig(const std::string& path,
                                 RGBMatrix::Options& matrix_options,
                                 rgb_matrix::RuntimeOptions& runtime_opt) {
  std::ifstream config_file(path);
  if (!config_file.is_open()) {
    return false;
  }

  json cfg = json::parse(config_file);

  for (auto& element : cfg["matrix_options"].items()) {
    const std::string& key = element.key();
    const json& value = element.value();

    if (key == "hardware_mapping") {
      matrix_options.hardware_mapping = strdup(value.get<std::string>().c_str());
    } else if (key == "rows") {
      matrix_options.rows = value.get<int>();
    } else if (key == "cols") {
      matrix_options.cols = value.get<int>();
    } else if (key == "chain_length") {
      matrix_options.chain_length = value.get<int>();
    } else if (key == "parallel") {
      matrix_options.parallel = value.get<int>();
    } else if (key == "pwm_bits") {
      matrix_options.pwm_bits = value.get<int>();
    } else if (key == "pwm_lsb_nanoseconds") {
      matrix_options.pwm_lsb_nanoseconds = value.get<int>();
    } else if (key == "pwm_dither_bits") {
      matrix_options.pwm_dither_bits = value.get<int>();
    } else if (key == "brightness") {
      matrix_options.brightness = value.get<int>();
    } else if (key == "scan_mode") {
      matrix_options.scan_mode = value.get<int>();
    } else if (key == "row_address_type") {
      matrix_options.row_address_type = value.get<int>();
    } else if (key == "multiplexing") {
      matrix_options.multiplexing = value.get<int>();
    } else if (key == "disable_hardware_pulsing") {
      matrix_options.disable_hardware_pulsing = value.get<bool>();
    } else if (key == "show_refresh_rate") {
      matrix_options.show_refresh_rate = value.get<bool>();
    } else if (key == "inverse_colors") {
      matrix_options.inverse_colors = value.get<bool>();
    } else if (key == "led_rgb_sequence") {
      matrix_options.led_rgb_sequence = strdup(value.get<std::string>().c_str());
    } else if (key == "pixel_mapper_config") {
      matrix_options.pixel_mapper_config = strdup(value.get<std::string>().c_str());
    } else if (key == "panel_type") {
      matrix_options.panel_type = strdup(value.get<std::string>().c_str());
    } else if (key == "limit_refresh_rate_hz") {
      matrix_options.limit_refresh_rate_hz = value.get<int>();
    } else if (key == "disable_busy_waiting") {
      matrix_options.disable_busy_waiting = value.get<bool>();
    } else if (key == "gpio_slowdown") {
      runtime_opt.gpio_slowdown = value.get<int>();
    } else if (key == "daemon") {
      runtime_opt.daemon = value.get<int>();
    } else if (key == "drop_privileges") {
      runtime_opt.drop_privileges = value.get<int>();
    } else if (key == "do_gpio_init") {
      runtime_opt.do_gpio_init = value.get<bool>();
    } else if (key == "drop_priv_user") {
      runtime_opt.drop_priv_user = strdup(value.get<std::string>().c_str());
    } else if (key == "drop_priv_group") {
      runtime_opt.drop_priv_group = strdup(value.get<std::string>().c_str());
    }
  }

  return true;
}
