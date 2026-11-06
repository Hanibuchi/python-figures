import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

plt.rcParams["font.family"] = "Hiragino Sans"

N_FRAMES = 6
PKT_PER_FRAME = 8
N = N_FRAMES * PKT_PER_FRAME
P = 0.1  # average loss rate (same for all models)
BURST_LEN = 4

GAP = 0.6  # horizontal gap between frames
C_OK = "#4C78A8"
C_LOST = "#E45756"
C_GOOD = "#54A24B"
C_BAD = "#F58518"


def bernoulli(rng):
    return rng.random(N) < P


def gilbert_elliott(rng):
    r = 1 / BURST_LEN
    g = P * r / (1 - P)
    bad = np.zeros(N, dtype=bool)
    state = rng.random() < P  # start from the stationary distribution
    for i in range(N):
        bad[i] = state
        state = (rng.random() >= r) if state else (rng.random() < g)
    return bad  # Bad = lost, Good = received


def frame(rng):
    return np.repeat(rng.random(N_FRAMES) < P, PKT_PER_FRAME)


def pick_seed(model, ok):
    # deterministic search for a realization that illustrates the model well
    for seed in range(10000):
        lost = model(np.random.default_rng(seed))
        if ok(lost):
            return lost
    raise RuntimeError("no illustrative seed found")


def runs(lost):
    # (start, length) of each run of consecutive losses
    out, i = [], 0
    while i < N:
        if lost[i]:
            j = i
            while j < N and lost[j]:
                j += 1
            out.append((i, j - i))
            i = j
        else:
            i += 1
    return out


lost_b = pick_seed(
    bernoulli,
    lambda l: l.sum() == 5 and all(n == 1 for _, n in runs(l)),
)
lost_ge = pick_seed(
    gilbert_elliott,
    lambda l: (
        len(runs(l)) == 1
        and runs(l)[0][1] == 5
        # the burst crosses a frame boundary
        and runs(l)[0][0] // PKT_PER_FRAME
        != (runs(l)[0][0] + 4) // PKT_PER_FRAME
    ),
)
lost_f = pick_seed(
    frame,
    lambda l: l.reshape(N_FRAMES, -1)[:, 0].tolist()
    == [False, False, True, False, False, False],
)


def px(i):
    return i + GAP * (i // PKT_PER_FRAME)


def draw_packets(ax, lost, y=0.0):
    for i in range(N):
        x = px(i)
        if lost[i]:
            ax.add_patch(Rectangle((x + 0.08, y + 0.08), 0.84, 0.84,
                                   fc="white", ec=C_LOST, lw=1.2))
            ax.plot([x + 0.22, x + 0.78], [y + 0.22, y + 0.78], color=C_LOST, lw=2)
            ax.plot([x + 0.22, x + 0.78], [y + 0.78, y + 0.22], color=C_LOST, lw=2)
        else:
            ax.add_patch(Rectangle((x + 0.08, y + 0.08), 0.84, 0.84,
                                   fc=C_OK, ec="none"))


def draw_frame_labels(ax, y):
    for f in range(N_FRAMES):
        xc = px(f * PKT_PER_FRAME) + PKT_PER_FRAME / 2
        ax.text(xc, y, f"フレーム{f + 1}", ha="center", va="center",
                fontsize=9, color="0.4")


def draw_frame_separators(ax, y0, y1):
    for f in range(1, N_FRAMES):
        x = px(f * PKT_PER_FRAME) - GAP / 2
        ax.plot([x, x], [y0, y1], color="0.75", lw=1, ls=":")


def setup(ax, ymin, ymax):
    x_end = px(N - 1) + 1
    ax.set_xlim(-6.5, x_end + 0.5)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.axis("off")


def row_label(ax, y, text):
    ax.text(-0.6, y + 0.5, text, ha="right", va="center", fontsize=10)


def title(ax, y, text, sub):
    ax.text(-6.5, y + 1.7, text, fontsize=14, fontweight="bold", va="bottom")
    ax.text(-6.5, y + 0.3, sub, fontsize=10, color="0.3", va="bottom")


fig = plt.figure(figsize=(11.5, 7.6))
gs = fig.add_gridspec(3, 1, height_ratios=[7.4, 9.8, 9.3], hspace=0.08)

# ---- 1. bernoulli ---------------------------------------------------------
ax = fig.add_subplot(gs[0])
setup(ax, -1.0, 6.4)
draw_frame_labels(ax, 3.0)
draw_frame_separators(ax, -0.2, 2.6)
draw_packets(ax, np.zeros(N, bool), y=1.4)
draw_packets(ax, lost_b, y=0.0)
row_label(ax, 1.4, "送信")
row_label(ax, 0.0, "結果")
for i in np.flatnonzero(lost_b):
    ax.text(px(i) + 0.5, -0.45, "p", ha="center", va="center",
            fontsize=9, color=C_LOST, style="italic")
title(ax, 3.4, "1. bernoulli：ランダムにぽつぽつ落ちる",
      f"各パケットが前後と無関係に、独立に確率 p で落ちる（図は p = {P}）")

# ---- 2. gilbert_elliott --------------------------------------------------
ax = fig.add_subplot(gs[1])
setup(ax, -1.9, 7.9)
draw_frame_labels(ax, 4.5)
draw_frame_separators(ax, -0.2, 4.1)
# state band
for i in range(N):
    c = C_BAD if lost_ge[i] else C_GOOD
    ax.add_patch(Rectangle((px(i), 2.9), 1.0 + (GAP if (i + 1) % PKT_PER_FRAME == 0
                                                 and i < N - 1 else 0),
                           0.7, fc=c, ec="none", alpha=0.85))
row_label(ax, 2.9, "回線の状態")
draw_packets(ax, np.zeros(N, bool), y=1.4)
draw_packets(ax, lost_ge, y=0.0)
row_label(ax, 1.4, "送信")
row_label(ax, 0.0, "結果")
(start, length), = runs(lost_ge)
x0, x1 = px(start), px(start + length - 1) + 1
ax.annotate("", xy=(x0, -0.5), xytext=(x1, -0.5),
            arrowprops=dict(arrowstyle="<->", color=C_LOST, lw=1.3))
ax.text((x0 + x1) / 2, -1.35,
        f"{length} パケット連続でロス（フレーム境界をまたいで継続）",
        ha="center", va="center", fontsize=9, color=C_LOST)
ax.text(px(1) + 0.5, 3.25, "Good", ha="center", va="center", fontsize=8,
        color="white", fontweight="bold")
ax.text((px(start) + px(start + length - 1) + 1) / 2, 3.25, "Bad",
        ha="center", va="center", fontsize=8, color="white", fontweight="bold")
title(ax, 4.9, "2. gilbert_elliott：まとまって連続で落ちる（バーストロス）",
      f"Good では1つも落ちず、Bad ではすべて落ちる（図は p = {P}, burst_len = {BURST_LEN}）")

# ---- 3. frame ------------------------------------------------------------
ax = fig.add_subplot(gs[2])
setup(ax, -2.9, 6.4)
draw_frame_labels(ax, 3.0)
draw_frame_separators(ax, -0.2, 2.6)
draw_packets(ax, np.zeros(N, bool), y=1.4)
draw_packets(ax, lost_f, y=0.0)
row_label(ax, 1.4, "送信")
row_label(ax, 0.0, "結果")
f_lost = int(np.flatnonzero(lost_f)[0]) // PKT_PER_FRAME
xs = px(f_lost * PKT_PER_FRAME)
ax.add_patch(Rectangle((xs - 0.15, -0.15), PKT_PER_FRAME + 0.3, 1.3,
                       fc="none", ec=C_LOST, lw=1.5, ls="--"))
xp = px((f_lost - 1) * PKT_PER_FRAME) + PKT_PER_FRAME / 2
ax.add_patch(FancyArrowPatch((xp, -0.2), (xs + PKT_PER_FRAME / 2 - 1, -0.3),
                             connectionstyle="arc3,rad=0.3", arrowstyle="-|>",
                             mutation_scale=14, lw=1.4, color="0.3"))
ax.text((xp + xs + PKT_PER_FRAME / 2) / 2, -2.45,
        f"全滅 → フレーム{f_lost}の特徴量をそのまま使う",
        ha="center", va="center", fontsize=9, color="0.25")
title(ax, 3.4, "3. frame：フレームがまるごと消える",
      f"フレームごとに確率 p で、そのフレームのパケットをすべて落とす（図は p = {P}）")

# shared legend
handles = [
    Rectangle((0, 0), 1, 1, fc=C_OK, ec="none", label="届いたパケット"),
    Rectangle((0, 0), 1, 1, fc="white", ec=C_LOST, label="落ちたパケット（×）"),
    Rectangle((0, 0), 1, 1, fc=C_GOOD, ec="none", label="Good 状態"),
    Rectangle((0, 0), 1, 1, fc=C_BAD, ec="none", label="Bad 状態"),
]
fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False,
           fontsize=10, bbox_to_anchor=(0.5, 0.1))

plt.savefig("packet_loss_plot.png", dpi=150, bbox_inches="tight")
plt.show()
