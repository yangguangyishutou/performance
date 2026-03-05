#ifndef BITSTREAM_H
#define BITSTREAM_H

#include <vector>
#include <cstdint>
#include <string>

namespace SSDC {

    // 位写入器：负责把不定长的 bit 拼成字节流
    class BitWriter {
    public:
        BitWriter();
        // 写入 0 或 1
        void writeBit(int bit);
        // 写入 val 的低 length 位 (例如 writeBits(10, 4) 写入 1010)
        void writeBits(uint64_t val, int length);
        // 强制刷新缓冲区，补齐最后一个字节
        void flush();
        // 获取最终的字节数据
        const std::vector<uint8_t>& getData() const;
        // 清空
        void clear();

    private:
        std::vector<uint8_t> buffer;
        uint8_t currentByte;
        int bitCount; // 当前字节已经写了多少位 (0-7)
    };

    // 位读取器：负责从字节流里把 bit 抠出来
    class BitReader {
    public:
        BitReader(const std::vector<uint8_t>& data);
        // 读取 1 bit
        int readBit();
        // 读取 length bits
        uint64_t readBits(int length);
        // 是否已读完
        bool isEOF() const;

    private:
        const std::vector<uint8_t>& buffer;
        size_t bytePos; // 当前读到第几个字节
        int bitPos;     // 当前字节读到第几位 (0-7)
    };

}

#endif // BITSTREAM_H
