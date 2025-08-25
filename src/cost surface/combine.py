import numpy as np

def weighetd_sum(cost_layers: dict, weights: dict) -> np.ndarray:
    total = np.zeros_like(next(iter(cost_layers.values())))
    for name, layer in cost_layers.items():
        w = weights.get(name, 1.0)
        total += layer * w
    return total

def apply_barriers(cost_surface, barrier_mask, value=99):
    cost_surface[barrier_mask] = value
    return cost_surface

def apply_reductions(cost_surface, track_mask, min_value=2):
    cost_surface[track_mask] = np.minimum(cost_surface[track_mask], min_value)
    return cost_surface