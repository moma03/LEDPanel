#include "scrolling_textbox.h"

using namespace rgb_matrix;
using Clock = std::chrono::steady_clock;

namespace {
// Canvas wrapper that clips to a rectangle and forwards to an underlying canvas.
class ClipCanvas : public Canvas {
public:
    ClipCanvas(Canvas *base, int origin_x, int origin_y, int clip_x, int clip_y, int clip_w, int clip_h)
        : base_(base), origin_x_(origin_x), origin_y_(origin_y), clip_x_(clip_x), clip_y_(clip_y), clip_w_(clip_w), clip_h_(clip_h) {}

    int width() const override { return base_->width(); }
    int height() const override { return base_->height(); }

    void SetPixel(int x, int y, uint8_t r, uint8_t g, uint8_t b) override {
        const int gx = x + origin_x_;
        const int gy = y + origin_y_;
        if (gx < clip_x_ || gx >= clip_x_ + clip_w_ || gy < clip_y_ || gy >= clip_y_ + clip_h_) return;
        base_->SetPixel(gx, gy, r, g, b);
    }

    void Clear() override {}
    void Fill(uint8_t, uint8_t, uint8_t) override {}

private:
    Canvas *base_;
    int origin_x_, origin_y_;
    int clip_x_, clip_y_, clip_w_, clip_h_;
};

// Canvas that ignores all drawing, useful for measuring text width.
class NullCanvas : public Canvas {
public:
    int width() const override { return 0; }
    int height() const override { return 0; }
    void SetPixel(int, int, uint8_t, uint8_t, uint8_t) override {}
    void Clear() override {}
    void Fill(uint8_t, uint8_t, uint8_t) override {}
};
} // namespace

ScrollingTextBox::ScrollingTextBox(Canvas *canvas,
                                   int x, int y, int width, int height,
                                   const Font &font,
                                   const Color &color,
                                   const std::string &text,
                                   float scroll_speed_px_per_sec,
                                   float wait_before_scroll_sec,
                                   int gap_px)
    : canvas_(canvas),
      x_(x), y_(y), w_(width), h_(height),
      font_(font), color_(color), text_(text),
      scroll_speed_px_per_sec_(scroll_speed_px_per_sec),
      wait_before_scroll_sec_(wait_before_scroll_sec),
      gap_px_(gap_px),
      text_width_(0),
      offset_px_(0.0f),
      scrolling_(false),
      last_change_(Clock::now()) {
    text_width_ = MeasureTextWidth(text_);
}

void ScrollingTextBox::SetCanvas(Canvas *canvas) {
    canvas_ = canvas;
}

void ScrollingTextBox::SetText(const std::string &text) {
    text_ = text;
    text_width_ = MeasureTextWidth(text_);
    offset_px_ = 0.0f;
    scrolling_ = false;
    last_change_ = Clock::now();
}

int ScrollingTextBox::MeasureTextWidth(const std::string &text) const {
    NullCanvas nc;
    // y baseline doesn't matter; background is null => transparent.
    return DrawText(&nc, font_, 0, 0, color_, nullptr, text.c_str());
}

void ScrollingTextBox::Update() {
    const auto now = Clock::now();
    const float dt = std::chrono::duration<float>(now - last_change_).count();

    ClipCanvas clip(canvas_, 0, 0, x_, y_, w_, h_);
    const int baseline = y_ + font_.baseline();

    // If text fits, just draw once.
    if (text_width_ <= w_) {
        DrawText(&clip, font_, x_, baseline, color_, nullptr, text_.c_str());
        last_change_ = now; // keep time fresh
        return;
    }

    if (!scrolling_) {
        // Initial wait before starting to scroll
        DrawText(&clip, font_, x_, baseline, color_, nullptr, text_.c_str());
        if (dt >= wait_before_scroll_sec_) {
            scrolling_ = true;
            last_change_ = now;
        }
        return;
    }

    // Scrolling state
    const float elapsed = dt;
    offset_px_ += scroll_speed_px_per_sec_ * elapsed;

    // Draw primary instance
    float start_x = x_ - offset_px_;
    DrawText(&clip, font_, static_cast<int>(start_x), baseline, color_, nullptr, text_.c_str());

    // Draw wrapped instance if needed (seamless wrap)
    const float wrap_start = start_x + text_width_ + gap_px_;
    if (wrap_start < x_ + w_) {
        DrawText(&clip, font_, static_cast<int>(wrap_start), baseline, color_, nullptr, text_.c_str());
    }

    // Reset loop when fully scrolled out
    if (offset_px_ >= text_width_ + gap_px_) {
        offset_px_ -= (text_width_ + gap_px_);
        scrolling_ = false;
    }

    last_change_ = now;
}
