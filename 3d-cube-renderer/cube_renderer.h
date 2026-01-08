#ifndef CUBE_RENDERER_H
#define CUBE_RENDERER_H
// Ensure single inclusion for various toolchains
#pragma once

#include <vector>
#include <cmath>
#include <algorithm>
#include <cstdint>

struct Vec3 {
    float x, y, z;
    
    Vec3() : x(0), y(0), z(0) {}
    Vec3(float x, float y, float z) : x(x), y(y), z(z) {}
    
    Vec3 operator+(const Vec3& v) const { return Vec3(x + v.x, y + v.y, z + v.z); }
    Vec3 operator-(const Vec3& v) const { return Vec3(x - v.x, y - v.y, z - v.z); }
    Vec3 operator*(float s) const { return Vec3(x * s, y * s, z * s); }
    
    float dot(const Vec3& v) const { return x * v.x + y * v.y + z * v.z; }
    
    Vec3 cross(const Vec3& v) const {
        return Vec3(y * v.z - z * v.y, z * v.x - x * v.z, x * v.y - y * v.x);
    }
    
    float length() const { return std::sqrt(x * x + y * y + z * z); }
    
    Vec3 normalized() const {
        float len = length();
        if (len == 0) return Vec3(0, 0, 0);
        return *this * (1.0f / len);
    }
};

struct Vec2 {
    float x, y;
    Vec2() : x(0), y(0) {}
    Vec2(float x, float y) : x(x), y(y) {}
    Vec2 operator-(const Vec2& v) const { return Vec2(x - v.x, y - v.y); }
};

struct Face {
    std::vector<Vec3> vertices;
    Vec3 normal;
    
    Face(const Vec3& v0, const Vec3& v1, const Vec3& v2, const Vec3& v3) {
        vertices.push_back(v0);
        vertices.push_back(v1);
        vertices.push_back(v2);
        vertices.push_back(v3);
        
        // Calculate face normal
        Vec3 edge1 = v1 - v0;
        Vec3 edge2 = v3 - v0;
        normal = edge1.cross(edge2).normalized();
    }
};

// Generic polygon mesh: list of vertices and faces expressed as index lists.
struct Mesh {
    std::vector<Vec3> vertices;
    // each face is a list of indices into `vertices`
    std::vector<std::vector<int>> faces;
};

class Cube {
public:
    Vec3 position;
    Vec3 rotation;
    float size;
    
    Cube(float size = 1.0f) : position(0, 0, 0), rotation(0, 0, 0), size(size) {}
    
    std::vector<Face> getFaces() const {
        std::vector<Face> faces;
        float s = size / 2.0f;
        
        // Generate cube vertices
        Vec3 v[8] = {
            Vec3(-s, -s, -s),
            Vec3(s, -s, -s),
            Vec3(s, s, -s),
            Vec3(-s, s, -s),
            Vec3(-s, -s, s),
            Vec3(s, -s, s),
            Vec3(s, s, s),
            Vec3(-s, s, s)
        };
        
        // Apply rotations
        for (int i = 0; i < 8; i++) {
            v[i] = rotateX(v[i], rotation.x);
            v[i] = rotateY(v[i], rotation.y);
            v[i] = rotateZ(v[i], rotation.z);
            v[i] = v[i] + position;
        }
        
        // Create faces
        faces.push_back(Face(v[0], v[1], v[2], v[3])); // front
        faces.push_back(Face(v[4], v[7], v[6], v[5])); // back
        faces.push_back(Face(v[0], v[3], v[7], v[4])); // left
        faces.push_back(Face(v[1], v[5], v[6], v[2])); // right
        faces.push_back(Face(v[3], v[2], v[6], v[7])); // top
        faces.push_back(Face(v[0], v[4], v[5], v[1])); // bottom
        
        return faces;
    }

    // Convert this cube into a generic Mesh (useful for rendering via
    // mesh-based renderer paths).
    Mesh ToMesh() const {
        Mesh m;
        float s = size / 2.0f;
        Vec3 v[8] = {
            Vec3(-s, -s, -s),
            Vec3(s, -s, -s),
            Vec3(s, s, -s),
            Vec3(-s, s, -s),
            Vec3(-s, -s, s),
            Vec3(s, -s, s),
            Vec3(s, s, s),
            Vec3(-s, s, s)
        };

        for (int i = 0; i < 8; i++) {
            v[i] = rotateX(v[i], rotation.x);
            v[i] = rotateY(v[i], rotation.y);
            v[i] = rotateZ(v[i], rotation.z);
            v[i] = v[i] + position;
            m.vertices.push_back(v[i]);
        }

        m.faces.push_back({0,1,2,3});
        m.faces.push_back({4,7,6,5});
        m.faces.push_back({0,3,7,4});
        m.faces.push_back({1,5,6,2});
        m.faces.push_back({3,2,6,7});
        m.faces.push_back({0,4,5,1});

        return m;
    }
    
private:
    Vec3 rotateX(const Vec3& v, float angle) const {
        float c = std::cos(angle);
        float s = std::sin(angle);
        return Vec3(v.x, v.y * c - v.z * s, v.y * s + v.z * c);
    }
    
    Vec3 rotateY(const Vec3& v, float angle) const {
        float c = std::cos(angle);
        float s = std::sin(angle);
        return Vec3(v.x * c + v.z * s, v.y, -v.x * s + v.z * c);
    }
    
    Vec3 rotateZ(const Vec3& v, float angle) const {
        float c = std::cos(angle);
        float s = std::sin(angle);
        return Vec3(v.x * c - v.y * s, v.x * s + v.y * c, v.z);
    }
};

class CubeRenderer {
public:
    int width, height;
    // framebuffer stores packed 0xRRGGBB colors per pixel
    std::vector<std::vector<uint32_t>> framebuffer;
    Vec3 lightDirection;
    // Colors used for interpolation between shadow and light
    uint8_t light_r = 255, light_g = 255, light_b = 255;
    uint8_t shadow_r = 0, shadow_g = 0, shadow_b = 0;
    
    CubeRenderer(int w, int h) : width(w), height(h), lightDirection(1, 1, 1) {
        lightDirection = lightDirection.normalized();
        framebuffer.resize(h, std::vector<uint32_t>(w, 0));
    }
    
    void clear() {
        for (auto& row : framebuffer) {
            std::fill(row.begin(), row.end(), 0u);
        }
    }
    
    // Return brightness [0,1] based on Lambertian dot product
    float getShadeValue(const Vec3& normal) const {
        float brightness = std::max(0.0f, normal.dot(lightDirection));
        if (brightness < 0.0f) brightness = 0.0f;
        if (brightness > 1.0f) brightness = 1.0f;
        return brightness;
    }
    
    void renderCube(const Cube& cube) {
        // Backwards-compatible: render cube by converting to a Mesh.
        renderMesh(cube.ToMesh());
    }

    // Render an arbitrary polygon mesh. Faces are lists of vertex indices
    // into `mesh.vertices`. Faces are rendered using a simple painter's
    // algorithm (sorted by average Z) and shaded by face normal.
    void renderMesh(const Mesh& mesh) {
        struct TempFace { std::vector<Vec3> verts; Vec3 normal; float avgZ; };
        std::vector<TempFace> temp;
        temp.reserve(mesh.faces.size());

        for (const auto &fidx : mesh.faces) {
            if (fidx.size() < 3) continue;
            TempFace tf;
            for (int idx : fidx) {
                if (idx >= 0 && idx < (int)mesh.vertices.size()) tf.verts.push_back(mesh.vertices[idx]);
            }
            // compute normal using first three vertices (robust enough for planar polygons)
            Vec3 edge1 = tf.verts[1] - tf.verts[0];
            Vec3 edge2 = tf.verts.size() > 2 ? tf.verts[2] - tf.verts[0] : Vec3(0,0,1);
            tf.normal = edge1.cross(edge2).normalized();
            tf.avgZ = 0.0f;
            for (const auto &v : tf.verts) tf.avgZ += v.z;
            tf.avgZ /= std::max(1, (int)tf.verts.size());
            temp.push_back(std::move(tf));
        }

        std::sort(temp.begin(), temp.end(), [](const TempFace &a, const TempFace &b){ return a.avgZ < b.avgZ; });

        for (const auto &tf : temp) {
            float brightness = getShadeValue(tf.normal);
            drawFilledQuad(tf.verts, brightness);
        }
    }
    
    void drawFilledQuad(const std::vector<Vec3>& vertices, float brightness) {
        // Simple projection: perspective divide
        std::vector<Vec2> proj(vertices.size());
        float focalLength = 5.0f;
        
        for (size_t i = 0; i < vertices.size(); i++) {
            float z = vertices[i].z + focalLength;
            if (z <= 0) z = 0.1f;
            float scale = focalLength / z;
            
            proj[i].x = vertices[i].x * scale + width / 2.0f;
            proj[i].y = vertices[i].y * scale + height / 2.0f;
        }
        
        // Find bounding box
        float minX = proj[0].x, maxX = proj[0].x;
        float minY = proj[0].y, maxY = proj[0].y;
        for (const auto& p : proj) {
            minX = std::min(minX, p.x);
            maxX = std::max(maxX, p.x);
            minY = std::min(minY, p.y);
            maxY = std::max(maxY, p.y);
        }
        
        int x0 = std::max(0, (int)minX);
        int x1 = std::min(width - 1, (int)maxX + 1);
        int y0 = std::max(0, (int)minY);
        int y1 = std::min(height - 1, (int)maxY + 1);
        
        // Precompute blended color from brightness (linear interpolation)
        auto lerp = [](uint8_t a, uint8_t b, float t) -> uint8_t {
            float v = a + (b - a) * t;
            if (v < 0.0f) v = 0.0f; if (v > 255.0f) v = 255.0f;
            return static_cast<uint8_t>(v + 0.5f);
        };
        uint8_t r = lerp(shadow_r, light_r, brightness);
        uint8_t g = lerp(shadow_g, light_g, brightness);
        uint8_t b = lerp(shadow_b, light_b, brightness);
        uint32_t packed = (static_cast<uint32_t>(r) << 16) | (static_cast<uint32_t>(g) << 8) | static_cast<uint32_t>(b);

        // Scanline fill (simple point-in-quad test)
        for (int y = y0; y <= y1; y++) {
            for (int x = x0; x <= x1; x++) {
                if (isPointInQuad(Vec2(x, y), proj)) {
                    framebuffer[y][x] = packed;
                }
            }
        }
    }
    
    bool isPointInQuad(const Vec2& p, const std::vector<Vec2>& quad) const {
        // Simple cross product test for point in quad
        for (size_t i = 0; i < quad.size(); i++) {
            Vec2 edge = quad[(i + 1) % quad.size()] - quad[i];
            Vec2 toPoint = p - quad[i];
            float cross = edge.x * toPoint.y - edge.y * toPoint.x;
            if (cross < -0.1f) return false;
        }
        return true;
    }
};

#endif // CUBE_RENDERER_H
