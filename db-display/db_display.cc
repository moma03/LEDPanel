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
#include "../common/include/scrolling_textbox.h"
#include "../common/include/scrolling_box.h"

using namespace rgb_matrix;

struct Departure { std::string platform; std::string line; std::string dest; std::string note; std::string time; std::string stops; std::string orig_time; };

// Draw header with station name
// returns height used
int DrawHeader(Canvas *c, const Font &fontBig, const std::string &station, int width) {
    int header_h = fontBig.height() + 4;
    // Station name large, white
    int y = fontBig.baseline() + 2;
    DrawText(c, fontBig, 4, y, Color(255,255,255), nullptr, station.c_str());
    // Bottom border line
    DrawLine(c, 0, header_h -1, width -1, header_h -1, Color(0,0,0));
    return header_h;
}

// Draw next departure main band
// Returns height used
int DrawMain(Canvas *c, const Font &fontBig, const Font &fontSmall, const Departure &d, int width) {
    int header_h = fontBig.height() + 4;
    // Main band below header
    int band_y = fontBig.height() + 6;
    int band_h = 26;

    // Draw line name
    int text_y = band_y + fontBig.baseline();
    DrawText(c, fontBig, 12, text_y, Color(0,0,0), nullptr, d.line.c_str());

    // Destination next to line
    DrawText(c, fontBig, 12 + 8 + DrawText(c, fontBig, 0,0, Color(0,0,0), nullptr, d.line.c_str()),
             text_y, Color(0,0,0), nullptr, d.dest.c_str());

    // If delay draw delayed departure time in red on right side otherwise draw scheduled time in white
    Color timeCol = d.note.empty() ? Color(255,255,255) : Color(255,0,0);
    int tw = DrawText(c, fontBig, 0,0, timeCol, nullptr, d.time.c_str());
    DrawText(c, fontBig, width - tw - 12, text_y, timeCol, nullptr, d.time.c_str());
    // if it was delayed, draw original planned departure time below in small font and white
    if (!d.note.empty()) {
        DrawText(c, fontSmall, width - tw - 12, band_y + fontBig.height()/2 + fontSmall.baseline(),
                 Color(255,255,255), nullptr, d.orig_time.c_str());
    }
    // The stops/destination area is rendered by a persistent ScrollingTextBox
    // created and updated from `main()` so we don't create ephemeral widgets here.

    // If any note, draw below in blue on white strip in a Scrolling text box
    if (!d.note.empty()) {
        int note_y = band_y + band_h;
        for (int yy=note_y; yy<note_y + fontSmall.height() +4; ++yy)
            for (int x=0;x<width;++x)
                c->SetPixel(x, yy, 0,0,200); // blue background
        // The note text is drawn by a persistent ScrollingTextBox from `main()`.
        return band_y + band_h + fontSmall.height() +4;
    }
    return band_y + band_h;
}

// Draw a next departure in a scrollable list
// with given height starting at start_y
void DrawList(Canvas *c, const Font &fontSmall, const std::vector<Departure> &list, int width, int start_y) {
    // Simple, compact list rendering: platform, destination, time (right-aligned-ish).
    int y = start_y;
    const int line_spacing = fontSmall.height() + 6;
    for (const auto &d : list) {
        // stop if out of canvas
        if (y + fontSmall.height() > c->height()) break;

        // Platform on the left
        DrawText(c, fontSmall, 6, y + fontSmall.baseline(), Color(0,0,0), nullptr, d.platform.c_str());

        // Destination a bit to the right of platform (fixed offset to keep layout simple)
        const int dest_x = 32;
        DrawText(c, fontSmall, dest_x, y + fontSmall.baseline(), Color(0,0,0), nullptr, d.dest.c_str());

        // Time on the right (approx right-aligned)
        const int time_x = std::max(6, width - 6 - 40);
        DrawText(c, fontSmall, time_x, y + fontSmall.baseline(), Color(0,0,0), nullptr, d.time.c_str());

        y += line_spacing;
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

    // try load matrix config, but fall back to defaults
    if (!LoadConfigFromFile("config.json", matrix_options, runtime_options)) {
        matrix_options.rows = 32;
        matrix_options.cols = 64;
        matrix_options.chain_length = 1;
        matrix_options.parallel = 1;
    }

    RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_options);
    if (!matrix) return 1;

    FrameCanvas *off = matrix->CreateFrameCanvas();
    Canvas *c = off;

    // Load fonts (UI settings are local defaults; matrix settings come from config.json)
    Font bigFont; bigFont.LoadFont("../rpi-rgb-led-matrix/fonts/clR6x12.bdf");
    Font smallFont; smallFont.LoadFont("../rpi-rgb-led-matrix/fonts/5x8.bdf");

    int width = c->width();
    int height = c->height();

    // Sample data (UI content is fixed here; matrix options load from config.json)
    std::vector<Departure> list = {
        {"1", "S5", "Paderborn Hbf", "Technischer Defekt am Zug", "10:27", "Bielefeld Hbf, Lage, Detmold, Bad Salzuflen", "10:44"},
        {"3", "S5", "Hannover Flughafen", "", "10:44", "Bielefeld Hbf, Lage, Detmold, Bad Salzuflen, Herford, Bünde, Löhne, Minden, Wunstorf", ""},
        {"2", "S5", "Paderborn", "Zug fällt aus", "11:44", "Bielefeld Hbf, Lage, Detmold, Bad Salzuflen", "11:59"},
        {"4", "RE 78", "Kassel-Wilhelmshöhe", "", "12:04", "Gütersloh Hbf, Verl, Rheda-Wiedenbrück, Langenberg, Harsewinkel, Sende, Warendorf, Münster Hbf", ""},
    };

    std::string station = "Steinheim (Westf.)";
    std::string ticker = "Ein Unwetter behindert den Bahnverkehr. Für weitere Informationen beachten Sie Durchsagen.";
    // Create persistent scrolling widgets for the main panel and the list/ticker.
    // Compute band positions used by DrawMain so scrollers align with layout.
    int band_y = bigFont.height() + 6;

    // Measure line width for indentation of destination
    int line_w = DrawText(c, bigFont, 0, 0, Color(0,0,0), nullptr, list[0].line.c_str());
    int dest_x = 12 + 8 + line_w;

    // Time width reserve (approx) to leave room on the right for time display
    int time_reserve = 60;

    // Main destination (large) scroller
    ScrollingTextBox mainDestScroller(c,
                                     dest_x,
                                     band_y,
                                     std::max(20, width - dest_x - time_reserve),
                                     bigFont.height(),
                                     bigFont,
                                     Color(0,0,0),
                                     list[0].dest,
                                     30.0f, 1.0f, 12);

    // Main stops (small) scroller (below destination)
    ScrollingTextBox mainStopsScroller(c,
                                      12 + 8,
                                      band_y + bigFont.height()/2,
                                      std::max(20, width - (12 + 8) - time_reserve - 12),
                                      smallFont.height(),
                                      smallFont,
                                      Color(0,0,0),
                                      list[0].stops,
                                      25.0f, 1.0f, 8);

    // Note scroller (small) - shown only when note exists
    int note_y = band_y + 26; // matches band_h used in DrawMain
    ScrollingTextBox noteScroller(c,
                                  6,
                                  note_y + 2,
                                  std::max(20, width - 12),
                                  smallFont.height(),
                                  smallFont,
                                  Color(255,255,255),
                                  list[0].note,
                                  30.0f, 1.0f, 8);

    // Compose list content into multi-line string for vertical ScrollingBox
    auto BuildListContent = [&](const std::vector<Departure> &items) {
        std::string s;
        for (const auto &d : items) {
            s += d.platform + " ";
            s += d.line + " ";
            s += d.dest + " ";
            s += d.time;
            s += "\n";
        }
        return s;
    };

    int list_start = bigFont.height() + 6 + 30;
    int height_left_for_list = height - list_start - smallFont.height() -2;

    ScrollingBox listBox(c,
                         6,
                         list_start,
                         width - 12,
                         std::max(10, height_left_for_list),
                         smallFont,
                         Color(0,0,0),
                         BuildListContent(std::vector<Departure>(list.begin()+1, list.end())),
                         15.0f, 1.0f, 3);

    // Ticker scroller at bottom
    int ticker_y = height - smallFont.height();
    ScrollingTextBox tickerScroller(c,
                                    6,
                                    ticker_y + smallFont.baseline(),
                                    width - 12,
                                    smallFont.height(),
                                    smallFont,
                                    Color(255,255,255),
                                    ticker,
                                    30.0f, 1.0f, 16);

    // Main loop
    while (true) {
        // draw static layout on offscreen
        DrawHeader(c, bigFont, station, width);
        DrawMain(c, bigFont, smallFont, list[0], width);

        // draw ticker red strip background
        int ty = height - smallFont.height();
        for (int yy=ty-2; yy<height; ++yy) for (int x=0;x<width;++x) c->SetPixel(x, yy, 200,0,0);

        // Update scrollers with current canvas, ensure they draw into the offscreen buffer
        mainDestScroller.SetCanvas(c);
        mainDestScroller.SetText(list[0].dest);
        mainDestScroller.Update();

        mainStopsScroller.SetCanvas(c);
        mainStopsScroller.SetText(list[0].stops);
        mainStopsScroller.Update();

        noteScroller.SetCanvas(c);
        noteScroller.SetText(list[0].note);
        noteScroller.Update();

        listBox.SetCanvas(c);
        listBox.SetContent(BuildListContent(std::vector<Departure>(list.begin()+1, list.end())));
        listBox.Update();

        tickerScroller.SetCanvas(c);
        tickerScroller.SetText(ticker);
        tickerScroller.Update();

        // swap buffers
        off = matrix->SwapOnVSync(off);
        c = off;
    }

    delete matrix;
    return 0;
}
