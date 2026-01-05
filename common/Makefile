CXXFLAGS = -Wall -O3 -fPIC -I../rpi-rgb-led-matrix/include -I./include -I./third_party/json
AR = ar

LIB = libledcommon.a
OBJS = src/config_loader.o src/scrolling_textbox.o

all: $(LIB)

$(LIB): $(OBJS)
	$(AR) rcs $(LIB) $(OBJS)

src/config_loader.o: src/config_loader.cpp include/config_loader.h
	g++ $(CXXFLAGS) -c src/config_loader.cpp -o src/config_loader.o

src/scrolling_textbox.o: src/scrolling_textbox.cpp include/scrolling_textbox.h
	g++ $(CXXFLAGS) -c src/scrolling_textbox.cpp -o src/scrolling_textbox.o

clean:
	rm -f $(LIB) $(OBJS)

.PHONY: all clean
