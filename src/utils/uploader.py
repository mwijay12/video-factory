# -*- coding: utf-8 -*-
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Set PYTHONPATH
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))


class SocialUploader:
    """
    Automated short-form video publisher using Playwright.
    Uses persistent browser profiles to maintain login state.
    """

    def __init__(self, platform="youtube"):
        self.platform = platform.lower()
        self.profiles_base = BASE_DIR / "assets" / "browser_profiles"
        self.profile_dir = self.profiles_base / self.platform
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def _get_browser_context(self, playwright, headless=True):
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--window-size=1280,900",
            "--disable-dev-shm-usage",
        ]
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=args,
            channel="chrome"
        )
        return context

    # ----------------------------------------------------------------
    # YOUTUBE SHORTS UPLOADER
    # ----------------------------------------------------------------
    def upload_youtube_shorts(self, video_path, title, description="", thumbnail_path=None):
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            print(f"[YouTube] Error: Video file not found: {video_path}")
            return False

        print(f"\n[YouTube Uploader] Preparing upload: {video_path.name}")

        with sync_playwright() as p:
            # ── Step 1: Try headless first to check login ──────────────
            print("  [1/7] Opening browser profile (headless)...")
            context = self._get_browser_context(p, headless=True)
            page = context.new_page()

            try:
                page.goto("https://studio.youtube.com", timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)

                # Check login state – look for account avatar or top-bar menu
                is_logged_in = self._is_youtube_logged_in(page)

                if not is_logged_in:
                    print("  [!] Session expired or not logged in. Launching visible browser...")
                    context.close()

                    # Reopen headfully so user can log in
                    context = self._get_browser_context(p, headless=False)
                    page = context.new_page()
                    page.goto("https://studio.youtube.com", timeout=60000, wait_until="domcontentloaded")

                    print("\n" + "=" * 70)
                    print("  ACTION REQUIRED: Please log in to YouTube in the browser window.")
                    print("  The script will continue automatically after you reach Studio.")
                    print("=" * 70 + "\n")

                    # Wait up to 10 minutes for login
                    deadline = time.time() + 600
                    while time.time() < deadline:
                        if self._is_youtube_logged_in(page):
                            break
                        page.wait_for_timeout(3000)
                    else:
                        print("  [ERROR] Login timeout (10 min). Upload aborted.")
                        context.close()
                        return False

                    print("  Login confirmed! Saving session. Please wait...")
                    page.wait_for_timeout(4000)

                # ── Step 2: Click Upload / Create ──────────────────────
                print("  [2/7] Opening upload dialog...")
                self._click_upload_button(page)

                # ── Step 3: Set the video file ─────────────────────────
                print("  [3/7] Selecting video file...")
                # The file dialog input is hidden inside #content
                with page.expect_file_chooser() as fc_info:
                    # Click the visible upload area
                    try:
                        page.click("#select-files-button", timeout=10000)
                    except Exception:
                        # Fallback: click the drop area
                        page.click("ytcp-uploads-dialog #content", timeout=10000)
                file_chooser = fc_info.value
                file_chooser.set_files(str(video_path))

                # ── Step 4: Wait for Details panel and fill metadata ───
                print("  [4/7] Waiting for Details panel...")
                page.wait_for_selector("#title-textarea", timeout=60000)
                page.wait_for_timeout(2000)

                print("  [4/7] Writing title...")
                title_box = page.locator("#title-textarea #textbox").first
                title_box.click()
                page.keyboard.press("Control+A")
                page.keyboard.type(title[:100])

                if description:
                    print("  [4/7] Writing description...")
                    desc_box = page.locator("#description-textarea #textbox").first
                    desc_box.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.type(description[:5000])

                # ── Step 5: Upload thumbnail (optional) ────────────────
                if thumbnail_path:
                    thumb_path_obj = Path(thumbnail_path).resolve()
                    if thumb_path_obj.exists():
                        print(f"  [5/7] Uploading thumbnail...")
                        try:
                            # Click the custom thumbnail button to reveal the upload input
                            thumb_btn = page.locator("ytcp-thumbnails-compact-editor-uploader, #still-images-button").first
                            thumb_btn.click(timeout=8000)
                            page.wait_for_timeout(1000)
                            # Set the file on the hidden input
                            thumb_input = page.locator("input[type=file][accept*='image']").first
                            thumb_input.set_input_files(str(thumb_path_obj))
                            page.wait_for_timeout(3000)
                            print("  Thumbnail uploaded.")
                        except Exception as te:
                            print(f"  [Warning] Thumbnail upload skipped: {te}")
                    else:
                        print(f"  [Warning] Thumbnail file not found: {thumbnail_path}")

                # ── Step 6: Mark 'Not Made for Kids' ──────────────────
                print("  [6/7] Configuring audience settings...")
                try:
                    # Wait for the radio group to be visible
                    kids_selector = "tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MADE_FOR_KIDS']"
                    page.wait_for_selector(kids_selector, timeout=15000)
                    kids_radio = page.locator(kids_selector).first
                    if not kids_radio.is_checked():
                        kids_radio.click()
                    page.wait_for_timeout(1000)
                except Exception as ke:
                    print(f"  [Warning] Could not set audience: {ke} — continuing.")

                # ── Step 7: Navigate through wizard to Visibility ──────
                print("  [7/7] Navigating wizard steps...")
                self._click_next_buttons(page, steps=3)

                # Set Visibility to PUBLIC
                print("  Setting visibility to PUBLIC...")
                try:
                    public_selector = "tp-yt-paper-radio-button[name='PUBLIC']"
                    page.wait_for_selector(public_selector, timeout=20000)
                    public_radio = page.locator(public_selector).first
                    if not public_radio.is_checked():
                        public_radio.click()
                    page.wait_for_timeout(1500)
                except Exception as ve:
                    print(f"  [Warning] Could not set PUBLIC visibility: {ve}")

                # Click Publish / Save
                print("  Clicking Publish button...")
                try:
                    # Wait for upload to finish before publishing
                    self._wait_for_upload_complete(page)
                    publish_btn = page.locator("#done-button").first
                    publish_btn.click()
                    page.wait_for_timeout(8000)
                except Exception as pe:
                    print(f"  [Warning] Publish click issue: {pe}")

                print("\n  ✅ [SUCCESS] YouTube upload completed successfully!")
                context.close()
                return True

            except Exception as e:
                print(f"\n  ❌ [ERROR] YouTube upload failed: {e}")
                # Take a screenshot for debugging
                try:
                    ss_path = BASE_DIR / "output" / "debug_screenshot_yt.png"
                    ss_path.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(ss_path))
                    print(f"  Debug screenshot saved: {ss_path}")
                except Exception:
                    pass
                try:
                    context.close()
                except Exception:
                    pass
                return False

    def _is_youtube_logged_in(self, page):
        """Check if user is logged into YouTube Studio."""
        try:
            # Multiple possible indicators of being logged in
            for selector in [
                "#avatar-btn",           # Account icon top right
                "ytd-topbar-logo-renderer",  # Studio logo (only shown when logged in)
                "#create-icon",          # Create button
                "ytcp-navbar",           # Studio nav bar
            ]:
                try:
                    el = page.wait_for_selector(selector, timeout=4000)
                    if el:
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def _click_upload_button(self, page):
        """Click the Upload / Create button in YouTube Studio."""
        # Try several known selectors for the upload entry point
        upload_selectors = [
            "#create-icon",
            "ytcp-button#create-icon",
            "button[aria-label='Create']",
            "#upload-icon",
        ]
        for sel in upload_selectors:
            try:
                page.wait_for_selector(sel, timeout=8000)
                page.click(sel)
                page.wait_for_timeout(1500)
                break
            except Exception:
                continue

        # Now look for "Upload videos" in the dropdown menu
        upload_menu_selectors = [
            "tp-yt-paper-item:has-text('Upload videos')",
            "paper-item:has-text('Upload videos')",
            "#text-item-0",   # first menu item in create menu
            "ytcp-ve:has-text('Upload')",
        ]
        for sel in upload_menu_selectors:
            try:
                page.wait_for_selector(sel, timeout=6000)
                page.click(sel)
                page.wait_for_timeout(2000)
                return
            except Exception:
                continue

        print("  [Warning] Could not find upload menu item by text – trying keyboard shortcut")
        # Fallback: navigate directly to upload URL
        page.goto("https://www.youtube.com/upload", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

    def _click_next_buttons(self, page, steps=3):
        """Click Next button through wizard steps."""
        for step_i in range(steps):
            try:
                # The Next button in Studio upload wizard
                next_btn_selectors = [
                    "#next-button",
                    "ytcp-button#next-button",
                    "button:has-text('Next')",
                ]
                clicked = False
                for sel in next_btn_selectors:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=8000):
                            btn.click()
                            page.wait_for_timeout(1500)
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    print(f"  [Warning] Could not click Next at step {step_i + 1}")
            except Exception as e:
                print(f"  [Warning] Next button step {step_i+1}: {e}")

    def _wait_for_upload_complete(self, page, timeout_secs=300):
        """Wait until the video file finishes uploading to YouTube servers."""
        print("  Waiting for video upload to complete...")
        deadline = time.time() + timeout_secs
        while time.time() < deadline:
            try:
                # Check progress text; when upload completes it shows processing
                progress_text = page.locator("ytcp-video-upload-progress").inner_text(timeout=3000)
                if "Upload complete" in progress_text or "Processing" in progress_text or "%" not in progress_text:
                    print(f"  Upload status: {progress_text.strip()[:60]}")
                    return
            except Exception:
                pass
            page.wait_for_timeout(3000)
        print("  [Warning] Upload progress check timed out — attempting to publish anyway.")

    # ----------------------------------------------------------------
    # TIKTOK UPLOADER
    # ----------------------------------------------------------------
    def upload_tiktok(self, video_path, caption):
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            print(f"Error: Video file not found: {video_path}")
            return False

        print(f"\n[TikTok Uploader] Initializing upload for: {video_path.name}...")

        with sync_playwright() as p:
            context = self._get_browser_context(p, headless=True)
            page = context.new_page()

            try:
                page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                # Detect login requirements
                is_logged_in = False
                try:
                    page.wait_for_selector("iframe", timeout=12000)
                    is_logged_in = True
                except Exception:
                    pass

                if not is_logged_in:
                    print("  [ALERT] TikTok login required! Launching interactive window...")
                    context.close()

                    context = self._get_browser_context(p, headless=False)
                    page = context.new_page()
                    page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000, wait_until="domcontentloaded")

                    print("\n" + "=" * 70)
                    print("  ACTION REQUIRED: PLEASE LOG IN TO TIKTOK IN THE OPENED WINDOW.")
                    print("  Once you reach the upload page, the script will resume.")
                    print("=" * 70 + "\n")

                    page.wait_for_selector("iframe", timeout=600000)
                    print("  Login confirmed!")
                    page.wait_for_timeout(5000)

                print("  Navigating to upload iframe...")
                iframe_element = page.wait_for_selector("iframe")
                frame = iframe_element.content_frame()

                print("  Selecting video file...")
                file_input = frame.wait_for_selector("input[type=file]", timeout=20000)
                file_input.set_input_files(str(video_path))

                print("  Waiting for upload progress...")
                frame.wait_for_selector(".editor-container, .caption-container-v2", timeout=60000)
                page.wait_for_timeout(3000)

                print("  Setting caption text...")
                caption_editor = frame.locator("div[contenteditable='true']").first
                caption_editor.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(caption)

                page.wait_for_timeout(2000)

                print("  Clicking Post...")
                post_button = frame.locator("button:has-text('Post')").first
                post_button.click()
                page.wait_for_timeout(8000)

                print("  [SUCCESS] TikTok Reel post completed successfully!")
                context.close()
                return True

            except Exception as e:
                print(f"  [ERROR] TikTok upload failed: {e}")
                try:
                    context.close()
                except Exception:
                    pass
                return False

    # ----------------------------------------------------------------
    # INSTAGRAM REELS UPLOADER
    # ----------------------------------------------------------------
    def upload_instagram_reels(self, video_path, caption):
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            print(f"Error: Video file not found: {video_path}")
            return False

        print(f"\n[Instagram Uploader] Initializing upload for: {video_path.name}...")

        with sync_playwright() as p:
            context = self._get_browser_context(p, headless=True)
            page = context.new_page()

            try:
                page.goto("https://www.instagram.com/", timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                is_logged_in = False
                try:
                    page.wait_for_selector("svg[aria-label='New post']", timeout=12000)
                    is_logged_in = True
                except Exception:
                    pass

                if not is_logged_in:
                    print("  [ALERT] Instagram login required! Launching interactive window...")
                    context.close()

                    context = self._get_browser_context(p, headless=False)
                    page = context.new_page()
                    page.goto("https://www.instagram.com/", timeout=60000, wait_until="domcontentloaded")

                    print("\n" + "=" * 70)
                    print("  ACTION REQUIRED: PLEASE LOG IN TO INSTAGRAM IN THE OPENED WINDOW.")
                    print("  Once you reach the home feed, the script will resume.")
                    print("=" * 70 + "\n")

                    page.wait_for_selector("svg[aria-label='New post']", timeout=600000)
                    print("  Login confirmed!")
                    page.wait_for_timeout(5000)

                print("  Opening create post dialog...")
                page.click("svg[aria-label='New post']")
                page.wait_for_selector("input[type=file]", timeout=15000)

                print("  Uploading video file...")
                file_input = page.locator("input[type=file]")
                file_input.set_input_files(str(video_path))

                page.wait_for_selector("button:has-text('Next')", timeout=20000)
                print("  Navigating to caption screen...")
                page.click("button:has-text('Next')")
                page.wait_for_timeout(1000)

                page.wait_for_selector("button:has-text('Next')", timeout=20000)
                page.click("button:has-text('Next')")
                page.wait_for_timeout(1000)

                print("  Entering caption text...")
                caption_box = page.locator("div[aria-label='Write a caption...']")
                caption_box.click()
                page.keyboard.type(caption)
                page.wait_for_timeout(1000)

                print("  Sharing Reel to feed...")
                page.click("button:has-text('Share')")

                page.wait_for_selector("text=Your reel has been shared.", timeout=90000)
                print("  [SUCCESS] Instagram Reel posted successfully!")
                context.close()
                return True

            except Exception as e:
                print(f"  [ERROR] Instagram upload failed: {e}")
                try:
                    context.close()
                except Exception:
                    pass
                return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload short-form videos to YouTube Shorts, TikTok, or Instagram Reels.")
    parser.add_argument("--platform", required=True, help="Target platform: youtube, tiktok, or instagram")
    parser.add_argument("--video", required=True, help="Local file path to the video file")
    parser.add_argument("--title", default="Visual Meditation", help="Video title (mainly for YouTube)")
    parser.add_argument("--caption", default="", help="Description or caption for the upload")
    parser.add_argument("--thumbnail", default=None, help="Optional local path to thumbnail image (YouTube only)")

    args = parser.parse_args()

    # Configure sys.stdout to UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    uploader = SocialUploader(platform=args.platform)

    if args.platform.lower() == "youtube":
        success = uploader.upload_youtube_shorts(
            video_path=args.video,
            title=args.title,
            description=args.caption,
            thumbnail_path=args.thumbnail
        )
        sys.exit(0 if success else 1)
    elif args.platform.lower() == "tiktok":
        success = uploader.upload_tiktok(
            video_path=args.video,
            caption=args.caption
        )
        sys.exit(0 if success else 1)
    elif args.platform.lower() == "instagram":
        success = uploader.upload_instagram_reels(
            video_path=args.video,
            caption=args.caption
        )
        sys.exit(0 if success else 1)
