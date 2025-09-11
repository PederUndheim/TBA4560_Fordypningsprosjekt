import numpy as np

def weighted_sum(layers: dict[str, np.ndarray], weights: dict[str, float]) -> np.ndarray:
    first = next(iter(layers.values()))
    total = np.zeros_like(first, dtype=np.float32)
    for name, arr in layers.items():
        w = float(weights.get(name, 1.0))
        total += arr.astype(np.float32, copy=False) * w
    return total

def sum_layers(*arrays: np.ndarray) -> np.ndarray:
    total = np.zeros_like(arrays[0], dtype=np.float32)
    for a in arrays:
        total += a.astype(np.float32, copy=False)
    return total

def max_combine(*arrays: np.ndarray) -> np.ndarray:
    out = arrays[0].astype(np.float32, copy=False)
    for a in arrays[1:]:
        out = np.maximum(out, a.astype(np.float32, copy=False))
    return out

def min_combine(*arrays: np.ndarray) -> np.ndarray:
    out = arrays[0].astype(np.float32, copy=False)
    for a in arrays[1:]:
        out = np.minimum(out, a.astype(np.float32, copy=False))
    return out

def clip_round(cost: np.ndarray, min_cost=1.0, max_cost=99.0) -> np.ndarray:
    out = np.clip(cost, min_cost, max_cost)
    return np.round(out).astype(np.uint8, copy=False)