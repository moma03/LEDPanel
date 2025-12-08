CXX := g++
PKG_CFLAGS := $(shell pkg-config --cflags yaml-cpp 2>/dev/null)
PKG_LIBS := $(shell pkg-config --libs yaml-cpp 2>/dev/null)
RGB_LIBS := -lledmatrix -lpthread

CXXFLAGS := -O2 -std=c++17 $(PKG_CFLAGS)
LDFLAGS := $(PKG_LIBS) $(RGB_LIBS)

SRCS := endles_gameOfLife.cpp baseWSettings.cpp
OBJS := $(SRCS:.cpp=.o)
TARGET := endles_gameOfLife

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

run: $(TARGET)
	# Running on hardware usually requires root to access GPIO
	sudo ./$(TARGET) endles_gameOfLife/settings.yaml

# Help target to show compile flags if pkg-config cannot find yaml-cpp
help:
	@echo "Build: make" \
		"(requires yaml-cpp pkg-config and rpi-rgb-led-matrix libs)"
	@echo "If pkg-config cannot find yaml-cpp, set PKG_CFLAGS and PKG_LIBS manually." \
	@echo "Example: make CXXFLAGS=\"-O2 -std=c++17 -I/path/to/yaml-cpp/include\" LDFLAGS=\"-L/path/to/yaml-cpp/lib -lyaml-cpp -lledmatrix -lpthread\""
