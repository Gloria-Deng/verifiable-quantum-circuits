# 可验证量子线路

我想知道，量子线路的成本还能从哪里省。这个项目里，我做了两件具体的事：找出倒平方根线路里可以消掉的门，以及用整数计算检查近似值在整个输入范围内会偏差多少。题目来自 [Google Quantum AI 的量子线路编译竞赛](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation)。

- **线路简化。** 我在早期 `invsqrt` 线路中移除了两对可抵消的 SWAP，公开榜显示的分数没有变化。
- **定点精度。** 我检查了常量种子方法在 3,133,452 个输入上的误差，并比较保留不同位数后最坏误差出现在哪里。[常量种子方法](https://www.kaggle.com/code/tobeetaylor/constseed-invsqrt-reconstruction)
- **线路组合。** 我选择并组合了倒平方根、解码组合优化和量子化学的公开方案，三条线路通过官方程序的全规模验证。2026 年 11 月 14 日的公开榜得分为 **27.28997**。线路和参数来自公开作品，选择、组合与验证由我完成。[maoxin123 的线路组合](https://www.kaggle.com/code/maoxin123/qcc-v25-coded-word-chemistry) · [leotang09 的提交包](https://www.kaggle.com/code/leotang09/vqcc-t7421-submission)

## 从哪段代码看起

| 脚本 | 用途 |
| --- | --- |
| [`src/estimate_score.py`](src/estimate_score.py) | 用三条线路的成本估算总分 |
| [`src/peephole_v17.py`](src/peephole_v17.py) | 查找可抵消的门，按需写出简化后的线路 |
| [`src/constseed_calibrate.py`](src/constseed_calibrate.py) | 复算倒平方根近似的误差，比较定点位宽 |

用 Python 3 输入三条线路的成本，估算器会打印 `GM 27.289965`：

```sh
python src/estimate_score.py 78765.63681893334 360209905486.0156 295358666.06853616
```

估算脚本只用 Python 标准库。运行其余两个实验需要安装 [`requirements.txt`](requirements.txt) 中的依赖。线路输入和官方验证工具可从比赛页面获取，估分使用的参考成本来自 [vqcc-harness](https://github.com/rikeda71/vqcc-harness)。

代码采用 [Apache License 2.0](LICENSE)。
