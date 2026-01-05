// baseWSettings.h
// Lightweight, stable interface for applications that use the rpi-rgb-led-matrix.
// Implementation details (yaml-cpp and led-matrix headers) are hidden in the .cpp

#pragma once

#include <memory>
#include <string>

namespace rgb_matrix { class RGBMatrix; class Canvas; class GPIO; }
namespace YAML { class Node; }

class BaseWSettings {
public:
    explicit BaseWSettings(const std::string& settings_file);
    virtual ~BaseWSettings();

    // Load settings and create the matrix. Returns true on success.
    bool Init();

    // Install signal handlers and run the derived app. Calls Init() internally.
    void Start();

    // Derived classes implement drawing behavior here.
    virtual void Run() = 0;

protected:
    // Accessors available to derived classes (implemented in the .cpp)
    // Canvas accessors and drawing helpers (no heavy headers required)
    int canvas_width() const;
    int canvas_height() const;
    void set_pixel(int x, int y, int r, int g, int b);
    void clear_canvas();
    void swap_on_vsync();

    // Settings accessors
    int get_int_setting(const std::string& key, int def) const;
    double get_double_setting(const std::string& key, double def) const;
    bool get_bool_setting(const std::string& key, bool def) const;
    bool has_setting(const std::string& key) const;

    // Sleep for up to 'ms' milliseconds but return early if exit requested.
    void WaitExitOrDelay(int ms = 16);
    bool ExitRequested() const;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
