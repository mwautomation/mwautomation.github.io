"""Local browser checks; all contact-form requests are mocked or blocked."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import tempfile
import threading

import html5lib
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = Path(tempfile.mkdtemp(prefix="mw-site-check-"))
PAGES = {
    "/": ("pl", "/polityka-prywatnosci/"),
    "/en/": ("en", "/en/privacy/"),
    "/polityka-prywatnosci/": ("pl", None),
    "/en/privacy/": ("en", None),
}
WIDTHS = [320, 360, 390, 768, 1024, 1440]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def check_navigation(page, width):
    if width >= 900:
        assert page.locator(".desktop-nav .language").is_visible()
        return
    trigger = page.locator("#menuBtn")
    trigger.click()
    assert page.locator("#mobileMenu").evaluate("d => d.open")
    assert page.locator("#mobileMenu button").evaluate("b => b === document.activeElement")
    assert page.locator("#mobileMenu .language").is_visible()
    page.keyboard.press("Shift+Tab")
    assert page.locator("#mobileMenu a").last.evaluate("a => a === document.activeElement")
    page.keyboard.press("Tab")
    assert page.locator("#mobileMenu button").evaluate("b => b === document.activeElement")
    page.keyboard.press("Escape")
    assert trigger.evaluate("b => b === document.activeElement")
    assert not page.locator("#mobileMenu").is_visible()


def check_links_and_images(page):
    for link in page.locator("a[href]").all():
        url = urlsplit(link.get_attribute("href"))
        if url.scheme or url.netloc:
            continue
        if not url.path:
            assert page.locator(f'[id="{url.fragment}"]').count(), url.fragment
        else:
            target = ROOT / unquote(url.path).lstrip("/")
            assert target.exists(), str(target)
    assert page.locator("img").evaluate_all("nodes => nodes.every(i => i.complete && i.naturalWidth > 0)")


def check_homepage(page, width, privacy):
    primary = ".section-heading p, .example p, .flow, .service-row p, .hero-note, .founder-role, .founder-copy p, .field label, .steps p"
    secondary = ".eyebrow, .tags span, .node small, .diagram-top, .diagram-bottom, .form-note, .footer"
    for selector, minimum in [(primary, 16), (secondary, 14)]:
        bad = page.locator(selector).evaluate_all(
            "(nodes, min) => nodes.filter(n => parseFloat(getComputedStyle(n).fontSize) < min).map(n => n.outerHTML)", minimum)
        assert not bad, (width, minimum, bad)
    expected = 1 if width <= 620 else 2 if width < 900 else 4
    columns = page.locator(".steps").evaluate("n => getComputedStyle(n).gridTemplateColumns.split(' ').length")
    assert columns == expected, (width, columns)
    assert page.locator(".number").count() == page.locator(".steps .number").count() == 4
    assert page.locator(".dots").count() == 0
    assert page.locator(".capability-icon").count() == 3
    assert page.locator(f'#formNote a[href="{privacy}"]').count() == 1
    assert page.locator(f'.footer a[href="{privacy}"]').count() == 1
    assert page.locator("#contactForm input, #contactForm textarea").evaluate_all(
        "fields => fields.map(f => f.name).join(',') === 'name,email,message'")
    assert page.locator("#contactForm").get_attribute("action") == "https://formspree.io/f/mgvkjvge"
    assert page.locator("a[href^='mailto:']").count() == 0
    assert page.locator("a[href*='linkedin.com']").count() == 4
    portrait = page.locator(".portrait-placeholder").bounding_box()
    assert portrait["width"] <= 281
    assert abs(portrait["height"] / portrait["width"] - 1.25) < .01
    submit = page.locator("button[type=submit]").bounding_box()
    assert submit["height"] >= 56
    assert abs(submit["width"] - page.locator("#contactForm").bounding_box()["width"]) < 1
    if width <= 620:
        assert page.locator(".headline-first").evaluate("n => n.getBoundingClientRect().width >= n.scrollWidth - 1"), width


def check_form(page, origin, route):
    requests = []
    def block(r):
        requests.append(r.request.url)
        r.abort()
    page.route("https://formspree.io/**", block)
    page.goto(origin + route)
    button = page.locator("button[type=submit]")
    button.click()
    assert page.locator("#name").evaluate("f => !f.validity.valid")
    page.locator("#name").fill("Test Person")
    page.locator("#email").fill("invalid")
    page.locator("#message").fill("Example workflow")
    button.click()
    assert page.locator("#email").evaluate("f => !f.validity.valid")
    assert not requests, "Invalid data reached the endpoint"
    page.locator("#email").fill("test@example.com")
    for response in ["server", "network", "success"]:
        page.unroute("https://formspree.io/**")
        if response == "network":
            page.route("https://formspree.io/**", lambda r: r.abort())
        else:
            code = 500 if response == "server" else 200
            page.route("https://formspree.io/**", lambda r: r.fulfill(
                status=code, body='{"ok":true}', content_type="application/json"))
        button.click()
        page.wait_for_function("!document.querySelector('#contactForm').hasAttribute('aria-busy')")
        assert button.is_enabled()
        assert button.locator("[aria-hidden=true]").count() == 1
        if response == "success":
            assert page.locator("#name").input_value() == ""
            expected = "wysłana" if route == "/" else "has been sent"
        else:
            assert page.locator("#message").input_value() == "Example workflow"
            expected = "spróbuj ponownie" if route == "/" else "please try again"
        assert expected in page.locator("#formStatus").inner_text()
    page.unroute("https://formspree.io/**")
    print("Mocked validation, server/network failures, retry and success:", route, flush=True)


for route in PAGES:
    parser = html5lib.HTMLParser(strict=False)
    parser.parse((ROOT / route.lstrip("/") / "index.html").read_text(encoding="utf-8"))
    assert not parser.errors, (route, parser.errors)
print("HTML valid: all four pages", flush=True)
server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
origin = f"http://127.0.0.1:{server.server_port}"
threading.Thread(target=server.serve_forever, daemon=True).start()
print("Screenshots:", SHOTS, flush=True)
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route("https://formspree.io/**", lambda r: r.abort())
        for route, (lang, privacy) in PAGES.items():
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 1000})
                page.goto(origin + route)
                page.evaluate("document.fonts.ready")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (route, width, "overflow")
                assert page.locator("h1").count() == 1
                check_links_and_images(page)
                check_navigation(page, width)
                if privacy:
                    check_homepage(page, width, privacy)
                else:
                    assert page.locator("#contactForm").count() == 0
                    assert page.locator("a.language").first.get_attribute("href") in PAGES
                    assert page.locator(".privacy-page").evaluate("n => parseFloat(getComputedStyle(n).fontSize) >= 16")
                name = "home" if privacy else "privacy"
                page.screenshot(path=str(SHOTS / f"{lang}-{name}-{width}.png"), full_page=True)
            page.emulate_media(reduced_motion="reduce")
            assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"
            page.emulate_media(reduced_motion="no-preference")
            print("Six viewport sizes, navigation, links and typography:", route, flush=True)
        page.unroute("https://formspree.io/**")
        for route in ["/", "/en/"]:
            check_form(page, origin, route)
        # Simulate 200% desktop zoom reflow: half the CSS viewport and 2x device scale.
        zoomed = browser.new_context(device_scale_factor=2)
        zoom_page = zoomed.new_page()
        zoom_page.on("pageerror", lambda e: errors.append(str(e)))
        for route in PAGES:
            for physical in [1024, 1440]:
                zoom_page.set_viewport_size({"width": physical // 2, "height": 500})
                zoom_page.goto(origin + route)
                zoom_page.evaluate("document.fonts.ready")
                assert zoom_page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (route, physical, "200% reflow")
                check_navigation(zoom_page, physical // 2)
            zoom_page.screenshot(path=str(SHOTS / f"{PAGES[route][0]}-{'home' if PAGES[route][1] else 'privacy'}-zoom-200.png"), full_page=True)
        zoomed.close()
        native = browser.new_context(java_script_enabled=False)
        for route in ["/", "/en/"]:
            fallback = native.new_page()
            fallback.goto(origin + route)
            assert fallback.locator("#contactForm").get_attribute("novalidate") is None
            assert fallback.locator("#name[required], #email[required], #message[required]").count() == 3
            fallback.close()
        native.close()
        assert not errors, errors
        browser.close()
        print("200% reflow, native form fallback and JavaScript checks passed.", flush=True)
finally:
    server.shutdown()
    server.server_close()
