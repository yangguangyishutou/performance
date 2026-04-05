# B span-safe rewrite 语料汇总

## 原始计数（全文件求和）

- `span_hits`: 12
- `span_misses_bounds`: 1
- `span_misses_slice_mismatch`: 25
- `global_replace_fallback_clusters`: 0

## 比率（在「有 spans 时尝试 span 路径」的语义下）

- **span hit ratio** ≈ hits / (hits + bounds_miss + slice_mismatch) = **0.3158**（分母 38）
- **slice mismatch ratio** ≈ slice_mismatch / 同上分母 = **0.6579**
- **global fallback**：按簇计数；本语料 gf=0（无 span 时整簇走 replace）

## 解读要点

- slice_mismatch 相对 hit 偏高时，优先排查 **B 改写后偏移** 或 **member_spans 与改写后文本不对齐**。
