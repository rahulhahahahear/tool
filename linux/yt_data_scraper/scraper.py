"""
YouTube Data Scraper Engine
Automates Playwright to search YouTube, scrape channel information, subscriber counts,
contact details, website links, and video source data.
"""

import time
import urllib.parse
import re
from typing import Callable, List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


def parse_subscribers_to_number(sub_str: str) -> int:
    """Converts subscriber string like '1.56M subscribers' or '750K' to integer."""
    if not sub_str:
        return 0
    s = sub_str.lower().replace("subscribers", "").replace("subscriber", "").strip()
    try:
        if "m" in s:
            val = float(s.replace("m", "").strip())
            return int(val * 1_000_000)
        elif "k" in s:
            val = float(s.replace("k", "").strip())
            return int(val * 1_000)
        elif "b" in s:
            val = float(s.replace("b", "").strip())
            return int(val * 1_000_000_000)
        else:
            clean = re.sub(r"[^\d.]", "", s)
            return int(float(clean)) if clean else 0
    except Exception:
        return 0


def extract_emails(text: str) -> List[str]:
    """Finds email addresses in text."""
    if not text:
        return []
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(pattern, text)
    # Filter common non-email false positives
    return list({e.lower() for e in matches if not e.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))})


def decode_youtube_redirect(redirect_url: str) -> str:
    """Decodes actual external URL from youtube.com/redirect?q=..."""
    if not redirect_url:
        return ""
    if "youtube.com/redirect" in redirect_url and "q=" in redirect_url:
        try:
            parsed = urllib.parse.urlparse(redirect_url)
            params = urllib.parse.parse_qs(parsed.query)
            if "q" in params:
                return urllib.parse.unquote(params["q"][0])
        except Exception:
            pass
    return redirect_url


class YouTubeDataScraper:
    def __init__(
        self,
        headless: bool = True,
        preferred_channel: str = "chrome",
        fetch_channel_details: bool = True,
        on_progress: Optional[Callable[[str], None]] = None,
        on_item_scraped: Optional[Callable[[Dict[str, Any], int, int], None]] = None,
    ):
        self.headless = headless
        self.preferred_channel = preferred_channel
        self.fetch_channel_details = fetch_channel_details
        self.on_progress = on_progress
        self.on_item_scraped = on_item_scraped
        self.stop_requested = False

    def request_stop(self):
        self.stop_requested = True
        self._log("Stopping YouTube scraper requested by user...")

    def _log(self, msg: str):
        if self.on_progress:
            self.on_progress(msg)

    def scrape(
        self,
        keyword: str,
        max_results: int = 15,
        search_mode: str = "both",  # 'channels', 'videos', or 'both'
        min_subscribers: int = 0,
        max_subscribers: int = 0
    ) -> List[Dict[str, Any]]:
        self.stop_requested = False
        results: List[Dict[str, Any]] = []
        seen_channels = set()

        with sync_playwright() as p:
            browser = self._launch_browser(p)
            if not browser:
                self._log("Failed to launch browser engine.")
                return results

            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    locale="en-US",
                    viewport={"width": 1280, "height": 850},
                )
                page = context.new_page()

                # Step 1: Channels Search
                if search_mode in ("channels", "both") and not self.stop_requested:
                    self._scrape_channels_search(page, keyword, max_results, results, seen_channels)

                # Step 2: Videos Search (if requested and we still need items)
                if search_mode in ("videos", "both") and len(results) < max_results and not self.stop_requested:
                    remaining = max_results - len(results)
                    self._scrape_videos_search(page, keyword, remaining, results, seen_channels)

                # Step 3: Fetch deep details for channels (About, Email, External Links)
                if self.fetch_channel_details and not self.stop_requested:
                    self._enrich_channel_details(page, results)

                # Apply subscriber filters if specified
                if min_subscribers > 0 or max_subscribers > 0:
                    filtered = []
                    for item in results:
                        sub_count = item.get("subscribers_count", 0)
                        if min_subscribers > 0 and sub_count < min_subscribers:
                            continue
                        if max_subscribers > 0 and sub_count > max_subscribers:
                            continue
                        filtered.append(item)
                    results = filtered

            finally:
                try:
                    browser.close()
                except Exception:
                    pass

        self._log(f"Scraping completed! Extracted {len(results)} YouTube listings.")
        return results

    def _launch_browser(self, p) -> Optional[Browser]:
        candidates = []
        if self.preferred_channel in ("chrome", "msedge"):
            candidates.append(self.preferred_channel)
            candidates.append("msedge" if self.preferred_channel == "chrome" else "chrome")
        elif self.preferred_channel == "chromium":
            candidates.extend(["chromium", "chrome"])
        else:
            candidates.extend(["chrome", "msedge", "chromium"])

        for channel in candidates:
            try:
                self._log(f"Launching browser using '{channel}'...")
                return p.chromium.launch(channel=channel, headless=self.headless)
            except Exception:
                continue

        try:
            self._log("Launching bundled Chromium...")
            return p.chromium.launch(headless=self.headless)
        except Exception:
            return None

    def _dismiss_consent(self, page: Page):
        try:
            btn = page.locator('button[aria-label*="Accept"], button:has-text("Accept all"), form[action*="consent"] button').first
            if btn.is_visible(timeout=2500):
                btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

    def _scrape_channels_search(self, page: Page, keyword: str, limit: int, results: list, seen: set):
        encoded = urllib.parse.quote_plus(keyword)
        # sp=EgIQAg%253D%253D filters Type: Channel
        url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgIQAg%253D%253D"
        self._log(f"Searching YouTube channels for '{keyword}'...")

        page.goto(url, wait_until="domcontentloaded", timeout=40000)
        self._dismiss_consent(page)

        try:
            page.wait_for_selector('ytd-channel-renderer', timeout=12000)
        except Exception:
            self._log("No direct channel cards found.")
            return

        # Scroll to load enough channels
        last_count = 0
        while len(page.locator('ytd-channel-renderer').all()) < limit and not self.stop_requested:
            page.evaluate("window.scrollBy(0, 1500)")
            page.wait_for_timeout(1400)
            cur_count = len(page.locator('ytd-channel-renderer').all())
            if cur_count == last_count:
                break
            last_count = cur_count

        cards = page.locator('ytd-channel-renderer').all()
        target = min(limit, len(cards))

        for i in range(target):
            if self.stop_requested or len(results) >= limit:
                break

            card = cards[i]
            try:
                title_el = card.locator('#channel-title, #text').first
                name = title_el.inner_text().strip() if title_el.is_visible() else f"Channel #{i+1}"

                link_el = card.locator('a#main-link').first
                raw_href = link_el.get_attribute("href") if link_el.is_visible() else ""
                ch_url = f"https://www.youtube.com{raw_href}" if raw_href and not raw_href.startswith("http") else raw_href

                if not ch_url or ch_url in seen:
                    continue
                seen.add(ch_url)

                # Extract handle / subscriber / video count from card text
                card_text = card.inner_text()
                lines = [l.strip() for l in card_text.split("\n") if l.strip()]

                handle = ""
                sub_text = ""
                vid_count = ""
                desc = ""

                for line in lines:
                    if line.startswith("@"):
                        handle = line.split("•")[0].strip()
                    if "subscriber" in line.lower():
                        sub_text = line
                    elif "video" in line.lower():
                        vid_count = line

                desc_el = card.locator('#description-text').first
                if desc_el.is_visible():
                    desc = desc_el.inner_text().strip()

                sub_num = parse_subscribers_to_number(sub_text)

                item = {
                    "name": name,
                    "handle": handle,
                    "subscribers": sub_text,
                    "subscribers_count": sub_num,
                    "videos_count": vid_count,
                    "contact": "",
                    "website": "",
                    "video_title": "",
                    "video_url": "",
                    "channel_url": ch_url,
                    "description": desc,
                }
                results.append(item)
                if self.on_item_scraped:
                    self.on_item_scraped(item, len(results), limit)

            except Exception as e:
                continue

    def _scrape_videos_search(self, page: Page, keyword: str, limit: int, results: list, seen: set):
        encoded = urllib.parse.quote_plus(keyword)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        self._log(f"Searching top YouTube videos for '{keyword}'...")

        page.goto(url, wait_until="domcontentloaded", timeout=40000)
        self._dismiss_consent(page)

        try:
            page.wait_for_selector('ytd-video-renderer', timeout=12000)
        except Exception:
            return

        while len(page.locator('ytd-video-renderer').all()) < limit and not self.stop_requested:
            page.evaluate("window.scrollBy(0, 1500)")
            page.wait_for_timeout(1400)

        v_cards = page.locator('ytd-video-renderer').all()

        for card in v_cards:
            if self.stop_requested or len(results) >= limit:
                break

            try:
                # Video Info
                title_el = card.locator('#video-title').first
                if not title_el.is_visible():
                    continue

                v_title = title_el.inner_text().strip()
                raw_v_url = title_el.get_attribute("href") or ""
                v_url = f"https://www.youtube.com{raw_v_url}" if raw_v_url and not raw_v_url.startswith("http") else raw_v_url

                # Channel Info
                ch_el = card.locator('#channel-name a, #channel-info a').first
                if not ch_el.is_visible():
                    continue

                ch_name = ch_el.inner_text().strip()
                raw_ch_url = ch_el.get_attribute("href") or ""
                ch_url = f"https://www.youtube.com{raw_ch_url}" if raw_ch_url and not raw_ch_url.startswith("http") else raw_ch_url

                if not ch_url or ch_url in seen:
                    continue
                seen.add(ch_url)

                item = {
                    "name": ch_name,
                    "handle": "",
                    "subscribers": "",
                    "subscribers_count": 0,
                    "videos_count": "",
                    "contact": "",
                    "website": "",
                    "video_title": v_title,
                    "video_url": v_url,
                    "channel_url": ch_url,
                    "description": "",
                }
                results.append(item)
                if self.on_item_scraped:
                    self.on_item_scraped(item, len(results), limit)

            except Exception:
                continue

    def _enrich_channel_details(self, page: Page, results: list):
        """Visits channel's about URL to extract emails, websites, exact subscriber count and bio."""
        total = len(results)
        self._log(f"Extracting contact details & links for {total} channels...")

        for idx, item in enumerate(results, 1):
            if self.stop_requested:
                break

            ch_url = item.get("channel_url")
            if not ch_url:
                continue

            about_url = f"{ch_url.rstrip('/')}/about"
            self._log(f"[{idx}/{total}] Checking About info for: {item.get('name')}")

            try:
                page.goto(about_url, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(1500)

                # Channel Handle & Subscribers from Header if missing
                header_text = ""
                try:
                    header_el = page.locator('#channel-header, #page-header, ytd-c4-tabbed-header-renderer').first
                    if header_el.is_visible():
                        header_text = header_el.inner_text()
                except Exception:
                    pass

                if not item["subscribers"] and header_text:
                    m = re.search(r'([\d.]+[KkMmBb]?\s*subscribers)', header_text, re.IGNORECASE)
                    if m:
                        item["subscribers"] = m.group(1)
                        item["subscribers_count"] = parse_subscribers_to_number(m.group(1))

                if not item["handle"] and header_text:
                    m = re.search(r'(@[a-zA-Z0-9_.-]+)', header_text)
                    if m:
                        item["handle"] = m.group(1)

                if not item["videos_count"] and header_text:
                    m = re.search(r'([\d,]+\s*videos)', header_text, re.IGNORECASE)
                    if m:
                        item["videos_count"] = m.group(1)

                # Page Body text for email discovery
                body_text = page.locator('body').inner_text()
                emails = extract_emails(body_text)
                if emails:
                    item["contact"] = ", ".join(emails[:2])

                # Extract External Links / Websites
                redirect_links = page.locator('a[href*="redirect"]').all()
                valid_links = []
                for r_link in redirect_links[:8]:
                    raw_href = r_link.get_attribute("href") or ""
                    decoded = decode_youtube_redirect(raw_href)
                    if decoded and "google.com" not in decoded and "youtube.com" not in decoded:
                        valid_links.append(decoded)

                if valid_links:
                    item["website"] = valid_links[0]
                    # If multiple, store in website or description
                    if len(valid_links) > 1 and not item.get("contact"):
                        socials = [l for l in valid_links[1:] if any(s in l for s in ("twitter", "x.com", "instagram", "linkedin", "facebook", "github"))]
                        if socials:
                            item["contact"] = socials[0]

                # Update callback
                if self.on_item_scraped:
                    self.on_item_scraped(item, idx, total)

            except Exception:
                continue
