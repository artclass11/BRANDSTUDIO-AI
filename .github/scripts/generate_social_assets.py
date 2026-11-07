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
def first_font(candidates):
    for p in candidates:
        if os.path.exists(p): return p
    raise RuntimeError("No Devanagari-capable font found")
REG = first_font(FONT_CANDIDATES)
BOLD = first_font(FONT_BOLD_CANDIDATES)
def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size=size, layout_engine=ImageFont.Layout.RAQM)
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
    d.text((78,62), brand["display"], fill=muted, font=font(23))
    d.text((W-78,64), "07 NOV 2026", fill=muted, font=font(18), anchor="ra")
    d.line((78,111,W-78,111),fill=linec,width=2)
    d.text((78,145), category.upper(), fill=accent, font=font(18))
    if total:
        d.text((W-78,145), f"{idx:02d} / {total:02d}", fill=muted, font=font(18), anchor="ra")
    return im
def rounded(d, xy, radius=22, fill=panel, outline=linec, width=2):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
def multiline(d, text, x, y, size, fill=ink, max_chars=30, spacing=16, bold=False):
    f = font(size,bold)
    t = wrap(text,max_chars)
    d.multiline_text((x,y), t, font=f, fill=fill, spacing=spacing, direction="ltr", language="mr")
    bb=d.multiline_textbbox((x,y),t,font=f,spacing=spacing,direction="ltr",language="mr")
    return bb[3]
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
        d.text((180,y0+65),"बाहेरील बाजू",font=font(20),fill=muted)
        d.text((600,y0+65),"आतील जागा",font=font(20),fill=(39,48,40))
        d.text((590,y0+420),"उष्णता प्रवाहाचा मार्ग",font=font(21),fill=accent)
    elif typ == "solar":
        d.polygon([(180,y0+300),(850,y0+180),(900,y0+340),(230,y0+450)], fill=(62,82,64), outline=ink)
        for r in range(2):
            for c in range(4):
                xx=260+c*135+r*18; yy=y0+280-c*24+r*56
                d.polygon([(xx,yy),(xx+110,yy-20),(xx+130,yy+42),(xx+20,yy+62)], fill=(30,51,68), outline=(171,190,188))
        d.line((160,y0+500,900,y0+500),fill=accent,width=5)
        d.text((320,y0+520),"सौर पॅनेल + सेवा मार्ग + निचरा",font=font(22),fill=ink)
    elif typ == "phone":
        rounded(d,(350,y0+5,720,y0+475),48,fill=(8,12,9),outline=muted,width=7)
        rounded(d,(390,y0+65,680,y0+420),28,fill=(23,35,25),outline=linec,width=3)
        rounded(d,(465,y0+165,610,y0+305),18,fill=(39,57,37),outline=accent,width=4)
        d.text((538,y0+215),"AI",font=font(58,True),fill=ink,anchor="mm")
        for xx in (380,680):
            d.line((xx,y0+220,xx+( -80 if xx==380 else 80),y0+220),fill=accent,width=5)
        d.text((538,y0+350),"ON-DEVICE",font=font(22),fill=muted,anchor="mm")
    elif typ == "flow":
        labels=["APP","AICORE","GEMINI NANO","NPU / CPU"]
        yy=y0+5
        for i,label in enumerate(labels):
            rounded(d,(240,yy,840,yy+88),18)
            d.text((540,yy+44),label,font=font(26,True),fill=ink,anchor="mm")
            if i<3:
                d.line((540,yy+88,540,yy+125),fill=accent,width=4)
                d.polygon([(540,yy+130),(527,yy+112),(553,yy+112)],fill=accent)
            yy+=120
    else:
        for i in range(4):
            yy=y0+40+i*112
            rounded(d,(150,yy,930,yy+76),16)
            d.ellipse((185,yy+22,215,yy+52),outline=accent,width=3)
            d.text((250,yy+19),str(i+1).zfill(2),font=font(21),fill=accent)
            d.text((315,yy+18),["तपासणी","नियोजन","अंमलबजावणी","पडताळणी"][i],font=font(25),fill=ink)
def render(post, filename, category, idx=0, total=0):
    im=base(category,idx,total); d=ImageDraw.Draw(im)
    end=multiline(d,post["title"],78,205,58,ink,25,16,True)
    multiline(d,post.get("subtitle",""),80,end+22,25,muted,52,10)
    diagram(d,post.get("diagram","checklist"),550)
    notes=post.get("notes",[])
    y=1085
    for i,note in enumerate(notes[:2]):
        d.text((86,y),f"0{i+1}",font=font(20),fill=accent)
        d.text((142,y),wrap(note,55),font=font(19),fill=ink,spacing=6)
        y+=54
    d.line((78,1240,W-78,1240),fill=linec,width=2)
    footer=brand.get("footer","")
    d.text((78,1267),footer,font=font(19),fill=muted)
    contact=brand.get("contact","")
    if contact and (not is_arc or post.get("phone_allowed",False)):
        d.text((W-78,1267),contact,font=font(19),fill=ink,anchor="ra")
    im.save(OUT/filename,quality=92,optimize=True,progressive=True)
    return OUT/filename
feed= data["feed"]
render(feed,"feed.jpg","EDITORIAL / FEED",0,0)
for i,post in enumerate(data["carousel"],1):
    render(post,f"carousel-{i:02d}.jpg","FIELD GUIDE / CAROUSEL",i,len(data["carousel"]))
print("Generated:",*[p.name for p in sorted(OUT.glob("*.jpg"))])
