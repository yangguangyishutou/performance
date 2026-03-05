#ifndef HUFFMANTREE_H
#define HUFFMANTREE_H

#include <vector>
#include <map>
#include <string>

namespace SSDC {

    struct Node {
        int id;             // Token ID (-1 for internal)
        long long freq;     // Frequency
        Node *left, *right;
        Node(int id, long long freq) : id(id), freq(freq), left(nullptr), right(nullptr) {}
        ~Node() { delete left; delete right; } // 简单的递归析构
    };

    // 编码结果结构体
    struct Code {
        uint64_t bits; // 编码的二进制值
        int length;    // 编码长度
    };

    class HuffmanBuilder {
    public:
        // 输入：Token ID -> 频率的映射
        // 输出：构建好的编码表 (Token ID -> Code)
        static std::map<int, Code> buildCodes(const std::map<int, long long>& frequencies);
        
    private:
        static void generateCodesRecursive(Node* node, uint64_t currentBits, int currentLen, std::map<int, Code>& codes);
    };
}

#endif // HUFFMANTREE_H
