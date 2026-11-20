import pandas as pd

def calculate_swing_points(
    high: pd.Series,
    low: pd.Series,
    left_bars: int = 5,
    right_bars: int = 5,
) -> pd.DataFrame:
    
    window = left_bars + right_bars + 1
    
    rolling_high = high.rolling(
        window=window,
        center=True,
    ).max()
    
    rolling_low = low.rolling(
        window=window,
        center=True,
    ).min()
    
    #identify potential swing points
    is_swing_high = high.eq(rolling_high)
    is_swing_low = low.eq(rolling_low)
    
    #swift confirmation to avoid look-ahead bias
    swing_high = high.where(is_swing_high).shift(right_bars)
    swing_low = low.where(is_swing_low).shift(right_bars)
    
    return pd.DataFrame({
        "swing_high": swing_high,
        "swing_low": swing_low,
    })
    

def cluster_price_levels(
    levels: pd.Series,
    tolerance_pct: float = 0.01,
    min_touches: int = 2,
) -> list[dict]:

    prices = sorted(levels.dropna().astype(float).tolist())

    if not prices:
        return []

    clusters = []
    current_cluster = [prices[0]]

    for price in prices[1:]:

        cluster_average = sum(current_cluster) / len(current_cluster)

        difference_pct = abs(
            price - cluster_average
        ) / cluster_average

        if difference_pct <= tolerance_pct:
            current_cluster.append(price)
        else:
            clusters.append(current_cluster)
            current_cluster = [price]

    clusters.append(current_cluster)

    results = []

    for cluster in clusters:

        if len(cluster) < min_touches:
            continue

        results.append({
            "level": round(sum(cluster) / len(cluster), 2),
            "touches": len(cluster),
            "zone_low": round(min(cluster), 2),
            "zone_high": round(max(cluster), 2),
        })

    return results
    
    prices = sorted(levels.dropna().astype(float).tolist())
    
    if not prices:
        return []
    
    clusters = []
    
    current_cluster = [prices[0]]
    
    for price in prices[1:]:
        
        cluster_average = sum(current_cluster) / len(current_cluster)
        
        difference_pct = abs(
            price - cluster_average
        ) / cluster_average
        
        if difference_pct <= tolerence_pct:
            current_cluster.append(price)
            
        else:
            clusters.append(current_cluster)
            current_cluster = [price]
            
    clusters.append(current_cluster)
    
    result = []
    
    for cluster in clusters:
        
        if len(cluster) < min_touches:
            continue
        
        results.append({
            "level": round(sum(cluster) / len(cluster), 2),
            "touches": len(cluster),
            "zone_low": round(min(cluster), 2),
            "zone_high": round(max(cluster), 2),
        })
        
    return results

def calculate_level_strength(
    levels: list[dict],
) -> list[dict]:
    
    if not levels:
        return []
    
    max_touches = max(
        level["touches"] for level in levels
    )
    
    results = []
    
    for level in levels:
        strength = (
            level["touches"] / max_touches
        ) * 100
        
        results.append({
            **level,
            "strength": round(strength, 2),
        })
        
    return results