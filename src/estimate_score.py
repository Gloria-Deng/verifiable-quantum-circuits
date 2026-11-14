#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按官方参照成本离线算总分（几何平均），省得消耗每日提交额度。

参照成本取自三方独立公布并互相一致的值，再用我们两发已知出分反查校准：
  v33 算得 24.855871 / 平台 24.85586；v29 算得 24.696641 / 平台 24.69663（相对差 4e-6）。
DQI 那一档只有在验证器零失败抽样时才可直接对榜；抽到失败样本时重复因子从 1.1913 抬到 1.1967，
成本约 +0.46%，需要按零失败读数另行换算。

用法：python 离线算分.py <invsqrt> <dqi> <dfthcsos> [对照GM]
"""
import sys

REF = {"invsqrt": 2076774.233715282, "dqi": 24439463583672.93, "dfthcsos": 3355599588.3155365}
SRC = "rikeda71/vqcc-harness harness/refs.json；nasir26 与 notsnaykey 两处独立记录同一组数"


def gm(costs):
    ratios = [REF[k] / c for k, c in zip(("invsqrt", "dqi", "dfthcsos"), costs)]
    return ratios, (ratios[0] * ratios[1] * ratios[2]) ** (1.0 / 3.0)


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    costs = [float(a.replace(",", "")) for a in argv[1:4]]
    ratios, g = gm(costs)
    print("参照成本：%s" % SRC)
    print("比率  invsqrt %.6f / dqi %.6f / dfthcsos %.6f" % tuple(ratios))
    print("GM    %.6f" % g)
    if len(argv) > 4:
        base = float(argv[4].replace(",", ""))
        print("对照 %.6f ⇒ %+.4f%%" % (base, (g / base - 1) * 100))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
