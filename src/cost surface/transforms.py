import numpy as np

def slope_cost(data: np.ndarray) -> np.ndarray:
    cost = np.full_like(data, 0.5, dtype=np.float32)
    cost[(data >= 10) & (data < 25)] = 1.0
    cost[(data >= 25) & (data < 30)] = 2.0
    cost[(data >= 30) & (data < 35)] = 5.0
    cost[(data >= 35) & (data < 40)] = 8.0
    cost[(data >= 40) & (data < 45)] = 12.0
    cost[(data >= 45) & (data < 55)] = 20.0
    cost[(data >= 55)] = 50.0
    return cost

def forest_cost(data: np.ndarray) -> np.ndarray:
    cost = np.zeros_like(data, dtype=np.float32)
    cost[(data >= 0) & (data <= 10)] = 0.5
    cost[(data > 10) & (data <= 50)] = 2.0
    cost[(data > 50) & (data <= 100)] = 5.0
    cost[(data > 100) & (data <= 200)] = 10.0
    cost[(data > 200) & (data <= 500)] = 20.0
    cost[(data > 500) & (data <= 1000)] = 35.0
    cost[data > 1000] = 50.0
    cost[data == -9999] = np.nan
    return cost


""" def curvature_cost(data: np.ndarray) -> np.ndarray:
    curv_norm = np.clip(data / np.nanmax(np.abs(data)), -1, 1)
    return np.where(curv_norm < 0, 1 + 2 * np.abs(curv_norm), 1 + 0.5 * curv_norm) """



