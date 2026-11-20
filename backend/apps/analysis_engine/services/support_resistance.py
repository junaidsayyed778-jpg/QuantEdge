import pandas as pd

#identify historical price peaks and bottoms
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
    
#Group nearby swing prices into zones
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

#Measure current trading volume against its recent average
def calculate_relative_volume(
    volume: pd.Series,
    period: int = 20,
) -> pd.Series:
    
    average_volume = volume.rolling(
        window=period,
        min_periods=period,
    ).mean()
    
    relative_volume = volume / average_volume
    
    return relative_volume.rename("relative_volume")

#Measure the historical volume activity associated with each price zone
def calculate_volume_confirmation(
    relative_volume: float,
) -> dict:
    
    if pd.isna(relative_volume):
        return {
            "volume_category": "insufficient_data",
            "volume_score": 0,
        }
        
    if relative_volume >= 2.0:
        category = "very_high"
        score = 100

    elif relative_volume >= 1.5:
        category = "high"
        score = 75

    elif relative_volume >= 1.0:
        category = "normal"
        score = 50

    else:
        category = "below_average"
        score = 25
        
    return {
        "volume_category": category,
        "volume_score": score,
    }
        
def calculate_zone_volume_confirmation(
    levels: list[dict],
    swing_prices: pd.Series,
    swing_relative_volume: pd.Series,
) -> list[dict]:
    
    observations = pd.DataFrame({
        "price": swing_prices,
        "relative_volume": swing_relative_volume,
    }).dropna()
    
    results = []
    
    for level in levels:
        
        zone_observations = observations[
            (observations["price"] >= level["zone_low"])
            & (observations["price"] <= level["zone_high"])
        ]
        
        if zone_observations.empty:
            results.append({
                **level,
                "average_relative_volume": None,
                "high_volume_touches": 0,
                "volume_confirmation": "insufficient_data",
            })
            continue
        
        average_rvol = zone_observations["relative_volume"].mean()
        
        confirmation = calculate_volume_confirmation(
            average_rvol
        )
        
        results.append({
            **level,
            "average_relative_volume": float(round(average_rvol, 2)),
            "high_volume_touches": int(
                (zone_observations["relative_volume"] >= 1.5).sum()
            ),
            "volume_confirmation": confirmation["volume_category"],
            "volume_score": confirmation["volume_score"],
        })
        
        
    return results

def calculate_reaction_score(reaction_pct: float) -> int:
    
    if pd.isna(reaction_pct):
        return 0
    
    if reaction_pct < 1:
        return 20
    elif reaction_pct < 2:
        return 40
    elif reaction_pct < 3:
        return 60
    elif reaction_pct < 5:
        return 80
    else: 
        return 100
    
#Measure how much price moved after touching a support or resistence zone
def calculate_zone_reactions(
    levels: list[dict],
    prices: pd.DataFrame,
    swing_points: pd.Series,
    right_bars: int = 5,
    reaction_window: int = 5,
    zone_type: str = "support",
) -> list[dict]:
    
    results = []
    
    for level in levels:
        
        observations = prices[
            swing_points.notna()
            & (swing_points >= level["zone_low"])
            & (swing_points <= level["zone_high"])
        ]
        
        reactions = []
        
        for index in observations.index:
            
            future_prices = prices.loc[index + 1:index + reaction_window]
            
            if len(future_prices) < reaction_window:
                continue
            
            if zone_type == "support":
                
                touch_price = swing_points.loc[index]
                reaction_pct = (
                    (future_prices["high"].max() - touch_price)
                    / touch_price
                ) * 100
                
            elif zone_type == "resistance":
                
                touch_price = swing_points.loc[index]
                reaction_pct = (
                    (touch_price - future_prices["low"].min())
                    / touch_price
                ) * 100
                
            else:
                raise ValueError(
                    "zone_type must be 'support' or 'resistance'"
                )
                
            reactions.append(max(0.0, float(reaction_pct)))
            
        if reactions:
            
            average_reaction = sum(reactions) / len(reactions)
            
            reaction_score = calculate_reaction_score(
                average_reaction
            )
            
        else:
            
            average_reaction = None
            reaction_score = 0
            
        results.append({
            **level,
            "average_reaction_pct": (
                round(average_reaction, 2)
                if average_reaction is not None
                else None
            ),
            "reaction_score": reaction_score,
            "reaction_observations": len(reactions),
        })
        
    return results
        
#Combine all three measurements into one overall score    
def calculate_zone_strength(
    reaction_levels: list[dict],
    volume_levels: list[dict],
    touch_weight: float = 0.40,
    volume_weight: float = 0.30,
    reaction_weight: float = 0.30,
) -> list[dict]:

    total_weight = touch_weight + volume_weight + reaction_weight

    if abs(total_weight - 1.0) >= 1e-9:
        raise ValueError("Weights must add up to 1.0")

    if not reaction_levels:
        return []

    max_touches = max(
        level["touches"] for level in reaction_levels
    )

    volume_lookup = {
        (level["zone_low"], level["zone_high"]): level
        for level in volume_levels
    }

    results = []

    for level in reaction_levels:
        zone_key = (
            level["zone_low"],
            level["zone_high"],
        )

        volume_data = volume_lookup.get(zone_key, {})

        touch_score = (
            level["touches"] / max_touches
        ) * 100

        volume_score = volume_data.get("volume_score", 0)
        reaction_score = level.get("reaction_score", 0)

        overall_strength = (
            touch_score * touch_weight
            + volume_score * volume_weight
            + reaction_score * reaction_weight
        )

        if overall_strength >= 75:
            category = "strong"
        elif overall_strength >= 50:
            category = "moderate"
        else:
            category = "weak"

        results.append({
            **level,
            "touch_score": round(touch_score),
            "volume_score": volume_score,
            "overall_strength": round(overall_strength, 2),
            "strength_category": category,
        })

    return results
