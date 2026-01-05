CXXFLAGS = -Wall -O3 -fPIC -I../rpi-rgb-led-matrix/include -I./include -I./third_party/json
AR = ar

LIB = libledcommon.a
OBJS = src/config_loader.o

all: $(LIB)

$(LIB): $(OBJS)
	$(AR) rcs $(LIB) $(OBJS)

src/config_loader.o: src/config_loader.cpp include/config_loader.h
	g++ $(CXXFLAGS) -c src/config_loader.cpp -o src/config_loader.o

clean:
	rm -f $(LIB) $(OBJS)

.PHONY: all clean
