#pragma once
#include "led-matrix.h"
#include "graphics.h"
#include <string>
#include <chrono>

class ScrollingTextBox {
public:
    ScrollingTextBox(rgb_matrix::Canvas *canvas,
                     int x, int y, int width, int height,
                     const rgb_matrix::Font &font,
                     const rgb_matrix::Color &color,
                     const std::string &text,
                     int speed = 1,
                     float wait_time = 1.0f,
                     bool endless = false);

    void Update();

private:
    rgb_matrix::Canvas *canvas_;
    int x_, y_, w_, h_;
    const rgb_matrix::Font &font_;
    rgb_matrix::Color color_;
    std::string text_;
    int speed_;
    float wait_time_;
    bool endless_;

    int text_width_;
    int offset_x_;
    std::chrono::steady_clock::time_point last_reset_time_;
};