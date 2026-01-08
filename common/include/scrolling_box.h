#ifndef SCROLLING_BOX_H
#define SCROLLING_BOX_H

#include <string>
#include <vector>
#include <chrono>
#include <functional>
#include <led-matrix.h>
#include <graphics.h>

// Vertical scrolling box with a scrollbar indicator on the right.
// - Content is provided as a list of lines (or a single string with '\n').
// - If content height fits, it is shown static.
// - If it overflows, waits and then scrolls vertically at configured speed.
// - Draws a thin scrollbar showing current viewport position.
class ScrollingBox {
public:
    ScrollingBox(rgb_matrix::Canvas *canvas,
                 int x, int y, int width, int height,
                 const rgb_matrix::Font &font,
                 const rgb_matrix::Color &color,
                 const std::string &content,
                 float scroll_speed_px_per_sec = 20.0f,
                 float wait_before_scroll_sec = 1.0f,
                 int scrollbar_width = 2);

    void Update();
    void SetCanvas(rgb_matrix::Canvas *canvas);
    void SetContent(const std::string &content);
    // Set a custom draw callback and the total content height (in px).
    // The callback will be invoked with a `Canvas*` to draw the full
    // content (origin (0,0) is the top-left of the content area) and
    // the available drawing width (content area width minus scrollbar).
    // When a draw callback is set, `SetContent` (string) is ignored.
    void SetDrawCallback(std::function<void(rgb_matrix::Canvas*, int)> draw_cb,
                         int content_height_px);

    // Clear the draw callback and revert to text content mode.
    void ClearDrawCallback();

private:
    rgb_matrix::Canvas *canvas_;
    int x_, y_, w_, h_;
    const rgb_matrix::Font &font_;
    rgb_matrix::Color color_;
    std::vector<std::string> lines_;
    std::function<void(rgb_matrix::Canvas*, int)> draw_callback_;

    float scroll_speed_px_per_sec_;
    float wait_before_scroll_sec_;
    int scrollbar_width_;

    int content_height_; // total height in pixels
    float offset_px_;
    bool scrolling_;
    bool end_pause_;
    std::chrono::steady_clock::time_point last_change_;

    void RecomputeMetrics();
    static std::vector<std::string> SplitLines(const std::string &s);
};

#endif // SCROLLING_BOX_H
