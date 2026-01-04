#include "cube_renderer.h"
#include "config_loader.h"
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
    srand(time(nullptr));
    
    // Load configuration
    RGBMatrix::Options matrix_options;
    RuntimeOptions runtime_options;
    CubeRendererOptions renderer_options;
    
    // Set defaults
    renderer_options.num_cubes = 3;
    renderer_options.cube_size = 2.5f;
    renderer_options.rotation_speed_x = 0.7f;
    renderer_options.rotation_speed_y = 0.5f;
    renderer_options.rotation_speed_z = 0.3f;
    renderer_options.position_animation_speed = 0.5f;
    renderer_options.position_animation_amplitude = 2.0f;
    renderer_options.light_r = 255;
    renderer_options.light_g = 255;
    renderer_options.light_b = 200;
    renderer_options.shadow_r = 100;
    renderer_options.shadow_g = 100;
    renderer_options.shadow_b = 100;
    renderer_options.light_dir_x = 0.8f;
    renderer_options.light_dir_y = 0.6f;
    renderer_options.light_dir_z = 1.0f;
    renderer_options.focal_length = 5.0f;
    renderer_options.frame_rate_ms = 33;
    
    // Try to load from config file
    if (!LoadConfigFromFile("config.json", matrix_options, runtime_options, renderer_options)) {
        std::cerr << "Warning: Could not load config.json, using defaults\n";
        // Set some basic defaults
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
    
    Canvas* canvas = matrix;
    
    // Calculate actual display dimensions accounting for chain_length, parallel, and pixel mapper
    int display_width, display_height;
    GetDisplayDimensions(matrix_options, display_width, display_height);
    
    std::cout << "Display resolution: " << display_width << "x" << display_height << std::endl;
    
    // Colors from config
    Color colorLight(renderer_options.light_r, renderer_options.light_g, renderer_options.light_b);
    Color colorShadow(renderer_options.shadow_r, renderer_options.shadow_g, renderer_options.shadow_b);
    Color colorBlack(0, 0, 0);
    
    CubeRenderer renderer(display_width, display_height);
    renderer.lightDirection = Vec3(renderer_options.light_dir_x, renderer_options.light_dir_y, renderer_options.light_dir_z).normalized();
    
    std::vector<Cube> cubes;
    
    // Create generative pattern: rotating cubes at different depths
    for (int i = 0; i < renderer_options.num_cubes; i++) {
        Cube c(renderer_options.cube_size);
        c.position = Vec3((i - 1) * 4, 0, -8 + i * 3);
        cubes.push_back(c);
    }
    
    float time = 0;
    int frame = 0;
    float frametime = renderer_options.frame_rate_ms * 1000.0f;  // Convert to microseconds
    float deltaTime = frametime / 1000000.0f;  // Convert to seconds
    
    // Animation loop
    while (true) {
        renderer.clear();
        
        // Animate cubes
        for (size_t i = 0; i < cubes.size(); i++) {
            cubes[i].rotation.x = time * renderer_options.rotation_speed_x + i * 2.094f;
            cubes[i].rotation.y = time * renderer_options.rotation_speed_y + i * 2.094f;
            cubes[i].rotation.z = time * renderer_options.rotation_speed_z;
            
            // Position animation
            cubes[i].position.y = std::sin(time * renderer_options.position_animation_speed + i) * renderer_options.position_animation_amplitude;
        }
        
        // Render all cubes
        for (const auto& cube : cubes) {
            renderer.renderCube(cube);
        }
        
        // Draw to LED matrix
        for (int y = 0; y < display_height; y++) {
            for (int x = 0; x < display_width; x++) {
                int shade = renderer.framebuffer[y][x];
                Color color;
                switch (shade) {
                    case 2: color = colorLight; break;
                    case 1: color = colorShadow; break;
                    default: color = colorBlack; break;
                }
                canvas->SetPixel(x, y, color.r, color.g, color.b);
            }
        }
        
        usleep((useconds_t)frametime);
        time += deltaTime;
        frame++;
        
        if (frame % 100 == 0) {
            std::cout << "Frame: " << frame << std::endl;
        }
    }
    
    delete matrix;
    return 0;
}
