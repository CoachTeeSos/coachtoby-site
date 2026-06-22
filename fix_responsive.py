import re

with open('index.html') as f:
    content = f.read()

# 1. Fix viewport meta — remove maximum-scale and user-scalable=no (bad for accessibility)
content = content.replace(
    'meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"',
    'meta name="viewport" content="width=device-width,initial-scale=1.0"'
)
print("Viewport fixed")

# 2. Add comprehensive responsive CSS before </style>
responsive_css = """
/* ============================================================
   RESPONSIVE — Phone-first design
   ============================================================ */

/* Base: phones (320px+) */
body { padding-bottom: 72px; }
.sp { padding: 12px 12px 80px; max-width: 100%; }
.tb { padding: 10px 12px; }
.tb-t { font-size: 1rem; }

/* Bottom nav: compact on small phones */
.bn { height: 52px; }
.bn-in { padding: 0 4px; }
.bn-i { min-width: 44px; min-height: 40px; padding: 4px 6px; gap: 2px; font-size: 0.6rem; }
.bn-ic { width: 18px; height: 18px; }
.bn-ic svg { width: 16px; height: 16px; stroke-width: 1.5; }

/* Search overlay */
.srch-top { padding: 8px 12px; }
.srch-top input { padding: 8px 12px; font-size: 0.85rem; }
.srch-res-item { padding: 10px 12px; font-size: 0.8rem; }
.srch-res-item .srch-ic { width: 28px; height: 28px; font-size: 0.7rem; }

/* Top bar search icon */
.tb-search { width: 32px; height: 32px; }
.tb-search svg { width: 16px; height: 16px; }

/* Module content: tables need horizontal scroll on phones */
table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; white-space: nowrap; }
th, td { padding: 4px 6px !important; font-size: 0.65rem !important; }

/* Grid layouts: single column on phones */
[style*="grid-template-columns:repeat(2"] { grid-template-columns: 1fr !important; }
[style*="grid-template-columns:repeat(3"] { grid-template-columns: 1fr !important; }
[style*="grid-template-columns:repeat(4"] { grid-template-columns: repeat(2, 1fr) !important; }

/* Ref boxes and cards */
.ref-box { padding: 8px 10px !important; font-size: 0.75rem !important; }
.ref-box-title { font-size: 0.8rem !important; }

/* Hero sections */
.hero { padding: 16px 0 !important; }
.hero h1 { font-size: 1.4rem !important; }
.hero p { font-size: 0.8rem !important; }

/* Section headers */
.sec-h { padding: 8px 0 !important; }
.sec-t { font-size: 0.85rem !important; }

/* List items */
.li { padding: 10px 12px !important; }
.li-ic { width: 32px !important; height: 32px !important; font-size: 0.8rem !important; }
.li-t { font-size: 0.85rem !important; }
.li-sub { font-size: 0.7rem !important; }

/* Buttons */
.btn { padding: 8px 14px !important; font-size: 0.8rem !important; min-height: 36px !important; }
.btn-s { padding: 6px 10px !important; min-height: 30px !important; font-size: 0.7rem !important; }

/* SVG diagrams: scale to container */
svg[max-width] { max-width: 100% !important; height: auto !important; }

/* Piano and staff containers */
[id$="-container"] { overflow-x: auto; -webkit-overflow-scrolling: touch; }

/* Toast */
.ft { bottom: 60px !important; font-size: 0.75rem !important; padding: 8px 14px !important; }

/* Achievement popup */
.ap { max-width: 90vw !important; padding: 14px !important; }
.ap-t { font-size: 1rem !important; }

/* Auth inputs */
.input { padding: 10px 12px !important; font-size: 0.85rem !important; }
.c label { font-size: 0.75rem !important; }

/* Progress bars */
.pr { height: 6px !important; }

/* ============================================================
   TABLET (600px+)
   ============================================================ */
@media (min-width: 600px) {
  body { padding-bottom: 80px; }
  .sp { padding: 20px 20px 100px; max-width: 540px; }
  .tb { padding: 14px 20px; }
  .tb-t { font-size: 1.1rem; }
  .bn { height: 56px; }
  .bn-in { padding: 0 8px; }
  .bn-i { min-width: 52px; min-height: 44px; padding: 4px 8px; font-size: 0.65rem; }
  .bn-ic { width: 20px; height: 20px; }
  .bn-ic svg { width: 18px; height: 18px; stroke-width: 1.6; }
  .tb-search { width: 36px; height: 36px; }
  .tb-search svg { width: 18px; height: 18px; }
  th, td { padding: 6px 8px !important; font-size: 0.72rem !important; }
  [style*="grid-template-columns:repeat(2"] { grid-template-columns: repeat(2, 1fr) !important; }
  .ref-box { padding: 12px !important; font-size: 0.78rem !important; }
  .hero h1 { font-size: 1.8rem !important; }
  .li-ic { width: 36px !important; height: 36px !important; }
}

/* ============================================================
   LARGE TABLET / DESKTOP (900px+)
   ============================================================ */
@media (min-width: 900px) {
  .sp { max-width: 640px; }
  [style*="grid-template-columns:repeat(4"] { grid-template-columns: repeat(4, 1fr) !important; }
  [style*="grid-template-columns:repeat(3"] { grid-template-columns: repeat(3, 1fr) !important; }
}
"""

style_end = content.find('</style>')
content = content[:style_end] + responsive_css + content[style_end:]
print("Responsive CSS added")

with open('index.html', 'w') as f:
    f.write(content)

# Validate
import subprocess, os
with open('index.html') as f:
    c = f.read()
s = c.find('<script>') + len('<script>')
e = c.find('</script>', s)
js = c[s:e]
with open('_check.js', 'w') as f:
    f.write(js)
r = subprocess.run(['node', '--check', '_check.js'], capture_output=True, text=True)
os.remove('_check.js')

if r.returncode == 0:
    print(f"JS VALID — SAVED ({len(c)} chars)")
else:
    print(f"JS ERROR: {r.stderr[:200]}")
