
CXX := g++
PKG_CFLAGS := $(shell pkg-config --cflags yaml-cpp 2>/dev/null)
PKG_LIBS := $(shell pkg-config --libs yaml-cpp 2>/dev/null)

# Path to rpi-rgb-led-matrix submodule (relative to this folder)
LED_DIR ?= $(abspath $(CURDIR)/../rpi-rgb-led-matrix)
LED_INC := -I$(LED_DIR)/include
LED_LIBS := -L$(LED_DIR)/lib -lledmatrix -lpthread

FALLBACK_YAML_INC := -I$(CURDIR)/fake_include
CXXFLAGS := -O2 -std=c++17 $(PKG_CFLAGS) $(LED_INC)
ifeq ($(strip $(PKG_CFLAGS)),)
CXXFLAGS += $(FALLBACK_YAML_INC)
endif

LDFLAGS := $(PKG_LIBS) $(LED_LIBS)

SRCS := endles_gameOfLife.cpp baseWSettings.cpp
OBJS := $(SRCS:.cpp=.o)
TARGET := endles_gameOfLife

.PHONY: all clean run help

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
		"(requires yaml-cpp pkg-config and rpi-rgb-led-matrix submodule at ../rpi-rgb-led-matrix)"
	@echo "If pkg-config cannot find yaml-cpp, set PKG_CFLAGS and PKG_LIBS manually." \
	@echo "Example: make CXXFLAGS=\"-O2 -std=c++17 -I/path/to/yaml-cpp/include\" LDFLAGS=\"-L/path/to/yaml-cpp/lib -lyaml-cpp -lledmatrix -lpthread\""
