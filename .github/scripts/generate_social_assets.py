from PIL import Image, ImageDraw, ImageFont, ImageOps
import json, os, textwrap
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
LOCAL_DATE = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
INPUT = ROOT / "daily-content" / (LOCAL_DATE + ".json")
if not INPUT.exists():
    raise FileNotFoundError("Missing daily brand brief: " + str(INPUT))
data = json.loads(INPUT.read_text(encoding="utf-8"))
OUT = ROOT / LOCAL_DATE
OUT.mkdir(exist_ok=True)
W, H = 1080, 1350

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Bold.ttf",
]
LATIN_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
LATIN_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def first_font(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    raise RuntimeError("Required font not found: " + " | ".join(candidates))

DEV_REG = first_font(FONT_CANDIDATES)
DEV_BOLD = first_font(FONT_BOLD_CANDIDATES)
LATIN_REG = first_font(LATIN_FONT_CANDIDATES)
LATIN_BOLD = first_font(LATIN_BOLD_CANDIDATES)

def font(size, bold=False, script="dev"):
    path = (LATIN_BOLD if bold else LATIN_REG) if script == "latin" else (DEV_BOLD if bold else DEV_REG)
    return ImageFont.truetype(path, size=size, layout_engine=ImageFont.Layout.RAQM)

def is_devanagari(ch):
    cp = ord(ch)
    return (0x0900 <= cp <= 0x097F) or (0xA8E0 <= cp <= 0xA8FF) or (0x1CD0 <= cp <= 0x1CFF)

def script_runs(value):
    runs, current, buf = [], None, []
    punctuation = " .,:;!?/\\|()[]{}@#%&—–-+·"
    for ch in str(value):
        if is_devanagari(ch):
            script = "dev"
        elif ch.isspace() or ch in punctuation:
            script = current or "latin"
        else:
            script = "latin"
        if current is not None and script != current:
            runs.append((current, "".join(buf)))
            buf = []
        current = script
        buf.append(ch)
    if buf:
        runs.append((current, "".join(buf)))
    return runs

def run_width(draw, value, fnt, script):
    if script == "dev":
        return draw.textlength(value, font=fnt, direction="ltr", language="mr")
    return draw.textlength(value, font=fnt, direction="ltr")

def draw_text(draw, xy, value, size, fill=None, bold=False, anchor=None):
    value = str(value)
    base_fill = fill or INK
    runs = script_runs(value)
    if not runs:
        return
    if len(runs) == 1:
        script, _ = runs[0]
        fnt = font(size, bold, script)
        kwargs = {"direction": "ltr"}
        if script == "dev":
            kwargs["language"] = "mr"
        draw.text(xy, value, font=fnt, fill=(ACCENT if script == "latin" else base_fill), anchor=anchor, **kwargs)
        return
    widths, total_width, max_height = [], 0, 0
    for script, part in runs:
        fnt = font(size, bold, script)
        width = run_width(draw, part, fnt, script)
        widths.append(width)
        sample = "अग्नि" if script == "dev" else "Ag"
        box = fnt.getbbox(sample)
        max_height = max(max_height, box[3] - box[1])
        total_width += width
    x, y = xy
    if anchor:
        if anchor[0] == "r":
            x -= total_width
        elif anchor[0] == "m":
            x -= total_width / 2
        if len(anchor) > 1 and anchor[1] == "m":
            y -= max_height / 2
    for (script, part), width in zip(runs, widths):
        fnt = font(size, bold, script)
        kwargs = {"direction": "ltr", "anchor": "lt"}
        if script == "dev":
            kwargs["language"] = "mr"
        draw.text((x, y), part, font=fnt, fill=(ACCENT if script == "latin" else base_fill), **kwargs)
        x += width

def draw_multiline(draw, xy, value, size, fill=None, spacing=8, bold=False):
    x, y = xy
    lines = str(value).splitlines()
    dev_f = font(size, bold, "dev")
    lat_f = font(size, bold, "latin")
    dev_box = dev_f.getbbox("अग्नि")
    lat_box = lat_f.getbbox("Ag")
    line_height = max(dev_box[3]-dev_box[1], lat_box[3]-lat_box[1], int(size * 1.2))
    for line in lines:
        draw_text(draw, (x, y), line, size, fill=fill, bold=bold)
        y += line_height + spacing
    return y - spacing

# BRANDSTUDIO approved light olive / white palette.
DEEP_OLIVE = (63, 74, 50)       # #3F4A32
OLIVE = (127, 143, 98)          # #7F8F62
WHITE = (255, 255, 255)         # #FFFFFF
OFFWHITE = (248, 250, 246)      # #F8FAF6
INK = (53, 60, 49)
MUTED = (100, 109, 91)
LINE = (220, 227, 213)
PALE = (240, 243, 237)
SOFT_OLIVE = (229, 235, 222)
ACCENT = DEEP_OLIVE
brand = data["brand"]

MONTHS_MR = {
    1:"जानेवारी", 2:"फेब्रुवारी", 3:"मार्च", 4:"एप्रिल", 5:"मे", 6:"जून",
    7:"जुलै", 8:"ऑगस्ट", 9:"सप्टेंबर", 10:"ऑक्टोबर", 11:"नोव्हेंबर", 12:"डिसेंबर"
}
today = datetime.strptime(LOCAL_DATE, "%Y-%m-%d")
date_label = "{} {} {}".format(today.day, MONTHS_MR[today.month], today.year)

def wrap(value, max_chars):
    return "\n".join(textwrap.wrap(str(value), width=max_chars, break_long_words=False, break_on_hyphens=False))

def rounded(draw, xy, radius=22, fill=WHITE, outline=LINE, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def arrow(draw, start, end, fill=OLIVE, width=7, head=20):
    draw.line((start[0], start[1], end[0], end[1]), fill=fill, width=width)
    import math
    angle = math.atan2(end[1]-start[1], end[0]-start[0])
    left = (end[0] - head*math.cos(angle-0.55), end[1] - head*math.sin(angle-0.55))
    right = (end[0] - head*math.cos(angle+0.55), end[1] - head*math.sin(angle+0.55))
    draw.polygon([end, left, right], fill=fill)

def base(category, idx, total):
    im = Image.new("RGB", (W, H), OFFWHITE)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 16, H), fill=DEEP_OLIVE)
    d.rectangle((42, 52, W-42, 126), fill=WHITE)
    draw_text(d, (78, 76), brand["display"], 24, fill=DEEP_OLIVE, bold=True)
    draw_text(d, (W-78, 80), date_label, 18, fill=MUTED, anchor="ra")
    d.line((78, 148, W-78, 148), fill=LINE, width=2)
    draw_text(d, (78, 174), category, 18, fill=OLIVE, bold=True)
    if total:
        draw_text(d, (W-78, 174), "{:02d} / {:02d}".format(idx, total), 18, fill=OLIVE, anchor="ra")
    return im

def diagram(draw, typ, y0=540):
    # One explanatory graphic per slide; all drawings are original concepts, not product photos.
    rounded(draw, (78, y0-42, 1002, 1050), 28, WHITE, LINE, 2)

    if typ == "robot_touch":
        # Camera -> visual/language plan -> fingertip touch feedback.
        rounded(draw, (130, y0+125, 310, y0+290), 22, PALE, LINE, 2)
        draw.ellipse((185, y0+158, 255, y0+228), outline=DEEP_OLIVE, width=7)
        draw.ellipse((207, y0+180, 233, y0+206), fill=OLIVE)
        draw_text(draw, (220, y0+245), "दृष्टी", 22, fill=DEEP_OLIVE, bold=True, anchor="mm")
        rounded(draw, (390, y0+125, 610, y0+290), 22, SOFT_OLIVE, OLIVE, 2)
        draw_text(draw, (500, y0+170), "VLA", 34, fill=DEEP_OLIVE, bold=True, anchor="mm")
        draw_text(draw, (500, y0+220), "कृतीचा आराखडा", 20, fill=INK, anchor="mm")
        arrow(draw, (315, y0+208), (382, y0+208))
        # Two tactile fingertips and a fragile object.
        rounded(draw, (715, y0+85, 820, y0+235), 34, SOFT_OLIVE, DEEP_OLIVE, 3)
        rounded(draw, (845, y0+85, 950, y0+235), 34, SOFT_OLIVE, DEEP_OLIVE, 3)
        draw.ellipse((760, y0+120, 780, y0+140), fill=OLIVE)
        draw.ellipse((890, y0+120, 910, y0+140), fill=OLIVE)
        draw.ellipse((805, y0+225, 865, y0+285), fill=(246, 239, 219), outline=DEEP_OLIVE, width=3)
        draw_text(draw, (830, y0+315), "स्पर्श सेन्सर", 20, fill=DEEP_OLIVE, bold=True, anchor="mm")
        arrow(draw, (615, y0+208), (700, y0+208))
        # Feedback path returns from touch to the plan.
        draw.line((830, y0+345, 830, y0+390, 500, y0+390, 500, y0+305), fill=OLIVE, width=5)
        arrow(draw, (500, y0+390), (500, y0+310), fill=OLIVE, width=5, head=16)
        draw_text(draw, (500, y0+420), "स्पर्शानुसार त्वरित सुधारणा", 22, fill=DEEP_OLIVE, bold=True, anchor="mm")
        draw_text(draw, (240, y0+40), "दृश्य-भाषा", 19, fill=MUTED, anchor="mm")
        draw_text(draw, (830, y0+40), "बोटांवरील स्पर्श", 19, fill=MUTED, anchor="mm")

    elif typ == "package_stack":
        # GPU/SoC and HBM stacks linked through an interposer and substrate.
        rounded(draw, (360, y0+65, 720, y0+180), 18, SOFT_OLIVE, DEEP_OLIVE, 3)
        draw_text(draw, (540, y0+105), "GPU / SoC", 31, fill=DEEP_OLIVE, bold=True, anchor="mm")
        for x in (160, 790):
            for k in range(3):
                rounded(draw, (x, y0+82+k*56, x+125, y0+125+k*56), 10, PALE, OLIVE, 2)
            draw_text(draw, (x+62, y0+280), "HBM", 22, fill=DEEP_OLIVE, bold=True, anchor="mm")
        # Interposer and high-density traces.
        rounded(draw, (130, y0+320, 950, y0+390), 12, (236, 239, 229), OLIVE, 2)
        for x in range(170, 920, 42):
            draw.line((x, y0+333, x+22, y0+376), fill=OLIVE, width=3)
        draw.rectangle((105, y0+405, 975, y0+438), fill=DEEP_OLIVE)
        draw_text(draw, (540, y0+455), "एकत्रित पॅकेज", 21, fill=DEEP_OLIVE, bold=True, anchor="mm")
        arrow(draw, (285, y0+250), (365, y0+190), fill=OLIVE, width=4, head=14)
        arrow(draw, (795, y0+250), (715, y0+190), fill=OLIVE, width=4, head=14)
        draw_text(draw, (540, y0+295), "सिलिकॉन इंटरपोजर", 19, fill=MUTED, anchor="mm")

    elif typ == "interposer":
        rounded(draw, (165, y0+80, 405, y0+200), 18, SOFT_OLIVE, DEEP_OLIVE, 3)
        draw_text(draw, (285, y0+125), "SoC", 32, fill=DEEP_OLIVE, bold=True, anchor="mm")
        for x in (660, 780):
            rounded(draw, (x, y0+70, x+95, y0+210), 12, PALE, OLIVE, 2)
            draw_text(draw, (x+47, y0+130), "HBM", 19, fill=DEEP_OLIVE, bold=True, anchor="mm")
        rounded(draw, (130, y0+285, 950, y0+385), 16, (236,239,229), OLIVE, 2)
        for x in range(175, 920, 22):
            draw.line((x, y0+300, x+90, y0+372), fill=OLIVE, width=3)
        for y in (y0+240, y0+255):
            draw.line((300, y, 705, y), fill=DEEP_OLIVE, width=3)
        draw_text(draw, (540, y0+425), "दाट जोडणीचे अनेक सूक्ष्म मार्ग", 22, fill=DEEP_OLIVE, bold=True, anchor="mm")

    elif typ == "bottleneck":
        labels = [
            ("१", "वेफर तयार करणे", False),
            ("२", "अॅडव्हान्स्ड पॅकेजिंग", True),
            ("३", "चाचणी व पडताळणी", False),
            ("४", "सिस्टममध्ये वापर", False),
        ]
        y = y0+45
        for num, label, active in labels:
            fill = SOFT_OLIVE if active else WHITE
            outline = DEEP_OLIVE if active else LINE
            rounded(draw, (180, y, 900, y+78), 16, fill, outline, 3 if active else 2)
            draw.ellipse((205, y+19, 245, y+59), fill=DEEP_OLIVE if active else PALE, outline=OLIVE, width=2)
            draw_text(draw, (225, y+28), num, 18, fill=WHITE if active else DEEP_OLIVE, bold=True, anchor="mm")
            draw_text(draw, (285, y+21), label, 25, fill=DEEP_OLIVE if active else INK, bold=active)
            if active:
                draw_text(draw, (865, y+25), "क्षमता ताण", 17, fill=DEEP_OLIVE, anchor="ra")
            y += 100

    elif typ == "panel_line":
        rounded(draw, (150, y0+85, 930, y0+370), 18, PALE, OLIVE, 3)
        for r in range(3):
            for c in range(5):
                x = 190 + c*145
                y = y0+120 + r*76
                rounded(draw, (x, y, x+105, y+48), 8, WHITE, DEEP_OLIVE, 2)
                draw.rectangle((x+18, y+16, x+87, y+31), fill=SOFT_OLIVE)
        draw_text(draw, (540, y0+410), "मोठ्या पॅनेलवर अनेक पॅकेज", 23, fill=DEEP_OLIVE, bold=True, anchor="mm")
        draw_text(draw, (540, y0+455), "ASEची उत्पादन-योजना: २०२७ पहिली सहामाही", 18, fill=MUTED, anchor="mm")

    elif typ == "takeaway":
        blocks = [
            (150, "गणना", "GPU / SoC"),
            (420, "मेमरी", "HBM"),
            (690, "जोडणी", "Interposer"),
        ]
        for x, title, sub in blocks:
            rounded(draw, (x, y0+150, x+220, y0+315), 22, SOFT_OLIVE, OLIVE, 2)
            draw_text(draw, (x+110, y0+205), title, 27, fill=DEEP_OLIVE, bold=True, anchor="mm")
            draw_text(draw, (x+110, y0+260), sub, 20, fill=MUTED, anchor="mm")
        arrow(draw, (370, y0+235), (410, y0+235), width=4, head=14)
        arrow(draw, (640, y0+235), (680, y0+235), width=4, head=14)
        draw_text(draw, (540, y0+390), "AI हार्डवेअरची क्षमता या तिन्हींच्या समन्वयावर", 22, fill=DEEP_OLIVE, bold=True, anchor="mm")

    else:
        for i, label in enumerate(["निरीक्षण", "नियोजन", "अंमलबजावणी", "पडताळणी"]):
            y = y0+50+i*96
            rounded(draw, (180, y, 900, y+70), 16, WHITE, LINE, 2)
            draw_text(draw, (230, y+19), "{:02d}".format(i+1), 20, fill=OLIVE, bold=True)
            draw_text(draw, (300, y+17), label, 24, fill=INK)

def render(post, filename, category, idx=0, total=0):
    im = base(category, idx, total)
    d = ImageDraw.Draw(im)
    title = post["title"]
    end = draw_multiline(d, (78, 220), wrap(title, 23), 54, fill=DEEP_OLIVE, spacing=12, bold=True)
    draw_multiline(d, (80, end+18), wrap(post.get("subtitle", ""), 52), 22, fill=MUTED, spacing=8)
    diagram(d, post.get("diagram", "checklist"), 545)
    notes = post.get("notes", [])
    y = 1080
    for i, note in enumerate(notes[:2]):
        draw_text(d, (86, y), "0{}".format(i+1), 19, fill=OLIVE, bold=True)
        draw_multiline(d, (142, y), wrap(note, 54), 18, fill=INK, spacing=4)
        y += 60
    d.line((78, 1234, W-78, 1234), fill=LINE, width=2)
    draw_text(d, (78, 1252), brand.get("footer", "BRANDSTUDIO"), 17, fill=MUTED)
    show_cta = (total == 0) or (total > 0 and idx == total)
    if show_cta:
        draw_text(d, (W-78, 1252), brand.get("contact", "+91 99218 94495"), 18, fill=DEEP_OLIVE, bold=True, anchor="ra")
        draw_text(d, (W/2, 1290), brand.get("website_display", "brandstudio-pi.vercel.app"), 16, fill=DEEP_OLIVE, anchor="mm")
    im.save(OUT / filename, quality=94, optimize=True, progressive=True)
    return OUT / filename

def make_reel_cover_preview():
    spec = data.get("reel_preview", {})
    im = Image.new("RGB", (1080, 1920), OFFWHITE)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 18, 1920), fill=DEEP_OLIVE)
    d.rectangle((58, 70, 1022, 180), fill=WHITE)
    draw_text(d, (96, 105), brand["display"], 30, fill=DEEP_OLIVE, bold=True)
    draw_text(d, (984, 112), date_label, 22, fill=MUTED, anchor="ra")
    d.line((96, 220, 984, 220), fill=LINE, width=3)
    draw_text(d, (96, 280), "REEL CONCEPT · HOLD", 22, fill=OLIVE, bold=True)
    draw_multiline(d, (96, 420), wrap(spec.get("title", "क्वांटम संगणकातील चुका कशा दुरुस्त होतात?"), 20), 64, fill=DEEP_OLIVE, spacing=18, bold=True)
    rounded(d, (96, 860, 984, 1380), 32, WHITE, LINE, 3)
    draw_text(d, (540, 970), "IBM  +  ORNL  +  AMD", 34, fill=DEEP_OLIVE, bold=True, anchor="mm")
    draw_text(d, (540, 1080), "क्वांटम प्रोसेसर  ↔  सुपरकॉम्प्युटर", 28, fill=INK, anchor="mm")
    draw_text(d, (540, 1190), "चूक शोधणे · डिकोडिंग · सुधारणा", 25, fill=MUTED, anchor="mm")
    draw_text(d, (96, 1510), "ही फक्त संकल्पनात्मक कव्हर-पूर्वदृश्य आहे.", 23, fill=MUTED)
    draw_text(d, (96, 1580), "अंतिम MP4, हक्क-पडताळणी आणि मानवी पाहणी बाकी.", 22, fill=DEEP_OLIVE, bold=True)
    d.line((96, 1740, 984, 1740), fill=LINE, width=3)
    draw_text(d, (96, 1785), brand.get("contact", "+91 99218 94495"), 23, fill=DEEP_OLIVE, bold=True)
    draw_text(d, (96, 1835), brand.get("website", "https://brandstudio-pi.vercel.app/"), 19, fill=MUTED)
    im.save(OUT / "reel-cover-preview.jpg", quality=92, optimize=True, progressive=True)
    return OUT / "reel-cover-preview.jpg"

def make_contact_sheet():
    feed = Image.open(OUT / "feed.jpg").convert("RGB")
    carousel = Image.open(OUT / "carousel-01.jpg").convert("RGB")
    reel = Image.open(OUT / "reel-cover-preview.jpg").convert("RGB")
    tile_w, tile_h = 320, 400
    gap, margin, header = 24, 24, 56
    sheet = Image.new("RGB", (margin*2 + tile_w*3 + gap*2, header + tile_h + margin), OFFWHITE)
    d = ImageDraw.Draw(sheet)
    draw_text(d, (margin, 16), "BRANDSTUDIO · ३-कॉलम फीड पूर्वदृश्य", 20, fill=DEEP_OLIVE, bold=True)
    labels = ["FEED", "CAROUSEL COVER", "REEL CONCEPT · HOLD"]
    for i, src in enumerate((feed, carousel, reel)):
        x = margin + i*(tile_w+gap)
        thumb = ImageOps.fit(src, (tile_w, tile_h), method=Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, header))
        d.rectangle((x, header, x+tile_w, header+tile_h), outline=LINE, width=2)
        draw_text(d, (x+8, header+tile_h+8), labels[i], 14, fill=DEEP_OLIVE, bold=True)
    sheet.save(OUT / "preview-contact-sheet.jpg", quality=92, optimize=True)
    return OUT / "preview-contact-sheet.jpg"

render(data["feed"], "feed.jpg", "जागतिक तंत्रज्ञान · रोबोटिक्स", 0, 0)
for i, post in enumerate(data["carousel"], 1):
    render(post, "carousel-{:02d}.jpg".format(i), "सेमीकंडक्टर · माहिती-कॅरोसेल", i, len(data["carousel"]))
make_reel_cover_preview()
make_contact_sheet()
print("Generated:", *[p.name for p in sorted(OUT.glob("*.jpg"))])
