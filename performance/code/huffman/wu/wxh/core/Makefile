CXX = g++
CXXFLAGS = -O3 -fPIC -std=c++17 -Wall

# 目标库文件
TARGET = libssdc_core.so

# 源文件 (增加了 ContextModel.cpp 和 ssdc_api.cpp)
SRCS = BitStream.cpp HuffmanTree.cpp ContextModel.cpp ssdc_api.cpp

# 对象文件
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -shared -o $@ $(OBJS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)
