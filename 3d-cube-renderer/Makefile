CXXFLAGS = -Wall -O3 -fPIC -I../rpi-rgb-led-matrix/include
LDFLAGS = -L../rpi-rgb-led-matrix/lib -lrgbmatrix -lstdc++ -lm

TARGETS = generative_art

all: $(TARGETS)

generative_art: generative_art.cc cube_renderer.h
	g++ $(CXXFLAGS) generative_art.cc -o generative_art $(LDFLAGS)

clean:
	rm -f $(TARGETS)

.PHONY: all clean
