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
    y = np.clip(y, 0.0, 1.0)          
    return y.astype(np.float32)

def logistic(x: np.ndarray, *, x0: float, k: float) -> np.ndarray:
    """
    Logistic membership function.
    Maps input x to [0,1] using parameters:
        x0 -> midpoint (value of x where output = 0.5)
        k  -> slope/steepness (larger = sharper transition)
    """
    x = _as_float(x)
    y = 1.0 / (1.0 + np.exp(-k * (x - x0)))
    y = np.clip(y, 0.0, 1.0)           
    return y.astype(np.float32)

def to_cost_x_y(unit_0_to_1: np.ndarray, min_cost=1.0, max_cost=99.0) -> np.ndarray:
    """
    Map a [0,1] unit value to [min_cost, max_cost].
    """
    out = min_cost + unit_0_to_1 * (max_cost - min_cost)
    return out.astype(np.float32, copy=False)


# --- Terrain transforms ---
def slope_cost_logistic(slope: np.ndarray, *, x0: float, k: float, min_cost=1.0, max_cost=99.0) -> np.ndarray:
    u = logistic(slope, x0=x0, k=k)
    return to_cost_x_y(u, min_cost=min_cost, max_cost=max_cost)

def curvature_cost_logistic(curvature: np.ndarray, *, x0: float, k: float, min_cost=3.0, max_cost=97.0) -> np.ndarray:
    u = logistic(curvature, x0=x0, k=k)
    return to_cost_x_y(u, min_cost=min_cost, max_cost=max_cost)



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

def reduction_layer_from_mask(mask: np.ndarray, validity_mask: np.ndarray = None, low_value: float = 2.0, elsewhere_value: float = 99.0) -> np.ndarray:
    """
    Build a 'reduction' layer that is low_value on mask (roads/tracks) if in validity mask (ex. not in avalanche danger), high elsewhere.
    Intended for MIN combine so tracks lower the cost.
    """
    mask = mask.astype(bool)
    if validity_mask is None:
        valid_mask = mask
    else:
        valid_mask = mask & validity_mask.astype(bool)

    out = np.full(mask.shape, elsewhere_value, dtype=np.float32)
    out[valid_mask] = low_value
    return out