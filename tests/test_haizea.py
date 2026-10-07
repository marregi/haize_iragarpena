import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
import pytz

import haizea


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 3, 28, 12)
        return tz.localize(value) if tz else value


class MadridTimestampLocalizationTests(unittest.TestCase):
    def test_current_data_handles_nonexistent_spring_timestamp(self):
        data = pd.DataFrame({"timestamp": ["2026-03-29 02:00:00"]})

        current, _ = haizea.get_current_data(data)

        self.assertEqual(len(current), 1)
        self.assertEqual(
            current["timestamp"].iloc[0],
            pd.Timestamp("2026-03-29 03:00:00", tz="Europe/Madrid"),
        )

    def test_forecast_handles_nonexistent_spring_timestamp(self):
        data = pd.DataFrame(
            {"timestamp": ["2026-03-29 02:00:00"], "wind_mps": [5.2]}
        )

        with patch.object(haizea, "datetime", FixedDateTime):
            forecast = haizea.get_forecast_from_sheet(data)

        self.assertEqual(forecast[0]["hours"][0]["hour"], "03:00")

    def test_ambiguous_fall_timestamp_uses_standard_time(self):
        timestamps = pd.Series(pd.to_datetime(["2026-10-25 02:30:00"]))

        localized = haizea.localize_madrid_timestamps(timestamps)

        self.assertEqual(localized.iloc[0].utcoffset(), timedelta(hours=1))


if __name__ == "__main__":
    unittest.main()
