"""
Channel Finder - Hierarchical Technical Analysis Tool

This module implements a human-like approach to finding trend channels:
1. First find the macro trend channel (dominant large-scale trend)
2. Then find internal channels/levels inside the macro channel
3. Build around 3 structural levels if possible
4. Detect breakout context

The goal is to imitate how a human would draw clean, meaningful trend channels.
"""

import pandas as pd
import numpy as np
from scipy import stats


class ChannelFinder:
    """
    Hierarchical channel finder that mimics human technical analysis.
    """

    def __init__(self, df):
        """
        Initialize with price data.

        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with OHLC data and swing_high/swing_low columns
        """
        self.df = df.copy()
        self.debug_info = {
            "macro_channel": None,
            "inner_channels": [],
            "local_channels": [],
            "touch_zones": [],
            "breakouts": [],
            "rejected_channels": [],
        }

    def find_major_swing_highs(self, min_importance=5):
        """
        Find major swing highs - those that are more significant.

        Parameters:
        -----------
        min_importance : int
            Minimum number of bars to look back/forward for significance

        Returns:
        --------
        list of dict
            Major swing high points with importance scores
        """
        if "swing_high" not in self.df.columns:
            return []

        swing_highs = self.df[self.df["swing_high"].notna()].copy()

        if len(swing_highs) == 0:
            return []

        # Calculate importance based on price movement around the swing
        major_highs = []
        for idx, row in swing_highs.iterrows():
            pos = self.df.index.get_loc(idx)
            price = row["swing_high"]

            # Calculate price range around this swing
            lookback = min(10, pos)
            lookforward = min(10, len(self.df) - pos - 1)

            if lookback > 0 and lookforward > 0:
                past_range = (
                    self.df["High"].iloc[pos - lookback : pos].max()
                    - self.df["Low"].iloc[pos - lookback : pos].min()
                )
                future_range = (
                    self.df["High"].iloc[pos + 1 : pos + lookforward + 1].max()
                    - self.df["Low"].iloc[pos + 1 : pos + lookforward + 1].min()
                )
                avg_range = (past_range + future_range) / 2

                # Importance based on how much the swing protrudes
                if avg_range > 0:
                    importance = (
                        price
                        - min(
                            self.df["Low"]
                            .iloc[pos - lookback : pos + lookforward + 1]
                            .min(),
                            self.df["Low"]
                            .iloc[pos - lookback : pos + lookforward + 1]
                            .min(),
                        )
                    ) / avg_range
                else:
                    importance = 1
            else:
                importance = 1

            major_highs.append(
                {
                    "index_pos": pos,
                    "datetime": idx,
                    "price": price,
                    "importance": importance,
                }
            )

        # Sort by importance and return
        major_highs.sort(key=lambda x: x["importance"], reverse=True)
        return major_highs

    def find_major_swing_lows(self, min_importance=5):
        """
        Find major swing lows - those that are more significant.

        Parameters:
        -----------
        min_importance : int
            Minimum number of bars to look back/forward for significance

        Returns:
        --------
        list of dict
            Major swing low points with importance scores
        """
        if "swing_low" not in self.df.columns:
            return []

        swing_lows = self.df[self.df["swing_low"].notna()].copy()

        if len(swing_lows) == 0:
            return []

        # Calculate importance based on price movement around the swing
        major_lows = []
        for idx, row in swing_lows.iterrows():
            pos = self.df.index.get_loc(idx)
            price = row["swing_low"]

            # Calculate price range around this swing
            lookback = min(10, pos)
            lookforward = min(10, len(self.df) - pos - 1)

            if lookback > 0 and lookforward > 0:
                past_range = (
                    self.df["High"].iloc[pos - lookback : pos].max()
                    - self.df["Low"].iloc[pos - lookback : pos].min()
                )
                future_range = (
                    self.df["High"].iloc[pos + 1 : pos + lookforward + 1].max()
                    - self.df["Low"].iloc[pos + 1 : pos + lookforward + 1].min()
                )
                avg_range = (past_range + future_range) / 2

                # Importance based on how much the swing protrudes
                if avg_range > 0:
                    importance = (
                        max(
                            self.df["High"]
                            .iloc[pos - lookback : pos + lookforward + 1]
                            .max(),
                            self.df["High"]
                            .iloc[pos - lookback : pos + lookforward + 1]
                            .max(),
                        )
                        - price
                    ) / avg_range
                else:
                    importance = 1
            else:
                importance = 1

            major_lows.append(
                {
                    "index_pos": pos,
                    "datetime": idx,
                    "price": price,
                    "importance": importance,
                }
            )

        # Sort by importance and return
        major_lows.sort(key=lambda x: x["importance"], reverse=True)
        return major_lows

    def find_macro_channel(self):
        """
        Step 1: Find the macro trend channel.

        Look for the dominant large-scale trend using major swing highs and lows.

        Returns:
        --------
        dict
            Macro channel information with upper/lower lines and debug info
        """
        major_highs = self.find_major_swing_highs()
        major_lows = self.find_major_swing_lows()

        if len(major_highs) < 2 or len(major_lows) < 2:
            self.debug_info["rejected_channels"].append(
                {
                    "type": "macro",
                    "reason": "Not enough major swing points",
                }
            )
            return None

        # Determine overall trend direction
        # Use first and last significant points
        first_high = major_highs[0]["price"]
        last_high = major_highs[min(2, len(major_highs) - 1)]["price"]
        first_low = major_lows[0]["price"]
        last_low = major_lows[min(2, len(major_lows) - 1)]["price"]

        # Calculate overall slope
        high_slope = (last_high - first_high) / max(1, len(self.df) - 1)
        low_slope = (last_low - first_low) / max(1, len(self.df) - 1)

        is_uptrend = high_slope > 0 and low_slope > 0
        is_downtrend = high_slope < 0 and low_slope < 0

        # Try to find valid macro channel
        macro_channel = None

        if is_uptrend:
            # For uptrend: try to find rising channel with two rising lines
            macro_channel = self._find_rising_macro_channel(major_highs, major_lows)
        elif is_downtrend:
            # For downtrend: try to find falling channel
            macro_channel = self._find_falling_macro_channel(major_highs, major_lows)
        else:
            # Sideways market - try horizontal channels
            macro_channel = self._find_horizontal_macro_channel(major_highs, major_lows)

        self.debug_info["macro_channel"] = macro_channel
        return macro_channel

    def _find_rising_macro_channel(self, major_highs, major_lows):
        """
        Find a rising macro channel for uptrends.
        """
        # Select top major highs for upper line
        upper_points = sorted(
            major_highs[: min(4, len(major_highs))], key=lambda x: x["index_pos"]
        )

        # Select top major lows for lower line
        lower_points = sorted(
            major_lows[: min(4, len(major_lows))], key=lambda x: x["index_pos"]
        )

        if len(upper_points) < 2 or len(lower_points) < 2:
            return None

        # Calculate upper line (connecting peaks)
        upper_line = self._fit_line(upper_points)
        if not upper_line:
            return None

        # Calculate lower line (connecting troughs)
        lower_line = self._fit_line(lower_points)
        if not lower_line:
            return None

        # Check that both lines are rising
        if upper_line["slope"] <= 0 or lower_line["slope"] <= 0:
            self.debug_info["rejected_channels"].append(
                {
                    "type": "macro",
                    "reason": "Lines not rising for uptrend",
                }
            )
            return None

        # Check that channel covers a good portion of the data
        coverage = self._calculate_channel_coverage(upper_line, lower_line)
        if coverage < 0.5:  # Need at least 50% coverage
            self.debug_info["rejected_channels"].append(
                {
                    "type": "macro",
                    "reason": f"Low coverage: {coverage:.2%}",
                }
            )
            return None

        # Check that lines are not too far from price at either end
        if self._check_line_floating_away(upper_line, lower_line):
            self.debug_info["rejected_channels"].append(
                {
                    "type": "macro",
                    "reason": "Lines float too far from price at one end",
                }
            )
            return None

        # Count touches
        upper_touches = self._count_touches(upper_line, "High")
        lower_touches = self._count_touches(lower_line, "Low")

        # Calculate score
        score = (
            coverage * 0.4
            + min(upper_touches, lower_touches) / 10 * 0.3
            + (
                upper_line["slope"] / lower_line["slope"]
                if lower_line["slope"] > 0
                else 0
            )
            * 0.3
        )

        return {
            "type": "rising",
            "upper_line": upper_line,
            "lower_line": lower_line,
            "upper_touches": upper_touches,
            "lower_touches": lower_touches,
            "coverage": coverage,
            "score": score,
            "upper_points": upper_points,
            "lower_points": lower_points,
            "debug": {
                "reason": "Valid rising macro channel",
                "slope_ratio": (
                    upper_line["slope"] / lower_line["slope"]
                    if lower_line["slope"] > 0
                    else 0
                ),
            },
        }

    def _find_falling_macro_channel(self, major_highs, major_lows):
        """
        Find a falling macro channel for downtrends.
        """
        # Select top major highs for upper line
        upper_points = sorted(
            major_highs[: min(4, len(major_highs))], key=lambda x: x["index_pos"]
        )

        # Select top major lows for lower line
        lower_points = sorted(
            major_lows[: min(4, len(major_lows))], key=lambda x: x["index_pos"]
        )

        if len(upper_points) < 2 or len(lower_points) < 2:
            return None

        # Calculate upper line
        upper_line = self._fit_line(upper_points)
        if not upper_line:
            return None

        # Calculate lower line
        lower_line = self._fit_line(lower_points)
        if not lower_line:
            return None

        # Check that both lines are falling
        if upper_line["slope"] >= 0 or lower_line["slope"] >= 0:
            self.debug_info["rejected_channels"].append(
                {
                    "type": "macro",
                    "reason": "Lines not falling for downtrend",
                }
            )
            return None

        # Check coverage
        coverage = self._calculate_channel_coverage(upper_line, lower_line)
        if coverage < 0.5:
            self.debug_info["rejected_channels"].append(
                {
                    "type": "macro",
                    "reason": f"Low coverage: {coverage:.2%}",
                }
            )
            return None

        # Check for floating
        if self._check_line_floating_away(upper_line, lower_line):
            self.debug_info["rejected_channels"].append(
                {
                    "type": "macro",
                    "reason": "Lines float too far from price at one end",
                }
            )
            return None

        # Count touches
        upper_touches = self._count_touches(upper_line, "High")
        lower_touches = self._count_touches(lower_line, "Low")

        # Calculate score
        score = coverage * 0.4 + min(upper_touches, lower_touches) / 10 * 0.3

        return {
            "type": "falling",
            "upper_line": upper_line,
            "lower_line": lower_line,
            "upper_touches": upper_touches,
            "lower_touches": lower_touches,
            "coverage": coverage,
            "score": score,
            "upper_points": upper_points,
            "lower_points": lower_points,
            "debug": {
                "reason": "Valid falling macro channel",
            },
        }

    def _find_horizontal_macro_channel(self, major_highs, major_lows):
        """
        Find a horizontal macro channel for sideways markets.
        """
        # Calculate average levels
        avg_high = np.mean([p["price"] for p in major_highs[:3]])
        avg_low = np.mean([p["price"] for p in major_lows[:3]])

        upper_line = {
            "slope": 0,
            "intercept": avg_high,
            "points": [p["index_pos"] for p in major_highs[:3]],
        }

        lower_line = {
            "slope": 0,
            "intercept": avg_low,
            "points": [p["index_pos"] for p in major_lows[:3]],
        }

        # Count touches
        upper_touches = self._count_touches(upper_line, "High")
        lower_touches = self._count_touches(lower_line, "Low")

        return {
            "type": "horizontal",
            "upper_line": upper_line,
            "lower_line": lower_line,
            "upper_touches": upper_touches,
            "lower_touches": lower_touches,
            "coverage": 0.7,
            "score": 0.5,
            "debug": {"reason": "Horizontal channel for sideways market"},
        }

    def _fit_line(self, points):
        """
        Fit a linear trendline through given points.

        Parameters:
        -----------
        points : list of dict
            Points with index_pos and price

        Returns:
        --------
        dict
            Line with slope, intercept, and points
        """
        if len(points) < 2:
            return None

        x = np.array([p["index_pos"] for p in points])
        y = np.array([p["price"] for p in points])

        # Use linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_value**2,
            "points": points,
        }

    def _calculate_channel_coverage(self, upper_line, lower_line):
        """
        Calculate what portion of the data is within the channel.
        """
        close_prices = self.df["Close"].values

        covered = 0
        for i in range(len(self.df)):
            upper_val = upper_line["slope"] * i + upper_line["intercept"]
            lower_val = lower_line["slope"] * i + lower_line["intercept"]

            if lower_val <= close_prices[i] <= upper_val:
                covered += 1

        return covered / len(self.df) if len(self.df) > 0 else 0

    def _check_line_floating_away(self, upper_line, lower_line):
        """
        Check if lines float too far from price at either end.
        """
        close_prices = self.df["Close"].values
        n = len(close_prices)

        if n < 10:
            return False

        # Check first 10% and last 10%
        check_range = max(10, n // 10)

        # First section
        first_upper = upper_line["slope"] * 0 + upper_line["intercept"]
        first_lower = lower_line["slope"] * 0 + lower_line["intercept"]
        first_avg_price = np.mean(close_prices[:check_range])

        first_dist = (
            max(abs(first_upper - first_avg_price), abs(first_lower - first_avg_price))
            / first_avg_price
        )

        # Last section
        last_upper = upper_line["slope"] * (n - 1) + upper_line["intercept"]
        last_lower = lower_line["slope"] * (n - 1) + lower_line["intercept"]
        last_avg_price = np.mean(close_prices[-check_range:])

        last_dist = (
            max(abs(last_upper - last_avg_price), abs(last_lower - last_avg_price))
            / last_avg_price
        )

        # If either end is more than 20% away, consider it floating
        return first_dist > 0.2 or last_dist > 0.2

    def _count_touches(self, line, price_col="Close", tolerance_pct=0.005):
        """
        Count how many times price actually touches the line within tolerance.
        Only count when price is close to the line and reverses or pauses.
        """
        touches = 0
        prices = self.df[price_col].values

        for i in range(len(self.df)):
            line_val = line["slope"] * i + line["intercept"]
            price = prices[i]

            if not (pd.isna(line_val) or pd.isna(price)):
                # Only count as a touch if price is very close to the line
                if abs(price - line_val) / line_val <= tolerance_pct:
                    touches += 1

        return touches

    def find_inner_channels(self, macro_channel):
        """
        Step 2: Find internal channels/levels inside the macro channel.

        Parameters:
        -----------
        macro_channel : dict
            The macro channel from step 1

        Returns:
        --------
        list of dict
            Inner channels found
        """
        if not macro_channel:
            return []

        inner_channels = []

        # Get swing points that are inside the macro channel
        swing_highs_df = self.df[self.df["swing_high"].notna()].copy()
        swing_lows_df = self.df[self.df["swing_low"].notna()].copy()

        # Convert to list of dicts
        swing_highs = []
        for idx, row in swing_highs_df.iterrows():
            pos = self.df.index.get_loc(idx)
            swing_highs.append({"index_pos": pos, "price": row["swing_high"]})

        swing_lows = []
        for idx, row in swing_lows_df.iterrows():
            pos = self.df.index.get_loc(idx)
            swing_lows.append({"index_pos": pos, "price": row["swing_low"]})

        # Find internal resistance lines (between macro upper and middle)
        internal_resistance = self._find_internal_lines(
            swing_highs, macro_channel, "resistance"
        )
        inner_channels.extend(internal_resistance)

        # Find internal support lines (between macro lower and middle)
        internal_support = self._find_internal_support_lines(
            swing_lows, macro_channel, "support"
        )
        inner_channels.extend(internal_support)

        self.debug_info["inner_channels"] = inner_channels
        return inner_channels

    def _find_internal_resistance_lines(self, swing_points, macro_channel, line_type):
        """
        Find internal support/resistance lines.
        """
        lines = []

        # Convert DataFrame to list of dicts if needed
        if isinstance(swing_points, pd.DataFrame):
            converted_points = []
            for idx, row in swing_points.iterrows():
                pos = self.df.index.get_loc(idx)
                price_col = "swing_high" if "swing_high" in row.index else "swing_low"
                converted_points.append({"index_pos": pos, "price": row[price_col]})
            swing_points = converted_points

        if len(swing_points) < 2:
            return lines

        # Get macro bounds
        n = len(self.df)
        upper_vals = [
            macro_channel["upper_line"]["slope"] * i
            + macro_channel["upper_line"]["intercept"]
            for i in range(n)
        ]
        lower_vals = [
            macro_channel["lower_line"]["slope"] * i
            + macro_channel["lower_line"]["intercept"]
            for i in range(n)
        ]

        # Group nearby swing points
        grouped = self._group_nearby_points(swing_points)

        for group in grouped:
            if len(group) < 2:
                continue

            # Fit line through group
            line = self._fit_line(group)
            if not line:
                continue

            # Check if line is inside macro channel
            avg_pos = np.mean([p["index_pos"] for p in group])
            avg_price = np.mean([p["price"] for p in group])

            upper_at_pos = (
                macro_channel["upper_line"]["slope"] * avg_pos
                + macro_channel["upper_line"]["intercept"]
            )
            lower_at_pos = (
                macro_channel["lower_line"]["slope"] * avg_pos
                + macro_channel["lower_line"]["intercept"]
            )

            # Check if line is meaningfully inside the channel
            if line_type == "resistance":
                if avg_price > upper_at_pos * 0.7 and avg_price < upper_at_pos:
                    touches = self._count_touches(line, "High")
                    if touches >= 2:
                        lines.append(
                            {
                                "type": "internal_resistance",
                                "line": line,
                                "touches": touches,
                                "points": group,
                                "score": touches / 10,
                                "debug": {"reason": f"Valid internal {line_type} line"},
                            }
                        )
            else:  # support
                if avg_price > lower_at_pos and avg_price < lower_at_pos * 1.3:
                    touches = self._count_touches(line, "Low")
                    if touches >= 2:
                        lines.append(
                            {
                                "type": "internal_support",
                                "line": line,
                                "touches": touches,
                                "points": group,
                                "score": touches / 10,
                                "debug": {"reason": f"Valid internal {line_type} line"},
                            }
                        )

        return lines

    # Alias for compatibility
    _find_internal_lines = _find_internal_resistance_lines

    def _find_internal_support_lines(self, swing_points, macro_channel, line_type):
        """
        Find internal support lines.
        """
        return self._find_internal_resistance_lines(
            swing_points, macro_channel, line_type
        )

        # Group nearby swing points
        grouped = self._group_nearby_points(swing_points)

        for group in grouped:
            if len(group) < 2:
                continue

            # Fit line through group
            line = self._fit_line(group)
            if not line:
                continue

            # Check if line is inside macro channel
            avg_pos = np.mean([p["index_pos"] for p in group])
            avg_price = np.mean([p["price"] for p in group])

            upper_at_pos = (
                macro_channel["upper_line"]["slope"] * avg_pos
                + macro_channel["upper_line"]["intercept"]
            )
            lower_at_pos = (
                macro_channel["lower_line"]["slope"] * avg_pos
                + macro_channel["lower_line"]["intercept"]
            )

            # Check if line is meaningfully inside the channel
            if line_type == "resistance":
                if avg_price > upper_at_pos * 0.7 and avg_price < upper_at_pos:
                    touches = self._count_touches(line, "High")
                    if touches >= 2:
                        lines.append(
                            {
                                "type": "internal_resistance",
                                "line": line,
                                "touches": touches,
                                "points": group,
                                "score": touches / 10,
                                "debug": {"reason": f"Valid internal {line_type} line"},
                            }
                        )
            else:  # support
                if avg_price > lower_at_pos and avg_price < lower_at_pos * 1.3:
                    touches = self._count_touches(line, "Low")
                    if touches >= 2:
                        lines.append(
                            {
                                "type": "internal_support",
                                "line": line,
                                "touches": touches,
                                "points": group,
                                "score": touches / 10,
                                "debug": {"reason": f"Valid internal {line_type} line"},
                            }
                        )

        return lines

    def _group_nearby_points(self, swing_points, max_distance=20):
        """
        Group nearby swing points together.
        """
        if len(swing_points) == 0:
            return []

        # Sort by position
        sorted_points = sorted(swing_points, key=lambda x: x["index_pos"])

        groups = []
        current_group = [sorted_points[0]]

        for i in range(1, len(sorted_points)):
            if (
                sorted_points[i]["index_pos"] - current_group[-1]["index_pos"]
                <= max_distance
            ):
                current_group.append(sorted_points[i])
            else:
                if len(current_group) >= 2:
                    groups.append(current_group)
                current_group = [sorted_points[i]]

        # Add last group
        if len(current_group) >= 2:
            groups.append(current_group)

        return groups

    def find_local_channels(self, macro_channel):
        """
        Step 3: Find small/local consolidation channels.

        Parameters:
        -----------
        macro_channel : dict
            The macro channel from step 1

        Returns:
        --------
        list of dict
            Local channels found
        """
        if not macro_channel:
            return []

        local_channels = []

        # Look for small consolidation patterns
        # Use recent swing points only
        recent_highs = self.df[self.df["swing_high"].notna()].tail(10)
        recent_lows = self.df[self.df["swing_low"].notna()].tail(10)

        if len(recent_highs) < 2 or len(recent_lows) < 2:
            return local_channels

        # Try to find small rising/falling channels
        high_points = []
        for idx, row in recent_highs.iterrows():
            pos = self.df.index.get_loc(idx)
            high_points.append({"index_pos": pos, "price": row["swing_high"]})

        low_points = []
        for idx, row in recent_lows.iterrows():
            pos = self.df.index.get_loc(idx)
            low_points.append({"index_pos": pos, "price": row["swing_low"]})

        # Try to fit a small channel
        if len(high_points) >= 2 and len(low_points) >= 2:
            upper_line = self._fit_line(high_points)
            lower_line = self._fit_line(low_points)

            if upper_line and lower_line:
                # Check if it's a valid small channel
                coverage = self._calculate_channel_coverage(upper_line, lower_line)

                if coverage > 0.6:  # Tight channel
                    local_channels.append(
                        {
                            "type": "local",
                            "upper_line": upper_line,
                            "lower_line": lower_line,
                            "coverage": coverage,
                            "score": coverage,
                            "debug": {"reason": "Valid local consolidation channel"},
                        }
                    )

        self.debug_info["local_channels"] = local_channels
        return local_channels

    def detect_breakout_context(self, macro_channel, inner_channels, local_channels):
        """
        Step 4: Detect breakout context.

        Parameters:
        -----------
        macro_channel : dict
            The macro channel
        inner_channels : list
            Inner channels
        local_channels : list
            Local channels

        Returns:
        --------
        dict
            Breakout context information
        """
        if not macro_channel:
            return {"potential_bullish_breakout_context": False}

        close_prices = self.df["Close"].values
        n = len(close_prices)

        # Get current position in macro channel
        current_price = close_prices[-1]

        upper_line = macro_channel["upper_line"]
        lower_line = macro_channel["lower_line"]

        upper_at_current = upper_line["slope"] * (n - 1) + upper_line["intercept"]
        lower_at_current = lower_line["slope"] * (n - 1) + lower_line["intercept"]

        # Calculate position in channel (0 = at bottom, 1 = at top)
        channel_range = upper_at_current - lower_at_current
        if channel_range > 0:
            position_in_channel = (current_price - lower_at_current) / channel_range
            # Clamp to valid range
            position_in_channel = max(0, min(1, position_in_channel))
        else:
            position_in_channel = 0.5

        # Check for breakout from inner channels
        breakout_info = {
            "potential_bullish_breakout_context": False,
            "potential_bearish_breakout_context": False,
            "current_position_in_macro": position_in_channel,
            "macro_type": macro_channel.get("type", "unknown"),
        }

        # Check recent price action for breakouts
        recent_prices = close_prices[-20:] if len(close_prices) >= 20 else close_prices

        for inner in inner_channels:
            line = inner.get("line")
            if not line:
                continue

            # Check if price broke above or below this line recently
            for i in range(max(0, len(close_prices) - 20), len(close_prices) - 1):
                line_val = line["slope"] * i + line["intercept"]
                next_line_val = line["slope"] * (i + 1) + line["intercept"]

                # Bullish breakout: price crossed above line
                if close_prices[i] < line_val and close_prices[i + 1] > next_line_val:
                    if position_in_channel < 0.7:  # Still in lower/middle part of macro
                        breakout_info["potential_bullish_breakout_context"] = True
                        breakout_info["breakout_details"] = {
                            "type": "bullish",
                            "from_line": inner.get("type"),
                            "position_in_macro": position_in_channel,
                        }

                # Bearish breakout: price crossed below line
                elif close_prices[i] > line_val and close_prices[i + 1] < next_line_val:
                    if position_in_channel > 0.3:  # Still in upper/middle part of macro
                        breakout_info["potential_bearish_breakout_context"] = True
                        breakout_info["breakout_details"] = {
                            "type": "bearish",
                            "from_line": inner.get("type"),
                            "position_in_macro": position_in_channel,
                        }

        self.debug_info["breakouts"] = [breakout_info]
        return breakout_info

    def find_touch_zones(self):
        """
        Find touch zones where price has reacted multiple times.

        Returns:
        --------
        list of dict
            Touch zones with price levels and touch counts
        """
        touch_zones = []

        # Find horizontal touch zones
        swing_highs = self.df[self.df["swing_high"].notna()].copy()
        swing_lows = self.df[self.df["swing_low"].notna()].copy()

        # Group similar high levels
        if len(swing_highs) > 0:
            high_prices = swing_highs["swing_high"].values
            high_indices = [self.df.index.get_loc(idx) for idx in swing_highs.index]

            zones = self._find_price_zones(high_prices, high_indices)
            for zone in zones:
                zone["type"] = "resistance_zone"
                touch_zones.append(zone)

        # Group similar low levels
        if len(swing_lows) > 0:
            low_prices = swing_lows["swing_low"].values
            low_indices = [self.df.index.get_loc(idx) for idx in swing_lows.index]

            zones = self._find_price_zones(low_prices, low_indices)
            for zone in zones:
                zone["type"] = "support_zone"
                touch_zones.append(zone)

        self.debug_info["touch_zones"] = touch_zones
        return touch_zones

    def _find_price_zones(self, prices, indices, tolerance_pct=0.02):
        """
        Find zones where multiple touches are at similar price levels.
        """
        if len(prices) < 2:
            return []

        zones = []
        used = set()

        for i in range(len(prices)):
            if i in used:
                continue

            zone_prices = [prices[i]]
            zone_indices = [indices[i]]

            for j in range(i + 1, len(prices)):
                if j in used:
                    continue

                # Check if prices are within tolerance
                if abs(prices[j] - prices[i]) / prices[i] <= tolerance_pct:
                    zone_prices.append(prices[j])
                    zone_indices.append(indices[j])
                    used.add(j)

            if len(zone_prices) >= 2:
                zones.append(
                    {
                        "avg_price": np.mean(zone_prices),
                        "touch_count": len(zone_prices),
                        "indices": zone_indices,
                        "prices": zone_prices,
                    }
                )
                used.add(i)

        return zones

    def analyze(self):
        """
        Main analysis method that runs all steps.

        Returns:
        --------
        dict
            Complete analysis with all channels and debug info
        """
        # Step 1: Find macro channel
        macro_channel = self.find_macro_channel()

        # Step 2: Find inner channels
        inner_channels = (
            self.find_inner_channels(macro_channel) if macro_channel else []
        )

        # Step 3: Find local channels
        local_channels = (
            self.find_local_channels(macro_channel) if macro_channel else []
        )

        # Step 4: Detect breakout context
        breakout_context = self.detect_breakout_context(
            macro_channel, inner_channels, local_channels
        )

        # Step 5: Find touch zones
        touch_zones = self.find_touch_zones()

        return {
            "macro_channel": macro_channel,
            "inner_channels": inner_channels,
            "local_channels": local_channels,
            "breakout_context": breakout_context,
            "touch_zones": touch_zones,
            "debug": self.debug_info,
        }


def find_channels(df):
    """
    Convenience function to find all channels in the data.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data and swing_high/swing_low columns

    Returns:
    --------
    dict
        Complete channel analysis
    """
    finder = ChannelFinder(df)
    return finder.analyze()
