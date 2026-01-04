#include "cube_renderer.h"
#include "../rpi-rgb-led-matrix/include/led-matrix.h"
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <unistd.h>
#include <iostream>

using rgb_matrix::Canvas;
using rgb_matrix::RGBMatrix;
using rgb_matrix::Color;

int main(int argc, char* argv[]) {
    srand(time(nullptr));
    
    // LED matrix setup
    RGBMatrix::Options matrix_options;
    matrix_options.rows = 32;
    matrix_options.cols = 32;
    matrix_options.chain_length = 1;
    matrix_options.parallel = 1;
    matrix_options.brightness = 100;
    
    RGBMatrix::RuntimeOptions runtime_options;
    RGBMatrix* matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_options);
    if (matrix == NULL) {
        std::cerr << "Unable to create matrix\n";
        return 1;
    }
    
    Canvas* canvas = matrix;
    
    // Colors: light, shadow, black
    Color colorLight(255, 255, 200);   // Bright yellow-white
    Color colorShadow(100, 100, 100);  // Dark gray
    Color colorBlack(0, 0, 0);         // Black
    
    CubeRenderer renderer(32, 32);
    renderer.lightDirection = Vec3(0.8f, 0.6f, 1.0f).normalized();
    
    std::vector<Cube> cubes;
    
    // Create generative pattern: rotating cubes at different depths
    for (int i = 0; i < 3; i++) {
        Cube c(2.5f);
        c.position = Vec3((i - 1) * 4, 0, -8 + i * 3);
        cubes.push_back(c);
    }
    
    float time = 0;
    int frame = 0;
    
    // Animation loop
    while (true) {
        renderer.clear();
        
        // Animate cubes
        for (size_t i = 0; i < cubes.size(); i++) {
            cubes[i].rotation.x = time * 0.7f + i * 2.094f;
            cubes[i].rotation.y = time * 0.5f + i * 2.094f;
            cubes[i].rotation.z = time * 0.3f;
            
            // Gentle position animation
            cubes[i].position.y = std::sin(time * 0.5f + i) * 2;
        }
        
        // Render all cubes
        for (const auto& cube : cubes) {
            renderer.renderCube(cube);
        }
        
        // Draw to LED matrix
        for (int y = 0; y < 32; y++) {
            for (int x = 0; x < 32; x++) {
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
        
        usleep(30000);  // ~30fps
        time += 0.016f;
        frame++;
        
        if (frame % 100 == 0) {
            std::cout << "Frame: " << frame << std::endl;
        }
    }
    
    delete matrix;
    return 0;
}
