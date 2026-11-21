from django.test import SimpleTestCase

from apps.analysis_engine.services.signal_generator import (
    calculate_trend_score,
    calculate_momentum_score,
    calculate_volume_score,
    calculate_volatility_score,
    calculate_support_resistance_score,
    calculate_final_signal
)
    
class TrendScoringTests(SimpleTestCase):

    def test_bullish_trend(self):
        score = calculate_trend_score(
            sma_20=120,
            sma_50=110,
            ema_20=125,
            ema_50=115,
            adx=32,
            plus_di=35,
            minus_di=15,
        )

        self.assertEqual(score, 100)

    def test_bearish_trend(self):
        score = calculate_trend_score(
            sma_20=100,
            sma_50=110,
            ema_20=105,
            ema_50=115,
            adx=35,
            plus_di=12,
            minus_di=30,
        )

        self.assertEqual(score, -100)

    def test_weak_trend(self):
        score = calculate_trend_score(
            sma_20=120,
            sma_50=110,
            ema_20=125,
            ema_50=115,
            adx=20,
            plus_di=35,
            minus_di=15,
        )

        self.assertEqual(score, 60)

    def test_neutral_trend(self):
        score = calculate_trend_score(
            sma_20=100,
            sma_50=100,
            ema_20=100,
            ema_50=100,
            adx=20,
            plus_di=20,
            minus_di=20,
        )

        self.assertEqual(score, 0)
        
class MomentumScoringTests(SimpleTestCase):

    def test_bullish_momentum(self):
        score = calculate_momentum_score(
            rsi=65,
            macd=5,
            macd_signal=3,
            stoch_k=80,
            stoch_d=60,
        )
        self.assertEqual(score, 100)

    def test_bearish_momentum(self):
        score = calculate_momentum_score(
            rsi=35,
            macd=-5,
            macd_signal=-3,
            stoch_k=20,
            stoch_d=40,
        )
        self.assertEqual(score, -100)

    def test_neutral_momentum(self):
        score = calculate_momentum_score(
            rsi=50,
            macd=3,
            macd_signal=3,
            stoch_k=50,
            stoch_d=50,
        )
        self.assertEqual(score, 0)

    def test_mixed_momentum(self):
        score = calculate_momentum_score(
            rsi=60,
            macd=2,
            macd_signal=3,
            stoch_k=70,
            stoch_d=60,
        )
        self.assertEqual(score, 20)
        
class VolumeScoringTests(SimpleTestCase):

    def test_strong_bullish_volume(self):
        score = calculate_volume_score(2.5, 1.2)
        self.assertEqual(score, 100)

    def test_strong_bearish_volume(self):
        score = calculate_volume_score(2.5, -1.2)
        self.assertEqual(score, -100)

    def test_normal_bullish_volume(self):
        score = calculate_volume_score(1.2, 0.8)
        self.assertEqual(score, 50)

    def test_low_volume(self):
        score = calculate_volume_score(0.7, 1.0)
        self.assertEqual(score, 25)

    def test_no_price_movement(self):
        score = calculate_volume_score(2.5, 0)
        self.assertEqual(score, 0)
        
class VolatilityScoringTests(SimpleTestCase):

    def test_upper_band_breakout(self):
        score = calculate_volatility_score(
            close=110,
            bb_upper=105,
            bb_lower=95,
            bb_middle=100,
        )
        self.assertEqual(score, 100)

    def test_lower_band_breakout(self):
        score = calculate_volatility_score(
            close=90,
            bb_upper=105,
            bb_lower=95,
            bb_middle=100,
        )
        self.assertEqual(score, -100)

    def test_price_above_middle_band(self):
        score = calculate_volatility_score(103, 110, 90, 100)
        self.assertEqual(score, 30)

    def test_price_below_middle_band(self):
        score = calculate_volatility_score(97, 110, 90, 100)
        self.assertEqual(score, -30)

    def test_price_at_middle_band(self):
        score = calculate_volatility_score(100, 110, 90, 100)
        self.assertEqual(score, 0)
        
class SupportResistanceScoringTests(SimpleTestCase):

    def setUp(self):
        self.support = [
            {
                "zone_low": 98,
                "zone_high": 100,
                "overall_strength": 80,
            }
        ]

        self.resistance = [
            {
                "zone_low": 110,
                "zone_high": 112,
                "overall_strength": 70,
            }
        ]

    def test_price_near_support(self):
        score = calculate_support_resistance_score(
            99, self.support, []
        )
        self.assertEqual(score, 80)

    def test_price_near_resistance(self):
        score = calculate_support_resistance_score(
            111, [], self.resistance
        )
        self.assertEqual(score, -70)

    def test_price_breaks_support(self):
        score = calculate_support_resistance_score(
            97, self.support, []
        )
        self.assertEqual(score, -80)

    def test_price_breaks_resistance(self):
        score = calculate_support_resistance_score(
            113, [], self.resistance
        )
        self.assertEqual(score, 70)

    def test_no_nearby_zones(self):
        score = calculate_support_resistance_score(
            105, self.support, self.resistance
        )
        self.assertEqual(score, 0)
        
class FinalSignalTests(SimpleTestCase):

    def test_strong_bullish_signal(self):
        result = calculate_final_signal(100, 100, 100, 100, 100)
        self.assertEqual(result["overall_score"], 100)
        self.assertEqual(result["signal"], "strong_bullish")

    def test_bullish_signal(self):
        result = calculate_final_signal(40, 40, 40, 40, 40)
        self.assertEqual(result["overall_score"], 40)
        self.assertEqual(result["signal"], "bullish")

    def test_neutral_signal(self):
        result = calculate_final_signal(0, 0, 0, 0, 0)
        self.assertEqual(result["overall_score"], 0)
        self.assertEqual(result["signal"], "neutral")

    def test_bearish_signal(self):
        result = calculate_final_signal(-40, -40, -40, -40, -40)
        self.assertEqual(result["overall_score"], -40)
        self.assertEqual(result["signal"], "bearish")

    def test_strong_bearish_signal(self):
        result = calculate_final_signal(-100, -100, -100, -100, -100)
        self.assertEqual(result["overall_score"], -100)
        self.assertEqual(result["signal"], "strong_bearish")

    def test_weighted_calculation(self):
        result = calculate_final_signal(100, 50, 0, 0, -50)
        self.assertEqual(result["overall_score"], 27.5)
        self.assertEqual(result["signal"], "bullish")