#include "../include/scrolling_box.h"
#include "../include/scrolling_textbox.h"
#include <../rpi-rgb-led-matrix/include/led-matrix.h>
#include <iostream>
#include <thread>

using rgb_matrix::Canvas;
using rgb_matrix::RGBMatrix;
using rgb_matrix::Color;
using rgb_matrix::RuntimeOptions;

int main(int argc, char* argv[]) {
    RGBMatrix::Options matrix_options;
    RuntimeOptions runtime_options;

    // Defaults (safe for many LED matrices)
    matrix_options.rows = 32;
    matrix_options.cols = 32;
    matrix_options.chain_length = 1;
    matrix_options.parallel = 1;
    runtime_options.do_gpio_init = false; // for desktop testing without GPIO

    RGBMatrix* matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_options);
    if (!matrix) {
        std::cerr << "Unable to create matrix\n";
        return 1;
    }

    rgb_matrix::FrameCanvas *offscreen = matrix->CreateFrameCanvas();
    Canvas* canvas = offscreen;
    const int width = canvas->width();
    const int height = canvas->height();

    // Load font
    rgb_matrix::Font font;
    if (!font.LoadFont("../rpi-rgb-led-matrix/fonts/5x7.bdf")) {
        std::cerr << "Failed to load font\n";
        return 1;
    }

    // Example multi-line content that will overflow vertically
    std::string content;
    for (int i = 1; i <= 30; ++i) {
        content += "Line ";
        content += std::to_string(i);
        content += " - This is a sample scrolling box line\n";
    }

    // White text color
    Color white(255,255,255);

    // Create ScrollingBox occupying full display
    ScrollingBox box(canvas, 0, 0, width, height, font, white, content, 20.0f, 2.0f, 4);

    // Main loop
    while (true) {
        canvas->Clear();
        box.SetCanvas(canvas);
        box.Update();
        offscreen = matrix->SwapOnVSync(offscreen);
        canvas = offscreen;
        std::this_thread::sleep_for(std::chrono::milliseconds(16));
    }

    delete matrix;
    return 0;
}
