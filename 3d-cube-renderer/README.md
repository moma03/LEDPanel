# 3D Cube Renderer for LED Matrix

A simple 3D renderer for creating generative art on LED matrices using rotating cubes with Phong-like shading.

## Features

- **3D Cube Rendering**: Renders cubes with proper 3D transformations (rotation, translation)
- **Shading System**: Three-level shading based on face normals and light direction
  - **Light**: Bright yellow-white (255, 255, 200) for front-facing surfaces
  - **Shadow**: Dark gray (100, 100, 100) for angled surfaces
  - **Black**: (0, 0, 0) for back-facing surfaces
- **Generative Animation**: Animated cubes with smooth rotation and position changes
- **Painter's Algorithm**: Proper depth sorting for overlapping faces

## Color Customization

Edit the color values in `generative_art.cc`:

```cpp
Color colorLight(255, 255, 200);   // Front-facing (bright)
Color colorShadow(100, 100, 100);  // Angled surfaces
Color colorBlack(0, 0, 0);         // Back-facing
```

## Building

```bash
cd 3d-cube-renderer
make
```

## Running

```bash
sudo ./generative_art
```

(Requires root/sudo for GPIO access to the LED matrix)

## Customizing the Art

Modify the cube generation in `generative_art.cc`:

```cpp
// Change number of cubes
for (int i = 0; i < 3; i++) {
    Cube c(2.5f);  // Size of cube
    c.position = Vec3((i - 1) * 4, 0, -8 + i * 3);  // Position
    cubes.push_back(c);
}

// Adjust rotation speeds in animation loop
cubes[i].rotation.x = time * 0.7f + i * 2.094f;
cubes[i].rotation.y = time * 0.5f + i * 2.094f;
```

## Key Parameters

- **Light Direction**: `renderer.lightDirection = Vec3(0.8f, 0.6f, 1.0f).normalized();`
- **Focal Length**: Change `5.0f` in `drawFilledQuad()` for perspective effect
- **Frame Rate**: Adjust `usleep(30000)` for faster/slower animation

## Architecture

- `cube_renderer.h`: Core 3D math and rendering engine
  - `Vec3`: 3D vector with dot product and cross product
  - `Cube`: 3D cube with rotation, translation, and face generation
  - `CubeRenderer`: Main renderer with projection and shading
- `generative_art.cc`: LED matrix integration and animation loop
