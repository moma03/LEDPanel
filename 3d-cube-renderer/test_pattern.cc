#include "test_pattern.h"
#include "config_loader.h"
#include "scrolling_textbox.h"
#include "scrolling_box.h"
#include "../rpi-rgb-led-matrix/include/led-matrix.h"
#include <cmath>
#include <string>
#include <iostream>

using rgb_matrix::Canvas;
using rgb_matrix::RGBMatrix;
using rgb_matrix::Color;
using rgb_matrix::RuntimeOptions;

int main(int argc, char* argv[]) {
    // Load configuration
    RGBMatrix::Options matrix_options;
    RuntimeOptions runtime_options;
    
    // Try to load from config file
    if (!LoadConfigFromFile("config.json", matrix_options, runtime_options)) {
        std::cerr << "Warning: Could not load config.json, using defaults\n";
        matrix_options.rows = 32;
        matrix_options.cols = 32;
        matrix_options.chain_length = 1;
        matrix_options.parallel = 1;
    }
    
    // Ensure GPIO init is enabled
    runtime_options.do_gpio_init = true;
    
    RGBMatrix* matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_options);
    if (matrix == NULL) {
        std::cerr << "Unable to create matrix\n";
        return 1;
    }
    
    // Use an offscreen frame canvas and swap it each frame to avoid flicker.
    rgb_matrix::FrameCanvas *offscreen = matrix->CreateFrameCanvas();
    Canvas* canvas = offscreen;
    
    // Calculate actual display dimensions accounting for chain_length, parallel, and pixel mapper
    int display_width, display_height;
    GetDisplayDimensions(matrix_options, display_width, display_height);
    
    std::cout << "Display resolution: " << display_width << "x" << display_height << std::endl;
    std::cout << "Test pattern running. Press Ctrl+C to exit.\n";
    
    TestPattern pattern(display_width, display_height);
    
    // Generate pattern
    pattern.clear();
    pattern.drawCross();
    pattern.drawResolution(display_width, display_height);

    // Load font for scrolling text
    rgb_matrix::Font font;
    if (!font.LoadFont("../rpi-rgb-led-matrix/fonts/5x7.bdf")) {
        std::cerr << "Failed to load font 5x7.bdf" << std::endl;
        return 1;
    }

    // Scrolling text box (transparent background, clipped)
    // Place near bottom, height = font height + 2px padding
    int textbox_height = font.height() + 2;
    int textbox_y = display_height - textbox_height - 1;
    ScrollingTextBox marquee(canvas,
                             64, textbox_y,
                             display_width/2, textbox_height,
                             font,
                             Color(255, 255, 0), // yellow text
                             "LED Matrix Test Pattern – scrolling text demo",
                             20.0f,   // px per second
                             2.0f,    // wait before scrolling
                             10);     // gap between repeats
    
    // Vertical scrolling box parameters (replaces bouncing box)
    const int box_height = std::max(0, display_height - textbox_height - 2);
    const float frame_dt = 33 / 1000.0f;

    // Build sample multi-line content for the scrolling box
    std::string vcontent;
    for (int i = 1; i <= 30; ++i) {
        vcontent += "Line ";
        vcontent += std::to_string(i);
        vcontent += " - sample scrolling content\n";
    }

    // Create vertical ScrollingBox occupying area above the textbox
    ScrollingBox vbox(canvas, 0, 0, display_width, box_height, font, Color(255,255,0), vcontent, 20.0f, 2.0f, 4);
    
    // Display loop (hold the pattern)
    while (true) {
        // Update vertical scrolling box
        vbox.SetCanvas(canvas);
        vbox.Update();

        // Ensure the marquee draws into the current offscreen canvas, then update it.
        marquee.SetCanvas(canvas);
        marquee.Update();

        // Swap the offscreen buffer to the display (waits for vsync).
        offscreen = matrix->SwapOnVSync(offscreen);
        canvas = offscreen;
    }
    
    delete matrix;
    return 0;
}
