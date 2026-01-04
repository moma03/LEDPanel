#include "cube_renderer.h"
#include "config_loader.h"
#include "../rpi-rgb-led-matrix/include/led-matrix.h"
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <unistd.h>
#include <iostream>
#include <vector>

using rgb_matrix::Canvas;
using rgb_matrix::RGBMatrix;
using rgb_matrix::Color;
using rgb_matrix::RuntimeOptions;

struct FallingCube {
    Vec3 position;
    Vec3 rotation;
    float velocity_y;
    float drift_x;
    float size;
    
    FallingCube(float x, float y, float z, float size = 1.5f) 
        : position(x, y, z), rotation(0, 0, 0), size(size) {
        velocity_y = 0.5f + (rand() % 100) / 200.0f;  // 0.5 to 1.0
        drift_x = (rand() % 200 - 100) / 500.0f;      // -0.2 to 0.2
    }
    
    void update(float time) {
        position.y += velocity_y;
        position.x += drift_x;
        rotation.x = time * 1.2f;
        rotation.y = time * 0.8f;
        rotation.z = time * 0.5f;
    }
};

int main(int argc, char* argv[]) {
    srand(time(nullptr));
    
    // Load configuration
    RGBMatrix::Options matrix_options;
    RuntimeOptions runtime_options;
    CubeRendererOptions renderer_options;
    
    // Set defaults
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
    
    // Calculate actual display dimensions
    int display_width, display_height;
    GetDisplayDimensions(matrix_options, display_width, display_height);
    
    std::cout << "Display resolution: " << display_width << "x" << display_height << std::endl;
    std::cout << "Falling cubes animation running. Press Ctrl+C to exit.\n";
    
    // Colors
    Color colorLight(renderer_options.light_r, renderer_options.light_g, renderer_options.light_b);
    Color colorShadow(renderer_options.shadow_r, renderer_options.shadow_g, renderer_options.shadow_b);
    Color colorBlack(0, 0, 0);
    
    CubeRenderer renderer(display_width, display_height);
    renderer.lightDirection = Vec3(renderer_options.light_dir_x, renderer_options.light_dir_y, renderer_options.light_dir_z).normalized();
    
    std::vector<FallingCube> cubes;
    
    float time = 0;
    int frame = 0;
    float spawn_timer = 0;
    float spawn_interval = 0.3f;  // Spawn a cube every 0.3 seconds
    
    // Animation loop
    while (true) {
        renderer.clear();
        
        // Spawn new cubes at the top
        spawn_timer += 0.016f;  // Approximate frame time
        if (spawn_timer >= spawn_interval) {
            spawn_timer = 0;
            float random_x = (rand() % (display_width - 5)) - display_width / 2.0f;
            cubes.push_back(FallingCube(random_x, -10, -8, 1.5f));
        }
        
        // Update and render cubes
        for (auto it = cubes.begin(); it != cubes.end(); ) {
            it->update(time);
            
            // Remove cubes that have fallen off the bottom
            if (it->position.y > display_height + 5) {
                it = cubes.erase(it);
            } else {
                // Render the cube
                Cube c(it->size);
                c.position = it->position;
                c.rotation = it->rotation;
                renderer.renderCube(c);
                ++it;
            }
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
        
        usleep((useconds_t)(renderer_options.frame_rate_ms * 1000));
        time += 0.016f;
        frame++;
        
        if (frame % 100 == 0) {
            std::cout << "Frame: " << frame << " | Active cubes: " << cubes.size() << std::endl;
        }
    }
    
    delete matrix;
    return 0;
}
