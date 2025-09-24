from __future__ import annotations
import os
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from .geometry import densify, sample_points

def plot_pair(out_png: str, auto_line: LineString, expert_line: LineString, sample_m: float):
    la_d = densify(auto_line, sample_m)
    samples = sample_points(la_d, sample_m)
    dists = np.array([expert_line.distance(p) for p in samples])

    ax = plt.figure(figsize=(8, 6)).gca()
    ax.plot(*expert_line.xy, label="Expert", linewidth=2)
    ax.plot(*la_d.xy, label="Auto", linestyle="--")
    sc = ax.scatter([p.x for p in samples], [p.y for p in samples], c=dists, s=9)
    plt.colorbar(sc, ax=ax, label="Deviation to expert (m)")
    ax.set_title("Auto vs Expert (colored by deviation)")
    ax.set_aspect("equal")
    ax.legend()
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()
