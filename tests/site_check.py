from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading, tempfile
import html5lib
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
screenshots = Path(tempfile.mkdtemp(prefix='mw-site-check-'))
print('Screenshots:', screenshots)
server = ThreadingHTTPServer(('127.0.0.1', 8765), partial(SimpleHTTPRequestHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
for file in ['index.html', 'en/index.html']:
    parser = html5lib.HTMLParser(strict=False)
    parser.parse((root / file).read_text(encoding='utf-8'))
    assert not parser.errors, (file, parser.errors)
    print('HTML valid:', file)
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    for route in ['/', '/en/']:
        for width in [360, 768, 1024, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto('http://127.0.0.1:8765' + route)
            page.evaluate('document.fonts.ready')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (route, width, 'overflow')
            assert page.locator('h1').count() == 1
            assert page.locator("a[href*='linkedin.com']").count() == 4
            for link in page.locator('a[href^="#"]').all():
                assert page.locator(link.get_attribute('href')).count(), link.get_attribute('href')
            if width < 900:
                page.locator('#menuBtn').click()
                assert page.locator('#mobileMenu').evaluate('(d)=>d.open')
                assert page.locator('#mobileMenu button').evaluate('(b)=>b===document.activeElement')
                page.keyboard.press('Shift+Tab')
                assert page.locator('#mobileMenu a').last.evaluate('(a)=>a===document.activeElement')
                page.keyboard.press('Tab')
                assert page.locator('#mobileMenu button').evaluate('(b)=>b===document.activeElement')
                page.keyboard.press('Escape')
                assert page.locator('#menuBtn').evaluate('(b)=>b===document.activeElement')
                assert not page.locator('#mobileMenu').is_visible()
            page.screenshot(path=str(screenshots / f'mw-{ "pl" if route=="/" else "en"}-{width}.png'), full_page=True)
            print('Layout/menu/links passed:', route, width)
        page.locator('button[type=submit]').click()
        assert page.locator('#name').evaluate('(f)=>!f.validity.valid')
        page.locator('#name').fill('Test Person')
        page.locator('#email').fill('invalid')
        page.locator('#message').fill('Example workflow')
        page.locator('button[type=submit]').click()
        assert page.locator('#email').evaluate('(f)=>!f.validity.valid')
        page.locator('#email').fill('test@example.com')
        page.route('https://formspree.io/**', lambda r: r.fulfill(status=500, body='{}', content_type='application/json'))
        page.locator('button[type=submit]').click()
        page.wait_for_function("document.querySelector('#formStatus').textContent.includes('LinkedIn')")
        assert page.locator('#message').input_value() == 'Example workflow'
        assert page.locator('button[type=submit]').is_enabled()
        page.unroute('https://formspree.io/**')
        page.route('https://formspree.io/**', lambda r: r.abort())
        page.locator('button[type=submit]').click()
        page.wait_for_function("!document.querySelector('#contactForm').hasAttribute('aria-busy')")
        assert page.locator('#message').input_value() == 'Example workflow'
        page.unroute('https://formspree.io/**')
        page.route('https://formspree.io/**', lambda r: r.fulfill(status=200, body='{"ok":true}', content_type='application/json'))
        page.locator('button[type=submit]').click()
        page.wait_for_function("document.querySelector('#name').value === ''")
        assert page.locator('#formStatus').inner_text()
        page.unroute('https://formspree.io/**')
        page.emulate_media(reduced_motion='reduce')
        assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == 'auto'
        print('Form validation/server failure/network failure/success/reduced motion passed:', route)
    assert not errors, errors
    print('No JavaScript errors. All browser checks passed.')
    browser.close()
server.shutdown()
