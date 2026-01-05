# ScrollingBox example

Build and run (from this folder):

```bash
# Example compile line — adjust include/library paths as needed for your setup
g++ -std=c++17 -Wall -O3 \
  -I../include -I../..//rpi-rgb-led-matrix/include \
  -L../../rpi-rgb-led-matrix/lib \
  scrolling_box_example.cc \
  ../src/scrolling_box.cpp ../src/scrolling_textbox.cpp ../src/config_loader.cpp ../graphics.o \
  -lrgbmatrix -lpthread -o scrolling_box_example

# Then run:
./scrolling_box_example
```

Notes:
- For Raspberry Pi hardware set `runtime_options.do_gpio_init = true` in the example.
- Adjust font path if needed.
