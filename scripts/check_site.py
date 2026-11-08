#!/usr/bin/env python3
"""Validate the published static files without third-party dependencies."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for name in ['src', 'href']:
            if attrs.get(name):
                self.references.append(attrs[name])
        if tag == 'img' and attrs.get('src'):
            self.images.append(attrs)
        if tag == 'a' and attrs.get('target') == '_blank':
            assert 'noopener' in attrs.get('rel', ''), f'Missing noopener: {attrs}'


def main():
    parser = PageParser()
    parser.feed((ROOT / 'index.html').read_text())
    assert len(parser.ids) == len(set(parser.ids)), 'Duplicate IDs'
    for reference in parser.references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            continue
        if url.path:
            assert (ROOT / unquote(url.path)).is_file(), f'Missing local resource: {reference}'
        if url.fragment and not url.path:
            assert url.fragment in parser.ids, f'Missing anchor: {reference}'
    sizes = json.loads((ROOT / 'assets/images/sources.json').read_text())
    for image in parser.images:
        assert image.get('alt'), f'Missing alt text: {image}'
        name = Path(image['src']).stem
        if name in sizes:
            assert int(image['width']) == sizes[name]['width'], f'Incorrect image width: {name}'
            assert int(image['height']) == sizes[name]['height'], f'Incorrect image height: {name}'
    data = json.loads((ROOT / 'assets/data/results.json').read_text())
    assert len(data['scenarios']) == 3 and len(data['ablation']) == 4
    for name, rows in data['scenarios'].items():
        assert len(rows) == 6, f'Expected six methods: {name}'
        for row in rows:
            assert len(row['values']) == 9
            assert abs(sum(float(v) for v in row['values'][:4]) - 100) < .01, row
    print(f'PASS: {len(parser.references)} local/external references checked; {len(parser.images)} image descriptions; 3 scenarios, 9 metrics, and 4 ablations.')


if __name__ == '__main__':
    main()
