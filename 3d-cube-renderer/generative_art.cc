#include "cube_renderer.h"
#include "cube_renderer_options.h"
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

// Helper: generate a UV sphere mesh
Mesh GenerateSphereMesh(const Vec3 &center, float radius, int latSegments, int lonSegments) {
    Mesh m;
    const int lonCount = lonSegments;
    const int latCount = latSegments;

    for (int lat = 0; lat <= latCount; ++lat) {
        float v = (float)lat / (float)latCount;
        float phi = v * M_PI; // 0..PI
        for (int lon = 0; lon <= lonCount; ++lon) {
            float u = (float)lon / (float)lonCount;
            float theta = u * 2.0f * M_PI; // 0..2PI
            float x = radius * std::sin(phi) * std::cos(theta);
            float y = radius * std::cos(phi);
            float z = radius * std::sin(phi) * std::sin(theta);
            m.vertices.emplace_back(center.x + x, center.y + y, center.z + z);
        }
    }

    // build faces (quads) between the latitude/longitude grid
    for (int lat = 0; lat < latCount; ++lat) {
        for (int lon = 0; lon < lonCount; ++lon) {
            int a = lat * (lonCount + 1) + lon;
            int b = a + 1;
            int c = a + (lonCount + 1);
            int d = c + 1;
            // make a quad face (a,b,d,c) - consistent winding
            m.faces.push_back({a, b, d, c});
        }
    }

    return m;
}

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
    
    // Try to load matrix/runtime config from config file (renderer options
    // are local to this example and kept as defaults).
    if (!LoadConfigFromFile("config.json", matrix_options, runtime_options)) {
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
    // configure renderer blended colors
    renderer.light_r = colorLight.r;
    renderer.light_g = colorLight.g;
    renderer.light_b = colorLight.b;
    renderer.shadow_r = colorShadow.r;
    renderer.shadow_g = colorShadow.g;
    renderer.shadow_b = colorShadow.b;
    
    // Create one cube in the center and a sphere next to it
    Cube cube(renderer_options.cube_size);
    cube.position = Vec3(0, 0, -8);

    // Sphere base mesh (center at origin) — we'll transform per-frame
    const float sphereRadius = renderer_options.cube_size * 0.9f;
    Mesh baseSphere = GenerateSphereMesh(Vec3(0,0,0), sphereRadius, 16, 16);
    Vec3 spherePosition(4.5f, 0.0f, -8.0f);
    
    float time = 0;
    int frame = 0;
    float frametime = renderer_options.frame_rate_ms * 1000.0f;  // Convert to microseconds
    float deltaTime = frametime / 1000000.0f;  // Convert to seconds
    
    // Animation loop
    while (true) {
        renderer.clear();
        
        // Animate cube
        cube.rotation.x = time * renderer_options.rotation_speed_x;
        cube.rotation.y = time * renderer_options.rotation_speed_y;
        cube.rotation.z = time * renderer_options.rotation_speed_z;
        cube.position.y = std::sin(time * renderer_options.position_animation_speed) * renderer_options.position_animation_amplitude;

        // Render cube
        renderer.renderCube(cube);

        // Transform and render sphere mesh: rotate and translate baseSphere per-frame
        // local rotation helpers
        auto rotateX = [](const Vec3 &v, float angle) {
            float c = std::cos(angle);
            float s = std::sin(angle);
            return Vec3(v.x, v.y * c - v.z * s, v.y * s + v.z * c);
        };
        auto rotateY = [](const Vec3 &v, float angle) {
            float c = std::cos(angle);
            float s = std::sin(angle);
            return Vec3(v.x * c + v.z * s, v.y, -v.x * s + v.z * c);
        };
        auto rotateZ = [](const Vec3 &v, float angle) {
            float c = std::cos(angle);
            float s = std::sin(angle);
            return Vec3(v.x * c - v.y * s, v.x * s + v.y * c, v.z);
        };

        Mesh sphereTransformed = baseSphere;
        for (auto &v : sphereTransformed.vertices) {
            Vec3 vv = v;
            vv = rotateX(vv, time * renderer_options.rotation_speed_x * 0.6f);
            vv = rotateY(vv, time * renderer_options.rotation_speed_y * 0.8f);
            vv = rotateZ(vv, time * renderer_options.rotation_speed_z * 0.4f);
            vv = vv + spherePosition;
            v = vv;
        }
        renderer.renderMesh(sphereTransformed);
        
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
        
        usleep((useconds_t)frametime);
        time += deltaTime;
        frame++;
    }
    
    delete matrix;
    return 0;
}
