// endles_gameOfLife.cpp
// Game of Life app for rpi-rgb-led-matrix using BaseWSettings

#include "baseWSettings.h"
#include <random>
#include <vector>
#include <chrono>
#include <thread>

class GameOfLifeApp : public BaseWSettings {
public:
    explicit GameOfLifeApp(const std::string& settings_file)
      : BaseWSettings(settings_file), rng_(std::random_device{}()) {}

    void Run() override {
        // Determine logical width/height from canvas
        auto c = canvas();
        if (!c) return;
        const int width = c->width();
        const int height = c->height();

        // Settings: speed, spawn probability, initial fill
        int speed_ms = 100; // default
        double spawn_chance = 0.002; // chance to randomly activate a dead cell each step
        double initial_fill = 0.12; // fraction of cells initially alive

        // Accept multiple key names to be forgiving with settings.yaml formats
        if (settings()["gol-speed-ms"]) speed_ms = settings()["gol-speed-ms"].as<int>();
        if (settings()["gol"]["speed_ms"]) speed_ms = settings()["gol"]["speed_ms"].as<int>();
        if (settings()["gol-spawn-chance"]) spawn_chance = settings()["gol-spawn-chance"].as<double>();
        if (settings()["gol"]["spawn_chance"]) spawn_chance = settings()["gol"]["spawn_chance"].as<double>();
        if (settings()["gol-initial-fill"]) initial_fill = settings()["gol-initial-fill"].as<double>();
        if (settings()["gol"]["initial_fill"]) initial_fill = settings()["gol"]["initial_fill"].as<double>();

        grid_current_.assign(width * height, false);
        grid_next_.assign(width * height, false);

        // Initialize randomly
        std::uniform_real_distribution<double> uni(0.0, 1.0);
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                if (uni(rng_) < initial_fill) grid_current_[y*width + x] = true;
            }
        }

        // main loop
        while (!ExitRequested()) {
            // compute neighbors with toroidal wrap
            for (int y = 0; y < height; ++y) {
                for (int x = 0; x < width; ++x) {
                    int alive = 0;
                    for (int dy = -1; dy <= 1; ++dy) {
                        for (int dx = -1; dx <= 1; ++dx) {
                            if (dx == 0 && dy == 0) continue;
                            int nx = (x + dx + width) % width;
                            int ny = (y + dy + height) % height;
                            if (grid_current_[ny*width + nx]) ++alive;
                        }
                    }
                    bool cur = grid_current_[y*width + x];
                    bool nxt = cur;
                    if (cur) {
                        nxt = (alive == 2 || alive == 3);
                    } else {
                        nxt = (alive == 3);
                        // random spontaneous birth
                        if (!nxt && uni(rng_) < spawn_chance) nxt = true;
                    }
                    grid_next_[y*width + x] = nxt;
                }
            }

            // draw to canvas
            // We'll draw alive cells as bright white (or configurable color later)
            for (int y = 0; y < height; ++y) {
                for (int x = 0; x < width; ++x) {
                    bool alive = grid_next_[y*width + x];
                    if (alive) {
                        c->SetPixel(x, y, 255, 255, 255);
                    } else {
                        c->SetPixel(x, y, 0, 0, 0);
                    }
                }
            }

            // swap buffers
            c = matrix()->SwapOnVSync(c);

            // commit next grid
            grid_current_.swap(grid_next_);

            // small delay with early exit check
            int slept = 0;
            while (slept < speed_ms && !ExitRequested()) {
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
                slept += 10;
            }
        }
    }

private:
    std::mt19937 rng_;
    std::vector<bool> grid_current_;
    std::vector<bool> grid_next_;
};

int main(int argc, char** argv) {
    std::string settings = "endles_gameOfLife/settings.yaml";
    if (argc > 1) settings = argv[1];

    GameOfLifeApp app(settings);
    app.Start();
    return 0;
}
