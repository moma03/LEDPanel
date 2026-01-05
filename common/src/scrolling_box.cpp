#include "scrolling_box.h"

using namespace rgb_matrix;
using Clock = std::chrono::steady_clock;

namespace {
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

class NullCanvas : public Canvas {
public:
    int width() const override { return 0; }
    int height() const override { return 0; }
    void SetPixel(int, int, uint8_t, uint8_t, uint8_t) override {}
    void Clear() override {}
    void Fill(uint8_t, uint8_t, uint8_t) override {}
};
} // namespace

static std::vector<std::string> split_lines(const std::string &s) {
    std::vector<std::string> out;
    size_t pos = 0;
    while (pos < s.size()) {
        size_t nl = s.find('\n', pos);
        if (nl == std::string::npos) { out.emplace_back(s.substr(pos)); break; }
        out.emplace_back(s.substr(pos, nl - pos));
        pos = nl + 1;
    }
    if (s.empty()) out.push_back("");
    return out;
}

ScrollingBox::ScrollingBox(Canvas *canvas,
                           int x, int y, int width, int height,
                           const Font &font,
                           const Color &color,
                           const std::string &content,
                           float scroll_speed_px_per_sec,
                           float wait_before_scroll_sec,
                           int scrollbar_width)
    : canvas_(canvas), x_(x), y_(y), w_(width), h_(height), font_(font), color_(color),
      scroll_speed_px_per_sec_(scroll_speed_px_per_sec), wait_before_scroll_sec_(wait_before_scroll_sec),
      scrollbar_width_(scrollbar_width), content_height_(0), offset_px_(0.0f), scrolling_(false), last_change_(Clock::now()) {
    lines_ = split_lines(content);
    RecomputeMetrics();
}

void ScrollingBox::SetCanvas(Canvas *canvas) { canvas_ = canvas; }

void ScrollingBox::SetContent(const std::string &content) {
    lines_ = split_lines(content);
    RecomputeMetrics();
    offset_px_ = 0.0f;
    scrolling_ = false;
    last_change_ = Clock::now();
}

void ScrollingBox::RecomputeMetrics() {
    // Each line height approximated by font.height()
    content_height_ = static_cast<int>(lines_.size() * font_.height());
}

void ScrollingBox::Update() {
    const auto now = Clock::now();
    const float dt = std::chrono::duration<float>(now - last_change_).count();

    ClipCanvas clip(canvas_, 0, 0, x_, y_, w_, h_);

    // If content fits, draw static starting at top
    if (content_height_ <= h_) {
        int draw_y = y_ + font_.baseline();
        for (size_t i = 0; i < lines_.size(); ++i) {
            DrawText(&clip, font_, x_, draw_y + (int)(i * font_.height()), color_, nullptr, lines_[i].c_str());
        }
        // draw scrollbar background/track faintly (optional) if content smaller -> full thumb
        // Do not animate; keep time fresh
        last_change_ = now;
        return;
    }

    if (!scrolling_) {
        // initial wait
        int draw_y = y_ + font_.baseline();
        for (size_t i = 0; i < lines_.size(); ++i) {
            DrawText(&clip, font_, x_, draw_y + (int)(i * font_.height()), color_, nullptr, lines_[i].c_str());
        }
        if (dt >= wait_before_scroll_sec_) {
            scrolling_ = true;
            last_change_ = now;
        }
        return;
    }

    // Scrolling active
    offset_px_ += scroll_speed_px_per_sec_ * dt;

    // Wrap-around when fully scrolled
    const int total = content_height_ + 1; // small buffer
    if (offset_px_ >= total) offset_px_ -= total;

    // Draw lines starting from -offset_px_
    int base_y = static_cast<int>(y_ - offset_px_ + font_.baseline());
    for (size_t i = 0; i < lines_.size(); ++i) {
        DrawText(&clip, font_, x_, base_y + (int)(i * font_.height()), color_, nullptr, lines_[i].c_str());
    }

    // Draw scrollbar on the right side within the box
    const int track_x = x_ + w_ - scrollbar_width_;
    const int track_w = scrollbar_width_;

    // Thumb size proportional to visible/total
    const float visible = static_cast<float>(h_);
    const float thumb_h = std::max(4.0f, (visible / static_cast<float>(content_height_)) * h_);
    const float max_thumb_pos = h_ - thumb_h;
    const float thumb_pos = (offset_px_ / static_cast<float>(content_height_)) * max_thumb_pos;

    // Draw track (light background) and thumb (brighter)
    // track: dim pixels
    for (int yy = 0; yy < h_; ++yy) {
        for (int xx = 0; xx < track_w; ++xx) {
            // slightly darker than content: scale color by 0.15
            uint8_t r = static_cast<uint8_t>(color_.r * 0.12f);
            uint8_t g = static_cast<uint8_t>(color_.g * 0.12f);
            uint8_t b = static_cast<uint8_t>(color_.b * 0.12f);
            clip.SetPixel(track_x + xx, y_ + yy, r, g, b);
        }
    }

    // thumb
    int thumb_top = y_ + static_cast<int>(thumb_pos);
    int thumb_h_i = static_cast<int>(thumb_h);
    for (int yy = 0; yy < thumb_h_i; ++yy) {
        for (int xx = 0; xx < track_w; ++xx) {
            clip.SetPixel(track_x + xx, thumb_top + yy, color_.r, color_.g, color_.b);
        }
    }

    last_change_ = now;
}
