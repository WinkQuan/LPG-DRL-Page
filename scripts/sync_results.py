#!/usr/bin/env python3
"""Read result tables from LPG-DRL.tex and render static, no-JS-compatible HTML."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
METRICS = [
    ("SR (%) ↑", "Success rate"), ("CR (%) ↓", "Collision rate"),
    ("TR (%) ↓", "Timeout rate"), ("OBR (%) ↓", "Out-of-bounds rate"),
    ("SC ↓", "Step count"), ("TL (m) ↓", "Trajectory length"),
    ("EC (J) ↓", "Energy consumption, as reported in the manuscript"),
    ("PS (rad) ↓", "Posture stability"), ("ET (s) ↓", "Execution time"),
]
SCENARIOS = [
    ("offroad", "Off-road with obstacles", "Uneven terrain · Cylindrical obstacles",
     "Off-road terrain with obstacles"),
    ("flat", "Flat terrain with obstacles", "Flat terrain · Cylindrical obstacles",
     "Flat terrain with obstacles"),
    ("obstacle-free", "Obstacle-free terrain", "Uneven terrain · No cylindrical obstacles",
     "Obstacle-free off-road terrain"),
]


def read_table(source, label, expected):
    block = source.split(r"\label{" + label + "}", 1)[1].split(r"\end{table*}", 1)[0]
    rows = []
    for line in block.splitlines():
        if line.lstrip().startswith("%"):
            continue
        line = re.sub(r"\\textbf\{([^}]+)\}", r"\1", line)
        cells = [cell.strip().rstrip("\\").strip() for cell in line.split("&")]
        if len(cells) < 10 or not all(re.fullmatch(r"\d+\.\d+", value) for value in cells[-9:]):
            continue
        name = cells[-10].replace(" (ours)", "")
        rows.append({"method": name, "values": cells[-9:]})
    if len(rows) != expected:
        raise ValueError(f"{label}: expected {expected} rows; found {len(rows)}. Check manuscript table structure.")
    return rows


def table_html(rows, name, table_id):
    best = [(max if i == 0 else min)(float(row["values"][i]) for row in rows) for i in range(9)]
    header = '<th scope="col">Method</th>' + ''.join(
        f'<th scope="col"><abbr title="{meaning}">{label}</abbr></th>' for label, meaning in METRICS)
    body = []
    for row in rows:
        ours = row["method"] == "LPG-DRL"
        name_html = html.escape(row["method"]) + (' <span>Ours</span>' if ours else '')
        values = ''.join(f'<td><strong>{value}</strong></td>' if float(value) == best[i]
                         else f'<td>{value}</td>' for i, value in enumerate(row["values"]))
        row_class = ' class="ours"' if ours else ''
        body.append(f'<tr{row_class}><th scope="row">{name_html}</th>{values}</tr>')
    return (f'<div class="table-shell"><div class="table-scroll" role="region" tabindex="0" aria-label="{name} metrics">'
            f'<table id="{table_id}"><caption class="sr-only">{name}. Higher success rate is better; lower values are preferred for all other metrics.</caption>'
            f'<thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
            '<p class="table-footnote">Values reproduced from the current manuscript. Scroll horizontally on smaller screens to see all nine metrics.</p></div>')


def replace_block(page, label, content):
    start, end = f'<!-- BEGIN GENERATED {label} -->', f'<!-- END GENERATED {label} -->'
    if page.count(start) != 1 or page.count(end) != 1:
        raise ValueError(f'Missing or duplicated HTML markers: {label}')
    before, remainder = page.split(start)
    _, after = remainder.split(end)
    return f'{before}{start}\n{content}\n      {end}{after}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manuscript', type=Path)
    args = parser.parse_args()
    source = args.manuscript.read_text()
    offroad = read_table(source, 'tab:offroad_comparison', 6)
    other = read_table(source, 'tab:scenario_ablation', 12)
    ablation = read_table(source, 'tab:ablation_study', 4)
    datasets = {'offroad': offroad, 'flat': other[6:], 'obstacle-free': other[:6]}
    manifest = json.loads((ROOT / 'assets/images/sources.json').read_text())
    fragments = []
    for key, title, subtitle, description in SCENARIOS:
        rows = datasets[key]
        ours = next(row for row in rows if row['method'] == 'LPG-DRL')
        baseline = next(row for row in rows if row['method'] == 'NPE-DRL')
        success = float(ours['values'][0])
        delta = success - float(baseline['values'][0])
        image = f'trajectory-{key}'
        size = manifest[image]
        caption = f'Representative trajectories in {description.lower()}. Original manuscript figure; colors identify the six compared methods.'
        fragments.append(f'''<article class="scenario-panel" id="panel-{key}" aria-labelledby="heading-{key}">
        <div class="scenario-heading"><h3 id="heading-{key}">{title}</h3><span>{subtitle}</span></div>
        <div class="scenario-showcase"><figure class="trajectory-figure"><a class="figure-link" href="assets/images/{image}-full.webp" data-lightbox data-caption="{caption}" aria-label="Enlarge trajectories: {title}"><img src="assets/images/{image}.webp" width="{size['width']}" height="{size['height']}" alt="Top-down comparison of LPG-DRL, NPE-DRL, D3QN-LfD, BC, DAgger, and APF trajectories in {description.lower()}." loading="lazy" decoding="async"><span class="zoom-label"><svg class="icon" aria-hidden="true"><use href="#i-expand"/></svg>View figure</span></a><figcaption>Representative navigation trajectories · Colors follow the original figure legend.</figcaption></figure>
        <div class="scenario-summary"><div><span class="summary-label">LPG-DRL success rate</span><p class="success-value">{success:.1f}<span>%</span></p><p class="success-caption">Highest among the<br>evaluated methods</p></div><div class="delta"><strong>+{delta:.1f} <span>pp</span></strong><p>Success rate vs. NPE-DRL</p></div></div></div>
        {table_html(rows, title, 'table-' + key)}
      </article>''')
    path = ROOT / 'index.html'
    page = replace_block(path.read_text(), 'RESULTS', '\n'.join(fragments))
    page = replace_block(page, 'ABLATION', table_html(ablation, 'Off-road ablation study', 'table-ablation'))
    # Preserve intrinsic aspect ratios for every exported manuscript figure.
    for name, dimensions in manifest.items():
        pattern = rf'(src="assets/images/{name}\.webp" width=")\d+(" height=")\d+(".*?)'
        page = re.sub(pattern, lambda m: f'{m[1]}{dimensions["width"]}{m[2]}{dimensions["height"]}{m[3]}', page)
    path.write_text(page)
    data_path = ROOT / 'assets/data/results.json'
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps({
        'source': 'paper_TAI/LPG-DRL.tex',
        'source_sha256': hashlib.sha256(args.manuscript.read_bytes()).hexdigest(),
        'metrics': [label for label, _ in METRICS],
        'scenarios': datasets, 'ablation': ablation,
    }, indent=2) + '\n')
    print('Synced 3 scenarios, 18 comparison rows, and 4 ablation rows from the manuscript.')


if __name__ == '__main__':
    main()
