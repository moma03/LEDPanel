CXXFLAGS = -Wall -O3 -fPIC -I../rpi-rgb-led-matrix/include -I../common/include -I../common/third_party/json
LDFLAGS = -L../rpi-rgb-led-matrix/lib -L../common -lrgbmatrix -lledcommon -lstdc++ -lm

COMMON_LIB = ../common/libledcommon.a
TARGETS = test_pattern falling_rain generative_art

all: $(TARGETS)

$(COMMON_LIB):
	$(MAKE) -C ../common

test_pattern: test_pattern.cc test_pattern.h $(COMMON_LIB)
	g++ $(CXXFLAGS) test_pattern.cc -o test_pattern $(LDFLAGS)

falling_rain: falling_rain.cc cube_renderer.h $(COMMON_LIB)
	g++ $(CXXFLAGS) falling_rain.cc -o falling_rain $(LDFLAGS)

generative_art: generative_art.cc cube_renderer.h $(COMMON_LIB)
	g++ $(CXXFLAGS) generative_art.cc -o generative_art $(LDFLAGS)

clean:
	rm -f $(TARGETS)

.PHONY: all clean
