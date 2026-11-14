# -*- coding: utf-8 -*-
"""常量种子 invsqrt 模型全定义域标定 v3(2026-11-10)。
v2 裁决结论:相位定标 F = out_frac + N_P + 1(37) 时,整数复算逐位复现
tobeetaylor notebook 的 margin 声称(table 0.6434 / pwq3 0.5577)。
v3 内容:
- F 固定 37,只算正确约定;
- 砍位量化改为"有效位截断"(27 位尾数,keep<27 才真砍);
- 宽度扫描修正 F 公式(out + N_P + 1)。
"""
import math
import numpy as np

N_P = 10
WIDTH = 2 * N_P + 2
MAX_X = 3 * (2**N_P - 2) ** 2
SHIFT_TOL = 25
MASK64 = (1 << 64) - 1
U64 = np.uint64

xs = np.arange(1, MAX_X + 1, dtype=np.int64)
print(f"domain x=1..{MAX_X:,}", flush=True)

target = np.empty(len(xs), dtype=np.uint64)
tol = np.empty(len(xs), dtype=np.uint64)
for i, x in enumerate(xs.tolist()):
    r = math.isqrt((1 << 130) // x)
    target[i] = ((r + 1) >> 1) & MASK64
    tol[i] = min(r >> SHIFT_TOL, 1 << 63)
tol_f = tol.astype(np.float64)
print("official target/tol tabulated.", flush=True)

s_arr = (WIDTH - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2

def seed_table(frac=8):
    i = np.arange(128, dtype=np.float64)
    Mc = (i + 0.5) / 32.0
    return np.round((1.0 / np.sqrt(Mc)) * 2.0**frac).astype(np.int64)

def fit_pwq3():
    out = []
    for m0, m1 in ((1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 4.0)):
        w = m1 - m0
        u = np.arange(128, dtype=np.float64) / 128.0
        M = m0 + u * w
        A = np.vander(u, 4)[:, ::-1]
        coef, *_ = np.linalg.lstsq(A, 1.0 / np.sqrt(M), rcond=None)
        out.append(tuple(coef))
    return out
_PWQ3 = fit_pwq3()

def seed_values(mode, seed_frac):
    x_norm = xs << (2 * s_arr)
    if mode == "table":
        return seed_table(seed_frac)[x_norm >> (WIDTH - 7)]
    top = (x_norm >> (WIDTH - 1)) & 1
    second = (x_norm >> (WIDTH - 2)) & 1
    third = (x_norm >> (WIDTH - 3)) & 1
    inter = np.where(top == 0, third, 2 + second)
    m0v = np.array([1., 1.5, 2., 3.])[inter]
    wv = np.array([.5, .5, 1., 1.])[inter]
    Mv = x_norm.astype(np.float64) / 2.0**(WIDTH - 2)
    kk = ((Mv - m0v) / wv * 128.0).astype(np.int64).astype(np.float64) / 128.0
    a, b, c, d = (np.array([t[j] for t in _PWQ3])[inter] for j in range(4))
    return ((((d * kk + c) * kk + b) * kk + a) * 2.0**seed_frac).astype(np.int64)

def constseed_P2(mode="table", seed_frac=8, n1_frac=16, n2_guard=24, out_frac=26):
    x_norm = xs << (2 * s_arr)
    S = seed_values(mode, seed_frac)
    Q1 = (x_norm * S * S) >> (WIDTH - 2 + 2 * seed_frac - n1_frac)
    C1 = (3 << n1_frac) - Q1
    P1 = (S * C1) >> seed_frac
    g = n2_guard + 2
    P1g = P1 << (g - n1_frac)
    Q2 = (x_norm * P1 * P1) >> (WIDTH - g + 2 * n1_frac)
    C2 = ((3 << g) - Q2) >> 1
    return (P1g * C2) >> (2 * g - out_frac)

def trunc_sig(P2, keep):
    """有效位截断:尾数位长按 x 逐点求(27 或 28),保留顶部 keep 位。keep>=位长为空操作。"""
    nb = (np.floor(np.log2(P2.astype(np.float64))).astype(np.int64) + 1)
    d = np.maximum(nb - keep, 0)
    return (P2 >> d) << d

def ratio(P2, out_frac, keep=None):
    F = out_frac + N_P + 1
    P = trunc_sig(P2, keep) if keep else P2
    approx_units = ((P.astype(np.uint64) << s_arr.astype(np.uint64)) << U64(64 - F))
    err = (approx_units - target).view(np.int64)
    return np.abs(err).astype(np.float64) / tol_f

def report(tag, arr):
    i = int(np.argmax(arr))
    v = float(arr[i])
    print(f"{tag:<46} worst = {v:.6f}  at x={int(xs[i]):,}", flush=True)
    return v

P2_t = constseed_P2("table")
P2_p = constseed_P2("pwq3")

print("== 常量种子 margin 全定义域(F=37,整数 isqrt target/tol) ==", flush=True)
report("constseed table (16,24,26) no-drop", ratio(P2_t, 26))
report("constseed pwq3  (16,24,26) no-drop", ratio(P2_p, 26))

print("== 有效位截断量化(顶部 keep 位) ==", flush=True)
for keep in (26, 25, 24):
    report(f"constseed pwq3  keep-top-{keep} (总计)", ratio(P2_p, 26, keep=keep))
    report(f"constseed table keep-top-{keep} (总计)", ratio(P2_t, 26, keep=keep))

print("== 宽度扫描(table 种子,keep-26 总计) ==", flush=True)
rows = []
for n1 in (14, 15, 16, 17, 18):
    for gr in (22, 23, 24, 25):
        for out in (25, 26, 27):
            P2 = constseed_P2("table", n1_frac=n1, n2_guard=gr, out_frac=out)
            r0 = float(np.max(ratio(P2, out)))
            r26 = float(np.max(ratio(P2, out, keep=26)))
            rows.append((n1, gr, out, r0, r26))
rows.sort(key=lambda t: t[4])
print(f"{'n1':>4} {'grd':>4} {'out':>4} | {'margin':>9} | {'keep26 total':>12}")
for n1, gr, out, r0, r26 in rows:
    mark = "  <-- mrmeows spec" if (n1, gr, out) == (16, 24, 26) else ""
    print(f"{n1:>4} {gr:>4} {out:>4} | {r0:>9.4f} | {r26:>12.4f}{mark}")
print("BEST keep-26 combo:", rows[0][:3], f"total={rows[0][4]:.4f}")
print("CALIBRATION_DONE")
