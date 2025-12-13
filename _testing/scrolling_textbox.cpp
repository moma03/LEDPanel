#include "scrolling_textbox.h"

using namespace rgb_matrix;

ScrollingTextBox::ScrollingTextBox(Canvas *canvas,
                                   int x, int y, int width, int height,
                                   const Font &font,
                                   const Color &color,
                                   const std::string &text,
                                   int speed,
                                   float wait_time,
                                   bool endless)
    : canvas_(canvas),
      x_(x), y_(y), w_(width), h_(height),
      font_(font), color_(color),
      text_(text), speed_(speed),
      wait_time_(wait_time), endless_(endless),
      offset_x_(0),
      last_reset_time_(std::chrono::steady_clock::now()) {
    // Measure text width
    text_width_ = DrawText(canvas_, font_, 0, 0, color_, text_.c_str());
}

void ScrollingTextBox::Update() {
    int baseline = y_ + h_ - 2; // simple baseline (could center vertically)

    if (endless_) {
        // Endless wrap-around scrolling
        int pos = -offset_x_;
        while (pos < w_) {
            DrawText(canvas_, font_, x_ + pos, baseline, color_, text_.c_str());
            pos += text_width_;
        }
        offset_x_ += speed_;
        if (offset_x_ >= text_width_) {
            offset_x_ = 0;
        }
    } else {
        // Loop mode (scroll then reset)
        int text_pos = x_ + w_ - offset_x_;
        DrawText(canvas_, font_, text_pos, baseline, color_, text_.c_str());

        if (text_width_ > w_) {
            offset_x_ += speed_;
            if (text_pos + text_width_ < x_) {
                auto now = std::chrono::steady_clock::now();
                float elapsed = std::chrono::duration<float>(now - last_reset_time_).count();
                if (elapsed >= wait_time_) {
                    offset_x_ = 0;
                    last_reset_time_ = now;
                }
            }
        } else {
            // Text fits inside box: just redraw & wait
            auto now = std::chrono::steady_clock::now();
            if (std::chrono::duration<float>(now - last_reset_time_).count() >= wait_time_) {
                last_reset_time_ = now;
            }
        }
    }
}