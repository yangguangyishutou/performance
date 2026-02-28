#include "HuffmanTree.h"
#include <queue>
#include <iostream>

namespace SSDC {

    struct CompareNode {
        bool operator()(Node* l, Node* r) {
            return l->freq > r->freq; // 最小堆
        }
    };

    std::map<int, Code> HuffmanBuilder::buildCodes(const std::map<int, long long>& frequencies) {
        std::map<int, Code> codes;
        if (frequencies.empty()) return codes;

        std::priority_queue<Node*, std::vector<Node*>, CompareNode> pq;

        for (auto const& [id, freq] : frequencies) {
            pq.push(new Node(id, freq));
        }

        // 如果只有一个节点，特殊处理
        if (pq.size() == 1) {
            Node* root = pq.top();
            codes[root->id] = {0, 1}; // 1 bit '0'
            delete root; // 清理
            return codes;
        }

        while (pq.size() > 1) {
            Node* left = pq.top(); pq.pop();
            Node* right = pq.top(); pq.pop();

            Node* parent = new Node(-1, left->freq + right->freq);
            parent->left = left;
            parent->right = right;
            pq.push(parent);
        }

        Node* root = pq.top();
        generateCodesRecursive(root, 0, 0, codes);
        
        delete root; // 会递归删除所有子节点
        return codes;
    }

    void HuffmanBuilder::generateCodesRecursive(Node* node, uint64_t currentBits, int currentLen, std::map<int, Code>& codes) {
        if (!node) return;

        // 叶子节点
        if (!node->left && !node->right) {
            codes[node->id] = {currentBits, currentLen};
            return;
        }

        // 左子树加 0
        generateCodesRecursive(node->left, currentBits, currentLen + 1, codes);
        
        // 右子树加 1 (注意位运算：将 1 移到 currentLen 位置)
        // 我们的 BitStream 是从低位写的，所以这里直接把高位加上去可能需要对应
        // 这里为了简单，我们假设 currentBits 的低位对应树的高层。
        // 比如路径 Left->Right，就是 01。
        // Left: ...0, Right: ...1
        uint64_t rightBits = currentBits | ((uint64_t)1 << currentLen);
        generateCodesRecursive(node->right, rightBits, currentLen + 1, codes);
    }
}
