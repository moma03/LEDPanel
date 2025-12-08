// /Users/moritzmanegold/Desktop/Projects/LEDPanel/endles_gameOfLife/baseWSettings.cpp
//
// Base class for applications using rpi-rgb-led-matrix with settings loaded from settings.yaml
//
// Requirements:
//  - yaml-cpp (https://github.com/jbeder/yaml-cpp)
//  - rpi-rgb-led-matrix library (led-matrix.h)
// Build example (pkg-config):
//  g++ baseWSettings.cpp -o app `pkg-config --cflags --libs yaml-cpp` -lledmatrix -lpthread
//
// The class loads common matrix options from a YAML file, creates the matrix and exposes
// the rgb_matrix::Canvas and rgb_matrix::RGBMatrix objects to derived classes. Derived
// classes must implement Run() to perform drawing. Signal handling for clean exit is provided.

#include <iostream>
#include <memory>
#include <string>
#include <csignal>
// Implementation for BaseWSettings (keeps heavy dependencies out of the header)
#include "baseWSettings.h"

#include "led-matrix.h"
#include "graphics.h"
#include <yaml-cpp/yaml.h>

#include <iostream>
#include <thread>

namespace {
	// file-scoped exit flag for signal handling
	static volatile bool g_exit_requested = false;

	void SignalHandler(int signo) {
		(void)signo;
		g_exit_requested = true;
	}
}

struct BaseWSettings::Impl {
	Impl(const std::string& settings_file)
	  : settings_file(settings_file), matrix(nullptr), canvas(nullptr), io(new rgb_matrix::GPIO()) {}

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
			if (settings[key]) return settings[key].as<int>();
			return def;
		};
		auto getBool = [&](const std::string& key, bool def)->bool {
			if (settings[key]) return settings[key].as<bool>();
			return def;
		};
		auto getString = [&](const std::string& key, const std::string& def)->std::string {
			if (settings[key]) return settings[key].as<std::string>();
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
		matrix_opts.hardware_mapping = getString("hardware_mapping", getString("led-gpio-mapping", "regular"));

		runtime_opts.gpio_slowdown = getInt("gpio_slowdown", getInt("led-slowdown-gpio", 1));
		runtime_opts.disable_hardware_pulsing = getBool("disable_hardware_pulsing", false);
		runtime_opts.rows = matrix_opts.rows;

		if (settings["pwm_lsb_nanoseconds"]) {
			runtime_opts.pwm_lsb_nanoseconds = settings["pwm_lsb_nanoseconds"].as<int>();
		}

		matrix = rgb_matrix::CreateMatrixFromOptions(matrix_opts, runtime_opts, io.get());
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
	std::unique_ptr<rgb_matrix::GPIO> io;
	rgb_matrix::RGBMatrix* matrix;
	rgb_matrix::Canvas* canvas;
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

rgb_matrix::RGBMatrix* BaseWSettings::matrix() const { return impl_->matrix; }
rgb_matrix::Canvas* BaseWSettings::canvas() const { return impl_->canvas; }
const YAML::Node& BaseWSettings::settings() const { return impl_->settings; }

void BaseWSettings::WaitExitOrDelay(int ms) {
	int slept = 0;
	while (!g_exit_requested && slept < ms) {
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
		++slept;
	}
}

bool BaseWSettings::ExitRequested() const { return g_exit_requested; }

