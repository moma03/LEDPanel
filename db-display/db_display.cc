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
#include "../common/include/update_event.h"

using namespace rgb_matrix;
using namespace std;


struct Departure { string platform; string line; string dest; string note; string time; string stops; string orig_time; };

// Draw header with station name
// returns height used
int DrawHeader(Canvas *c, const Font &fontBig, const string &station, int width, int top=0) {
    // Station name large, white
    int y = fontBig.baseline() + 1 + top;
    DrawText(c, fontBig, 3, y, Color(255,255,255), nullptr, station.c_str());
    // Bottom border line
    y += 4;
    DrawLine(c, 0, y-1, width -1, y-1, Color(255,255,255));
    return y;
}

// Draw next departure main band
// Returns height used
int DrawMain(Canvas *c, const Font &fontBig, const Font &fontSmall, const Departure &d, int width, int top=0) {
    // Main band below header
    int band_y = fontBig.height() + 6;
    int band_h = 26;

    int text_y = band_y + fontBig.baseline();
    int cur_x = 3;
    // Draw platform
    cur_x += DrawText(c, fontBig, cur_x, text_y, Color(255,255,255), nullptr, d.platform.c_str());
    // Draw line name
    cur_x += 4;
    int start_line_x = cur_x;
    cur_x += DrawText(c, fontBig, cur_x, text_y, Color(255,255,0), nullptr, d.line.c_str());
    // Destination
    cur_x += 8;
                                     
    // If delay draw delayed departure time in red on right side otherwise draw scheduled time in white
    Color timeCol = d.note.empty() ? Color(255,255,255) : Color(255,0,0);
    // Draw time right-aligned (need to calculate text width first)
    int tw = DrawText(c, fontBig, 0, 0, timeCol, nullptr, d.time.c_str());
    DrawText(c, fontBig, width - tw - 4, text_y, timeCol, nullptr, d.time.c_str());

    // Main destination (large) scroller
    ScrollingTextBox mainDestScroller(c, cur_x, band_y,
                                        max(20, width - cur_x - tw - 8),
                                        fontBig.height(),
                                        fontBig,
                                        Color(255,255,255),
                                        d.dest,
                                        30.0f, 1.0f, 12);
    mainDestScroller.SetCanvas(c);

    int band_bottom = band_y + fontSmall.height() +4;
    // if it was delayed, draw original planned departure time below in small font and white
    if (!d.note.empty()) {
        DrawText(c, fontSmall, width - tw - 12, band_bottom, Color(255,255,255), nullptr, d.orig_time.c_str());
    }

    // Next, stops scroller below main band
    ScrollingTextBox stopsScroller(c, start_line_x, band_bottom,
                                   width - start_line_x - tw - 8,
                                   fontSmall.height(),
                                   fontSmall,
                                   Color(200,200,200),
                                   d.stops,
                                   20.0f, 1.0f, 8);
    stopsScroller.SetCanvas(c);

    // If any note, draw below in blue on white strip in a Scrolling text box
    if (!d.note.empty()) {
        band_bottom = band_bottom + fontSmall.height() +4;
        // make white strip
        for (int yy=band_bottom-2; yy<band_bottom + fontSmall.height() +4; ++yy)
            for (int x=0;x<width;++x)
                c->SetPixel(x, yy, 0,0,200);
        ScrollingTextBox noteScroller(c, start_line_x, band_bottom,
                                      width - start_line_x - tw - 8,
                                      fontSmall.height(),
                                      fontSmall,
                                      Color(0,0,255),
                                      d.note,
                                      30.0f, 1.0f, 8);
        noteScroller.SetCanvas(c);
    }
    return 0;
}

// Draw a next departure in a scrollable list
// with given height starting at start_y
void DrawList(Canvas *c, const Font &fontSmall, const vector<Departure> &list, int width, int start_y) {
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
        const int time_x = max(6, width - 6 - 40);
        DrawText(c, fontSmall, time_x, y + fontSmall.baseline(), Color(0,0,0), nullptr, d.time.c_str());

        y += line_spacing;
    }
}

void DrawTicker(Canvas *c, const Font &fontSmall, const string &msg, int width, int height) {
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
    vector<Departure> list = {
        {"1", "S5", "Paderborn Hbf", "Technischer Defekt am Zug", "10:27", "Bielefeld Hbf, Lage, Detmold, Bad Salzuflen", "10:44"},
        {"3", "S5", "Hannover Flughafen", "", "10:44", "Bielefeld Hbf, Lage, Detmold, Bad Salzuflen, Herford, Bünde, Löhne, Minden, Wunstorf", ""},
        {"2", "S5", "Paderborn", "Zug fällt aus", "11:44", "Bielefeld Hbf, Lage, Detmold, Bad Salzuflen", "11:59"},
        {"4", "RE 78", "Kassel-Wilhelmshöhe", "", "12:04", "Gütersloh Hbf, Verl, Rheda-Wiedenbrück, Langenberg, Harsewinkel, Sende, Warendorf, Münster Hbf", ""},
    };

    string station = "Steinheim (Westf.)";
    string ticker = "Ein Unwetter behindert den Bahnverkehr. Für weitere Informationen beachten Sie Durchsagen.";
    // Create persistent scrolling widgets for the main panel and the list/ticker.
    // Compute band positions used by DrawMain so scrollers align with layout.
    int band_y = bigFont.height() + 6;

    // Measure line width for indentation of destination
    int line_w = DrawText(c, bigFont, 0, 0, Color(0,0,0), nullptr, list[0].line.c_str());
    int dest_x = 12 + 8 + line_w;

    // Time width reserve (approx) to leave room on the right for time display
    int time_reserve = 60;

    // Compose list content into multi-line string for vertical ScrollingBox
    auto BuildListContent = [&](const vector<Departure> &items) {
        string s;
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
                         max(10, height_left_for_list),
                         smallFont,
                         Color(255,255,255),
                         BuildListContent(vector<Departure>(list.begin()+1, list.end())),
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

    // Central update event — widgets subscribe to this so a single call
    // in the main loop updates all animated widgets.
    UpdateEvent updateEvent;

    // Subscribe scrollers to the update event so they all update when
    // `updateEvent.Notify()` is called from the main loop.
    auto sub_list = updateEvent.Subscribe([&]() { listBox.Update(); });
    auto sub_ticker = updateEvent.Subscribe([&]() { tickerScroller.Update(); });

    // Main loop
    while (true) {
        // blue background
        for (int y=0;y<height;++y) for (int x=0;x<width;++x) c->SetPixel(x, y, 0,0,200);

        // draw static layout on offscreen
        DrawHeader(c, bigFont, station, width);
        DrawMain(c, bigFont, smallFont, list[0], width);

        listBox.SetCanvas(c);
        const string listContent = BuildListContent(vector<Departure>(list.begin()+1, list.end()));
        static string prev_list_content;
        if (prev_list_content != listContent) {
            listBox.SetContent(listContent);
            prev_list_content = listContent;
        }

        tickerScroller.SetCanvas(c);
        static string prev_ticker;
        if (prev_ticker != ticker) {
            tickerScroller.SetText(ticker);
            prev_ticker = ticker;
        }

        // Single entry point to update all animated widgets.
        updateEvent.Notify();

        // swap buffers
        off = matrix->SwapOnVSync(off);
        c = off;
    }

    delete matrix;
    return 0;
}
