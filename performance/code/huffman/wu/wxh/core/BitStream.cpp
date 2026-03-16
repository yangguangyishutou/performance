#include "BitStream.h"
#include <stdexcept>

namespace SSDC {

    // === Writer Implementation ===
    BitWriter::BitWriter() : currentByte(0), bitCount(0) {}

    void BitWriter::writeBit(int bit) {
        // 将 bit 放到 currentByte 的最低位 (或者是最高位，这里我们统一：从高位到低位写)
        // 比如写 1，变成 10000000 (如果 bitCount=0)
        // 这里采用：buffer 从低位向高位填，或者从高向低。
        // 为了简单，我们用 "从低到高" 的逻辑：currentByte |= (bit << bitCount)
        
        if (bit) {
            currentByte |= (1 << bitCount);
        }
        bitCount++;
        if (bitCount == 8) {
            buffer.push_back(currentByte);
            currentByte = 0;
            bitCount = 0;
        }
    }

    void BitWriter::writeBits(uint64_t val, int length) {
        for (int i = 0; i < length; ++i) {
            // 取出 val 的第 i 位
            writeBit((val >> i) & 1);
        }
    }

    void BitWriter::flush() {
        if (bitCount > 0) {
            buffer.push_back(currentByte);
            bitCount = 0;
            currentByte = 0;
        }
    }

    const std::vector<uint8_t>& BitWriter::getData() const {
        return buffer;
    }
    
    void BitWriter::clear() {
        buffer.clear();
        currentByte = 0;
        bitCount = 0;
    }

    // === Reader Implementation ===
    BitReader::BitReader(const std::vector<uint8_t>& data) 
        : buffer(data), bytePos(0), bitPos(0) {}

    int BitReader::readBit() {
        if (bytePos >= buffer.size()) return -1; // EOF

        int bit = (buffer[bytePos] >> bitPos) & 1;
        bitPos++;
        if (bitPos == 8) {
            bitPos = 0;
            bytePos++;
        }
        return bit;
    }

    uint64_t BitReader::readBits(int length) {
        uint64_t val = 0;
        for (int i = 0; i < length; ++i) {
            int bit = readBit();
            if (bit == -1) break; 
            val |= ((uint64_t)bit << i);
        }
        return val;
    }

    bool BitReader::isEOF() const {
        return bytePos >= buffer.size();
    }
}
