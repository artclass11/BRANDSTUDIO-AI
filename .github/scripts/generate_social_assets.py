from PIL import Image, ImageDraw, ImageFont
import json, os, textwrap, subprocess
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
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
LATIN_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]
LATIN_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]
def first_font(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    raise RuntimeError("Required font file not found: " + " | ".join(candidates))
DEV_REG = first_font(FONT_CANDIDATES)
DEV_BOLD = first_font(FONT_BOLD_CANDIDATES)
LATIN_REG = first_font(LATIN_FONT_CANDIDATES)
LATIN_BOLD = first_font(LATIN_BOLD_CANDIDATES)

def font(size, bold=False, script="dev"):
    path = (LATIN_BOLD if bold else LATIN_REG) if script == "latin" else (DEV_BOLD if bold else DEV_REG)
    return ImageFont.truetype(path, size=size, layout_engine=ImageFont.Layout.RAQM)

def _is_devanagari(ch):
    cp = ord(ch)
    return (0x0900 <= cp <= 0x097F) or (0xA8E0 <= cp <= 0xA8FF) or (0x1CD0 <= cp <= 0x1CFF)

def _script_runs(text):
    runs = []
    current = None
    buf = []
    for ch in text:
        if _is_devanagari(ch):
            script = "dev"
        elif ch.isspace() or ch in ".,!?;:/\\\\|()[]{}@#%&—–-+·":
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

def _run_width(d, text, f, script):
    if script == "dev":
        return d.textlength(text, font=f, direction="ltr", language="mr")
    return d.textlength(text, font=f, direction="ltr")

def draw_text(d, xy, text, size, fill=ink, bold=False, anchor=None):
    text = str(text)
    runs = _script_runs(text)
    if not runs:
        return
    if len(runs) == 1:
        script, _ = runs[0]
        f = font(size, bold, script)
        kwargs = {"direction": "ltr"}
        if script == "dev":
            kwargs["language"] = "mr"
        d.text(xy, text, font=f, fill=(accent if script == "latin" else fill), anchor=anchor, **kwargs)
        return
    widths = []
    total_width = 0
    max_height = 0
    for script, part in runs:
        f = font(size, bold, script)
        widths.append(_run_width(d, part, f, script))
        sample = "अग्नि" if script == "dev" else "Ag"
        box = f.getbbox(sample)
        max_height = max(max_height, box[3] - box[1])
        total_width += widths[-1]
    x, y = xy
    if anchor:
        if anchor[0] == "r":
            x -= total_width
        elif anchor[0] == "m":
            x -= total_width / 2
        if len(anchor) > 1 and anchor[1] == "m":
            y -= max_height / 2
    for (script, part), width in zip(runs, widths):
        f = font(size, bold, script)
        kwargs = {"direction": "ltr", "anchor": "lt"}
        if script == "dev":
            kwargs["language"] = "mr"
        d.text((x, y), part, font=f, fill=(accent if script == "latin" else fill), **kwargs)
        x += width

def draw_multiline(d, xy, text, size, fill=ink, spacing=8, bold=False):
    x, y = xy
    lines = str(text).splitlines()
    dev_f = font(size, bold, "dev")
    lat_f = font(size, bold, "latin")
    dev_box = dev_f.getbbox("अग्नि")
    lat_box = lat_f.getbbox("Ag")
    line_height = max(dev_box[3]-dev_box[1], lat_box[3]-lat_box[1], int(size*1.15))
    for line in lines:
        draw_text(d, (x,y), line, size, fill=fill, bold=bold)
        y += line_height + spacing
    return y - spacing

brand = data["brand"]
is_arc = brand["account"] == "@arcstudio91"
bg = (11, 18, 15) if is_arc else (16, 20, 14)
panel = (23, 37, 29) if is_arc else (31, 39, 25)
ink = (237, 241, 228) if is_arc else (246, 247, 235)
muted = (161, 178, 156) if is_arc else (177, 190, 151)
accent = (207, 131, 91) if is_arc else (174, 192, 111)
linec = (69, 88, 72) if is_arc else (91, 107, 60)
def wrap(text, max_chars):
    return "\n".join(textwrap.wrap(text, width=max_chars, break_long_words=False, break_on_hyphens=False))
def base(category, idx, total):
    im = Image.new("RGB", (W,H), bg)
    d = ImageDraw.Draw(im)
    for x in range(42, W-40, 42):
        d.line((x, 55, x, H-70), fill=(16,26,20), width=1)
    for y in range(60, H-60, 42):
        d.line((38, y, W-38, y), fill=(16,26,20), width=1)
    draw_text(d, (78,62), brand["display"], 23, fill=muted)
    draw_text(d, (W-78,64), "07 NOV 2026", 18, fill=accent, anchor="ra")
    d.line((78,111,W-78,111),fill=linec,width=2)
    draw_text(d, (78,145), category.upper(), 18, fill=accent)
    if total:
        draw_text(d, (W-78,145), f"{idx:02d} / {total:02d}", 18, fill=accent, anchor="ra")
    return im
def rounded(d, xy, radius=22, fill=panel, outline=linec, width=2):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
def multiline(d, text, x, y, size, fill=ink, max_chars=30, spacing=16, bold=False):
    t = wrap(text,max_chars)
    return draw_multiline(d, (x,y), t, size, fill=fill, spacing=spacing, bold=bold)
def diagram(d, typ, y0=560):
    x0, x1 = 100, 980
    rounded(d,(78,y0-45,1002,1060),28)
    cx=(x0+x1)//2
    if typ == "thermal":
        d.rectangle((180,y0+100,520,y0+350), fill=(37,56,43), outline=muted, width=4)
        d.rectangle((520,y0+100,830,y0+350), fill=(219,220,201), outline=muted, width=4)
        d.rectangle((135,y0+320,880,y0+380), fill=(108,128,109), outline=ink, width=3)
        d.rectangle((470,y0+290,570,y0+390), fill=accent, outline=ink, width=3)
        for yy in (y0+225,y0+270):
            d.line((240,yy,780,yy),fill=accent,width=8)
            d.polygon([(780,yy),(750,yy-18),(750,yy+18)],fill=accent)
        draw_text(d, (180,y0+65), "बाहेरील बाजू", 20, fill=muted)
        draw_text(d, (600,y0+65), "आतील जागा", 20, fill=(39,48,40))
        draw_text(d, (590,y0+420), "उष्णता प्रवाहाचा मार्ग", 21, fill=accent)
    elif typ == "solar":
        d.polygon([(180,y0+300),(850,y0+180),(900,y0+340),(230,y0+450)], fill=(62,82,64), outline=ink)
        for r in range(2):
            for c in range(4):
                xx=260+c*135+r*18; yy=y0+280-c*24+r*56
                d.polygon([(xx,yy),(xx+110,yy-20),(xx+130,yy+42),(xx+20,yy+62)], fill=(30,51,68), outline=(171,190,188))
        d.line((160,y0+500,900,y0+500),fill=accent,width=5)
        draw_text(d, (320,y0+520), "सौर पॅनेल + सेवा मार्ग + निचरा", 22, fill=ink)
    elif typ == "phone":
        rounded(d,(350,y0+5,720,y0+475),48,fill=(8,12,9),outline=muted,width=7)
        rounded(d,(390,y0+65,680,y0+420),28,fill=(23,35,25),outline=linec,width=3)
        rounded(d,(465,y0+165,610,y0+305),18,fill=(39,57,37),outline=accent,width=4)
        draw_text(d, (538,y0+215), "AI", 58, bold=True, fill=ink, anchor="mm")
        for xx in (380,680):
            d.line((xx,y0+220,xx+( -80 if xx==380 else 80),y0+220),fill=accent,width=5)
        draw_text(d, (538,y0+350), "ON-DEVICE", 22, fill=accent, anchor="mm")
    elif typ == "flow":
        labels=["APP","AICORE","GEMINI NANO","NPU / CPU"]
        yy=y0+5
        for i,label in enumerate(labels):
            rounded(d,(240,yy,840,yy+88),18)
            draw_text(d, (540,yy+44), label, 26, bold=True, fill=ink, anchor="mm")
            if i<3:
                d.line((540,yy+88,540,yy+125),fill=accent,width=4)
                d.polygon([(540,yy+130),(527,yy+112),(553,yy+112)],fill=accent)
            yy+=120
    else:
        for i in range(4):
            yy=y0+40+i*112
            rounded(d,(150,yy,930,yy+76),16)
            d.ellipse((185,yy+22,215,yy+52),outline=accent,width=3)
            draw_text(d, (250,yy+19), str(i+1).zfill(2), 21, fill=accent)
            draw_text(d, (315,yy+18), ["तपासणी","नियोजन","अंमलबजावणी","पडताळणी"][i], 25, fill=ink)
def render(post, filename, category, idx=0, total=0):
    im=base(category,idx,total); d=ImageDraw.Draw(im)
    end=multiline(d,post["title"],78,205,58,ink,25,16,True)
    multiline(d,post.get("subtitle",""),80,end+22,25,muted,52,10)
    diagram(d,post.get("diagram","checklist"),550)
    notes=post.get("notes",[])
    y=1085
    for i,note in enumerate(notes[:2]):
        draw_text(d, (86,y), f"0{i+1}", 20, fill=accent)
        draw_multiline(d, (142,y), wrap(note,55), 19, fill=ink, spacing=6)
        y+=54
    d.line((78,1240,W-78,1240),fill=linec,width=2)
    footer=brand.get("footer","")
    draw_text(d, (78,1267), footer, 19, fill=muted)
    contact=brand.get("contact","")
    if contact and (not is_arc or post.get("phone_allowed",False)):
        draw_text(d, (W-78,1267), contact, 19, fill=accent, anchor="ra")
    im.save(OUT/filename,quality=92,optimize=True,progressive=True)
    return OUT/filename
feed= data["feed"]
render(feed,"feed.jpg","EDITORIAL / FEED",0,0)
for i,post in enumerate(data["carousel"],1):
    render(post,f"carousel-{i:02d}.jpg","FIELD GUIDE / CAROUSEL",i,len(data["carousel"]))
print("Generated:",*[p.name for p in sorted(OUT.glob("*.jpg"))])
