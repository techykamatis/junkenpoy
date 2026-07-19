#!/usr/bin/env python3
"""Render the OKF markdown bundle in this folder to browsable static HTML.

Canonical source stays the .md files (OKF v0.1). This produces matching .html so
the wiki is viewable on GitHub Pages at /junkenpoy/wiki/. Run: python3 _render.py
"""
import re
import glob
import os
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
PHONE_DISPLAY = "970-485-8701"
PHONE_TEL = "+19704858701"

NAV = [
    ("index.html", "Home"),
    ("about.html", "About"),
    ("services.html", "Services"),
    ("service-area.html", "Service Area"),
    ("pricing.html", "Pricing"),
    ("booking.html", "Book"),
    ("faq.html", "FAQ"),
]

JSONLD = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Junk En Poy LLC",
  "description": "Locally owned junk removal and hauling service in Summit County, Colorado.",
  "telephone": "+1-970-485-8701",
  "email": "junkenpoy@gmail.com",
  "url": "https://techykamatis.github.io/junkenpoy/",
  "areaServed": [
    {"@type": "City", "name": "Breckenridge"},
    {"@type": "City", "name": "Frisco"},
    {"@type": "City", "name": "Silverthorne"},
    {"@type": "City", "name": "Dillon"},
    {"@type": "City", "name": "Keystone"},
    {"@type": "City", "name": "Blue River"}
  ],
  "address": {"@type": "PostalAddress", "addressRegion": "CO", "addressCountry": "US"},
  "sameAs": [
    "https://www.facebook.com/share/1B4aPGw6PC",
    "https://www.instagram.com/junk.en.poy"
  ]
}
</script>'''

CSS = '''
:root{--ink:#1a1d1a;--paper:#f7f6f1;--green:#2e7d32;--green-d:#1b5e20;--accent:#f4a300;--muted:#5c6560;--line:#e3e1d8}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--paper);line-height:1.65}
a{color:var(--green-d)}
.topbar{background:var(--green-d);color:#fff}
.topbar .wrap{display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;max-width:900px;margin:0 auto;padding:.6rem 1.1rem}
.brand{font-weight:800;letter-spacing:.3px;color:#fff;text-decoration:none;font-size:1.15rem}
.brand span{color:var(--accent)}
.callbtn{background:var(--accent);color:#1a1d1a;font-weight:800;text-decoration:none;padding:.5rem .9rem;border-radius:999px;white-space:nowrap}
nav.main{background:var(--green);border-top:1px solid rgba(255,255,255,.15)}
nav.main .wrap{max-width:900px;margin:0 auto;padding:.3rem 1.1rem;display:flex;gap:.2rem;flex-wrap:wrap}
nav.main a{color:#eaf5ea;text-decoration:none;padding:.4rem .7rem;border-radius:6px;font-size:.92rem;font-weight:600}
nav.main a:hover,nav.main a.active{background:rgba(255,255,255,.18);color:#fff}
main{max-width:760px;margin:0 auto;padding:1.6rem 1.1rem 3rem}
h1{font-size:2rem;line-height:1.2;margin:.2rem 0 1rem}
h2{font-size:1.35rem;margin:2rem 0 .6rem;padding-top:.4rem;border-top:2px solid var(--line)}
h1+*,h2+*{margin-top:.4rem}
ul{padding-left:1.2rem}
li{margin:.25rem 0}
.pill{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--green-d);background:#e4efe4;border:1px solid #cfe3cf;padding:.15rem .5rem;border-radius:999px;margin-bottom:.7rem}
.cta{margin:1.6rem 0;padding:1.1rem 1.2rem;background:#fff;border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:10px}
.cta a.big{display:inline-block;background:var(--green-d);color:#fff;font-weight:800;text-decoration:none;padding:.7rem 1.2rem;border-radius:999px;margin-top:.5rem}
footer{background:var(--ink);color:#cfd3cf;font-size:.9rem}
footer .wrap{max-width:760px;margin:0 auto;padding:1.4rem 1.1rem}
footer a{color:var(--accent)}
.homecards{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin:1.2rem 0}
.homecards a{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:.9rem 1rem;text-decoration:none;color:var(--ink)}
.homecards a:hover{border-color:var(--green)}
.homecards b{color:var(--green-d)}
@media(max-width:560px){.homecards{grid-template-columns:1fr}h1{font-size:1.6rem}}
'''

STICKY = f'''<div class="cta">
<strong>Free, same-day estimate.</strong> Text a photo of your junk or give us a call — we do all the loading.
<br><a class="big" href="sms:{PHONE_TEL}">Text a photo</a> &nbsp; <a class="big" href="tel:{PHONE_TEL}" style="background:var(--accent);color:#1a1d1a">Call {PHONE_DISPLAY}</a>
</div>'''


def parse(md_path):
    raw = open(md_path, encoding="utf-8").read()
    meta = {}
    body = raw
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    return meta, body


def title_of(meta, body, slug):
    if meta.get("title"):
        return meta["title"]
    h = re.search(r"^#\s+(.+)$", body, re.M)
    return h.group(1).strip() if h else slug


def render(md_path):
    slug = os.path.splitext(os.path.basename(md_path))[0]
    meta, body = parse(md_path)
    title = title_of(meta, body, slug)
    desc = meta.get("description", "Locally owned junk removal in Summit County, CO. Call or text 970-485-8701.")

    html_body = markdown.markdown(body, extensions=["extra", "sane_lists"])
    # OKF links are absolute bundle-relative (/page.md). This is a flat bundle, so map
    # /page.md and page.md alike to the sibling page.html for the published site.
    html_body = re.sub(r'href="/([^"/:]+?)\.md"', r'href="\1.html"', html_body)
    html_body = re.sub(r'href="([^":/]+?)\.md"', r'href="\1.html"', html_body)
    # Drop the leading H1 (we render our own header block) to avoid duplication.
    html_body = re.sub(r"^\s*<h1>.*?</h1>", "", html_body, count=1, flags=re.S)

    pill = f'<span class="pill">{meta["type"]}</span>' if meta.get("type") else ""
    nav_parts = []
    for href, label in NAV:
        cls = ' class="active"' if href == slug + ".html" else ""
        nav_parts.append(f'<a href="{href}"{cls}>{label}</a>')
    nav = "".join(nav_parts)

    page_title = f"{title} — Junk En Poy" if slug != "index" else "Junk En Poy — Junk Removal Wiki | Summit County, CO"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Junk En Poy LLC">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://techykamatis.github.io/junkenpoy/wiki/{slug}.html">
<meta property="og:image" content="https://techykamatis.github.io/junkenpoy/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Junk En Poy — Junk Removal & Hauling, Summit County CO.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page_title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://techykamatis.github.io/junkenpoy/og-image.png">
<link rel="canonical" href="https://techykamatis.github.io/junkenpoy/wiki/{slug}.html">
<style>{CSS}</style>
{JSONLD}
</head>
<body>
<header class="topbar">
  <div class="wrap">
    <a class="brand" href="index.html">Junk <span>En</span> Poy</a>
    <a class="callbtn" href="tel:{PHONE_TEL}">📞 {PHONE_DISPLAY}</a>
  </div>
</header>
<nav class="main"><div class="wrap">{nav}</div></nav>
<main>
  {pill}
  <h1>{title}</h1>
  {html_body}
  {STICKY}
</main>
<footer><div class="wrap">
  <strong>Junk En Poy LLC</strong> — junk removal &amp; hauling, Summit County, CO<br>
  Call/Text <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a> ·
  <a href="mailto:junkenpoy@gmail.com">junkenpoy@gmail.com</a> ·
  <a href="../">Main site</a><br>
  <span style="opacity:.6">Structured with the Open Knowledge Format (OKF v0.1).</span>
</div></footer>
</body>
</html>'''


def main():
    count = 0
    for md_path in sorted(glob.glob(os.path.join(HERE, "*.md"))):
        slug = os.path.splitext(os.path.basename(md_path))[0]
        if slug == "log":
            continue  # reserved OKF history file — kept as .md, not published as a page
        out = os.path.join(HERE, slug + ".html")
        open(out, "w", encoding="utf-8").write(render(md_path))
        count += 1
        print("rendered", slug + ".html")
    print(f"done: {count} pages")


if __name__ == "__main__":
    main()
