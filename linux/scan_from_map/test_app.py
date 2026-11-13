"""
Test suite for Google Maps Scraper and Manager (scan_from_map module)
"""

import unittest
import os
import csv

try:
    from .exporter import export_to_csv, export_to_txt
except (ImportError, ValueError):
    from exporter import export_to_csv, export_to_txt


class TestScanFromMapTool(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            {
                "name": "Alpha Cafe",
                "phone": "+1 212-555-0101",
                "website": "https://alphacafe.example.com",
                "rating": "4.8",
                "reviews": "1,250",
                "category": "Coffee Shop",
                "address": "123 Main St, New York, NY 10001",
                "hours": "Open ⋅ Closes 8 PM",
                "url": "https://maps.google.com/?q=Alpha+Cafe",
                "notes": "Great prospect"
            },
            {
                "name": "Beta Bistro & Bakery",
                "phone": "+1 212-555-0102",
                "website": "https://betabistro.example.com",
                "rating": "4.2",
                "reviews": "430",
                "category": "Bakery",
                "address": "456 5th Ave, New York, NY 10002",
                "hours": "Closed ⋅ Opens 7 AM",
                "url": "https://maps.google.com/?q=Beta+Bistro",
                "notes": "Follow up next week"
            }
        ]
        self.test_csv = "unit_test_output.csv"
        self.test_txt = "unit_test_output.txt"

    def tearDown(self):
        for f in (self.test_csv, self.test_txt):
            if os.path.exists(f):
                os.remove(f)

    def test_export_to_csv(self):
        export_to_csv(self.sample_data, self.test_csv)
        self.assertTrue(os.path.exists(self.test_csv))

        with open(self.test_csv, mode="r", encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            self.assertEqual(reader[0]["Name"], "Alpha Cafe")
            self.assertEqual(reader[0]["Phone"], "+1 212-555-0101")
            self.assertEqual(reader[0]["Website"], "https://alphacafe.example.com")
            self.assertEqual(reader[0]["Rating"], "4.8")
            self.assertEqual(reader[0]["Reviews"], "1,250")
            self.assertEqual(reader[0]["Category"], "Coffee Shop")
            self.assertEqual(reader[0]["Address"], "123 Main St, New York, NY 10001")
            self.assertEqual(reader[0]["Hours"], "Open ⋅ Closes 8 PM")
            self.assertEqual(reader[0]["Notes"], "Great prospect")

            self.assertEqual(reader[1]["Name"], "Beta Bistro & Bakery")
            self.assertEqual(reader[1]["Phone"], "+1 212-555-0102")

    def test_export_to_txt(self):
        export_to_txt(self.sample_data, self.test_txt, keyword="test cafes")
        self.assertTrue(os.path.exists(self.test_txt))

        with open(self.test_txt, mode="r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("GOOGLE MAPS SCRAPED DATA REPORT", content)
            self.assertIn("Search Query: test cafes", content)
            self.assertIn("Total Businesses: 2", content)
            self.assertIn("[1] Alpha Cafe", content)
            self.assertIn("+1 212-555-0101", content)
            self.assertIn("https://alphacafe.example.com", content)
            self.assertIn("4.8 (1,250 reviews)", content)
            self.assertIn("123 Main St, New York, NY 10001", content)
            self.assertIn("[2] Beta Bistro & Bakery", content)

    def test_data_editing_logic(self):
        records = list(self.sample_data)
        records[0]["phone"] = "+1 212-999-8888"
        records[0]["name"] = "Alpha Cafe (Updated)"
        self.assertEqual(records[0]["phone"], "+1 212-999-8888")
        self.assertEqual(records[0]["name"], "Alpha Cafe (Updated)")

        new_item = {
            "name": "Gamma Roasters",
            "phone": "+1 212-555-0103",
            "website": "https://gamma.example.com",
            "rating": "4.9",
            "reviews": "85",
            "category": "Coffee Roasters",
            "address": "789 Broadway, NY",
            "hours": "Open",
            "url": "",
            "notes": "New addition"
        }
        records.append(new_item)
        self.assertEqual(len(records), 3)

        records.pop(1)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["name"], "Alpha Cafe (Updated)")
        self.assertEqual(records[1]["name"], "Gamma Roasters")


if __name__ == "__main__":
    unittest.main()
