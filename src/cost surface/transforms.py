import numpy as np

EPS = 1e-9

# --- Mathematical transforms ---

def _as_float(a: np.ndarray) -> np.ndarray:
    return a.astype(np.float32, copy=False)

# --- Generalized Cauchy membership function ---
def generalized_cauchy(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Generalized Cauchy membership function.
    Maps input x to [0,1] using parameters:
        a -> width/scale
        b -> shape exponent
        c -> center
    """
    x = _as_float(x)
    y = 1.0 / (1.0 + ((x - c) / (a + EPS)) ** (2 * b))
    y = np.clip(y, 0.0, 1.0)             # clamp to [0,1]
    return y.astype(np.float32)

def to_cost_1_99(unit_0_to_1: np.ndarray, min_cost=1.0, max_cost=99.0) -> np.ndarray:
    """
    Map a [0,1] unit value to [min_cost, max_cost].
    """
    out = min_cost + unit_0_to_1 * (max_cost - min_cost)
    return out.astype(np.float32, copy=False)



# --- Terrain transforms ---
def slope_cost(slope: np.ndarray, *, a: float, b: float, c: float,
               min_cost=1.0, max_cost=99.0) -> np.ndarray:
    u = generalized_cauchy(slope, a=a, b=b, c=c)
    return to_cost_1_99(u, min_cost=min_cost, max_cost=max_cost)

def curvature_cost(curvature: np.ndarray, *, a: float, b: float, c: float,
                   min_cost=1.0, max_cost=99.0) -> np.ndarray:
    u = generalized_cauchy(np.abs(curvature), a=a, b=b, c=c)
    return to_cost_1_99(u, min_cost=min_cost, max_cost=max_cost)

def travel_angle_cost(alpha_deg: np.ndarray, *, a: float, b: float, c: float,
                      min_cost=1.0, max_cost=99.0) -> np.ndarray:
    u = generalized_cauchy(alpha_deg, a=a, b=b, c=c)
    return to_cost_1_99(u, min_cost=min_cost, max_cost=max_cost)



# --- Layer builder for MIN/MAX-logic ---

def barrier_layer_from_mask(mask: np.ndarray, barrier_value: float = 99.0, min_cost=1.0) -> np.ndarray:
    """
    Build a 'barrier' layer that is 1 everywhere, barrier_value where mask is True.
    Intended for MAX combine so barriers trump.
    """
    mask = _as_float(mask)
    layer = np.full_like(mask, min_cost, dtype=np.float32)
    layer[mask.astype(bool)] = barrier_value
    return layer

def reduction_layer_from_mask(mask: np.ndarray, dem: np.ndarray, low_value: float = 2.0, elsewhere_value: float = 99.0, elev_threshold: float = 800.0, penalty_factor: float = 7.0) -> np.ndarray:
    """
    Build a 'reduction' layer that is low_value on mask (roads/tracks), high elsewhere.
    Intended for MIN combine so tracks lower the cost.
    """
    mask = mask.astype(bool)
    out = np.full(mask.shape, elsewhere_value, dtype=np.float32)

    # Compute elevation multiplier for masked cells
    multiplier = np.ones_like(dem, dtype=np.float32)
    multiplier[dem >= elev_threshold] = penalty_factor  # increase cost at high elevation

    # Apply to low-value locations only
    out[mask] = low_value * multiplier[mask]
    return out
