"""Render job_search_tracker.csv as a self-contained offline dashboard (spec: .claude/commands/html-report.md).

Usage: python tools/html_report.py [output.html]   (default: reports/application-dashboard.html)
"""
import csv
import glob
import html
import math
import os
import re
import sys
from collections import Counter
from datetime import date

BUCKETS = {"drafted": "Drafted", "applied": "Active", "interview": "Interview", "offer": "Offer", "hired": "Hired"}
COLORS = {"Drafted": "#64748b", "Active": "#3b82f6", "Interview": "#f59e0b", "Offer": "#8b5cf6", "Hired": "#22c55e", "Rejected/Closed": "#ef4444"}
ORDER = list(COLORS)
STAGES = ["Interview", "Offer", "Hired"]  # funnel rank after Active


def e(v):
    return html.escape(str(v), quote=True)


def bucket(status):
    return BUCKETS.get(status.strip().lower(), "Rejected/Closed")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def reached(row, outcomes):
    """Highest stage reached: current status, or an outcome.md checkbox naming a later stage."""
    text = outcomes.get(norm(row["company"]) + norm(row["role"]), "")
    ticked = [s for s in STAGES if re.search(rf"\[x\][^\n]*{s.lower()}", text)]
    best = max(([row["bucket"]] if row["bucket"] in STAGES else []) + ticked, key=STAGES.index, default=None)
    return best or row["bucket"]


def bars(counts, color="#3b82f6", label=""):
    items = sorted(counts.items(), key=lambda kv: -kv[1]) or [("none", 0)]
    top = max(v for _, v in items) or 1
    h = 28 * len(items) + 8
    rows = "".join(
        f'<text x="0" y="{28*i+22}" class="lbl">{e(k)}</text>'
        f'<rect x="150" y="{28*i+8}" width="{max(2, 260*v/top):.1f}" height="18" rx="4" fill="{color}"/>'
        f'<text x="{156+260*v/top:.1f}" y="{28*i+22}" class="num">{v}</text>'
        for i, (k, v) in enumerate(items))
    aria = e(f"{label}: " + ", ".join(f"{v} {k}" for k, v in items))
    return f'<svg viewBox="0 0 460 {h}" role="img" aria-label="{aria}">{rows}</svg>'


def doughnut(counts):
    total = sum(counts.values())
    if not total:
        return '<p class="muted">No data yet.</p>'
    parts, a = [], -math.pi / 2
    for k in ORDER:
        v = counts.get(k, 0)
        if not v:
            continue
        if v == total:  # a full circle cannot be drawn as one arc
            parts.append(f'<circle cx="90" cy="90" r="70" fill="none" stroke="{COLORS[k]}" stroke-width="28"/>')
            break
        b = a + 2 * math.pi * v / total
        x1, y1, x2, y2 = 90 + 70 * math.cos(a), 90 + 70 * math.sin(a), 90 + 70 * math.cos(b), 90 + 70 * math.sin(b)
        parts.append(f'<path d="M{x1:.2f},{y1:.2f} A70,70 0 {int(b-a>math.pi)} 1 {x2:.2f},{y2:.2f}" fill="none" stroke="{COLORS[k]}" stroke-width="28"/>')
        a = b
    legend = "".join(f'<text x="190" y="{40+22*i}" class="lbl"><tspan fill="{COLORS[k]}">●</tspan> {e(k)}: {counts[k]}</text>'
                     for i, k in enumerate(k for k in ORDER if counts.get(k)))
    aria = e("Status breakdown: " + ", ".join(f"{counts[k]} {k}" for k in ORDER if counts.get(k)))
    return f'<svg viewBox="0 0 360 180" role="img" aria-label="{aria}">{"".join(parts)}<text x="90" y="97" text-anchor="middle" class="big">{total}</text>{legend}</svg>'


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "reports/application-dashboard.html"
    with open("job_search_tracker.csv", encoding="utf8", newline="") as f:
        rows = [dict(r, deadline=r.get("deadline") or "") for r in csv.DictReader(f)]
    outcomes = {}
    for p in glob.glob("documents/applications/*/outcome.md"):
        outcomes[norm(os.path.basename(os.path.dirname(p)).replace("_", ""))] = open(p, encoding="utf8").read().lower()
    for r in rows:
        r["bucket"] = bucket(r["status"])
        r["reached"] = reached(r, outcomes)

    all_status = Counter(r["bucket"] for r in rows)
    sent = [r for r in rows if r["bucket"] != "Drafted"]  # drafted rows were never submitted
    funnel = {"Applied": len(sent)}
    for s in STAGES:
        funnel[s] = sum(1 for r in sent if r["reached"] in STAGES[STAGES.index(s):])
    past_screen = round(100 * funnel["Interview"] / len(sent)) if sent else 0
    final = [r for r in sent if r["status"].strip().lower() in ("rejected", "no_response", "no response", "offer_declined", "offer declined", "withdrawn")]
    true_rej = sum(1 for r in final if r["status"].strip().lower() in ("rejected", "no_response", "no response"))
    rej_rate = f"{round(100*true_rej/len(final))}%" if final else "—"

    cards = [("Sent", len(sent), "#0ea5e9")] + [(k, all_status.get(k, 0), COLORS[k]) for k in ORDER]
    card_html = "".join(f'<div class="card" style="border-left-color:{c}"><div class="n">{n}</div><div>{e(k)}</div></div>' for k, n, c in cards)

    rows.sort(key=lambda r: (r["company"].lower()))
    rows.sort(key=lambda r: r["date"], reverse=True)
    def cell(v):
        return e(v) if v else "—"

    def link(url):
        return f'<a href="{e(url)}" target="_blank" rel="noopener">open</a>' if url.startswith("http") else "—"
    trs = "".join(
        f'<tr data-status="{e(r["bucket"])}" data-sector="{e(r["sector"])}" data-q="{e((r["company"]+" "+r["role"]+" "+r["sector"]).lower())}">'
        f'<td>{cell(r["date"])}</td><td>{cell(r["deadline"])}</td><td><b>{cell(r["company"])}</b></td><td>{cell(r["role"])}</td>'
        f'<td>{cell(r["sector"])}</td><td>{cell(r["fit_rating"])}</td>'
        f'<td><span class="pill" style="background:{COLORS[r["bucket"]]}">{e(r["bucket"])}</span></td>'
        f'<td title="{e(r["notes"])}">{cell(r["notes"][:80])}</td>'
        f'<td>{link(r["source"])}</td></tr>'
        for r in rows)
    opts = lambda vals: "".join(f'<option value="{e(v)}">{e(v)}</option>' for v in vals)
    today = date.today().isoformat()

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Job Search Dashboard</title><style>
:root{{--bg:#f8fafc;--card:#fff;--fg:#0f172a;--muted:#64748b;--line:#e2e8f0;--alt:#f1f5f9}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1220;--card:#111a2e;--fg:#e2e8f0;--muted:#94a3b8;--line:#1e293b;--alt:#0f172a}}}}
body{{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg)}}main{{max-width:1200px;margin:auto;padding:16px}}
header{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}}.muted{{color:var(--muted)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:16px 0}}
.card{{background:var(--card);border-left:5px solid;border-radius:8px;padding:12px;box-shadow:0 1px 3px #0002}}.card .n{{font-size:28px;font-weight:700}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}@media (max-width:800px){{.grid{{grid-template-columns:1fr}}}}
.chart-card{{background:var(--card);border-radius:8px;padding:12px;box-shadow:0 1px 3px #0002}}h3{{margin:0 0 8px;font-size:15px}}
svg{{width:100%;height:auto}}.lbl,.num{{font-size:13px;fill:var(--fg)}}.big{{font-size:28px;font-weight:700;fill:var(--fg)}}
.filters{{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 8px}}select,input{{padding:6px 8px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg)}}
.tw{{overflow-x:auto;background:var(--card);border-radius:8px}}table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}tbody tr:nth-child(even){{background:var(--alt)}}
.pill{{color:#fff;border-radius:999px;padding:2px 10px;font-size:12px}}a{{color:#3b82f6}}footer{{margin:24px 0;color:var(--muted);font-size:13px}}
</style></head><body><main>
<header><h1>🔍 Job Search Dashboard</h1><span class="muted">Generated: {today}</span></header>
<p class="muted">Sent: {len(sent)} · Drafted, not yet sent: {all_status.get("Drafted", 0)} · Past resume screen: {past_screen}% · Rejection rate: {rej_rate}</p>
<section class="cards">{card_html}</section>
<section class="grid">
<div class="chart-card"><h3>Status breakdown</h3>{doughnut(all_status)}</div>
<div class="chart-card"><h3>By sector (sent)</h3>{bars(Counter(r["sector"] or "—" for r in sent), label="By sector") if sent else '<p class="muted">Nothing sent yet.</p>'}</div>
<div class="chart-card"><h3>By channel (sent)</h3>{bars(Counter(r["channel"] or "other" for r in sent), "#0ea5e9", "By channel") if sent else '<p class="muted">Nothing sent yet.</p>'}</div>
<div class="chart-card"><h3>Application funnel</h3>{bars(funnel, "#22c55e", "Funnel")}</div>
</section>
<div class="filters"><select id="fs"><option value="">All statuses</option>{opts(k for k in ORDER if all_status.get(k))}</select>
<select id="fc"><option value="">All sectors</option>{opts(sorted({r["sector"] for r in rows if r["sector"]}))}</select>
<input id="fq" placeholder="🔍 company, role, sector" aria-label="Search applications"></div>
<div class="tw"><table><thead><tr><th>Date</th><th>Deadline</th><th>Company</th><th>Role</th><th>Sector</th><th>Fit</th><th>Status</th><th>Notes</th><th>Source</th></tr></thead><tbody id="tb">{trs}</tbody></table></div>
<footer>Generated by Claude Code · ai-job-search · {today}</footer></main>
<script>
const fs=document.getElementById('fs'),fc=document.getElementById('fc'),fq=document.getElementById('fq');
function f(){{const s=fs.value,c=fc.value,q=fq.value.toLowerCase();for(const tr of document.querySelectorAll('#tb tr'))
tr.hidden=!((!s||tr.dataset.status===s)&&(!c||tr.dataset.sector===c)&&tr.dataset.q.includes(q));}}
[fs,fc].forEach(x=>x.onchange=f);fq.oninput=f;
</script></body></html>"""
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf8", newline="\n") as fh:
        fh.write(page)
    print(f"Dashboard: {out} | sent {len(sent)} | drafted {all_status.get('Drafted', 0)} | " + " ".join(f"{k} {all_status.get(k, 0)}" for k in ORDER[1:]))


if __name__ == "__main__":
    main()
