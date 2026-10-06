import numpy as np
import matplotlib.pyplot as plt

q = 1.0  # step size


def symmetric(x):
    # zero bin: |x| < 0.5q
    return q * np.round(x / q)


def dead_zone(x):
    # zero bin: |x| < 0.75q (width 1.5q), other bins width q
    return q * np.sign(x) * np.floor(np.abs(x) / q + 0.25)


x = np.linspace(-3, 3, 3001)

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(x, x, ":", color="gray", label="y = x (no quantization)")
ax.plot(x, symmetric(x), lw=2.5, label="Symmetric")
ax.plot(x, dead_zone(x), "--", lw=2, label="Dead-zone")

ax.set_xlabel("input x (in units of q)")
ax.set_ylabel("output y = Q(x)")
ax.set_aspect("equal")
ax.grid(alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig("quantizer_plot.png", dpi=150)
plt.show()
