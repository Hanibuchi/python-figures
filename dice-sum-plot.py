from fractions import Fraction

import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Hiragino Sans", "sans-serif"]

FACES = 6
NORMAL = range(1, FACES + 1)
RED_HI = range(4, FACES + 1)   # 白のペン: 赤を4以上にする
BLUE_LO = range(1, 4)          # 青のペン: 青を3以下にする

# (タイトル, 各ダイスの出目の範囲のリスト, 比較用に重ねる通常分布の個数)
CASES = [
    ("サイコロ 1 個", [NORMAL], None),
    ("サイコロ 2 個", [NORMAL] * 2, None),
    ("サイコロ 3 個", [NORMAL] * 3, None),
    ("赤を 4 以上にした場合（赤 4〜6 + 青 1〜6）", [RED_HI, NORMAL], 2),
    ("青を 3 以下にした場合（赤 1〜6 + 青 1〜3）", [NORMAL, BLUE_LO], 2),
]
COLOR = "#3a6fb0"
INK = "#333333"
MUTED = "#777777"


def sum_distribution(dice):
    """各ダイスの出目の範囲から合計の確率分布 (合計値, 場合の数) を畳み込みで求める"""
    counts = np.array([1])
    for faces in dice:
        die = np.zeros(max(faces) + 1, dtype=int)
        die[list(faces)] = 1
        counts = np.convolve(counts, die)
    sums = np.arange(len(counts))
    nz = counts > 0
    return sums[nz], counts[nz]


fig, axes = plt.subplots(
    len(CASES), 1, figsize=(8, 15), sharey=True,
    gridspec_kw={"hspace": 0.55},
)

for ax, (label, dice, ref_n) in zip(axes, CASES):
    sums, counts = sum_distribution(dice)
    total = int(np.prod([len(f) for f in dice]))
    probs = counts / total

    ax.bar(sums, probs, width=0.8, color=COLOR, zorder=2)

    if ref_n:
        rs, rc = sum_distribution([NORMAL] * ref_n)
        ax.step(rs, rc / FACES ** ref_n, where="mid", color=MUTED, lw=1.2,
                zorder=4, label=f"通常のサイコロ {ref_n} 個")
        ax.legend(loc="upper right", fontsize=9, frameon=False)

    # 最頻値（ピーク）に分数で確率を表示
    peak = probs.max()
    for s, c, p in zip(sums, counts, probs):
        if p == peak:
            frac = Fraction(int(c), total)
            ax.text(s, p + 0.006, f"{frac.numerator}/{frac.denominator}",
                    ha="center", va="bottom", fontsize=9, color=INK)

    mean = float(np.sum(sums * probs))
    sd = float(np.sqrt(np.sum((sums - mean) ** 2 * probs)))
    ax.axvline(mean, ymax=0.8, color=MUTED, ls="--", lw=1, zorder=3)

    ax.set_title(
        f"{label}の合計（全 {total} 通り）   "
        f"平均 {mean:g}・標準偏差 {sd:.2f}",
        loc="left", fontsize=11, color=INK,
    )
    ax.set_xticks(sums)
    ax.set_xlim(0.3, 18.7)
    ax.set_ylim(0, 0.2)
    ax.set_ylabel("確率", color=INK)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

axes[-1].set_xlabel("出目の合計", color=INK)
fig.suptitle("サイコロの合計の分布（ペンで出目を制限すると山がずれるが、7 の確率は 1/6 のまま）",
             fontsize=13, color=INK, y=0.93)

plt.savefig("dice_sum_plot.png", dpi=150, bbox_inches="tight")
plt.show()
