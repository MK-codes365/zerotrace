CXX = g++
CXXFLAGS = -fPIC -O2 -Wall
LDFLAGS = -shared

TARGET = libwiper.so
SRC = wiper_core_linux.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TARGET)
