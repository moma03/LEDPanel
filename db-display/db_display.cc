// db_display.cc
// Simple Deutsche Bahn style platform display demo

#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <thread>

#include "../rpi-rgb-led-matrix/include/led-matrix.h"
#include "../rpi-rgb-led-matrix/include/graphics.h"
#include "../common/include/config_loader.h"

using namespace rgb_matrix;

struct Departure { std::string platform; std::string line; std::string dest; std::string note; std::string time; };

void DrawHeader(Canvas *c, const Font &fontBig, const std::string &station, int width) {
    // Blue background bar
    c->Fill(0, 64, 200);
    // Station name large, white
    int y = fontBig.baseline() + 2;
    DrawText(c, fontBig, 4, y, Color(255,255,255), nullptr, station.c_str());
}

void DrawMain(Canvas *c, const Font &fontBig, const Font &fontSmall, const Departure &d, int width) {
    // Main band below header
    int band_y = fontBig.height() + 6;
    int band_h = 26;
    // white background for main departure
    for (int yy = band_y; yy < band_y + band_h; ++yy) for (int x=0;x<width;++x) c->SetPixel(x, yy, 255,255,255);

    // Draw line (orange) and destination
    int text_y = band_y + fontBig.baseline();
    DrawText(c, fontBig, 12, text_y, Color(0,0,0), nullptr, d.dest.c_str());

    // Line badge
    int badge_x = 4;
    int badge_y = band_y + 4;
    // draw orange rectangle
    for (int yy=badge_y; yy<badge_y+fontBig.height(); ++yy)
        for (int xx=badge_x; xx<badge_x+fontBig.height()+4; ++xx)
            c->SetPixel(xx, yy, 255,140,0);
    DrawText(c, fontSmall, badge_x+2, badge_y+fontSmall.baseline(), Color(0,0,0), nullptr, d.line.c_str());

    // Time on right (red)
    std::string time = d.time;
    int tw = DrawText(c, fontBig, 0, 0, Color(0,0,0), nullptr, time.c_str());
    DrawText(c, fontBig, width - tw - 8, text_y, Color(200,0,0), nullptr, time.c_str());
}

void DrawList(Canvas *c, const Font &fontSmall, const std::vector<Departure> &list, int width, int start_y) {
    int row_h = fontSmall.height() + 4;
    for (size_t i=0;i<list.size();++i) {
        int y = start_y + i * row_h;
        // alternate background: blue/white
        if (i % 2 == 0) {
            for (int yy=y; yy<y+row_h; ++yy) for (int x=0;x<width;++x) c->SetPixel(x, yy, 0,64,200);
        } else {
            for (int yy=y; yy<y+row_h; ++yy) for (int x=0;x<width;++x) c->SetPixel(x, yy, 255,255,255);
        }
        // platform number left
        DrawText(c, fontSmall, 6, y+fontSmall.baseline()+1, Color(255,255,255), nullptr, list[i].platform.c_str());
        // line & dest
        DrawText(c, fontSmall, 36, y+fontSmall.baseline()+1, Color(255,255,255), nullptr, list[i].line.c_str());
        DrawText(c, fontSmall, 80, y+fontSmall.baseline()+1, Color(255,255,255), nullptr, list[i].dest.c_str());
        // time right (inverted color on white rows)
        Color timeCol = (i %2 ==0) ? Color(255,255,255) : Color(0,0,0);
        int tw = DrawText(c, fontSmall, 0, 0, timeCol, nullptr, list[i].time.c_str());
        DrawText(c, fontSmall, width - tw - 6, y+fontSmall.baseline()+1, timeCol, nullptr, list[i].time.c_str());
        // note under dest if present
        if (!list[i].note.empty()) {
            DrawText(c, fontSmall, 36, y+fontSmall.baseline()+1 + fontSmall.height()/2, Color(255,255,255), nullptr, list[i].note.c_str());
        }
    }
}

void DrawTicker(Canvas *c, const Font &fontSmall, const std::string &msg, int width, int height) {
    int y = height - fontSmall.height();
    // red strip
    for (int yy=y-2; yy<height; ++yy) for (int x=0;x<width;++x) c->SetPixel(x, yy, 200,0,0);
    DrawText(c, fontSmall, 6, y + fontSmall.baseline(), Color(255,255,255), nullptr, msg.c_str());
}

int main(int argc, char **argv) {
    RGBMatrix::Options matrix_options;
    rgb_matrix::RuntimeOptions runtime_options;
    CubeRendererOptions dummy;

    // try load config, but fall back to defaults
    if (!LoadConfigFromFile("config.json", matrix_options, runtime_options, dummy)) {
        matrix_options.rows = 32;
        matrix_options.cols = 64;
        matrix_options.chain_length = 1;
        matrix_options.parallel = 1;
    }

    RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_options);
    if (!matrix) return 1;

    FrameCanvas *off = matrix->CreateFrameCanvas();
    Canvas *c = off;

    // Load fonts
    Font bigFont; bigFont.LoadFont("../rpi-rgb-led-matrix/fonts/clR6x12.bdf");
    Font smallFont; smallFont.LoadFont("../rpi-rgb-led-matrix/fonts/5x8.bdf");

    int width = c->width();
    int height = c->height();

    // Sample data
    std::vector<Departure> list = {
        {"1", "S5", "Paderborn Hbf", "Technischer Defekt am Zug", "10:27"},
        {"3", "S5", "Hannover Flughafen", "", "10:44"},
        {"2", "S5", "Paderborn", "Zug fällt aus", "11:44"}
    };

    std::string station = "Steinheim (Westf.)";
    std::string ticker = "Ein Unwetter behindert den Bahnverkehr. Für weitere Informationen beachten Sie Durchsagen.";

    while (true) {
        // draw on offscreen
        DrawHeader(c, bigFont, station, width);
        DrawMain(c, bigFont, smallFont, list[0], width);
        int list_start = bigFont.height() + 6 + 30;
        DrawList(c, smallFont, list, width, list_start);
        DrawTicker(c, smallFont, ticker, width, height);

        // swap
        off = matrix->SwapOnVSync(off);
        c = off;

        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }

    delete matrix;
    return 0;
}
