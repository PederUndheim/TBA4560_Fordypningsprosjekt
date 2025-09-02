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

def compute_surface_cost(
    *,
    slope: np.ndarray,
    curvature: np.ndarray,
    travel_angle: np.ndarray,
    roads_reduction: np.ndarray | None = None,
    tractorroads_trails_reduction: np.ndarray | None = None,
    rivers_barrier: np.ndarray | None = None,
    weights: dict[str, float],
    min_cost: float = 1.0,
    max_cost: float = 99.0,
) -> np.ndarray:
    """
    Pipeline:
      SurfaceSumCost = weighted_sum({slope, curvature, alpha})
      SurfaceRawCost = MIN( MAX(SurfaceSumCost, rivers_barrier), roads_reduction )
    """
    layers = {"slope": slope, "curvature": curvature, "travel_angle": travel_angle}
    surface_sum = weighted_sum(layers, weights)

    # MAX: barriers trump
    with_barriers = surface_sum
    if rivers_barrier is not None:
        with_barriers = max_combine(with_barriers, rivers_barrier)

    # MIN: reductions lower cost on roads/tracks
    reduction_layers = [arr for arr in [roads_reduction, tractorroads_trails_reduction] if arr is not None]
    with_reductions = with_barriers

    if reduction_layers:
        with_reductions = min_combine(with_barriers, *reduction_layers)
        
    return np.clip(with_reductions, min_cost, max_cost)