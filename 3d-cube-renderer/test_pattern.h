#ifndef TEST_PATTERN_H
#define TEST_PATTERN_H

#include <vector>
#include <string>
#include <cmath>

struct TestPattern {
    std::vector<std::vector<int>> framebuffer;
    int width, height;
    
    TestPattern(int w, int h) : width(w), height(h) {
        framebuffer.resize(h, std::vector<int>(w, 0));
    }
    
    void clear() {
        for (auto& row : framebuffer) {
            std::fill(row.begin(), row.end(), 0);
        }
    }
    
    void drawCross() {
        // Draw diagonal from top-left to bottom-right
        for (int i = 0; i < std::min(width, height); i++) {
            int x = (i * width) / std::min(width, height);
            int y = (i * height) / std::min(width, height);
            if (x < width && y < height) {
                framebuffer[y][x] = 2;  // light
            }
        }
        
        // Draw diagonal from top-right to bottom-left
        for (int i = 0; i < std::min(width, height); i++) {
            int x = width - 1 - (i * width) / std::min(width, height);
            int y = (i * height) / std::min(width, height);
            if (x >= 0 && x < width && y < height) {
                framebuffer[y][x] = 2;  // light
            }
        }
        
        // Draw border
        for (int x = 0; x < width; x++) {
            framebuffer[0][x] = 1;           // top
            framebuffer[height-1][x] = 1;   // bottom
        }
        for (int y = 0; y < height; y++) {
            framebuffer[y][0] = 1;           // left
            framebuffer[y][width-1] = 1;    // right
        }
    }
    
    void drawPixel(int x, int y, int shade) {
        if (x >= 0 && x < width && y >= 0 && y < height) {
            framebuffer[y][x] = shade;
        }
    }
    
    // Draw a simple number 0-9 (3x5 pixels each)
    void drawDigit(int digit, int startX, int startY, int shade) {
        // Simple 3x5 digit patterns
        const int patterns[10][5] = {
            {0b111, 0b101, 0b101, 0b101, 0b111}, // 0
            {0b010, 0b110, 0b010, 0b010, 0b111}, // 1
            {0b111, 0b001, 0b111, 0b100, 0b111}, // 2
            {0b111, 0b001, 0b111, 0b001, 0b111}, // 3
            {0b101, 0b101, 0b111, 0b001, 0b001}, // 4
            {0b111, 0b100, 0b111, 0b001, 0b111}, // 5
            {0b111, 0b100, 0b111, 0b101, 0b111}, // 6
            {0b111, 0b001, 0b010, 0b100, 0b100}, // 7
            {0b111, 0b101, 0b111, 0b101, 0b111}, // 8
            {0b111, 0b101, 0b111, 0b001, 0b111}  // 9
        };
        
        if (digit < 0 || digit > 9) return;
        
        for (int row = 0; row < 5; row++) {
            int pattern = patterns[digit][row];
            for (int col = 0; col < 3; col++) {
                if (pattern & (1 << (2 - col))) {
                    drawPixel(startX + col, startY + row, shade);
                }
            }
        }
    }
    
    void drawText(const std::string& text, int startX, int startY, int shade) {
        int x = startX;
        for (char c : text) {
            if (c >= '0' && c <= '9') {
                drawDigit(c - '0', x, startY, shade);
                x += 4;  // 3 pixels + 1 spacing
            }
        }
    }
    
    void drawResolution(int width, int height) {
        // Convert dimensions to strings
        std::string res = "";
        
        // Width
        if (width >= 100) res += char('0' + (width / 100));
        if (width >= 10) res += char('0' + ((width / 10) % 10));
        res += char('0' + (width % 10));
        
        res += "x";
        
        // Height
        if (height >= 100) res += char('0' + (height / 100));
        if (height >= 10) res += char('0' + ((height / 10) % 10));
        res += char('0' + (height % 10));
        
        // Calculate center position
        int textWidth = res.length() * 4;
        int centerX = (this->width - textWidth) / 2;
        int centerY = (this->height - 5) / 2;
        
        drawText(res, centerX, centerY, 2);  // light color
    }
};

#endif // TEST_PATTERN_H
