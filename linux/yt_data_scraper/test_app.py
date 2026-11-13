"""
Unit test suite for YouTube Data Scraper
"""

import unittest
import os
import csv

try:
    from .scraper import parse_subscribers_to_number
    from .exporter import export_to_csv, export_to_txt
except (ImportError, ValueError):
    from scraper import parse_subscribers_to_number
    from exporter import export_to_csv, export_to_txt


class TestYouTubeDataScraper(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            {
                "name": "Tech Reviews Hub",
                "handle": "@techreviews",
                "subscribers": "1.2M subscribers",
                "subscribers_count": 1200000,
                "videos_count": "540 videos",
                "contact": "contact@techreviews.com",
                "website": "https://techreviews.com",
                "video_title": "Top 10 Laptops of 2026",
                "video_url": "https://youtube.com/watch?v=sample1",
                "channel_url": "https://youtube.com/@techreviews",
                "description": "Tech reviews and guides.",
            },
            {
                "name": "Python Mastery",
                "handle": "@pythonmastery",
                "subscribers": "45K subscribers",
                "subscribers_count": 45000,
                "videos_count": "120 videos",
                "contact": "info@pythonmastery.org",
                "website": "https://pythonmastery.org",
                "video_title": "Python Async Tutorial",
                "video_url": "https://youtube.com/watch?v=sample2",
                "channel_url": "https://youtube.com/@pythonmastery",
                "description": "Learn python easily.",
            }
        ]
        self.test_csv = "unit_test_yt.csv"
        self.test_txt = "unit_test_yt.txt"

    def tearDown(self):
        for f in (self.test_csv, self.test_txt):
            if os.path.exists(f):
                os.remove(f)

    def test_subscriber_parsing(self):
        self.assertEqual(parse_subscribers_to_number("1.5M subscribers"), 1500000)
        self.assertEqual(parse_subscribers_to_number("750K subscribers"), 750000)
        self.assertEqual(parse_subscribers_to_number("2.25M"), 2250000)
        self.assertEqual(parse_subscribers_to_number("500 subscribers"), 500)
        self.assertEqual(parse_subscribers_to_number(""), 0)
        self.assertEqual(parse_subscribers_to_number(None), 0)

    def test_export_all_columns_csv(self):
        export_to_csv(self.sample_data, self.test_csv)
        self.assertTrue(os.path.exists(self.test_csv))

        with open(self.test_csv, "r", encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            self.assertEqual(reader[0]["Channel Name"], "Tech Reviews Hub")
            self.assertEqual(reader[0]["Contact / Email"], "contact@techreviews.com")
            self.assertEqual(reader[0]["Subscribers"], "1.2M subscribers")
            self.assertEqual(reader[1]["Channel Name"], "Python Mastery")

    def test_export_selected_columns_csv(self):
        selected = ["Channel Name", "Contact / Email", "Website / Links"]
        export_to_csv(self.sample_data, self.test_csv, selected_columns=selected)

        with open(self.test_csv, "r", encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            # Only selected columns should be present in headers
            self.assertEqual(list(reader[0].keys()), selected)
            self.assertEqual(reader[0]["Channel Name"], "Tech Reviews Hub")
            self.assertEqual(reader[0]["Contact / Email"], "contact@techreviews.com")

    def test_export_txt(self):
        export_to_txt(self.sample_data, self.test_txt, keyword="tech")
        self.assertTrue(os.path.exists(self.test_txt))

        with open(self.test_txt, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("YOUTUBE DATA SCRAPER REPORT", content)
            self.assertIn("Tech Reviews Hub", content)
            self.assertIn("@techreviews", content)
            self.assertIn("contact@techreviews.com", content)
            self.assertIn("Python Mastery", content)


if __name__ == "__main__":
    unittest.main()
