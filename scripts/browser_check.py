#!/usr/bin/env python3
"""Smoke-test desktop/mobile rendering, scenario tabs, image viewing and citation copying."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:4173')
    parser.add_argument('--chrome', default='/usr/bin/google-chrome')
    parser.add_argument('--output', type=Path, default=ROOT / 'test-results')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / 'assets/data/results.json').read_text())
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chrome, headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, permissions=['clipboard-read', 'clipboard-write'])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: errors.append(f'HTTP {response.status}: {response.url}') if response.status >= 400 else None)
        page.goto(args.url, wait_until='networkidle')
        expect(page.locator('.pending')).to_have_count(3)
        expect(page.locator('a[data-resource]')).to_have_count(0)
        for key, rows in data['scenarios'].items():
            page.locator(f'#tab-{key}').click()
            panel = page.locator(f'#panel-{key}')
            expect(panel).to_be_visible()
            expect(page.locator('.scenario-panel:visible')).to_have_count(1)
            actual = panel.locator('tbody tr').evaluate_all('(rows) => rows.map(row => [...row.querySelectorAll("td")].map(cell => cell.textContent.trim()))')
            assert actual == [row['values'] for row in rows], f'Table mismatch in {key}'
            panel.locator('img').scroll_into_view_if_needed()
            expect(panel.locator('img')).to_have_js_property('complete', True)
            assert panel.locator('img').evaluate('(img) => img.naturalWidth > 0'), f'Missing {key} image'
        page.locator('#tab-offroad').focus()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#tab-flat')).to_be_focused()
        expect(page.locator('#panel-flat')).to_be_visible()
        page.keyboard.press('End')
        expect(page.locator('#panel-obstacle-free')).to_be_visible()
        page.keyboard.press('Home')
        expect(page.locator('#panel-offroad')).to_be_visible()
        hero = page.locator('.hero-image')
        hero.click()
        expect(page.locator('#figure-dialog')).to_be_visible()
        expect(page.locator('#close-viewer')).to_be_focused()
        page.keyboard.press('Escape')
        expect(page.locator('#figure-dialog')).not_to_be_visible()
        expect(hero).to_be_focused()
        page.locator('#copy-citation').click()
        expect(page.locator('#copy-status')).to_have_text('Citation copied to clipboard.')
        copied = page.evaluate('navigator.clipboard.readText()')
        assert copied == page.locator('#bibtex').inner_text().strip()
        for summary in page.locator('.method-details summary').all():
            summary.click()
        # Load images before screenshots; ordinary visitors trigger loading by scrolling.
        page.locator('img[src]').evaluate_all('(images) => images.forEach(img => img.loading = "eager")')
        page.wait_for_function('Array.from(document.querySelectorAll("img[src]")).every(img => img.complete && img.naturalWidth > 0)')
        for summary in page.locator('.method-details summary').all():
            summary.click()
        for width in [1440, 1024, 768, 390, 320]:
            page.set_viewport_size({'width': width, 'height': 1000 if width >= 768 else 844})
            page.evaluate('window.scrollTo({top: 0, behavior: "instant"})')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow at {width}px'
            page.screenshot(path=str(args.output / f'page-{width}.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('#tab-flat').click()
        expect(page.locator('#panel-flat')).to_be_visible()
        page.locator('#panel-flat .figure-link').click()
        expect(page.locator('#figure-dialog')).to_be_visible()
        page.locator('#close-viewer').click()
        expect(page.locator('#figure-dialog')).not_to_be_visible()
        assert not errors, errors
        # No-JavaScript visitors can still read all scenarios and follow original figures.
        plain = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
        fallback = plain.new_page()
        fallback.goto(args.url, wait_until='networkidle')
        expect(fallback.locator('.scenario-panel:visible')).to_have_count(3)
        expect(fallback.locator('.scenario-tabs')).not_to_be_visible()
        expect(fallback.locator('#copy-citation')).not_to_be_visible()
        assert fallback.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'No-JS overflow'
        plain.close()
        context.close()
        browser.close()
    print('PASS: 5 viewport widths; all scenario data; keyboard tabs; desktop/mobile image viewer; clipboard; no-JS fallback; no runtime or HTTP errors.')


if __name__ == '__main__':
    main()
