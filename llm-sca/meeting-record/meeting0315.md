看项目方法
- mvn 里面 其实不是一个 binary 其实是一个 script 去执行 lib 里面的 jar 包
- 从总的入口进去 main

A B 两个 model
- 模型结构一样 -> weight 比较
- 不一样 -> 如何判断

微调后的
- 加了 adapter 的（两种形式 只有 AB 矩阵、融合进来）
- FFT 的 weight 都能映射上 -> js 来比较

py 小技巧 解析用的是 js - 不同语言之间如何传输数据 json
- cmd
- http py 里面开了 server

todo
- https://arxiv.org/abs/2411.17453
- **GUI 和 拿到的 graph 的映射**
  - GUI 里面 有边、数据(动态 debug print)
  - 打印 model 结构