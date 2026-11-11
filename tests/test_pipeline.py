import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
from scripts.clean import clean_events, VALID_EVENT_TYPES
from scripts.transform import transform_events
from scripts.features import feature_events


class PipelineTests(unittest.TestCase):
    def frame(self, rows):
        return pd.DataFrame(rows, columns=["user_id", "timestamp", "event_type", "duration_seconds"])

    def test_clean_formats_and_types(self):
        times = ["2026-02-28 10:29:30", "01/25/2026 06:45:26", "2026-04-28T00:51:56.561", "2026-04-06T23:44:55"]
        source = self.frame([["u1", t, "click", "61"] for t in times])
        original = source.copy(deep=True)
        result = clean_events(source)
        self.assertEqual(result.timestamp.tolist(), ["2026-02-28T10:29:30", "2026-01-25T06:45:26", "2026-04-28T00:51:56", "2026-04-06T23:44:55"])
        self.assertEqual(str(result.duration_seconds.dtype), "int64")
        assert_frame_equal(source, original)

    def test_invalid_rows(self):
        good = ["u1", "2026-01-01T12:00:00", "login", "60"]
        rows = [good]
        for column, values in [(0, [None, "", " "]), (1, ["bad", "2026-02-30T12:00:00", "2026-01-01T25:00:00", ""]), (2, ["VIEW", "buy", "unknown", "test", ""]), (3, ["0", "-1", "1.5", "NaN", "inf", "bad", "", str(2**63)])]:
            for value in values:
                row = good.copy()
                row[column] = value
                rows.append(row)
        self.assertEqual(len(clean_events(self.frame(rows))), 1)

    def test_all_valid_types(self):
        result = clean_events(self.frame([["u1", "2026-01-01T00:00:00", event, "1"] for event in VALID_EVENT_TYPES]))
        self.assertEqual(set(result.event_type), VALID_EVENT_TYPES)

    def test_transform_and_features(self):
        clean = clean_events(self.frame([["001", "2026-01-04T23:59:59", "view", "90"], ["002", "2026-01-05T00:00:00", "login", "1"]]))
        transformed = transform_events(clean)
        self.assertEqual(transformed.date.tolist(), ["2026-01-04", "2026-01-05"])
        assert_frame_equal(transformed[clean.columns], clean)
        result = feature_events(transformed)
        assert_frame_equal(result[transformed.columns], transformed)
        self.assertEqual(result.weekday.tolist(), ["Sunday", "Monday"])
        self.assertEqual(result.duration_minutes.tolist(), [1.5, 1/60])
        self.assertEqual(len(result), len(clean))

    def test_empty_and_all_invalid(self):
        for source in [self.frame([]), self.frame([["u", "bad", "view", "0"]])]:
            result = feature_events(transform_events(clean_events(source)))
            self.assertTrue(result.empty)
            self.assertEqual(list(result.columns), list(source.columns) + ["date", "duration_minutes", "weekday"])


if __name__ == "__main__":
    unittest.main()
