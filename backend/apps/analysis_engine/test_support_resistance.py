import pandas as pd
from django.test import SimpleTestCase
from apps.analysis_engine.services.support_resistance import (
    calculate_swing_points,
)

class SwingPointTests(SimpleTestCase):

    def test_swing_high_detection(self):
        high = pd.Series([1, 2, 5, 2, 1])
        low = pd.Series([5, 4, 3, 2, 1])

        result = calculate_swing_points(
            high,
            low,
            left_bars=2,
            right_bars=2,
        )

        self.assertEqual(result["swing_high"].iloc[4], 5)
        self.assertTrue(result["swing_high"].iloc[:4].isna().all())

    def test_swing_low_detection(self):
        high = pd.Series([1, 2, 3, 4, 5])
        low = pd.Series([5, 4, 1, 4, 5])

        result = calculate_swing_points(
            high,
            low,
            left_bars=2,
            right_bars=2,
        )

        self.assertEqual(result["swing_low"].iloc[4], 1)
        self.assertTrue(result["swing_low"].iloc[:4].isna().all())
        
from apps.analysis_engine.services.support_resistance import (
    cluster_price_levels,
)

class PriceLevelClusteringTests(SimpleTestCase):

    def test_groups_nearby_prices(self):
        prices = pd.Series([100, 101, 102, 150, 151])

        result = cluster_price_levels(
            prices,
            tolerance_pct=0.02,
            min_touches=2,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["touches"], 3)
        self.assertEqual(result[1]["touches"], 2)

    def test_ignores_zones_with_insufficient_touches(self):
        prices = pd.Series([100, 101, 150])

        result = cluster_price_levels(
            prices,
            tolerance_pct=0.02,
            min_touches=2,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["touches"], 2)

    def test_empty_prices_return_empty_list(self):
        prices = pd.Series([], dtype=float)

        result = cluster_price_levels(prices)

        self.assertEqual(result, [])
        
from apps.analysis_engine.services.support_resistance import (
    calculate_swing_points,
    cluster_price_levels,
    calculate_relative_volume,
)

class RelativeVolumeTests(SimpleTestCase):

    def test_calculates_relative_volume(self):
        volume = pd.Series([10, 20, 30, 60])

        result = calculate_relative_volume(volume, period=3)

        self.assertTrue(result.iloc[:2].isna().all())
        self.assertAlmostEqual(result.iloc[2], 1.5)
        self.assertAlmostEqual(result.iloc[3], 60 / (110 / 3))

    def test_returns_series(self):
        volume = pd.Series([10, 20, 30, 40])

        result = calculate_relative_volume(volume, period=3)

        self.assertIsInstance(result, pd.Series)
        self.assertEqual(result.name, "relative_volume")
       
from apps.analysis_engine.services.support_resistance import (
    calculate_swing_points,
    cluster_price_levels,
    calculate_relative_volume,
    calculate_zone_volume_confirmation,
    calculate_zone_reactions,
    calculate_zone_strength,
)
 
class ZoneVolumeConfirmationTests(SimpleTestCase):

    def test_calculates_zone_volume_score(self):
        levels = [
            {
                "level": 100,
                "touches": 2,
                "zone_low": 99,
                "zone_high": 101,
            }
        ]

        swing_prices = pd.Series([100, 100, None])
        swing_rvol = pd.Series([2.5, 1.5, None])

        result = calculate_zone_volume_confirmation(
            levels,
            swing_prices,
            swing_rvol,
        )

        self.assertEqual(result[0]["volume_confirmation"], "very_high")
        self.assertEqual(result[0]["volume_score"], 100)
        self.assertEqual(result[0]["high_volume_touches"], 2)

    def test_handles_missing_volume_observations(self):
        levels = [
            {
                "level": 100,
                "touches": 2,
                "zone_low": 99,
                "zone_high": 101,
            }
        ]

        swing_prices = pd.Series([100, 100])
        swing_rvol = pd.Series([None, None])

        result = calculate_zone_volume_confirmation(
            levels,
            swing_prices,
            swing_rvol,
        )

        self.assertEqual(
            result[0]["volume_confirmation"],
            "insufficient_data",
        )
        self.assertEqual(result[0]["volume_score"], 0)
        
class ZoneReactionTests(SimpleTestCase):

    def test_calculates_support_reaction(self):
        prices = pd.DataFrame({
            "high": [101, 102, 110, 108, 105, 103, 102],
            "low":  [99, 100, 100, 103, 102, 101, 100],
        })

        swing_points = pd.Series(
            [None, 100, None, None, None, None, None]
        )

        levels = [{
            "level": 100,
            "touches": 1,
            "zone_low": 99,
            "zone_high": 101,
        }]

        result = calculate_zone_reactions(
            levels, prices, swing_points,
            reaction_window=5,
            zone_type="support",
        )

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["average_reaction_pct"], 10.0)
        self.assertEqual(result[0]["reaction_observations"], 1)

    def test_calculates_resistance_reaction(self):
        prices = pd.DataFrame({
            "high": [111, 112, 109, 108, 107, 106, 105],
            "low":  [109, 110, 100, 102, 103, 104, 105],
        })

        swing_points = pd.Series(
            [None, 110, None, None, None, None, None]
        )

        levels = [{
            "level": 110,
            "touches": 1,
            "zone_low": 109,
            "zone_high": 111,
        }]

        result = calculate_zone_reactions(
            levels, prices, swing_points,
            reaction_window=5,
            zone_type="resistance",
        )

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(
            result[0]["average_reaction_pct"],
            9.090909,
            places=5,
        )

    def test_ignores_insufficient_future_data(self):
        prices = pd.DataFrame({
            "high": [101, 102, 110],
            "low": [99, 100, 100],
        })

        swing_points = pd.Series([None, 100, None])

        levels = [{
            "level": 100,
            "touches": 1,
            "zone_low": 99,
            "zone_high": 101,
        }]

        result = calculate_zone_reactions(
            levels, prices, swing_points,
            reaction_window=5,
            zone_type="support",
        )

        self.assertEqual(result, [])
        
class ZoneReactionTests(SimpleTestCase):

    def test_calculates_support_reaction(self):
        prices = pd.DataFrame({
            "high": [101, 102, 110, 108, 105, 103, 102],
            "low":  [99, 100, 100, 103, 102, 101, 100],
        })

        swing_points = pd.Series(
            [None, 100, None, None, None, None, None]
        )

        levels = [{
            "level": 100,
            "touches": 1,
            "zone_low": 99,
            "zone_high": 101,
        }]

        result = calculate_zone_reactions(
            levels, prices, swing_points,
            reaction_window=5,
            zone_type="support",
        )

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["average_reaction_pct"], 10.0)
        self.assertEqual(result[0]["reaction_observations"], 1)

    def test_calculates_resistance_reaction(self):
        prices = pd.DataFrame({
            "high": [111, 112, 109, 108, 107, 106, 105],
            "low":  [109, 110, 100, 102, 103, 104, 105],
        })

        swing_points = pd.Series(
            [None, 110, None, None, None, None, None]
        )

        levels = [{
            "level": 110,
            "touches": 1,
            "zone_low": 109,
            "zone_high": 111,
        }]

        result = calculate_zone_reactions(
            levels, prices, swing_points,
            reaction_window=5,
            zone_type="resistance",
        )

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(
            result[0]["average_reaction_pct"],
            9.09,
            places=2,
        )

    def test_ignores_insufficient_future_data(self):
        prices = pd.DataFrame({
            "high": [101, 102, 110],
            "low": [99, 100, 100],
        })

        swing_points = pd.Series([None, 100, None])

        levels = [{
            "level": 100,
            "touches": 1,
            "zone_low": 99,
            "zone_high": 101,
        }]

        result = calculate_zone_reactions(
            levels, prices, swing_points,
            reaction_window=5,
            zone_type="support",
        )

        self.assertEqual(result, [])
        
        
class ZoneStrengthTests(SimpleTestCase):

    def test_calculates_weighted_zone_strength(self):
        reaction_levels = [
            {
                "level": 100,
                "touches": 4,
                "zone_low": 99,
                "zone_high": 101,
                "reaction_score": 80,
            }
        ]

        volume_levels = [
            {
                "level": 100,
                "zone_low": 99,
                "zone_high": 101,
                "volume_score": 75,
            }
        ]

        result = calculate_zone_strength(
            reaction_levels,
            volume_levels,
        )

        self.assertAlmostEqual(result[0]["strength_score"], 86.5)
        self.assertEqual(result[0]["strength"], "strong")

    def test_returns_empty_list_without_reaction_levels(self):
        result = calculate_zone_strength([], [])
        self.assertEqual(result, [])

    def test_rejects_invalid_weights(self):
        with self.assertRaises(ValueError):
            calculate_zone_strength(
                [],
                [],
                touch_weight=0.5,
                volume_weight=0.5,
                reaction_weight=0.5,
            )