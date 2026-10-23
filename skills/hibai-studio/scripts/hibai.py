#!/usr/bin/env python3
"""HibAI Studio — talking video -> ready-to-post 9:16 reel.

One command, many steps. Every step reads and writes plain JSON inside a
work folder, so any step can be re-run on its own.

    python hibai.py doctor
    python hibai.py new <work> <video>
    python hibai.py dashboard <work>          # HibAI brief page, writes brief.json
    python hibai.py transcribe <work>         # word-timed transcript
    python hibai.py script <work>             # numbered sentences + retake hints
    python hibai.py fix <work> fixes.json     # corrected wording
    python hibai.py drop <work> 3 5 | restore <work> 3
    python hibai.py plan <work>               # silence + dropped lines -> edit list
    python hibai.py render <work> [--preview]  # --preview = fast, low quality
    python hibai.py sheet <work> [t1 t2 ...]  # 6-frame contact sheet
    python hibai.py srt <work>
    python hibai.py check <work>

Work folder files:
    project.json   source video facts
    brief.json     what the user wants (from the dashboard)
    transcript.json sentences -> words with source times (+ text fixes, drops)
    edit.json      kept source ranges, zoom per range, output word timings
    captions.ass   styled captions that ffmpeg burns in
    final.mp4      the reel
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
FONTS = os.path.join(SKILL, "fonts")
W_OUT, H_OUT, FPS = 1080, 1920, 30

# Instagram / TikTok buttons cover these areas, so nothing important goes there.
SAFE_TOP = 150
CAPTION_BOTTOM = 1460
SIDE_MARGIN = 140

DEFAULT_BRIEF = {
    "language": "ar",            # whisper language: ar | en | fr | auto
    "video_type": "talking",
    "goal": "",
    "hook": "",
    "colors": {"main": "#8eff01", "accent": "#8b53fe", "text": "#ffffff", "ground": "#0d0f14"},
    "font": "Segoe UI",
    "caption_style": "pop",      # pop | clean | box | none
    "caption_size": "big",       # medium | big | huge
    "words_per_card": 3,
    "pace": "normal",            # fast | normal | calm
    "zoom": True,
    "progress_bar": True,
    "handle": "",
    "cta": "",
    "notes": "",
}

PACE = {  # gap between words that still counts as "one breath", zoom set
    "fast":   {"gap": 0.22, "pad": 0.08, "zooms": [1.0, 1.10, 1.0, 1.06, 1.14, 1.0, 1.08]},
    "normal": {"gap": 0.40, "pad": 0.12, "zooms": [1.0, 1.07, 1.0, 1.04, 1.10, 1.0]},
    "calm":   {"gap": 1.20, "pad": 0.25, "zooms": [1.0, 1.0, 1.04, 1.0]},
}
SIZE = {"medium": 74, "big": 88, "huge": 104}


# ---------- small helpers ----------

def die(msg):
    print("❌ " + msg)
    sys.exit(1)


def jload(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        die(f"missing {os.path.basename(path)} — run the step before this one")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def jsave(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration:stream=codec_type,width,height,color_transfer",
               "-of", "json", path]).stdout
    data = json.loads(out or "{}")
    info = {"duration": float(data.get("format", {}).get("duration", 0) or 0), "audio": False}
    for st in data.get("streams", []):
        if st.get("codec_type") == "video" and "width" not in info:
            info.update(width=st["width"], height=st["height"], hdr=st.get("color_transfer") in ("arib-std-b67", "smpte2084"))
        if st.get("codec_type") == "audio":
            info["audio"] = True
    return info


def brief(work):
    b = json.loads(json.dumps(DEFAULT_BRIEF))
    user = jload(os.path.join(work, "brief.json"), {})
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(b.get(k), dict):
            b[k].update(v)
        else:
            b[k] = v
    return b


def ass_color(hexcode, alpha="00"):
    h = hexcode.lstrip("#")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ass_time(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_text(s):
    s = s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")
    # keep "20%" / "10x" in one piece inside right-to-left lines
    # (isolates, not marks: they don't change which way the whole line reads)
    return f"⁦{s}⁩" if re.search(r"\d", s) else s


# ---------- doctor / new ----------

def cmd_doctor(_args):
    ok = True
    for tool, why in (("ffmpeg", "cuts and builds the video"), ("ffprobe", "reads video info")):
        found = shutil.which(tool)
        print(("✅ " if found else "❌ ") + f"{tool} — {why}")
        ok &= bool(found)
    try:
        import whisper  # noqa: F401
        print("✅ whisper — writes down the speech with word timing")
    except ImportError:
        ok = False
        print("❌ whisper — install with: python -m pip install -U openai-whisper")
    out = run(["ffmpeg", "-hide_banner", "-filters"]).stdout
    has_subs = " subtitles " in out
    print(("✅ " if has_subs else "❌ ") + "caption burner (ffmpeg libass)")
    ok &= has_subs
    fonts = [f for f in os.listdir(FONTS)] if os.path.isdir(FONTS) else []
    print(f"ℹ️  extra fonts in skill: {', '.join(fonts) or 'none (system fonts are used)'}")
    print("READY" if ok else "MISSING TOOLS")
    sys.exit(0 if ok else 2)


def cmd_new(args):
    work, src = os.path.abspath(args[0]), os.path.abspath(args[1])
    if not os.path.exists(src):
        die(f"video not found: {src}")
    os.makedirs(work, exist_ok=True)
    info = probe(src)
    if not info.get("width"):
        die("that file has no picture in it")
    if not info["audio"]:
        die("that video has no sound — this mode needs someone talking")
    info["src"] = src
    jsave(os.path.join(work, "project.json"), info)
    shape = "vertical" if info["height"] > info["width"] else "landscape"
    print(f"🎬 {info['duration']:.1f}s · {info['width']}x{info['height']} ({shape})"
          + (" · iPhone HDR" if info.get("hdr") else ""))


# ---------- transcript ----------

def cmd_transcribe(args):
    work = os.path.abspath(args[0])
    model_name = args[args.index("--model") + 1] if "--model" in args else "medium"
    proj = jload(os.path.join(work, "project.json"))
    lang = brief(work)["language"]
    wav = os.path.join(work, "voice.wav")
    r = run(["ffmpeg", "-v", "error", "-y", "-i", proj["src"], "-vn", "-ac", "1", "-ar", "16000", wav])
    if r.returncode:
        die(r.stderr.strip()[-400:])
    import whisper
    print(f"🎧 listening with the '{model_name}' model…", flush=True)
    model = whisper.load_model(model_name)
    res = model.transcribe(wav, language=None if lang == "auto" else lang,
                           word_timestamps=True, fp16=False, verbose=None)
    sentences = []
    for seg in res["segments"]:
        words = [{"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3)}
                 for w in seg.get("words", []) if w["word"].strip()]
        if words:
            sentences.append({"words": words})
    jsave(os.path.join(work, "transcript.json"), {"language": res.get("language", lang), "sentences": sentences})
    print(f"✅ {len(sentences)} sentences, {sum(len(s['words']) for s in sentences)} words")


def sentence_text(s):
    return " ".join(w["w"] for w in s["words"])


def cmd_script(args):
    work = os.path.abspath(args[0])
    tr = jload(os.path.join(work, "transcript.json"))
    lines = []
    for i, s in enumerate(tr["sentences"]):
        mark = "  ✂️ dropped" if s.get("drop") else ""
        lines.append(f"[{i}] {s['words'][0]['s']:6.2f}s  {sentence_text(s)}{mark}")
    print("\n".join(lines))
    with open(os.path.join(work, "script.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    # A retake: the speaker says nearly the same line twice; the later one is usually the keeper.
    kept = [(i, s) for i, s in enumerate(tr["sentences"]) if not s.get("drop")]
    hints = []
    for (i, a), (j, b) in zip(kept, kept[1:]):
        if difflib.SequenceMatcher(None, sentence_text(a), sentence_text(b)).ratio() > 0.6:
            hints.append(i)
            print(f"🔁 [{i}] and [{j}] sound like a retake — suggest dropping [{i}]")
    if not hints:
        print("no retakes spotted")


def cmd_fix(args):
    """fixes.json: {"sentences": {"3": "the corrected words"}, "hot": ["word", ...]}"""
    work = os.path.abspath(args[0])
    path = os.path.join(work, "transcript.json")
    tr = jload(path)
    fx = jload(os.path.abspath(args[1]))
    for key, text in fx.get("sentences", {}).items():
        s = tr["sentences"][int(key)]
        new = text.split()
        old = s["words"]
        if len(new) == len(old):
            for w, t in zip(old, new):
                w["w"] = t
        else:
            # Different word count: spread the corrected words over the sentence by length.
            t0, t1 = old[0]["s"], old[-1]["e"]
            total = sum(len(t) for t in new) or 1
            acc, words = 0, []
            for t in new:
                a = t0 + (t1 - t0) * acc / total
                acc += len(t)
                words.append({"w": t, "s": round(a, 3), "e": round(t0 + (t1 - t0) * acc / total, 3)})
            s["words"] = words
            print(f"ℹ️ [{key}] word count changed ({len(old)}→{len(new)}), timing spread evenly")
    tr["hot"] = fx.get("hot", tr.get("hot", []))
    jsave(path, tr)
    print(f"✅ fixed {len(fx.get('sentences', {}))} sentences · {len(tr['hot'])} highlight words")


def cmd_drop(args, value=True):
    work = os.path.abspath(args[0])
    path = os.path.join(work, "transcript.json")
    tr = jload(path)
    for n in args[1:]:
        tr["sentences"][int(n)]["drop"] = value
    jsave(path, tr)
    print(("✂️ dropped " if value else "↩️ restored ") + ", ".join(args[1:]) + " — run plan again")


# ---------- edit plan ----------

def cmd_plan(args):
    work = os.path.abspath(args[0])
    proj = jload(os.path.join(work, "project.json"))
    tr = jload(os.path.join(work, "transcript.json"))
    b = brief(work)
    pace = PACE.get(b["pace"], PACE["normal"])
    dur = proj["duration"]

    # 1) source ranges = spoken words of kept sentences, joined when the pause is short
    ranges = []
    for si, s in enumerate(tr["sentences"]):
        if s.get("drop"):
            continue
        for w in s["words"]:
            a, e = max(0.0, w["s"] - pace["pad"]), min(dur, w["e"] + pace["pad"])
            if ranges and a - ranges[-1]["e"] <= pace["gap"] and ranges[-1]["sent"] <= si:
                ranges[-1]["e"] = max(ranges[-1]["e"], e)
            else:
                ranges.append({"s": a, "e": e, "sent": si})
    # padding can overlap neighbours — clamp
    for r0, r1 in zip(ranges, ranges[1:]):
        if r1["s"] < r0["e"]:
            mid = (r0["e"] + r1["s"]) / 2
            r0["e"], r1["s"] = mid, mid
    if not ranges:
        die("nothing left to keep — every sentence is dropped")

    # 2) zoom per range (punch-ins hide the jump cuts); calm pace holds a zoom for ≥4s
    zooms, zi, held = [], 0, 0.0
    for i, r in enumerate(ranges):
        if i and (b["pace"] != "calm" or held >= 4.0):
            zi, held = zi + 1, 0.0
        held += r["e"] - r["s"]
        zooms.append(pace["zooms"][zi % len(pace["zooms"])] if b["zoom"] else 1.0)

    # 3) output time for every kept word
    offset, out = 0.0, []
    for r in ranges:
        r["out"] = round(offset, 3)
        offset += r["e"] - r["s"]
    hot = set(tr.get("hot", []))

    def to_out(t):
        for r in ranges:
            if r["s"] - 1e-6 <= t <= r["e"] + 1e-6:
                return r["out"] + t - r["s"]
        return None

    for si, s in enumerate(tr["sentences"]):
        if s.get("drop"):
            continue
        words = []
        for w in s["words"]:
            a, e = to_out(w["s"]), to_out(w["e"])
            if a is None or e is None:
                continue
            words.append({"w": w["w"], "s": round(a, 3), "e": round(max(e, a + 0.1), 3), "hot": w["w"] in hot})
        if words:
            out.append({"sent": si, "words": words})

    edit = {"ranges": [{"s": round(r["s"], 3), "e": round(r["e"], 3), "out": r["out"], "zoom": z}
                       for r, z in zip(ranges, zooms)],
            "duration": round(offset, 3), "lines": out}
    jsave(os.path.join(work, "edit.json"), edit)
    cut = dur - offset
    print(f"✂️ {len(ranges)} pieces · {dur:.1f}s → {offset:.1f}s (removed {cut:.1f}s, {cut / dur * 100:.0f}%)")


# ---------- captions (.ass) ----------

def caption_cards(edit, per_card):
    """Split each sentence into small cards of a few words."""
    cards = []
    for line in edit["lines"]:
        ws = line["words"]
        chunk = []
        for w in ws:
            chunk.append(w)
            if len(chunk) >= per_card or sum(len(x["w"]) for x in chunk) > 20:
                cards.append(chunk)
                chunk = []
        if chunk:
            cards.append(chunk)
    starts = [max(0.0, c[0]["s"] - 0.05) for c in cards]
    timed = []
    for i, c in enumerate(cards):
        s = starts[i]
        e = c[-1]["e"] + 0.25
        if i + 1 < len(cards):
            e = min(e, starts[i + 1])  # never two cards on screen at once
        timed.append({"s": s, "e": max(e, s + 0.1), "words": c})
    if timed and timed[0]["s"] > 0.0:
        timed[0]["s"] = 0.0  # the first caption shows from frame one — the hook needs words
    return timed


def build_ass(work, edit, b):
    c = b["colors"]
    size = SIZE.get(b["caption_size"], 88)
    style = b["caption_style"]
    white, main, accent = ass_color(c["text"]), ass_color(c["main"]), ass_color(c["accent"])
    shadow = ass_color("#000000", "60")
    box = style == "box"
    border_style, outline, back = (3, 18, ass_color(c["ground"], "30")) if box else (1, 5, shadow)
    margin_v = H_OUT - CAPTION_BOTTOM
    head = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W_OUT}", f"PlayResY: {H_OUT}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",  # Encoding -1 = pick left-to-right or right-to-left per line
        f"Style: Cap,{b['font']},{size},{white},{white},{ass_color('#000000', '20') if not box else back},{back},-1,0,0,0,100,100,0,0,{border_style},{outline},{0 if box else 3},2,{SIDE_MARGIN},{SIDE_MARGIN},{margin_v},-1",
        f"Style: Hook,{b['font']},{int(size * 1.15)},{white},{white},{ass_color(c['ground'], '10')},{ass_color(c['ground'], '10')},-1,0,0,0,100,100,0,0,3,26,0,8,{SIDE_MARGIN - 40},{SIDE_MARGIN - 40},{SAFE_TOP + 130},-1",
        f"Style: Tag,{b['font']},46,{main},{main},{ass_color('#000000', '40')},{shadow},-1,0,0,0,100,100,0,0,1,3,2,8,{SIDE_MARGIN},{SIDE_MARGIN},{SAFE_TOP + 40},-1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    ev = []
    if style != "none":
        for card in caption_cards(edit, int(b["words_per_card"])):
            ws = card["words"]
            for j, w in enumerate(ws):
                a = card["s"] if j == 0 else w["s"]
                e = ws[j + 1]["s"] if j + 1 < len(ws) else card["e"]
                if e <= a:
                    continue
                parts = []
                for k, x in enumerate(ws):
                    t = ass_text(x["w"])
                    if k == j:
                        col = accent if x["hot"] else main
                        pop = r"\fscx118\fscy118\t(0,110,\fscx100\fscy100)" if style == "pop" else ""
                        parts.append(f"{{\\c{col}{pop}}}{t}{{\\r}}")
                    elif x["hot"] and k < j:
                        parts.append(f"{{\\c{accent}}}{t}{{\\r}}")
                    else:
                        parts.append(t)
                fade = r"{\fad(60,0)}" if j == 0 else ""
                ev.append(f"Dialogue: 0,{ass_time(a)},{ass_time(e)},Cap,,0,0,0,,{fade}{' '.join(parts)}")
    if b.get("hook"):
        ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(min(3.2, edit['duration']))},Hook,,0,0,0,,"
                  r"{\fad(0,250)\fscx92\fscy92\t(0,180,\fscx100\fscy100)}" + ass_text(b["hook"]))
    if b.get("handle"):
        ev.append(f"Dialogue: 1,{ass_time(3.2)},{ass_time(edit['duration'])},Tag,,0,0,0,,{{\\fad(300,0)\\alpha&H30&}}{ass_text(b['handle'])}")
    if b.get("cta"):
        t0 = max(0.0, edit["duration"] - 2.5)
        ev.append(f"Dialogue: 2,{ass_time(t0)},{ass_time(edit['duration'])},Hook,,0,0,0,,{{\\fad(200,0)}}{ass_text(b['cta'])}")
    path = os.path.join(work, "captions.ass")
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(head + ev) + "\n")
    return path


# ---------- render ----------

def crop_for(w, h, z):
    """9:16 window inside the source at zoom z, a bit above centre so the face stays in frame."""
    target = W_OUT / H_OUT
    if w / h > target:
        ch, cw = h, h * target
    else:
        cw, ch = w, w / target
    cw, ch = int(cw / z) // 2 * 2, int(ch / z) // 2 * 2
    x = (w - cw) // 2
    y = int((h - ch) * 0.3)
    return f"crop={cw}:{ch}:{x}:{y}"


def audio_chain(edit):
    parts, labels = [], []
    for i, r in enumerate(edit["ranges"]):
        parts.append(f"[0:a]atrim=start={r['s']:.3f}:end={r['e']:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.02,afade=t=out:st={max(0, r['e'] - r['s'] - 0.02):.3f}:d=0.02[a{i}]")
        labels.append(f"[a{i}]")
    parts.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[acat]")
    return parts


def measure_loudness(src, edit, work):
    fc = audio_chain(edit) + ["[acat]loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[ao]"]
    script = os.path.join(work, "_audio.ffscript")
    with open(script, "w", encoding="utf-8") as f:
        f.write(";\n".join(fc))
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-/filter_complex", script, "-map", "[ao]", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    return json.loads(m.group(0)) if m else None


def cmd_render(args):
    work = os.path.abspath(args[0])
    preview = "--preview" in args
    proj = jload(os.path.join(work, "project.json"))
    edit = jload(os.path.join(work, "edit.json"))
    b = brief(work)
    build_ass(work, edit, b)
    fontdir = os.path.join(work, "fonts")
    os.makedirs(fontdir, exist_ok=True)
    if os.path.isdir(FONTS):
        for f in os.listdir(FONTS):
            shutil.copy2(os.path.join(FONTS, f), fontdir)

    src, w, h = proj["src"], proj["width"], proj["height"]
    fc = []
    vl = []
    for i, r in enumerate(edit["ranges"]):
        fc.append(f"[0:v]trim=start={r['s']:.3f}:end={r['e']:.3f},setpts=PTS-STARTPTS,"
                  f"{crop_for(w, h, r['zoom'])},scale={W_OUT}:{H_OUT}:flags=lanczos,setsar=1,fps={FPS}[v{i}]")
        vl.append(f"[v{i}]")
    fc.append("".join(vl) + f"concat=n={len(vl)}:v=1:a=0[vcat]")
    dur = edit["duration"]
    if b["progress_bar"]:
        # a full-width strip that slides in from the left as the video plays
        fc.append(f"color=c=0x{b['colors']['main'].lstrip('#')}:s={W_OUT}x8:r={FPS}:d={dur:.3f}[bar]")
        fc.append(f"[vcat][bar]overlay=x='-w+w*t/{dur:.3f}':y={CAPTION_BOTTOM + 28}:eof_action=pass[vbar]")
    else:
        fc.append("[vcat]null[vbar]")
    # No colour grading on the person — only format + captions on top.
    fc.append("[vbar]format=yuv420p,subtitles=captions.ass:fontsdir=fonts[vo]")

    fc += audio_chain(edit)
    m = None if preview else measure_loudness(src, edit, work)
    if m:
        fc.append(f"[acat]loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                  f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
                  "aresample=48000[ao]")
    else:
        fc.append("[acat]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]")

    script = os.path.join(work, "_video.ffscript")
    with open(script, "w", encoding="utf-8") as f:
        f.write(";\n".join(fc))
    out = os.path.join(work, "preview.mp4" if preview else "final.mp4")
    quality = ["-preset", "veryfast", "-crf", "28"] if preview else ["-preset", "slow", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-/filter_complex", "_video.ffscript",
           "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", *quality, "-pix_fmt", "yuv420p",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print(f"🎞️ building {'a quick preview' if preview else 'the final reel'} ({dur:.1f}s)…", flush=True)
    r = run(cmd, cwd=work)
    if r.returncode:
        die(r.stderr.strip()[-800:])
    size = os.path.getsize(out) / 1048576
    print(f"✅ {os.path.basename(out)} · {dur:.1f}s · {size:.1f} MB")


# ---------- review ----------

def cmd_sheet(args):
    work = os.path.abspath(args[0])
    # whichever of final / preview was built last
    built = [os.path.join(work, n) for n in ("final.mp4", "preview.mp4") if os.path.exists(os.path.join(work, n))]
    if not built:
        die("no video yet — run render first")
    video = max(built, key=os.path.getmtime)
    dur = probe(video)["duration"]
    times = [float(x) for x in args[1:]] or [round(dur * f, 2) for f in (0.03, 0.2, 0.38, 0.56, 0.74, 0.92)]
    times = (times + times[-1:] * 6)[:6]
    tiles = []
    for i, t in enumerate(times):
        p = os.path.join(work, f"_tile{i}.jpg")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
             "-vf", f"scale=360:640,drawtext=text='{t:.1f}s':x=12:y=12:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=6", p])
        tiles.append(p)
    inputs = sum((["-i", p] for p in tiles), [])
    out = os.path.join(work, "sheet.jpg")
    r = run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
             "".join(f"[{i}:v]" for i in range(6)) + "xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0",
             "-q:v", "3", out])
    for p in tiles:
        os.remove(p)
    if r.returncode:
        die(r.stderr[-400:])
    print(f"🖼️ {out}")


def cmd_srt(args):
    work = os.path.abspath(args[0])
    edit = jload(os.path.join(work, "edit.json"))

    def t(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    srt, txt = [], []
    for i, line in enumerate(edit["lines"], 1):
        words = " ".join(w["w"] for w in line["words"])
        srt.append(f"{i}\n{t(line['words'][0]['s'])} --> {t(line['words'][-1]['e'] + 0.2)}\n{words}\n")
        txt.append(words)
    with open(os.path.join(work, "final.srt"), "w", encoding="utf-8") as f:
        f.write("\n".join(srt))
    with open(os.path.join(work, "final.txt"), "w", encoding="utf-8") as f:
        f.write(" ".join(txt) + "\n")
    print("✅ final.srt + final.txt")


def cmd_check(args):
    work = os.path.abspath(args[0])
    video = os.path.join(work, "final.mp4")
    info = probe(video)
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"])
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    size = os.path.getsize(video) / 1048576
    edit = jload(os.path.join(work, "edit.json"))
    first = caption_cards(edit, int(brief(work)["words_per_card"]))
    problems = []
    if lufs and abs(float(lufs[-1]) + 14) > 1.5:
        problems.append(f"loudness {lufs[-1]} LUFS (aim -14)")
    if peak and float(peak[-1]) > -1.0:
        problems.append(f"peak {peak[-1]} dB is too hot")
    if size > 30:
        problems.append(f"file is {size:.0f} MB (keep under 30)")
    if first and first[0]["s"] > 0.5:
        problems.append("first caption appears after 0.5s")
    if (info.get("width"), info.get("height")) != (W_OUT, H_OUT):
        problems.append(f"size is {info.get('width')}x{info.get('height')}")
    print(f"⏱️ {info['duration']:.1f}s · 🔊 {lufs[-1] if lufs else '?'} LUFS · peak {peak[-1] if peak else '?'} dB · 📦 {size:.1f} MB")
    print("✅ all checks pass" if not problems else "⚠️ " + " · ".join(problems))
    sys.exit(0 if not problems else 3)


def cmd_dashboard(args):
    sys.path.insert(0, HERE)
    import dashboard_server
    dashboard_server.serve(os.path.abspath(args[0]), keep="--keep" in args, open_browser="--no-open" not in args)


COMMANDS = {
    "doctor": cmd_doctor, "new": cmd_new, "dashboard": cmd_dashboard,
    "transcribe": cmd_transcribe, "script": cmd_script, "fix": cmd_fix,
    "drop": cmd_drop, "restore": lambda a: cmd_drop(a, False),
    "plan": cmd_plan, "render": cmd_render, "sheet": cmd_sheet, "srt": cmd_srt, "check": cmd_check,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
