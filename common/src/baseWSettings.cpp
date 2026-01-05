// BaseWSettings implementation moved into common/

#include "baseWSettings.h"

#include <iostream>
#include <memory>
#include <string>
#include <csignal>

#include <led-matrix.h>
#include <graphics.h>
#include <yaml-cpp/yaml.h>

#include <thread>

namespace {
    static volatile bool g_exit_requested = false;
    void SignalHandler(int signo) { (void)signo; g_exit_requested = true; }
}

struct BaseWSettings::Impl {
    Impl(const std::string& settings_file)
        : settings_file(settings_file), matrix(nullptr), canvas(nullptr) {}

    ~Impl() {
        if (matrix) {
            matrix->Clear();
            delete matrix;
            matrix = nullptr;
        }
    }

    bool LoadSettings() {
        try {
            settings = YAML::LoadFile(settings_file);
        } catch (const std::exception& e) {
            std::cerr << "YAML load error: " << e.what() << "\n";
            return false;
        }
        return true;
    }

    bool CreateMatrix() {
        rgb_matrix::RGBMatrix::Options matrix_opts;
        rgb_matrix::RuntimeOptions runtime_opts;

        auto getInt = [&](const std::string& key, int def)->int {
            if (settings[std::string(key)]) return settings[std::string(key)].as<int>();
            return def;
        };
        auto getBool = [&](const std::string& key, bool def)->bool {
            if (settings[std::string(key)]) return settings[std::string(key)].as<bool>();
            return def;
        };
        auto getString = [&](const std::string& key, const std::string& def)->std::string {
            if (settings[std::string(key)]) return settings[std::string(key)].as<std::string>();
            return def;
        };

        auto readDimension = [&](const std::string& plain, const std::string& pref, int def){
            if (settings[plain]) return settings[plain].as<int>();
            if (settings[pref]) return settings[pref].as<int>();
            return def;
        };

        matrix_opts.rows = readDimension("rows", "led-rows", 32);
        matrix_opts.cols = readDimension("cols", "led-cols", 64);
        matrix_opts.chain_length = readDimension("chain", "led-chain", 1);
        matrix_opts.parallel = readDimension("parallel", "led-parallel", 1);
        matrix_opts.pwm_bits = getInt("pwm_bits", 11);
        matrix_opts.brightness = getInt("brightness", 100);
        hardware_mapping_storage = getString("hardware_mapping", getString("led-gpio-mapping", "regular"));
        matrix_opts.hardware_mapping = hardware_mapping_storage.c_str();

        runtime_opts.gpio_slowdown = getInt("gpio_slowdown", getInt("led-slowdown-gpio", 1));
        matrix_opts.disable_hardware_pulsing = getBool("disable_hardware_pulsing", false);

        if (settings[std::string("pwm_lsb_nanoseconds")]) {
            matrix_opts.pwm_lsb_nanoseconds = settings[std::string("pwm_lsb_nanoseconds")].as<int>();
        }

        matrix = rgb_matrix::CreateMatrixFromOptions(matrix_opts, runtime_opts);
        if (!matrix) {
            std::cerr << "CreateMatrixFromOptions returned null\n";
            return false;
        }
        canvas = matrix->CreateFrameCanvas();
        if (!canvas) {
            std::cerr << "Failed to get Canvas from matrix\n";
            delete matrix;
            matrix = nullptr;
            return false;
        }
        return true;
    }

    void SetupSignalHandlers() {
        std::signal(SIGTERM, SignalHandler);
        std::signal(SIGINT, SignalHandler);
    }

    // members
    std::string settings_file;
    YAML::Node settings;
    std::string hardware_mapping_storage;
    rgb_matrix::RGBMatrix* matrix;
    rgb_matrix::FrameCanvas* canvas;
};

BaseWSettings::BaseWSettings(const std::string& settings_file)
  : impl_(new Impl(settings_file)) {}

BaseWSettings::~BaseWSettings() = default;

bool BaseWSettings::Init() {
    if (!impl_->LoadSettings()) return false;
    if (!impl_->CreateMatrix()) return false;
    return true;
}

void BaseWSettings::Start() {
    impl_->SetupSignalHandlers();
    if (!Init()) return;
    Run();
    if (impl_->matrix) impl_->matrix->Clear();
}

void BaseWSettings::WaitExitOrDelay(int ms) {
    int slept = 0;
    while (!g_exit_requested && slept < ms) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        ++slept;
    }
}

bool BaseWSettings::ExitRequested() const { return g_exit_requested; }

int BaseWSettings::canvas_width() const {
    return impl_->canvas ? impl_->canvas->width() : 0;
}

int BaseWSettings::canvas_height() const {
    return impl_->canvas ? impl_->canvas->height() : 0;
}

void BaseWSettings::set_pixel(int x, int y, int r, int g, int b) {
    if (impl_->canvas) impl_->canvas->SetPixel(x, y, r, g, b);
}

void BaseWSettings::clear_canvas() {
    if (impl_->canvas) impl_->canvas->Clear();
}

void BaseWSettings::swap_on_vsync() {
    if (!impl_->matrix || !impl_->canvas) return;
    impl_->canvas = impl_->matrix->SwapOnVSync(impl_->canvas);
}

int BaseWSettings::get_int_setting(const std::string& key, int def) const {
    try {
        if (impl_->settings[key]) return impl_->settings[key].as<int>();
    } catch (...) {}
    return def;
}

double BaseWSettings::get_double_setting(const std::string& key, double def) const {
    try {
        if (impl_->settings[key]) return impl_->settings[key].as<double>();
    } catch (...) {}
    return def;
}

bool BaseWSettings::get_bool_setting(const std::string& key, bool def) const {
    try {
        if (impl_->settings[key]) return impl_->settings[key].as<bool>();
    } catch (...) {}
    return def;
}

bool BaseWSettings::has_setting(const std::string& key) const {
    try { return bool(impl_->settings[key]); } catch (...) { return false; }
}
