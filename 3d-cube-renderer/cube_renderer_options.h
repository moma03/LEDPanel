#ifndef CUBE_RENDERER_OPTIONS_H
#define CUBE_RENDERER_OPTIONS_H

struct CubeRendererOptions {
    int num_cubes = 1;
    float cube_size = 2.5f;
    float rotation_speed_x = 0.7f;
    float rotation_speed_y = 0.5f;
    float rotation_speed_z = 0.3f;
    float position_animation_speed = 0.5f;
    float position_animation_amplitude = 2.0f;
    int light_r = 255;
    int light_g = 255;
    int light_b = 200;
    int shadow_r = 100;
    int shadow_g = 100;
    int shadow_b = 100;
    float light_dir_x = 0.8f;
    float light_dir_y = 0.6f;
    float light_dir_z = 1.0f;
    float focal_length = 5.0f;
    int frame_rate_ms = 33;
};

#endif // CUBE_RENDERER_OPTIONS_H
