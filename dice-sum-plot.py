from fractions import Fraction

import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Hiragino Sans", "sans-serif"]

FACES = 6
N_DICE = [1, 2, 3]
COLOR = "#3a6fb0"
INK = "#333333"
MUTED = "#777777"


def sum_distribution(n):
    """n 個のサイコロの出目の合計の確率分布 (合計値, 場合の数) を畳み込みで求める"""
    counts = np.array([1])
    for _ in range(n):
        counts = np.convolve(counts, np.ones(FACES, dtype=int))
    sums = np.arange(n, n * FACES + 1)
    return sums, counts


fig, axes = plt.subplots(
    len(N_DICE), 1, figsize=(8, 9), sharey=True,
    gridspec_kw={"hspace": 0.55},
)

for ax, n in zip(axes, N_DICE):
    sums, counts = sum_distribution(n)
    total = FACES ** n
    probs = counts / total

    ax.bar(sums, probs, width=0.8, color=COLOR, zorder=2)

    # 最頻値（ピーク）に分数で確率を表示
    peak = probs.max()
    for s, c, p in zip(sums, counts, probs):
        if p == peak:
            frac = Fraction(int(c), total)
            ax.text(s, p + 0.006, f"{frac.numerator}/{frac.denominator}",
                    ha="center", va="bottom", fontsize=9, color=INK)

    mean = n * 3.5
    sd = np.sqrt(n * 35 / 12)
    ax.axvline(mean, ymax=0.8, color=MUTED, ls="--", lw=1, zorder=3)

    ax.set_title(
        f"サイコロ {n} 個の出目の合計（全 {total} 通り）   "
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
fig.suptitle("サイコロの数を増やすと、合計の分布は中央に山ができる形に近づく",
             fontsize=13, color=INK, y=0.97)

plt.savefig("dice_sum_plot.png", dpi=150, bbox_inches="tight")
plt.show()
