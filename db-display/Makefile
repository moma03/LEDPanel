CXXFLAGS = -Wall -O3 -I../rpi-rgb-led-matrix/include -I../common/include -I../common/third_party/json
LDFLAGS = -L../rpi-rgb-led-matrix/lib -L../common -lrgbmatrix -lledcommon -lstdc++ -lm

COMMON_LIB = ../common/libledcommon.a
TARGET = db_display

all: $(COMMON_LIB) $(TARGET)

$(COMMON_LIB):
	$(MAKE) -C ../common

$(TARGET): db_display.cc $(COMMON_LIB)
	g++ $(CXXFLAGS) db_display.cc -o $(TARGET) $(LDFLAGS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
