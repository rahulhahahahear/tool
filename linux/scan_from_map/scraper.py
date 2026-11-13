"""
Google Maps Scraper Engine
Uses Playwright to automate Chromium/Chrome/Edge to scrape business listings from Google Maps.
"""

import time
import urllib.parse
import re
from typing import Callable, List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


class GoogleMapsScraper:
    def __init__(
        self,
        headless: bool = True,
        preferred_channel: str = "chrome",
        on_progress: Optional[Callable[[str], None]] = None,
        on_item_scraped: Optional[Callable[[Dict[str, Any], int, int], None]] = None,
    ):
        """
        :param headless: Whether to run the browser in headless mode.
        :param preferred_channel: 'chrome' or 'msedge' or None (bundled chromium).
        :param on_progress: Callback function receiving a status message string.
        :param on_item_scraped: Callback function receiving (item_dict, current_idx, total_count).
        """
        self.headless = headless
        self.preferred_channel = preferred_channel
        self.on_progress = on_progress
        self.on_item_scraped = on_item_scraped
        self.stop_requested = False

    def request_stop(self):
        """Signals the scraper to stop as soon as possible."""
        self.stop_requested = True
        self._log("Stopping scraper requested by user...")

    def _log(self, msg: str):
        if self.on_progress:
            self.on_progress(msg)

    def scrape(self, keyword: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Scrapes Google Maps for a given keyword.
        :param keyword: Search query (e.g., 'dentists in Chicago', 'restaurants in London')
        :param max_results: Maximum number of listings to extract.
        :return: List of business dictionaries.
        """
        self.stop_requested = False
        results: List[Dict[str, Any]] = []

        with sync_playwright() as p:
            browser = self._launch_browser(p)
            if not browser:
                self._log("Failed to launch any browser (Chrome, Edge, or Chromium).")
                return results

            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    locale="en-US",
                    viewport={"width": 1280, "height": 850},
                )
                page = context.new_page()

                encoded_query = urllib.parse.quote_plus(keyword)
                url = f"https://www.google.com/maps/search/{encoded_query}"
                self._log(f"Navigating to Google Maps search: {keyword}")

                page.goto(url, wait_until="domcontentloaded", timeout=45000)

                if self.stop_requested:
                    return results

                # Handle cookie/consent modals if present
                self._dismiss_consent(page)

                # Wait for either the search feed or a single place result
                feed_found = self._wait_for_feed(page)
                if not feed_found:
                    # Check if Google Maps directly opened a single place
                    if page.locator('h1.DUwDvf').is_visible():
                        self._log("Direct place page detected. Extracting single result...")
                        item = self._extract_detail_pane(page, fallback_name=keyword)
                        results.append(item)
                        if self.on_item_scraped:
                            self.on_item_scraped(item, 1, 1)
                        return results

                    self._log("No listing feed or places found for this keyword.")
                    return results

                feed = page.locator('div[role="feed"]')

                # Scroll to collect enough cards
                self._log("Loading listings from search feed...")
                self._scroll_feed(page, feed, max_results)

                if self.stop_requested:
                    return results

                # Get all place cards
                cards = page.locator('div.Nv2PK').all()
                total_found = len(cards)
                target_count = min(max_results, total_found)
                self._log(f"Found {total_found} places in search results. Extracting details for {target_count} items...")

                for i in range(target_count):
                    if self.stop_requested:
                        self._log("Scraping stopped by user.")
                        break

                    card = page.locator('div.Nv2PK').nth(i)
                    link = card.locator('a.hfpxzc').first

                    # Basic fallback name from aria-label
                    place_name = link.get_attribute("aria-label") or f"Place #{i+1}"
                    self._log(f"[{i+1}/{target_count}] Extracting: {place_name}")

                    try:
                        # Force click the card link to open detail pane
                        link.click(force=True, timeout=6000)
                    except Exception:
                        try:
                            card.click(force=True, timeout=4000)
                        except Exception:
                            pass

                    # Allow detail panel to populate
                    try:
                        page.wait_for_selector('h1.DUwDvf', timeout=4000)
                    except Exception:
                        pass
                    page.wait_for_timeout(900)

                    # Extract all fields from the active detail pane
                    item = self._extract_detail_pane(page, fallback_name=place_name)

                    # Fallbacks from the card if detail panel missed category/rating
                    self._apply_card_fallbacks(card, item)

                    results.append(item)
                    if self.on_item_scraped:
                        self.on_item_scraped(item, i + 1, target_count)

                    # Small delay to keep browser responsive
                    time.sleep(0.3)

            finally:
                try:
                    browser.close()
                except Exception:
                    pass

        self._log(f"Scraping completed! Extracted {len(results)} business listings.")
        return results

    def _launch_browser(self, p) -> Optional[Browser]:
        """Tries to launch preferred channel, then fallbacks for Linux."""
        candidates = []
        if self.preferred_channel in ("chromium", "chrome", "msedge"):
            candidates.append(self.preferred_channel)
        candidates.extend(["chromium", "chrome"])

        for channel in candidates:
            try:
                self._log(f"Launching browser using '{channel}'...")
                return p.chromium.launch(channel=channel, headless=self.headless)
            except Exception:
                continue

        # Try bundled chromium
        try:
            self._log("Launching bundled Chromium...")
            return p.chromium.launch(headless=self.headless)
        except Exception:
            return None

    def _dismiss_consent(self, page: Page):
        """Dismisses Google cookie/consent dialog if shown."""
        try:
            accept_btn = page.locator('button[aria-label*="Accept all"], form[action*="consent"] button').first
            if accept_btn.is_visible(timeout=2500):
                accept_btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

    def _wait_for_feed(self, page: Page) -> bool:
        """Waits for search feed or returns False if not found."""
        try:
            page.wait_for_selector('div[role="feed"]', timeout=12000)
            return True
        except Exception:
            return False

    def _scroll_feed(self, page: Page, feed, max_results: int):
        """Scrolls feed down until target results reached or end of list."""
        last_count = 0
        stuck_cycles = 0

        while not self.stop_requested:
            current_cards = page.locator('div.Nv2PK').count()
            if current_cards >= max_results:
                break

            self._log(f"Loaded {current_cards}/{max_results} listings, scrolling for more...")
            feed.evaluate("el => el.scrollTop = el.scrollHeight")
            page.wait_for_timeout(1600)

            new_count = page.locator('div.Nv2PK').count()
            if new_count == last_count:
                stuck_cycles += 1
                if stuck_cycles >= 4:
                    # Feed stopped growing or reached end
                    break
            else:
                stuck_cycles = 0
                last_count = new_count

            # Check if Google reached end of list
            if "reached the end of the list" in page.content():
                break

    def _extract_detail_pane(self, page: Page, fallback_name: str = "") -> Dict[str, Any]:
        """Extracts business details from the active side panel."""
        data = {
            "name": fallback_name,
            "phone": "",
            "website": "",
            "rating": "",
            "reviews": "",
            "category": "",
            "address": "",
            "hours": "",
            "url": page.url,
            "notes": ""
        }

        # 1. Name
        try:
            title_el = page.locator('h1.DUwDvf').first
            if title_el.is_visible():
                t = title_el.inner_text().strip()
                if t and t.lower() != "results":
                    data["name"] = t
        except Exception:
            pass

        # 2. Phone
        try:
            phone_el = page.locator('button[data-item-id^="phone:"]').first
            if phone_el.is_visible():
                raw = phone_el.get_attribute("aria-label") or phone_el.inner_text()
                data["phone"] = raw.replace("Phone: ", "").strip()
            else:
                # Fallback search for phone pattern in action buttons
                phone_btns = page.locator('button[aria-label*="Phone"]').all()
                if phone_btns:
                    raw = phone_btns[0].get_attribute("aria-label") or phone_btns[0].inner_text()
                    data["phone"] = raw.replace("Phone: ", "").strip()
        except Exception:
            pass

        # 3. Website
        try:
            web_el = page.locator('a[data-item-id="authority"]').first
            if web_el.is_visible():
                data["website"] = web_el.get_attribute("href") or ""
            else:
                web_links = page.locator('a[aria-label*="Website:"]').all()
                if web_links:
                    data["website"] = web_links[0].get_attribute("href") or ""
        except Exception:
            pass

        # 4. Address
        try:
            addr_el = page.locator('button[data-item-id="address"]').first
            if addr_el.is_visible():
                raw = addr_el.get_attribute("aria-label") or addr_el.inner_text()
                data["address"] = raw.replace("Address: ", "").strip()
            else:
                addr_btns = page.locator('button[aria-label*="Address:"]').all()
                if addr_btns:
                    raw = addr_btns[0].get_attribute("aria-label") or addr_btns[0].inner_text()
                    data["address"] = raw.replace("Address: ", "").strip()
        except Exception:
            pass

        # 5. Rating
        try:
            rating_el = page.locator('div.F7nice span[aria-hidden="true"]').first
            if rating_el.is_visible():
                data["rating"] = rating_el.inner_text().strip()
            else:
                # Try finding rating in aria-label
                stars_el = page.locator('span[aria-label*="stars"]').first
                if stars_el.is_visible():
                    m = re.search(r'([\d.]+)\s*stars', stars_el.get_attribute("aria-label") or "")
                    if m:
                        data["rating"] = m.group(1)
        except Exception:
            pass

        # 6. Reviews count
        try:
            rev_el = page.locator('div.F7nice span[aria-label*="review"]').first
            if rev_el.is_visible():
                raw = rev_el.get_attribute("aria-label") or rev_el.inner_text()
                clean = re.sub(r'[^\d,]', '', raw)
                data["reviews"] = clean
            else:
                # Check for reviews pattern in header
                header_text = page.locator('div.TIHn2').first.inner_text()
                m = re.search(r'\(?([\d,]+)\)?\s*(?:reviews)?', header_text)
                if m:
                    data["reviews"] = m.group(1).replace("(", "").replace(")", "")
        except Exception:
            pass

        # 7. Category
        try:
            cat_el = page.locator('button.DkEaL').first
            if cat_el.is_visible():
                data["category"] = cat_el.inner_text().strip()
            else:
                cat_btns = page.locator('button[jsaction*="category"]').all()
                if cat_btns:
                    data["category"] = cat_btns[0].inner_text().strip()
        except Exception:
            pass

        # 8. Hours
        try:
            hours_el = page.locator('button[data-item-id="oh"]').first
            if hours_el.is_visible():
                raw = hours_el.get_attribute("aria-label") or hours_el.inner_text()
                data["hours"] = raw.replace("· See more hours", "").strip()
        except Exception:
            pass

        return data

    def _apply_card_fallbacks(self, card, item: Dict[str, Any]):
        """Uses card text to fill missing category or rating if detail panel missed it."""
        try:
            card_text = card.inner_text()
            lines = [line.strip() for line in card_text.split("\n") if line.strip()]

            # Fallback category
            if not item["category"]:
                for line in lines:
                    if "·" in line:
                        parts = line.split("·")
                        cand = parts[0].strip()
                        if cand and not any(ch.isdigit() for ch in cand) and len(cand) < 40:
                            item["category"] = cand
                            break

            # Fallback rating
            if not item["rating"]:
                for line in lines:
                    if re.match(r'^[1-5]\.\d$', line):
                        item["rating"] = line
                        break

            # Fallback address
            if not item["address"]:
                for line in lines:
                    if "·" in line:
                        parts = line.split("·")
                        if len(parts) > 1:
                            cand_addr = parts[-1].strip()
                            if cand_addr and any(ch.isdigit() for ch in cand_addr):
                                item["address"] = cand_addr
                                break
        except Exception:
            pass
