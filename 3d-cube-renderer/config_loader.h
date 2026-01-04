#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H

#include <string>
#include "../rpi-rgb-led-matrix/include/led-matrix.h"

struct CubeRendererOptions {
    int num_cubes;
    float cube_size;
    float rotation_speed_x;
    float rotation_speed_y;
    float rotation_speed_z;
    float position_animation_speed;
    float position_animation_amplitude;
    int light_r, light_g, light_b;
    int shadow_r, shadow_g, shadow_b;
    float light_dir_x, light_dir_y, light_dir_z;
    float focal_length;
    int frame_rate_ms;
};

// Loads matrix and cube renderer options from a JSON config file
bool LoadConfigFromFile(const std::string& path,
                       rgb_matrix::RGBMatrix::Options& matrix_options,
                       rgb_matrix::RuntimeOptions& runtime_opt,
                       CubeRendererOptions& renderer_opt);

#endif // CONFIG_LOADER_H
