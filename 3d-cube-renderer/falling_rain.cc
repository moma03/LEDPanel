#include "cube_renderer.h"
#include "cube_renderer_options.h"
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
    
    // Try to load matrix/runtime config from config file (renderer options
    // are local to this example and kept as defaults).
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
    // configure renderer blended colors
    renderer.light_r = colorLight.r;
    renderer.light_g = colorLight.g;
    renderer.light_b = colorLight.b;
    renderer.shadow_r = colorShadow.r;
    renderer.shadow_g = colorShadow.g;
    renderer.shadow_b = colorShadow.b;
    
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
        for (auto &cobj : cubes) {
            cobj.update(time);

            // Projective coordinates vary; use a simple screen-space test by
            // approximating projection: screen_y = world_y * (f / (z+f)) + display_height/2
            const float focal = 5.0f; // matches renderer's focal length default
            float z = cobj.position.z + focal;
            if (z <= 0.1f) z = 0.1f;
            float scale = focal / z;
            float screen_y = cobj.position.y * scale + display_height / 2.0f;

            // If below screen, teleport back to top and give a new fixed random velocity
            if (screen_y > display_height + 5) {
                // place above the top in world coords (choose a negative world y)
                // pick a screen target around -10 pixels and convert back to world y
                float target_screen_y = -10.0f;
                float world_y = (target_screen_y - display_height / 2.0f) / scale;
                cobj.position.y = world_y;
                // randomize horizontal position within display width (in world units)
                float rx = static_cast<float>(rand() % (display_width - 5)) - display_width / 2.0f;
                cobj.position.x = rx;
                // new fixed velocity (no acceleration)
                cobj.velocity_y = 0.1f + (rand() % 100) / 200.0f;  // 0.5 to 1.0
                cobj.drift_x = (rand() % 200 - 100) / 500.0f;      // -0.2 to 0.2
            }

            // Render the cube
            Cube c(cobj.size);
            c.position = cobj.position;
            c.rotation = cobj.rotation;
            renderer.renderCube(c);
        }
        
        // Draw to LED matrix
        for (int y = 0; y < display_height; y++) {
            for (int x = 0; x < display_width; x++) {
                uint32_t packed = renderer.framebuffer[y][x];
                uint8_t r = (packed >> 16) & 0xFF;
                uint8_t g = (packed >> 8) & 0xFF;
                uint8_t b = packed & 0xFF;
                canvas->SetPixel(x, y, r, g, b);
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
