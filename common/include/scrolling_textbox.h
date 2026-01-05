#ifndef SCROLLING_TEXTBOX_H
#define SCROLLING_TEXTBOX_H

#include <string>
#include <chrono>
#include <led-matrix.h>
#include <graphics.h>

// Lightweight scrolling text box with clipping.
// - If text fits: it stays still.
// - If it overflows: waits wait_before_scroll_sec, then scrolls left at scroll_speed_px_per_sec.
// - Wraps seamlessly with gap_px spacing; supports partial glyphs via clipping.
// - Does not clear background: caller should clear or repaint the area as needed.
class ScrollingTextBox {
public:
    ScrollingTextBox(rgb_matrix::Canvas *canvas,
                     int x, int y, int width, int height,
                     const rgb_matrix::Font &font,
                     const rgb_matrix::Color &color,
                     const std::string &text,
                     float scroll_speed_px_per_sec = 20.0f,
                     float wait_before_scroll_sec = 1.0f,
                     int gap_px = 8);

    // Call every frame; uses steady clock for timing.
    void Update();

    // Update text and reset scroll state.
    void SetText(const std::string &text);

private:
    rgb_matrix::Canvas *canvas_;
    int x_, y_, w_, h_;
    const rgb_matrix::Font &font_;
    rgb_matrix::Color color_;
    std::string text_;

    float scroll_speed_px_per_sec_;
    float wait_before_scroll_sec_;
    int gap_px_;

    int text_width_;
    float offset_px_;
    bool scrolling_;
    std::chrono::steady_clock::time_point last_change_;

    // Internal helpers
    int MeasureTextWidth(const std::string &text) const;
};

#endif // SCROLLING_TEXTBOX_H
