CXXFLAGS = -Wall -O3 -fPIC -I../rpi-rgb-led-matrix/include -I./include
LDFLAGS = -L../rpi-rgb-led-matrix/lib -lrgbmatrix -lstdc++ -lm

TARGETS = generative_art test_pattern falling_rain

all: $(TARGETS)

generative_art: generative_art.cc config_loader.cpp cube_renderer.h config_loader.h
	g++ $(CXXFLAGS) generative_art.cc config_loader.cpp -o generative_art $(LDFLAGS)

test_pattern: test_pattern.cc config_loader.cpp test_pattern.h config_loader.h
	g++ $(CXXFLAGS) test_pattern.cc config_loader.cpp -o test_pattern $(LDFLAGS)

falling_rain: falling_rain.cc config_loader.cpp cube_renderer.h config_loader.h
	g++ $(CXXFLAGS) falling_rain.cc config_loader.cpp -o falling_rain $(LDFLAGS)

clean:
	rm -f $(TARGETS)

.PHONY: all clean
