#!/usr/bin/env python3
"""
Generate a self-contained lecture-viewer website for ECE 252.

It scans ../lectures/compiled/*.pdf, groups the PDFs by lecture number
(distinguishing lecture "notes" from "slides"), and writes index.html
next to this script. Lecture data is embedded directly into the HTML so
the page works when opened straight from disk (file://), with no server
and no fetch/CORS problems.

Re-run this script any time the compiled PDFs change:

    python3 site/build_site.py
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMPILED = HERE.parent / "lectures" / "compiled"
# Path used inside the HTML, relative to site/index.html
REL_PREFIX = "../lectures/compiled"

# Filenames that are course resources rather than numbered lectures.
EXTRA_LABELS = {
    "assignments.pdf": ("Assignments", "All course assignments"),
    "notebook.pdf": ("Full Course Notebook", "Every lecture note combined into one PDF"),
    "ECELinux-VSCode-Setup.pdf": ("ECE Linux + VS Code Setup", "Environment setup guide"),
}

LECTURE_RE = re.compile(r"^L(\d{2})-(slides-)?(.+)\.pdf$")


def pretty_title(raw: str) -> str:
    """Turn 'The_Byzantine_Generals_Problem' into 'The Byzantine Generals Problem'."""
    text = raw.replace("_", " ").strip()
    # 'I O' -> 'I/O' for the async I/O lectures.
    text = re.sub(r"\bI O\b", "I/O", text)
    return text


def scan():
    lectures = {}  # num -> {"title", "notes", "slides"}
    extras = []
    reference = None

    for pdf in sorted(COMPILED.glob("*.pdf")):
        name = pdf.name
        m = LECTURE_RE.match(name)
        if m:
            num = int(m.group(1))
            is_slides = bool(m.group(2))
            title = pretty_title(m.group(3))
            entry = lectures.setdefault(num, {"num": num, "title": title, "notes": None, "slides": None})
            rel = f"{REL_PREFIX}/{name}"
            if is_slides:
                entry["slides"] = rel
                # Prefer the notes title, but fall back to the slides title.
                if entry["notes"] is None:
                    entry["title"] = title
            else:
                entry["notes"] = rel
                entry["title"] = title  # notes title wins
            continue

        if name in EXTRA_LABELS:
            label, desc = EXTRA_LABELS[name]
            extras.append({"title": label, "desc": desc, "href": f"{REL_PREFIX}/{name}"})

    # The reference sheet lives in its own folder.
    ref = HERE.parent / "lectures" / "referencesheet" / "ece252-referencesheet.pdf"
    if ref.exists():
        reference = {
            "title": "Reference Sheet",
            "desc": "Exam/quick-reference sheet",
            "href": "../lectures/referencesheet/ece252-referencesheet.pdf",
        }
    if reference:
        extras.insert(0, reference)

    ordered = [lectures[n] for n in sorted(lectures)]
    return ordered, extras


def build_html(lectures, extras):
    data = json.dumps({"lectures": lectures, "extras": extras}, indent=2)
    return HTML_TEMPLATE.replace("/*__DATA__*/", data)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ECE 252 &middot; Lecture Materials</title>
<style>
  :root {
    --bg: #0f1117;
    --bg-soft: #171a23;
    --card: #1b1f2a;
    --card-hover: #232838;
    --border: #2b3143;
    --text: #e6e9f0;
    --muted: #9aa3b8;
    --accent: #6ea8fe;
    --accent-2: #b18cff;
    --notes: #4fd1a5;
    --slides: #ffb454;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: radial-gradient(1200px 600px at 80% -10%, #1c2233 0%, var(--bg) 55%) fixed;
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
    min-height: 100vh;
  }
  header {
    padding: 48px 24px 24px;
    max-width: 1200px;
    margin: 0 auto;
  }
  h1 {
    margin: 0;
    font-size: clamp(28px, 4vw, 44px);
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  .subtitle { color: var(--muted); margin-top: 8px; font-size: 16px; }
  .toolbar {
    max-width: 1200px;
    margin: 8px auto 0;
    padding: 0 24px;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }
  .search {
    flex: 1 1 320px;
    display: flex;
    align-items: center;
    background: var(--bg-soft);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 14px;
  }
  .search input {
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-size: 15px;
    width: 100%;
  }
  .search svg { flex: none; margin-right: 10px; opacity: 0.6; }
  .count { color: var(--muted); font-size: 14px; white-space: nowrap; }

  main { max-width: 1200px; margin: 0 auto; padding: 24px; }
  .section-title {
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin: 28px 4px 14px;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    min-height: 150px;
    transition: transform .12s ease, background .12s ease, border-color .12s ease;
  }
  .card:hover {
    background: var(--card-hover);
    border-color: #3a4763;
    transform: translateY(-3px);
  }
  .badge {
    align-self: flex-start;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--accent);
    background: rgba(110,168,254,0.12);
    border: 1px solid rgba(110,168,254,0.35);
    padding: 3px 10px;
    border-radius: 999px;
    margin-bottom: 12px;
  }
  .card h3 {
    margin: 0 0 14px;
    font-size: 17px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
  .card .actions { margin-top: auto; display: flex; gap: 8px; flex-wrap: wrap; }
  .btn {
    appearance: none;
    border: 1px solid var(--border);
    background: var(--bg-soft);
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 10px;
    cursor: pointer;
    transition: transform .1s ease, filter .1s ease;
    text-decoration: none;
  }
  .btn:hover { filter: brightness(1.15); transform: translateY(-1px); }
  .btn.notes { border-color: rgba(79,209,165,0.5); color: var(--notes); }
  .btn.slides { border-color: rgba(255,180,84,0.5); color: var(--slides); }
  .btn:disabled { opacity: 0.35; cursor: not-allowed; }

  .extra-card { min-height: 120px; }
  .extra-card .badge { color: var(--accent-2); background: rgba(177,140,255,0.12); border-color: rgba(177,140,255,0.35); }
  .extra-card .desc { color: var(--muted); font-size: 13px; margin: -6px 0 14px; }

  footer { max-width: 1200px; margin: 40px auto; padding: 0 24px 40px; color: var(--muted); font-size: 13px; }

  /* Modal viewer */
  .modal {
    position: fixed; inset: 0; display: none;
    background: rgba(5,7,12,0.85);
    z-index: 50;
    padding: 24px;
  }
  .modal.open { display: flex; flex-direction: column; }
  .modal-bar {
    display: flex; align-items: center; gap: 12px;
    padding: 0 4px 12px;
  }
  .modal-bar h2 { font-size: 16px; margin: 0; flex: 1; font-weight: 600; }
  .modal iframe {
    flex: 1; width: 100%; border: none; border-radius: 12px;
    background: #fff;
  }
  .icon-btn {
    background: var(--card); border: 1px solid var(--border); color: var(--text);
    border-radius: 10px; padding: 8px 12px; cursor: pointer; font-size: 14px; font-weight: 600;
    text-decoration: none;
  }
  .icon-btn:hover { filter: brightness(1.2); }
  .no-results { color: var(--muted); padding: 20px 4px; display: none; }
</style>
</head>
<body>
  <header>
    <h1>ECE 252 &mdash; Systems Programming &amp; Concurrency</h1>
    <div class="subtitle">Lecture notes &amp; slide decks. Click a lecture to read it right here.</div>
  </header>

  <div class="toolbar">
    <label class="search">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input id="search" type="search" placeholder="Search lectures by number or title&hellip;" autocomplete="off" />
    </label>
    <span class="count" id="count"></span>
  </div>

  <main>
    <div class="section-title">Lectures</div>
    <div class="grid" id="lecture-grid"></div>
    <div class="no-results" id="no-results">No lectures match your search.</div>

    <div class="section-title">Course Resources</div>
    <div class="grid" id="extra-grid"></div>
  </main>

  <footer>
    Generated from <code>lectures/compiled/</code>. Re-run <code>python3 site/build_site.py</code> to refresh.
  </footer>

  <div class="modal" id="modal" aria-hidden="true">
    <div class="modal-bar">
      <h2 id="modal-title"></h2>
      <a class="icon-btn" id="modal-open" target="_blank" rel="noopener">Open in new tab &nearr;</a>
      <a class="icon-btn" id="modal-download" download>Download &darr;</a>
      <button class="icon-btn" id="modal-close">Close &times;</button>
    </div>
    <iframe id="modal-frame" title="PDF viewer"></iframe>
  </div>

<script>
const DATA = /*__DATA__*/;

const lectureGrid = document.getElementById('lecture-grid');
const extraGrid = document.getElementById('extra-grid');
const countEl = document.getElementById('count');
const noResults = document.getElementById('no-results');
const searchEl = document.getElementById('search');

const modal = document.getElementById('modal');
const modalFrame = document.getElementById('modal-frame');
const modalTitle = document.getElementById('modal-title');
const modalOpen = document.getElementById('modal-open');
const modalDownload = document.getElementById('modal-download');

function openViewer(title, href) {
  modalTitle.textContent = title;
  modalFrame.src = href;
  modalOpen.href = href;
  modalDownload.href = href;
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
}
function closeViewer() {
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  modalFrame.src = 'about:blank';
}
document.getElementById('modal-close').addEventListener('click', closeViewer);
modal.addEventListener('click', (e) => { if (e.target === modal) closeViewer(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeViewer(); });

function pad(n) { return String(n).padStart(2, '0'); }

function makeButton(label, cls, title, href) {
  const b = document.createElement('button');
  b.className = 'btn ' + cls;
  b.textContent = label;
  if (href) {
    b.addEventListener('click', () => openViewer(title, href));
  } else {
    b.disabled = true;
  }
  return b;
}

function renderLectures(filter) {
  lectureGrid.innerHTML = '';
  const q = filter.trim().toLowerCase();
  let shown = 0;
  for (const lec of DATA.lectures) {
    const label = 'L' + pad(lec.num);
    const haystack = (label + ' ' + lec.title).toLowerCase();
    if (q && !haystack.includes(q)) continue;
    shown++;

    const card = document.createElement('div');
    card.className = 'card';

    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = 'Lecture ' + lec.num;
    card.appendChild(badge);

    const h3 = document.createElement('h3');
    h3.textContent = lec.title;
    card.appendChild(h3);

    const actions = document.createElement('div');
    actions.className = 'actions';
    actions.appendChild(makeButton('Notes', 'notes', label + ' Notes \u2014 ' + lec.title, lec.notes));
    actions.appendChild(makeButton('Slides', 'slides', label + ' Slides \u2014 ' + lec.title, lec.slides));
    card.appendChild(actions);

    lectureGrid.appendChild(card);
  }
  countEl.textContent = shown + ' / ' + DATA.lectures.length + ' lectures';
  noResults.style.display = shown === 0 ? 'block' : 'none';
}

function renderExtras() {
  extraGrid.innerHTML = '';
  for (const x of DATA.extras) {
    const card = document.createElement('div');
    card.className = 'card extra-card';

    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = 'Resource';
    card.appendChild(badge);

    const h3 = document.createElement('h3');
    h3.textContent = x.title;
    card.appendChild(h3);

    if (x.desc) {
      const d = document.createElement('div');
      d.className = 'desc';
      d.textContent = x.desc;
      card.appendChild(d);
    }

    const actions = document.createElement('div');
    actions.className = 'actions';
    actions.appendChild(makeButton('Open', 'notes', x.title, x.href));
    card.appendChild(actions);

    extraGrid.appendChild(card);
  }
}

searchEl.addEventListener('input', () => renderLectures(searchEl.value));
renderLectures('');
renderExtras();
</script>
</body>
</html>
"""


def main():
    if not COMPILED.exists():
        raise SystemExit(f"Compiled PDFs not found at {COMPILED}")
    lectures, extras = scan()
    html = build_html(lectures, extras)
    out = HERE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  {len(lectures)} lectures, {len(extras)} resources")


if __name__ == "__main__":
    main()
