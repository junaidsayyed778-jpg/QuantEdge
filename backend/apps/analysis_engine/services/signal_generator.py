#evalutes whether a stock's current trend is :
#1.Bullish (upward direction)
#2.Bearish (downwards direction)
#weak or certain
def calculate_trend_score(
    sma_20,
    sma_50,
    ema_20,
    ema_50,
    adx,
    plus_di,
    minus_di,
):
    
    score = 0
    
    # SMA trend
    if sma_20 > sma_50:
        score += 30
    elif sma_20 < sma_50:
        score -= 30
        
    # EMA trend
    if ema_20 > ema_50:
        score += 30
    elif ema_20 < ema_50:
        score -= 30
        
    #ADX directional confirmation
    if adx > 25:
        if plus_di > minus_di:
            score += 40
        elif minus_di > plus_di:
            score -= 40
            
    return score

def calculate_momentum_score(
    rsi,
    macd,
    macd_signal,
    stoch_k,
    stoch_d,
):
    score = 0

    # RSI momentum
    if rsi > 55:
        score += 30
    elif rsi < 45:
        score -= 30

    # MACD momentum
    if macd > macd_signal:
        score += 40
    elif macd < macd_signal:
        score -= 40

    # Stochastic momentum
    if stoch_k > stoch_d:
        score += 30
    elif stoch_k < stoch_d:
        score -= 30

    return score

def calculate_volume_score(
    relative_volume,
    price_change_pct,
):
    score = 0
    
    #volume strength
    if relative_volume >=2.0:
        volume_strength = 100
    elif relative_volume >= 1.5:
        volume_strength = 75
    elif relative_volume >= 1.0:
        volume_strength = 50
    else:
        volume_strength = 25
        
    #confirm direction using movement
    if price_change_pct > 0:
        score = volume_strength
    elif price_change_pct < 0:
        score = -volume_strength
        
    return score
        
def calculate_volatility_score(
    close,
    bb_upper,
    bb_lower,
    bb_middle,
):
    score = 0
    
    #Price above upper Bollinger Band
    if close > bb_upper:
        score = 100
        
    #Price below lower Bollinger Band
    elif close < bb_lower:
        score =- 100
        
    #Price above middle band
    elif close > bb_middle:
        score = 30
    
    #Price below middle band
    elif close < bb_middle:
        score = -30
        
    return score

def calculate_support_resistance_score(
    current_price,
    support_zone,
    resistance_zones,
):
    candidates = []
    
    #Support analysis
    for zone in support_zone:
        zone_low = zone["zone_low"]
        zone_high = zone["zone_high"]
        strength = zone["overall_strength"]
        
        if current_price < zone_low:
            score = -strength
        elif current_price <= zone_high:
            score = strength
        else:
            distance_pct = (
                (current_price - zone_high) / current_price
            ) * 100
            
            if distance_pct <= 2:
                score = strength * 0.7
            else:
                continue
            
        candidates.append(score)
        
    #Resistance analysis
    for zone in resistance_zones:
        zone_low = zone["zone_low"]
        zone_high = zone["zone_high"]
        strength = zone["overall_strength"]
        
        if current_price > zone_high:
            score = strength
        elif current_price >= zone_low:
            score = -strength
        else: 
            distance_pct = (
                (zone_low - current_price) / current_price
            ) * 100
            
            if distance_pct <= 2:
                score = -strength * 0.7
            else:
                continue
            
        candidates.append(score)
        
    if not candidates:
        return 0

    return max(candidates, key=abs)

def calculate_final_signal(
    trend_score,
    momentum_score,
    volume_score,
    volatility_score,
    support_resistance_score,
):
    weights = {
        "trend": 0.25,
        "momentum": 0.25,
        "volume": 0.15,
        "volatility": 0.15,
        "support_resistance": 0.20,
    }

    category_scores = {
        "trend": trend_score,
        "momentum": momentum_score,
        "volume": volume_score,
        "volatility": volatility_score,
        "support_resistance": support_resistance_score,
    }

    overall_score = sum(
        category_scores[key] * weights[key]
        for key in weights
    )

    overall_score = round(overall_score, 2)

    if overall_score >= 60:
        signal = "strong_bullish"
    elif overall_score >= 20:
        signal = "bullish"
    elif overall_score <= -60:
        signal = "strong_bearish"
    elif overall_score <= -20:
        signal = "bearish"
    else:
        signal = "neutral"

    return {
        "overall_score": overall_score,
        "signal": signal,
        "category_scores": category_scores,
    }