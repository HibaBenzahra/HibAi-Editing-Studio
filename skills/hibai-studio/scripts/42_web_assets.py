# -*- coding: utf-8 -*-
"""Real logos, icons and website screenshots for a project → <work>/assets/  (Windows · macOS · Linux)

  python 42_web_assets.py <work> logo  <brand> [--color brand|theme|#hex]   ← official brand logo (Simple Icons, 3,000+ brands, CC0)
  python 42_web_assets.py <work> icon  <set:name> [--color theme|#hex]      ← UI icon (Iconify: lucide, tabler, ph, mdi, solar…)
  python 42_web_assets.py <work> shot  <url> [--mobile] [--full] [--name x] ← screenshot of a public web page (Chrome)
  python 42_web_assets.py <work> find  <words>                              ← suggest logo slugs / icon names for a word
  python 42_web_assets.py <work> rec   <video> --name x [--from s] [--to s]  ← the user's screen recording → frames for HK.spot

Examples:  logo claude · logo chatgpt · logo instagram · icon lucide:folder-open · icon ph:sparkle-fill · shot https://claude.ai --mobile
Every file gets a .json next to it (source + licence). Logos keep their real brand colour unless --color says otherwise.
Behind a login (a private feed, a paid app)? The page can't be captured — ask the user for a screenshot / screen recording,
or rebuild the interface in code (see SKILL.md «real interfaces»).
"""
import json, os, re, subprocess, sys, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

UA = {"User-Agent": "hibai-studio-skill (asset fetch)"}
HERE = os.path.dirname(os.path.abspath(__file__))

def get(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower().replace("+", "plus").replace(".", "dot").replace("&", "and"))

def theme_color(work, key="acc"):
    p = os.path.join(work, "theme.json")
    return json.load(open(p, encoding="utf-8")).get(key) if os.path.exists(p) else None

def save(work, name, data, meta):
    d = os.path.join(work, "assets"); os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name)
    open(path, "wb").write(data)
    json.dump(meta, open(os.path.splitext(path)[0] + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ assets/{name}  ({meta.get('license', '')})")
    return path

# Simple Icons: slug list with official colours (cached once)
SI_CACHE = os.path.join(os.path.expanduser("~"), ".hibai-studio", "simple-icons.json")
def si_index():
    if not os.path.exists(SI_CACHE):
        os.makedirs(os.path.dirname(SI_CACHE), exist_ok=True)
        data = get("https://cdn.jsdelivr.net/npm/simple-icons@latest/data/simple-icons.json", 60)
        open(SI_CACHE, "wb").write(data)
    d = json.load(open(SI_CACHE, encoding="utf-8"))
    return d if isinstance(d, list) else d.get("icons", [])

def logo(work, brand, color):
    idx = si_index(); want = slug(brand)
    hit = next((i for i in idx if slug(i.get("slug") or i["title"]) == want or slug(i["title"]) == want), None)
    if not hit:
        close = [i["title"] for i in idx if want in slug(i["title"])][:8]
        sys.exit(f"❌ no logo for «{brand}»" + (f" — close: {', '.join(close)}" if close else " — try `find`, a screenshot, or rebuild it"))
    s = hit.get("slug") or slug(hit["title"])
    svg = get(f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{s}.svg").decode("utf-8")
    col = "#" + hit["hex"] if color in (None, "brand") else (theme_color(work) if color == "theme" else color)
    svg = svg.replace("<svg ", f'<svg fill="{col}" ', 1)
    save(work, f"logo-{s}.svg", svg.encode("utf-8"),
         {"kind": "logo", "brand": hit["title"], "color": col, "brandHex": "#" + hit["hex"],
          "source": "https://simpleicons.org", "license": "CC0 (Simple Icons) — brand marks belong to their owners; editorial use"})

def icon(work, spec, color):
    if ":" not in spec:
        sys.exit("❌ icon needs set:name, e.g. lucide:folder-open")
    prefix, name = spec.split(":", 1)
    col = theme_color(work) if color in (None, "theme") else color
    q = "?" + urllib.parse.urlencode({"color": col}) if col else ""
    try:
        svg = get(f"https://api.iconify.design/{prefix}/{name}.svg{q}")
    except Exception:
        sys.exit(f"❌ no icon {spec} — try `find {name}`")
    save(work, f"icon-{prefix}-{name}.svg", svg,
         {"kind": "icon", "icon": spec, "color": col, "source": f"https://icon-sets.iconify.design/{prefix}/",
          "license": "open icon set via Iconify (Lucide ISC · Tabler MIT · Phosphor MIT · MDI Apache-2.0…)"})

def find(words):
    q = urllib.parse.quote(words)
    try:
        r = json.loads(get(f"https://api.iconify.design/search?query={q}&limit=24&prefixes=lucide,tabler,ph,solar,mdi"))
        print("icons:", "  ".join(r.get("icons", [])[:24]) or "—")
    except Exception as e:
        print("icons: search failed", e)
    want = slug(words)
    print("logos:", "  ".join(i["title"] for i in si_index() if want and want in slug(i["title"]))[:600] or "—")

def shot(work, url, mobile, full, name):
    node = r"""
const path=require('path'),fs=require('fs');
const pp=require(path.join(process.argv[2],'node_modules','puppeteer-core'));
const cands=[process.env.CHROME_PATH,'C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
 (process.env.LOCALAPPDATA||'')+'/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
 '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser'];
const exe=cands.find(c=>c&&fs.existsSync(c));
(async()=>{const b=await pp.launch({executablePath:exe,headless:'new',args:['--no-sandbox','--hide-scrollbars']});
 const p=await b.newPage(); const mob=process.argv[5]==='1';
 await p.setViewport(mob?{width:430,height:932,deviceScaleFactor:3,isMobile:true,hasTouch:true}:{width:1440,height:900,deviceScaleFactor:2});
 if(mob) await p.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1');
 await p.goto(process.argv[3],{waitUntil:'networkidle2',timeout:60000}).catch(()=>{});
 await new Promise(r=>setTimeout(r,2500));
 await p.screenshot({path:process.argv[4],fullPage:process.argv[6]==='1'}); console.log(await p.title()); await b.close();})();
"""
    d = os.path.join(work, "assets"); os.makedirs(d, exist_ok=True)
    nm = name or slug(urllib.parse.urlparse(url).netloc + urllib.parse.urlparse(url).path)[:40] or "page"
    out = os.path.join(d, f"shot-{nm}.png")
    js = os.path.join(d, "_shot.js"); open(js, "w", encoding="utf-8").write(node)
    skill = os.path.dirname(HERE)
    r = subprocess.run(["node", js, skill, url, out, "1" if mobile else "0", "1" if full else "0"], capture_output=True, text=True, encoding="utf-8")
    os.remove(js)
    if r.returncode or not os.path.exists(out):
        sys.exit("❌ screenshot failed: " + (r.stderr or r.stdout)[-300:])
    json.dump({"kind": "screenshot", "url": url, "title": r.stdout.strip(), "mobile": mobile,
               "license": "screenshot of a public page — editorial use"}, open(out[:-4] + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ assets/shot-{nm}.png  «{r.stdout.strip()[:60]}»")

def rec(work, src, name, t0, t1):
    """screen recording → assets/rec/<name>/0001.jpg … (30 fps, 1080 wide) for HK.spot(t, {rec:{name, n}}) — HK.rec(name, n) preloads"""
    if not os.path.exists(src): sys.exit(f"❌ no such video: {src}")
    nm = slug(name or os.path.splitext(os.path.basename(src))[0])[:40] or "rec"
    d = os.path.join(work, "assets", "rec", nm); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith(".jpg"): os.remove(os.path.join(d, f))
    cut = (["-ss", str(t0)] if t0 else []) + (["-to", str(t1)] if t1 else [])
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *cut, "-i", src, "-vf", "fps=30,scale=1080:-2", "-q:v", "2",
                    os.path.join(d, "%04d.jpg")], check=True)
    n = len([f for f in os.listdir(d) if f.endswith(".jpg")])
    from PIL import Image
    w, h = Image.open(os.path.join(d, "0001.jpg")).size
    json.dump({"kind": "screen recording", "src": os.path.basename(src), "n": n, "fps": 30, "size": [w, h]},
              open(d + ".json", "w", encoding="utf-8"), indent=1)
    print(f"✅ assets/rec/{nm}/ · {n} frames ({n / 30:.1f} s, {w}x{h}) → HK.rec('{nm}', {n}) · HK.spot(t, {{rec:{{name:'{nm}', n:{n}}}, …}})")

if __name__ == "__main__":
    VAL = ("--color", "--name", "--from", "--to")           # options that take a value
    a = [x for i, x in enumerate(sys.argv[1:]) if not x.startswith("--") and (i == 0 or sys.argv[i] not in VAL)]
    flags = sys.argv[1:]
    opt = lambda k: flags[flags.index(k) + 1] if k in flags and flags.index(k) + 1 < len(flags) else None
    if len(a) < 3:
        sys.exit(__doc__)
    work, cmd, arg = os.path.abspath(a[0]), a[1], " ".join(a[2:])
    for k in ("--color", "--name", "--from", "--to"):                       # option values aren't part of the argument
        v = opt(k)
        if v and arg.endswith(v): arg = arg[: -len(v)].strip()
    if cmd == "logo": logo(work, arg, opt("--color"))
    elif cmd == "icon": icon(work, arg, opt("--color"))
    elif cmd == "shot": shot(work, arg, "--mobile" in flags, "--full" in flags, opt("--name"))
    elif cmd == "find": find(arg)
    elif cmd == "rec": rec(work, arg, opt("--name"), opt("--from"), opt("--to"))
    else: sys.exit(__doc__)
