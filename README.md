# 可验证量子线路：组合、分析与资源评估

围绕 [Google Quantum AI – Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation) 的参赛项目，研究可在经典计算机上验证的量子线路，比较融合、组合优化与量子化学三个任务的资源开销。

## 项目成果

| 工作 | 结果 |
| --- | --- |
| 公开线路组合与验证 | 三个任务的公开线路使用官方程序完成全规模验证，结果均通过 |
| 参赛提交 | 2026 年 11 月 14 日公开榜 **27.28997**；17:17（北京时间）位列 **404 / 3,023 队** |
| 线路简化实验 | 对早期版本扫描可抵消操作，在 `invsqrt` 中移除两对 SWAP；公开榜显示分数未变 |
| 数值分析 | 检查 `invsqrt` 常量种子方案在 3,133,452 个输入上的误差，并研究截断精度 |

**27.28997 分的最终提交组合来自 leotang09 等参赛者已公开的线路和参数**。本项目完成方案选择、组合、官方验证和提交；数值分析和早期线路简化是另外开展的实验，不等同于该高分方案的原创线路设计。

## 问题与方法

比赛需要同时提交三类线路：`invsqrt`（倒平方根相位）、`dqi`（解码与组合优化）和 `dfthcsos`（量子化学）。每个任务由官方验证程序检查线路行为，并计算其资源成本；总成绩根据三个任务相对于参考成本的改善倍数计算。

项目中的工作包括：

1. 准备官方工具与依赖，分别验证三类线路；
2. 比较公开线路和参数，组合成完整提交，并在超算上使用官方程序验证；
3. 研究可抵消的量子门以及倒平方根近似的数值精度；
4. 根据三个任务的成本估算总成绩，辅助比较不同组合。

## 代码

| 文件 | 用途 |
| --- | --- |
| [estimate_score.py](src/estimate_score.py) | 根据三个任务的成本估算组合成绩 |
| [peephole_v17.py](src/peephole_v17.py) | 扫描可抵消的门，并可输出简化线路 |
| [constseed_calibrate.py](src/constseed_calibrate.py) | 复算常量种子近似在输入范围内的误差 |

成绩估算只需 Python：

```bash
python src/estimate_score.py 78765.63681893334 360209905486.0156 295358666.06853616
```

上述输入对应一次公开线路组合的三个成本，估算值约为 **27.289965**。`peephole_v17.py` 需要 `numpy` 与 `kickmix`，`constseed_calibrate.py` 需要 `numpy`；完整数值计算和官方验证在配置好比赛环境的计算节点执行。比赛线路与官方数据从比赛页面获取。

## 参考与贡献

- [Google Quantum AI 比赛说明](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation)
- [Qualtran](https://github.com/quantumlib/Qualtran) 和 [kickmix](https://pypi.org/project/kickmix/)
- 本项目成绩估算所用参考成本参照 [rikeda71/vqcc-harness](https://github.com/rikeda71/vqcc-harness) 等公开资料。
- 常量种子数值分析参考 tobeetaylor 的公开方法；高分提交采用 maoxin123、leotang09 及其他参赛者公开的线路和参数。

## 许可

项目代码采用 [Apache License 2.0](LICENSE)。第三方资料和模型分别遵循其原有许可。
