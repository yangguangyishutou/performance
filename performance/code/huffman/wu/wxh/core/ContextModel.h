#ifndef CONTEXTMODEL_H
#define CONTEXTMODEL_H

#include <vector>
#include <map>
#include "BitStream.h"
#include "HuffmanTree.h"

namespace SSDC {

    // 上下文数量：0=Default, 1=Class, 2=Func, 3=String/Var
    const int NUM_CONTEXTS = 4;

    class ContextModel {
    public:
        ContextModel();

        // 核心功能：压缩
        // 输入：token数组, context数组
        // 输出：二进制压缩数据 (包含头部信息)
        std::vector<uint8_t> compress(const std::vector<int>& tokens, const std::vector<int>& contexts);

        // 核心功能：解压 (为了完整性，虽然演示主要看压缩率)
        // 输入：二进制压缩数据
        // 输出：token数组 (contexts 会在内部被隐含还原，但为了简单这里只吐出 tokens)
        std::vector<int> decompress(const std::vector<uint8_t>& compressedData);

    private:
        // 辅助：将频率表写入 BitWriter (作为文件头)
        void writeHeader(BitWriter& writer, const std::vector<std::map<int, long long>>& freqs);
        // 辅助：从 BitReader 读取频率表
        std::vector<std::map<int, long long>> readHeader(BitReader& reader);
    };
}

#endif // CONTEXTMODEL_H
