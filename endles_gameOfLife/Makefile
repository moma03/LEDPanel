CXX=g++
CXXFLAGS = -std=c++20 -Iinclude -Wall -Wextra

SRC = $(wildcard src/*.cpp)
OBJ = $(SRC:.cpp=.o)
DEPS = $(OBJ:.o=.d)

TARGET = main

# Where our library resides. You mostly only need to change the
# RGB_LIB_DISTRIBUTION, this is where the library is checked out.
RGB_LIB_DISTRIBUTION=../rpi-rgb-led-matrix
RGB_INCDIR=$(RGB_LIB_DISTRIBUTION)/include
RGB_LIBDIR=$(RGB_LIB_DISTRIBUTION)/lib
RGB_LIBRARY_NAME=rgbmatrix
RGB_LIBRARY=$(RGB_LIBDIR)/lib$(RGB_LIBRARY_NAME).a
LDFLAGS+=-L$(RGB_LIBDIR) -l$(RGB_LIBRARY_NAME) -lrt -lm -lpthread

all : $(TARGET)

$(RGB_LIBRARY): FORCE
	$(MAKE) -C $(RGB_LIBDIR)

$(TARGET): $(OBJ) $(RGB_LIBRARY)
	$(CXX) $(OBJ) -o $@ $(LDFLAGS)

src/%.o : src/%.cpp
	$(CXX) -I$(RGB_INCDIR) $(CXXFLAGS) -MMD -MP -c $< -o $@

-include $(DEPS)

clean:
	rm -f $(OBJ) $(TARGET) $(DEPS)

FORCE:
.PHONY: FORCE
