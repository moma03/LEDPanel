// -*- mode: c++; c-basic-offset: 2; indent-tabs-mode: nil; -*-
//
// This code is public domain
// (but note, once linked against the led-matrix library, this is
// covered by the GPL v2)
//
// This is a grab-bag of various demos and not very readable.
#include "led-matrix.h"

#include <getopt.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <algorithm>

#include <iostream>
#include "config_loader.h"

using std::min;
using std::max;

#define TERM_ERR  "\033[1;31m"
#define TERM_NORM "\033[0m"

using namespace rgb_matrix;

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
  interrupt_received = true;
}

class DemoRunner {
protected:
  DemoRunner(Canvas *canvas) : canvas_(canvas) {}
  inline Canvas *canvas() { return canvas_; }

public:
  virtual ~DemoRunner() {}
  virtual void Run() = 0;

private:
  Canvas *const canvas_;
};

// Simple class that generates a rotating block on the screen.
class RotatingBlockGenerator : public DemoRunner {
public:
  RotatingBlockGenerator(Canvas *m) : DemoRunner(m) {}

  uint8_t scale_col(int val, int lo, int hi) {
    if (val < lo) return 0;
    if (val > hi) return 255;
    return 255 * (val - lo) / (hi - lo);
  }

  void Run() override {
    const int cent_x = canvas()->width() / 2;
    const int cent_y = canvas()->height() / 2;

    // The square to rotate (inner square + black frame) needs to cover the
    // whole area, even if diagonal. Thus, when rotating, the outer pixels from
    // the previous frame are cleared.
    const int rotate_square = min(canvas()->width(), canvas()->height()) * 1.41;
    const int min_rotate = cent_x - rotate_square / 2;
    const int max_rotate = cent_x + rotate_square / 2;

    // The square to display is within the visible area.
    const int display_square = min(canvas()->width(), canvas()->height()) * 0.7;
    const int min_display = cent_x - display_square / 2;
    const int max_display = cent_x + display_square / 2;

    const float deg_to_rad = 2 * 3.14159265 / 360;
    int rotation = 0;
    while (!interrupt_received) {
      ++rotation;
      usleep(15 * 1000);
      rotation %= 360;
      for (int x = min_rotate; x < max_rotate; ++x) {
        for (int y = min_rotate; y < max_rotate; ++y) {
          float rot_x, rot_y;
          Rotate(x - cent_x, y - cent_x,
                 deg_to_rad * rotation, &rot_x, &rot_y);
          if (x >= min_display && x < max_display &&
              y >= min_display && y < max_display) { // within display square
            canvas()->SetPixel(rot_x + cent_x, rot_y + cent_y,
                               scale_col(x, min_display, max_display),
                               255 - scale_col(y, min_display, max_display),
                               scale_col(y, min_display, max_display));
          } else {
            // black frame.
            canvas()->SetPixel(rot_x + cent_x, rot_y + cent_y, 0, 0, 0);
          }
        }
      }
    }
  }

private:
  void Rotate(int x, int y, float angle, float *new_x, float *new_y) {
    *new_x = x * cosf(angle) - y * sinf(angle);
    *new_y = x * sinf(angle) + y * cosf(angle);
  }
};

// Conway's game of life
// Contributed by: Vliedel
class GameLife : public DemoRunner {
public:
  GameLife(Canvas *m, int delay_ms=500, bool torus=true)
    : DemoRunner(m), delay_ms_(delay_ms), torus_(torus) {
    width_ = canvas()->width();
    height_ = canvas()->height();

    // Allocate memory
    values_ = new int*[width_];
    for (int x=0; x<width_; ++x) {
      values_[x] = new int[height_];
    }
    newValues_ = new int*[width_];
    for (int x=0; x<width_; ++x) {
      newValues_[x] = new int[height_];
    }

    // Init values randomly
    srand(time(NULL));
    for (int x=0; x<width_; ++x) {
      for (int y=0; y<height_; ++y) {
        values_[x][y]=rand()%2;
      }
    }
    r_ = rand()%255;
    g_ = rand()%255;
    b_ = rand()%255;

    if (r_<150 && g_<150 && b_<150) {
      int c = rand()%3;
      switch (c) {
      case 0:
        r_ = 200;
        break;
      case 1:
        g_ = 200;
        break;
      case 2:
        b_ = 200;
        break;
      }
    }
  }

  ~GameLife() {
    for (int x=0; x<width_; ++x) {
      delete [] values_[x];
    }
    delete [] values_;
    for (int x=0; x<width_; ++x) {
      delete [] newValues_[x];
    }
    delete [] newValues_;
  }

  void Run() override {
    while (!interrupt_received) {

      updateValues();

      for (int x=0; x<width_; ++x) {
        for (int y=0; y<height_; ++y) {
          if (values_[x][y])
            canvas()->SetPixel(x, y, r_, g_, b_);
          else
            canvas()->SetPixel(x, y, 0, 0, 0);
        }
      }
      usleep(delay_ms_ * 1000); // ms
    }
  }

private:
  int numAliveNeighbours(int x, int y) {
    int num=0;
    if (torus_) {
      // Edges are connected (torus)
      num += values_[(x-1+width_)%width_][(y-1+height_)%height_];
      num += values_[(x-1+width_)%width_][y                    ];
      num += values_[(x-1+width_)%width_][(y+1        )%height_];
      num += values_[(x+1       )%width_][(y-1+height_)%height_];
      num += values_[(x+1       )%width_][y                    ];
      num += values_[(x+1       )%width_][(y+1        )%height_];
      num += values_[x                  ][(y-1+height_)%height_];
      num += values_[x                  ][(y+1        )%height_];
    }
    else {
      // Edges are not connected (no torus)
      if (x>0) {
        if (y>0)
          num += values_[x-1][y-1];
        if (y<height_-1)
          num += values_[x-1][y+1];
        num += values_[x-1][y];
      }
      if (x<width_-1) {
        if (y>0)
          num += values_[x+1][y-1];
        if (y<31)
          num += values_[x+1][y+1];
        num += values_[x+1][y];
      }
      if (y>0)
        num += values_[x][y-1];
      if (y<height_-1)
        num += values_[x][y+1];
    }
    return num;
  }

  void updateValues() {
    // Copy values to newValues
    for (int x=0; x<width_; ++x) {
      for (int y=0; y<height_; ++y) {
        newValues_[x][y] = values_[x][y];
      }
    }
    // update newValues based on values
    for (int x=0; x<width_; ++x) {
      for (int y=0; y<height_; ++y) {
        int num = numAliveNeighbours(x,y);
        if (values_[x][y]) {
          // cell is alive
          if (num < 2 || num > 3)
            newValues_[x][y] = 0;
        }
        else {
          // cell is dead
          if (num == 3)
            newValues_[x][y] = 1;
        }
      }
    }
    // copy newValues to values
    for (int x=0; x<width_; ++x) {
      for (int y=0; y<height_; ++y) {
        values_[x][y] = newValues_[x][y];
      }
    }
  }

  int** values_;
  int** newValues_;
  int delay_ms_;
  int r_;
  int g_;
  int b_;
  int width_;
  int height_;
  bool torus_;
};

class EndlessGameOfLife : public DemoRunner {
public:
  EndlessGameOfLife(Canvas *m) : DemoRunner(m) {}

  // Endlessly runs Conway's Game of Life, by continuously awaking random cells to life, with
  // probability 1/1000 per cell per iteration.
  void Run() override {
    const int width = canvas()->width();
    const int height = canvas()->height();

    // Initialize all cells to dead.
    std::vector<std::vector<bool>> cells(width, std::vector<bool>(height, false));

    // Make 70% of the cells alive initially.
    for (int x = 0; x < width; ++x) {
      for (int y = 0; y < height; ++y) {
        if (rand() % 100 < 70) {
          cells[x][y] = true;
        }
      }
    }


    srand(time(NULL));

    while (!interrupt_received) {
      // Update cells based on Game of Life rules.
      std::vector<std::vector<bool>> new_cells = cells;
      for (int x = 0; x < width; ++x) {
        for (int y = 0; y < height; ++y) {
          int alive_neighbors = 0;
          for (int dx = -1; dx <= 1; ++dx) {
            for (int dy = -1; dy <= 1; ++dy) {
              if (dx == 0 && dy == 0) continue;
              int nx = x + dx;
              int ny = y + dy;
              if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                alive_neighbors += cells[nx][ny] ? 1 : 0;
              }
            }
          }
          if (cells[x][y]) {
            new_cells[x][y] = (alive_neighbors == 2 || alive_neighbors == 3);
          } else {
            new_cells[x][y] = (alive_neighbors == 3);
          }
        }
      }

      // Randomly awaken dead cells.
      for (int x = 0; x < width; ++x) {
        for (int y = 0; y < height; ++y) {
          if (!new_cells[x][y] && (rand() % 500 == 0)) {
            new_cells[x][y] = true;
          }
        }
      }

      cells = new_cells;

      // Render the cells to the canvas.
      for (int x = 0; x < width; ++x) {
        for (int y = 0; y < height; ++y) {
          if (cells[x][y]) {
            canvas()->SetPixel(x, y, 255, 255, 255); // Alive cell: white
          } else {
            canvas()->SetPixel(x, y, 0, 0, 0);       // Dead cell: black
          }
        }
      }

      usleep(1000 * 10); // 100 ms
    }
  }
};


static int usage(const char *progname) {
  fprintf(stderr, "usage: %s <options> -D <demo-nr> [optional parameter]\n", progname);
  fprintf(stderr, "Options:\n");
  fprintf(stderr, "\t-D <demo-nr>              : Always needs to be set\n");


  rgb_matrix::PrintMatrixFlags(stderr);

  fprintf(stderr, "Demos, choosen with -D\n");
  fprintf(stderr, "\t0  - some rotating square\n"
          "\t1  - Conway's game of life (-m <time-step-ms>)\n"
          "\t2  - Endless Conway's game of life\n");
  fprintf(stderr, "Example:\n\t%s -D 1 runtext.ppm\n"
          "Scrolls the runtext until Ctrl-C is pressed\n", progname);
  return 1;
}

int main(int argc, char *argv[]) {
  int demo = -1;
  int scroll_ms = 30;

  const char *demo_parameter = NULL;
  RGBMatrix::Options matrix_options;
  rgb_matrix::RuntimeOptions runtime_opt;

  // Load options from config file (separated into config_loader)
  if (!LoadMatrixOptionsFromConfig("config.json", matrix_options, runtime_opt)) {
    std::cerr << TERM_ERR << "Error: Could not open or parse config.json file." << TERM_NORM << std::endl;
    return 1;
  }

  // First things first: extract the command line flags that contain
  // relevant matrix options.
  if (!ParseOptionsFromFlags(&argc, &argv, &matrix_options, &runtime_opt)) {
    return usage(argv[0]);
  }

  int opt;
  while ((opt = getopt(argc, argv, "dD:r:P:c:p:b:m:LR:")) != -1) {
    switch (opt) {
    case 'D':
      demo = atoi(optarg);
      break;

    case 'm':
      scroll_ms = atoi(optarg);
      break;

    default: /* '?' */
      return usage(argv[0]);
    }
  }

  if (optind < argc) {
    demo_parameter = argv[optind];
  }

  if (demo < 0) {
    fprintf(stderr, TERM_ERR "Expected required option -D <demo>\n" TERM_NORM);
    return usage(argv[0]);
  }

  RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_opt);
  if (matrix == NULL)
    return 1;

  printf("Size: %dx%d. Hardware gpio mapping: %s\n",
         matrix->width(), matrix->height(), matrix_options.hardware_mapping);

  Canvas *canvas = matrix;

  // The DemoRunner objects are filling
  // the matrix continuously.
  DemoRunner *demo_runner = NULL;
  switch (demo) {
  case 0:
    demo_runner = new RotatingBlockGenerator(canvas);
    break;

  case 1:
    demo_runner = new GameLife(canvas, scroll_ms);
    break;

  case 2:
    demo_runner = new EndlessGameOfLife(canvas);
    break;
  }

  if (demo_runner == NULL)
    return usage(argv[0]);

  // Set up an interrupt handler to be able to stop animations while they go
  // on. Each demo tests for while (!interrupt_received) {},
  // so they exit as soon as they get a signal.
  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  printf("Press <CTRL-C> to exit and reset LEDs\n");

  // Now, run our particular demo; it will exit when it sees interrupt_received.
  demo_runner->Run();

  delete demo_runner;
  delete canvas;

  printf("Received CTRL-C. Exiting.\n");
  return 0;
}
