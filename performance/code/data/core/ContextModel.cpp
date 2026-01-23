#include "ContextModel.h"
#include <iostream>

namespace SSDC {

    ContextModel::ContextModel() {}

    std::vector<uint8_t> ContextModel::compress(const std::vector<int>& tokens, const std::vector<int>& contexts) {
        // 1. 统计频率 (Context-Aware Frequency Counting)
        std::vector<std::map<int, long long>> freqs(NUM_CONTEXTS);
        for (size_t i = 0; i < tokens.size(); ++i) {
            int ctx = contexts[i];
            if (ctx < 0 || ctx >= NUM_CONTEXTS) ctx = 0;
            freqs[ctx][tokens[i]]++;
        }

        // 2. 构建编码表 (Multi-Tree Building)
        std::vector<std::map<int, Code>> codeMaps(NUM_CONTEXTS);
        for (int i = 0; i < NUM_CONTEXTS; ++i) {
            codeMaps[i] = HuffmanBuilder::buildCodes(freqs[i]);
        }

        BitWriter writer;

        // 3. 写入文件头 (Header)
        // 为了能解压，必须把频率表存进去。
        // 格式简单的设计为：[ContextCount] -> For each Context: [TokenCount] -> [TokenID, Freq] ...
        writeHeader(writer, freqs);
        
        // 写入总 Token 数量 (方便解压循环)
        // 实际工程可能用 EOF 符号，这里为了简单直接存数量
        uint64_t totalTokens = tokens.size();
        // 假设 Token 数不超过 32 位整数范围
        writer.writeBits(totalTokens, 32);

        // 4. 写入压缩数据 (Context-Aware Encoding)
        for (size_t i = 0; i < tokens.size(); ++i) {
            int id = tokens[i];
            int ctx = contexts[i];
            if (ctx < 0 || ctx >= NUM_CONTEXTS) ctx = 0;

            // 在对应的上下文中查找编码
            if (codeMaps[ctx].count(id)) {
                Code c = codeMaps[ctx][id];
                writer.writeBits(c.bits, c.length);
            } else {
                // 理论上不可能发生，除非逻辑错
                std::cerr << "Error: Token " << id << " not found in context " << ctx << std::endl;
            }
        }

        writer.flush();
        return writer.getData();
    }
    
    // 这里只演示压缩逻辑，解压逻辑为了节省代码量暂留空或简化
    // 实际工程中，解压就是压缩的逆过程：读Header -> 建树 -> 读Bits -> 游走树
    std::vector<int> ContextModel::decompress(const std::vector<uint8_t>& compressedData) {
        return std::vector<int>(); 
    }

    void ContextModel::writeHeader(BitWriter& writer, const std::vector<std::map<int, long long>>& freqs) {
        // 简单的 Header 格式：
        // 4 bits: Context Count (虽然固定是4)
        writer.writeBits(NUM_CONTEXTS, 4); 

        for (int i = 0; i < NUM_CONTEXTS; ++i) {
            // 16 bits: 该 Context 下有多少个 Unique Tokens
            uint64_t mapSize = freqs[i].size();
            writer.writeBits(mapSize, 16);

            for (auto const& [id, count] : freqs[i]) {
                // 16 bits: Token ID (假设 vocab < 65536)
                writer.writeBits(id, 16);
                // 32 bits: Frequency (用于重建哈夫曼树)
                // 也可以只存 code length，那样更省空间，但算法复杂点。这里直接存频次。
                writer.writeBits(count, 32); 
            }
        }
    }
}
