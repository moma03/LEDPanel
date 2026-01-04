CXXFLAGS = -Wall -O3 -fPIC -I../rpi-rgb-led-matrix/include -I./include
LDFLAGS = -L../rpi-rgb-led-matrix/lib -lrgbmatrix -lstdc++ -lm

TARGETS = generative_art

all: $(TARGETS)

generative_art: generative_art.cc config_loader.cpp cube_renderer.h config_loader.h
	g++ $(CXXFLAGS) generative_art.cc config_loader.cpp -o generative_art $(LDFLAGS)

clean:
	rm -f $(TARGETS)

.PHONY: all clean
