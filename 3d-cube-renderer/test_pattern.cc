#include "test_pattern.h"
#include "config_loader.h"
#include "scrolling_textbox.h"
#include "../rpi-rgb-led-matrix/include/led-matrix.h"
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <unistd.h>
#include <iostream>

using rgb_matrix::Canvas;
using rgb_matrix::RGBMatrix;
using rgb_matrix::Color;
using rgb_matrix::RuntimeOptions;

int main(int argc, char* argv[]) {
    // Load configuration
    RGBMatrix::Options matrix_options;
    RuntimeOptions runtime_options;
    CubeRendererOptions renderer_options;
    
    // Set defaults
    renderer_options.num_cubes = 3;
    renderer_options.cube_size = 2.5f;
    renderer_options.light_r = 255;
    renderer_options.light_g = 255;
    renderer_options.light_b = 200;
    renderer_options.shadow_r = 100;
    renderer_options.shadow_g = 100;
    renderer_options.shadow_b = 100;
    renderer_options.frame_rate_ms = 33;
    
    // Try to load from config file
    if (!LoadConfigFromFile("config.json", matrix_options, runtime_options, renderer_options)) {
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
    
    // Colors
    Color colorLight(renderer_options.light_r, renderer_options.light_g, renderer_options.light_b);
    Color colorShadow(renderer_options.shadow_r, renderer_options.shadow_g, renderer_options.shadow_b);
    Color colorBlack(0, 0, 0);
    
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
                             0, textbox_y,
                             display_width/2, textbox_height,
                             font,
                             colorLight,
                             "LED Matrix Test Pattern – scrolling text demo",
                             20.0f,   // px per second
                             1.0f,    // wait before scrolling
                             10);     // gap between repeats
    
    // Vertical bouncing box parameters
    const int box_width = 15; 
    const int box_height = std::max(0, display_height - textbox_height - 2); 
    float box_x = 0.0f; 
    int box_dir = 1; // 1 = moving right, -1 = moving left 
    const float box_speed = 40.0f; // pixels per second (slower)
    const float frame_dt = renderer_options.frame_rate_ms / 1000.0f;
    
    // Display loop (hold the pattern)
    while (true) {
        // Draw base pattern to the offscreen frame canvas
        for (int y = 0; y < display_height; y++) {
            for (int x = 0; x < display_width; x++) {
                int shade = pattern.framebuffer[y][x];
                Color color;
                switch (shade) {
                    case 2: color = colorLight; break;
                    case 1: color = colorShadow; break;
                    default: color = colorBlack; break;
                }
                canvas->SetPixel(x, y, color.r, color.g, color.b);
            }
        }

        // Update bouncing box position and color
        {
            int max_x = std::max(0, display_width - box_width);
            box_x += box_dir * box_speed * frame_dt;
            if (box_x < 0.0f) { box_x = 0.0f; box_dir = 1; }
            if (box_x > max_x) { box_x = (float)max_x; box_dir = -1; }

            // advance hue
            // initialize hue variables if missing
            static float box_hue = 0.0f;
            const float hue_speed = 30.0f; // degrees per second
            box_hue += hue_speed * frame_dt;
            if (box_hue >= 360.0f) box_hue -= 360.0f;

            auto hsv_to_rgb = [](float h, float s, float v){
                float C = v * s;
                float X = C * (1 - fabs(fmod(h / 60.0f, 2) - 1));
                float m = v - C;
                float r=0,g=0,b=0;
                if (h < 60) { r = C; g = X; b = 0; }
                else if (h < 120) { r = X; g = C; b = 0; }
                else if (h < 180) { r = 0; g = C; b = X; }
                else if (h < 240) { r = 0; g = X; b = C; }
                else if (h < 300) { r = X; g = 0; b = C; }
                else { r = C; g = 0; b = X; }
                uint8_t R = (uint8_t)std::round((r + m) * 255.0f);
                uint8_t G = (uint8_t)std::round((g + m) * 255.0f);
                uint8_t B = (uint8_t)std::round((b + m) * 255.0f);
                return rgb_matrix::Color(R,G,B);
            };

            rgb_matrix::Color boxColor = hsv_to_rgb(box_hue, 1.0f, 0.8f);

            int ix = (int)std::round(box_x);
            // Draw filled vertical box so background is covered
            for (int y = 0; y < box_height; y++) {
                for (int bx = 0; bx < box_width; bx++) {
                    int px = ix + bx;
                    if (px >= 0 && px < display_width) {
                        canvas->SetPixel(px, y, boxColor.r, boxColor.g, boxColor.b);
                    }
                }
            }
        }

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
