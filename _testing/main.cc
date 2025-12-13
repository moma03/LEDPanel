#include "led-matrix.h"
#include "graphics.h"
#include "scrolling_textbox.h"
#include <unistd.h> // for usleep

using namespace rgb_matrix;

int main(int argc, char **argv) {
    RGBMatrix::Options options;
    rgb_matrix::RuntimeOptions runtime_opt;
    options.rows = 64;
    options.cols = 128;
    options.chain_length = 4;
    options.parallel = 1;
    options.brightness = 100;
    options.pwm_bits = 4;
    options.pixel_mapper_config = "U-Mapper;Rotate:180";
    options.show_refresh_rate = true;
    runtime_opt.gpio_slowdown = 2;

    RGBMatrix *matrix = CreateMatrixFromOptions(options, runtime_opt);
    if (matrix == nullptr) return 1;

    Canvas *canvas = matrix;

    Font font;
    font.LoadFont("../rpi-rgb-led-matrix/fonts/5x8.bdf");

    Font bigFont;
    bigFont.LoadFont("../rpi-rgb-led-matrix/fonts/clR6x12.bdf");

    canvas->Fill(0, 0, 180); // blue background
    DrawText(canvas, bigFont, 12, 100, Color(255, 255, 0), "Achtung Zugdurchfahrt");


    Color color(255, 255, 0);
    ScrollingTextBox scroller(canvas, 0, 0, 64, 16,
                              font, color,
                              "Hello hello moin servus gruezi hallo salut ciao",
                              1, 1.5f, false);




    while (true) {
        // Draw "Achtung Zugdurchfahrt" text
        

        // Update and draw the scrolling text box
        scroller.Update();
        usleep(200);
    }

    delete matrix;
    return 0;
}