#!/usr/bin/env python
"""Peephole cancellation + emit for kickmix circuits (v17 candidate builder).

For each target: multi-pass deletion of identical CCX/CCZ pairs (sorted-controls
key, fixed target) whose interleaved window touches no pair wire except Z-type
ops (CZ/Z/S/T) on controls. Emits optimized .kmb when EMIT_DIR is set.
Non-cascading upper bound is printed first (strict/zwindow).
"""
import sys
import os
import re
import collections
import numpy as np
import kickmix as km

KINDS = ['CX', 'CY', 'CZ', 'X', 'Y', 'Z', 'S', 'T', 'H', 'R', 'HMR', 'NEG',
         'CCX', 'CCZ', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1', 'SWAP', 'CSWAP']
KIND_CODE = {}
for idx, name in enumerate(KINDS):
    KIND_CODE[name] = idx
KZ = frozenset([KIND_CODE['CZ'], KIND_CODE['Z'], KIND_CODE['S'], KIND_CODE['T']])
KCCX = KIND_CODE['CCX']
KCCZ = KIND_CODE['CCZ']
KSWAP = KIND_CODE['SWAP']
KCSWAP = KIND_CODE['CSWAP']
TSWAP = frozenset([KCCX, KCCZ, KSWAP, KCSWAP])

WIRE_RE = re.compile('^([qb])([0-9]+)$')
INT_RE = re.compile('^-?[0-9]+$')
MAX_PASSES = int(os.environ.get('MAX_PASSES', '12'))


def parse_wire(tok):
    m = WIRE_RE.match(tok)
    if m:
        if m.group(1) == 'q':
            return int(m.group(2))
        return (1 << 29) | int(m.group(2))
    if INT_RE.match(tok):
        return int(tok)
    return -1


def load_ops(path):
    circ = km.Circuit.from_file(path, format='kmb')
    nq = circ.num_qubits
    nb = circ.num_bits
    stat = circ.operation_statistics()
    text = str(circ)
    del circ
    codes = []
    a1 = []
    a2 = []
    a3 = []
    header_lines = []
    unknown = collections.Counter()
    idx = 0
    for line in text.splitlines():
        if line.startswith('APPEND_TO_REGISTER') or line.startswith('REGISTER'):
            header_lines.append(line)
            continue
        n = idx
        idx += 1
        p = line.split()
        kind = p[0]
        hist_code = KIND_CODE.get(kind, 63)
        if hist_code == 63:
            unknown[kind] += 1
        codes.append(hist_code)
        n1 = parse_wire(p[1]) if len(p) > 1 else -1
        n2 = parse_wire(p[2]) if len(p) > 2 else -1
        n3 = parse_wire(p[3]) if len(p) > 3 else -1
        a1.append(n1)
        a2.append(n2)
        a3.append(n3)
    codes = np.array(codes, dtype=np.int8)
    a1 = np.array(a1, dtype=np.int64)
    a2 = np.array(a2, dtype=np.int64)
    a3 = np.array(a3, dtype=np.int64)
    return text, header_lines, codes, a1, a2, a3, unknown, stat, nq, nb


def canon(code, ws):
    if code == KCCZ:
        w = list(ws)
        w.sort()
        return ('CCZ', w[0], w[1], w[2])
    if code == KSWAP:
        w = sorted(ws[0:2])
        return ('SWAP', w[0], w[1], -7)
    if code == KCSWAP:
        return ('CSWAP', ws[0], min(ws[1], ws[2]), max(ws[1], ws[2]))
    return ('CCX', min(ws[0], ws[1]), max(ws[0], ws[1]), ws[2])


def scan_passes(codes, a1, a2, a3, max_passes):
    n = len(codes)
    alive = np.ones(n, dtype=bool)
    strict0 = 0
    z0 = 0
    total_deleted = 0
    for p in range(max_passes):
        touch = {}
        nzl = {}
        zl = {}
        lastt = {}
        cancels = []
        for i in range(n):
            if not alive[i]:
                continue
            code = int(codes[i])
            w1 = int(a1[i])
            w2 = int(a2[i])
            w3 = int(a3[i])
            if code in TSWAP:
                if code == KSWAP:
                    ws = (w1, w2)
                else:
                    ws = (w1, w2, w3)
                key = canon(code, (w1, w2, w3))
                j = lastt.get(key)
                if j is not None:
                    tw = [touch.get(w, -1) for w in ws]
                    if max(tw) == j:
                        if p == 0:
                            strict0 += 1
                        cancels.append((j, i))
                        lastt.pop(key, None)
                        continue
                    if code == KCCX or code == KCCZ:
                        zw = [nzl.get(w, -1) for w in (w1, w2, w3)]
                        zt = zl.get(w3, -1)
                        if max(zw + [zt]) == j:
                            if p == 0:
                                z0 += 1
                            cancels.append((j, i))
                            lastt.pop(key, None)
                            continue
                lastt[key] = i
                for w in ws:
                    touch[w] = i
                    nzl[w] = i
                    zl[w] = i
            elif code in KZ:
                for w in (w1, w2):
                    if w >= 0:
                        touch[w] = i
                        zl[w] = i
            else:
                for w in (w1, w2, w3):
                    if w >= 0:
                        touch[w] = i
                        nzl[w] = i
        if not cancels:
            break
        for j, i in cancels:
            alive[j] = False
            alive[i] = False
        total_deleted += 2 * len(cancels)
        print('  pass%d: deleted %d (cum %d)' % (p, 2 * len(cancels), total_deleted), flush=True)
    return alive, total_deleted, strict0, z0


def emit(text, header_lines, alive, out_path):
    keep_pos = 0
    alive_list = alive.tolist()
    idx = -1
    out_lines = []
    for line in text.splitlines():
        if line.startswith('APPEND_TO_REGISTER') or line.startswith('REGISTER'):
            out_lines.append(line)
            continue
        idx += 1
        if alive_list[idx]:
            out_lines.append(line)
    full = chr(10).join(out_lines) + chr(10)
    circ = km.Circuit(full)
    circ.to_file(out_path, format='kmb')
    return len(circ)


def process(path, emit_dir):
    print('=== %s ===' % path, flush=True)
    text, header_lines, codes, a1, a2, a3, unknown, stat, nq, nb = load_ops(path)
    n = len(codes)
    ntl = int((codes == KCCX).sum() + (codes == KCCZ).sum())
    print('ops=%d q=%d b=%d static_toffoli=%d tlike=%d unknown=%s'
          % (n, nq, nb, stat.num_toffoli_like, ntl, dict(unknown)), flush=True)
    alive, deleted, strict0, z0 = scan_passes(codes, a1, a2, a3, MAX_PASSES)
    print('RESULT %s: strict0=%d zwin0=%d deleted=%d of tlike=%d (%.3f%%)'
          % (os.path.basename(path), strict0, z0, deleted, ntl,
             100.0 * deleted / max(ntl, 1)), flush=True)
    out = None
    if emit_dir and deleted > 0:
        if not os.path.isdir(emit_dir):
            os.makedirs(emit_dir)
        out = os.path.join(emit_dir, os.path.basename(path))
        newlen = emit(text, header_lines, alive, out)
        c2 = km.Circuit.from_file(out, format='kmb')
        t2 = c2.operation_statistics().num_toffoli_like
        print('EMITTED %s: len=%d (was %d) static_toffoli=%d (was %d)'
              % (out, len(c2), n, t2, stat.num_toffoli_like), flush=True)
    return deleted, out


def main():
    emit_dir = os.environ.get('EMIT_DIR', '')
    targets = sys.argv[1:]
    results = []
    for t in targets:
        deleted, out = process(t, emit_dir)
        results.append((t, deleted, out))
    print('SUMMARY_JSON %s' % repr(results), flush=True)


main()
