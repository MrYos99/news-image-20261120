#!/usr/bin/env python3
"""Compose the 20 November 2026 world-news front page (1024x1024).

Build-time tool (Pillow is available on this machine). The entry itself is
the composed JPEG; main.py only copies it into /output at grade time, which
is the pattern the kit's starter uses and the rules allow.

Layout (1024x1024):
  masthead  0..118    date + kicker
  hero      118..430  Shenzhen: Trump, Xi and Putin agree to cut nuclear risk
  row 1     430..700  Cyclone Akvan / Berlin / APEC
  row 2     700..946  Hormuz / Nvidia / SCO Delhi
  ticker    946..1024 also-today strip (113 sanctions, Crimea bridge)

All text is drawn with PIL (crisp vector type) over a moderate bottom
scrim, so nothing is garbled the way AI-generated text would be. Each
panel keeps its own natural colours and light: the hero is warm daylight,
the cyclone is blue-grey with orange rescue jackets, Berlin is cool
grey-blue, APEC is warm sunset, Hormuz is golden hour, Nvidia is
Jensen Huang on a dark keynote stage with green accents, Delhi is
warm sandstone morning. No panel sits under
a heavy dark wash. No randomness anywhere: same inputs give the same
bytes every run.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
ASSETS = "assets"
OUT = "entry.png"

SERIF_BOLD = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NAVY = (11, 22, 34)
AMBER = (255, 179, 0)
WHITE = (255, 255, 255)
SOFT = (226, 232, 238)


def font(path, size):
    return ImageFont.truetype(path, size)


def cover_crop(im, tw, th, focus_y=0.5, focus_x=0.5):
    """Resize + crop so the image exactly fills tw x th.

    focus_y (0..1) places the crop window vertically: 0.5 = centred.
    focus_x (0..1) places it horizontally: 0.5 = centred, 1.0 = right.
    """
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    im = im.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    slack_x = im.width - tw
    x = round(slack_x * focus_x) if slack_x > 0 else 0
    slack = im.height - th
    y = round(slack * focus_y) if slack > 0 else 0
    return im.crop((x, y, x + tw, y + th))


def scrim(base_img, box, max_alpha=180):
    """Bottom-up black gradient scrim inside box (x0, y0, x1, y1).

    Kept moderate on purpose: the photo stays visible above the text,
    and the gradient only deepens near the bottom where the type sits.
    """
    x0, y0, x1, y1 = box
    height = y1 - y0
    overlay = Image.new("RGBA", (x1 - x0, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(height):
        a = int(max_alpha * (i / height) ** 1.8)
        od.line([(0, i), (x1 - x0, i)], fill=(0, 0, 0, a))
    base_img.paste(overlay, (x0, y0), overlay)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap to a pixel width."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def panel(base, img_path, box, tag, headline, sub, head_size=22,
          sub_size=17, focus_y=0.5, focus_x=0.5, max_head_lines=3,
          scrim_alpha=180):
    x0, y0, x1, y1 = box
    tw, th = x1 - x0, y1 - y0
    im = Image.open(img_path).convert("RGB")
    base.paste(cover_crop(im, tw, th, focus_y, focus_x), (x0, y0))
    scrim(base, (x0, y0 + th // 2, x1, y1), max_alpha=scrim_alpha)
    d = ImageDraw.Draw(base)
    pad = 16
    tx = x0 + pad
    # sub-line at the very bottom
    sub_f = font(SANS, sub_size)
    sub_lines = wrap(d, sub, sub_f, tw - 2 * pad)
    sub_h = len(sub_lines) * (sub_size + 5)
    # headline above the sub-line
    head_f = font(SANS_BOLD, head_size)
    head_lines = wrap(d, headline, head_f, tw - 2 * pad)[:max_head_lines]
    head_h = len(head_lines) * (head_size + 4)
    # tag above the headline, on a dark chip so it reads on any photo
    tag_f = font(SANS_BOLD, 16)
    ty = y1 - pad - sub_h - head_h - 26
    tag_w = d.textlength(tag, font=tag_f)
    chip = Image.new("RGBA", (int(tag_w) + 16, 26), (7, 16, 26, 200))
    base.paste(chip, (tx - 8, ty - 3), chip)
    d = ImageDraw.Draw(base)
    d.text((tx, ty), tag, font=tag_f, fill=AMBER)
    hy = ty + 26
    for ln in head_lines:
        d.text((tx, hy), ln, font=head_f, fill=WHITE,
               stroke_width=1, stroke_fill=(0, 0, 0))
        hy += head_size + 4
    sy = hy + 2
    for ln in sub_lines:
        d.text((tx, sy), ln, font=sub_f, fill=SOFT,
               stroke_width=1, stroke_fill=(0, 0, 0))
        sy += sub_size + 5


def main():
    base = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(base)

    # ---- masthead ------------------------------------------------------
    d.text((W // 2, 30), "THE WORLD IN ONE DAY",
           font=font(SANS_BOLD, 21), fill=AMBER, anchor="ma")
    d.text((W // 2, 52), "FRIDAY 20 NOVEMBER 2026",
           font=font(SERIF_BOLD, 46), fill=WHITE, anchor="ma")
    d.line([(24, 116), (W - 24, 116)], fill=AMBER, width=3)

    # ---- hero: Shenzhen trilateral -------------------------------------
    panel(base,
          f"{ASSETS}/media-generation-panel-hero-shenzhen-0-5d13afcb-382c-4931-be14-18e871652280.webp",
          (0, 118, W, 430),
          "SHENZHEN",
          "TRUMP, XI AND PUTIN AGREE TO CUT NUCLEAR RISK",
          "The first meeting of the three leaders lasts 90 minutes. "
          "They also agree to keep energy flowing. "
          "Ukraine is not mentioned.",
          head_size=36, sub_size=20, focus_y=0.35, max_head_lines=2)

    # ---- row 1: cyclone / Berlin / APEC -------------------------------
    gx, gy = 10, 430
    cw, ch, gut = 328, 270, 10
    panel(base,
          f"{ASSETS}/media-generation-panel-cyclone-gopalpur-0-d8b4da9e-a6a2-4fda-a224-17549e2e0067.webp",
          (gx, gy, gx + cw, gy + ch),
          "ODISHA, INDIA",
          "CYCLONE AKVAN HITS THE COAST NEAR GOPALPUR",
          "Winds reach 90 to 100 km/h. 120,000 people are evacuated "
          "and 300 rescue teams are on the ground.",
          focus_y=0.5)
    panel(base,
          f"{ASSETS}/media-generation-panel-berlin-coalition-0-d7284467-a8b6-4578-a841-aac6fed39c8f.webp",
          (gx + cw + gut, gy, gx + 2 * cw + gut, gy + ch),
          "BERLIN",
          "ALLIES PLEDGE MORE AID FOR UKRAINE",
          "Day two of the Coalition of the Willing brings 30 leaders "
          "together. Germany and Norway each give $300 million. "
          "The EU proposes 45 billion euros for 2027.",
          focus_y=0.4)
    panel(base,
          f"{ASSETS}/media-generation-panel-apec-shenzhen-0-a16b267c-82fa-447a-bc5d-e2fe01e34426.webp",
          (gx + 2 * cw + 2 * gut, gy, gx + 3 * cw + 2 * gut, gy + ch),
          "APEC",
          "APEC ENDS WITH THE SHENZHEN OUTLOOK",
          "Leaders close the summit with a joint outlook from Shenzhen.",
          focus_y=0.45)

    # ---- row 2: Hormuz / Nvidia / SCO Delhi ---------------------------
    gy2 = 700
    ch2 = 246
    panel(base,
          f"{ASSETS}/media-generation-panel-hormuz-oil-0-3aa0a043-8ef1-4d59-9a57-1e8d97cc853f.webp",
          (gx, gy2, gx + cw, gy2 + ch2),
          "STRAIT OF HORMUZ",
          "US AND CHINA AGREE TO KEEP OIL FLOWING",
          "Oil keeps moving through the strait. "
          "Iran refuses UN nuclear inspections.",
          focus_y=0.45)
    panel(base,
          f"{ASSETS}/media-generation-panel-nvidia-huang-a-0-34006fc0.webp",
          (gx + cw + gut, gy2, gx + 2 * cw + gut, gy2 + ch2),
          "MARKETS",
          "NVIDIA POSTS RECORD REVENUE OF $115.8 BILLION",
          "The chipmaker reports its biggest quarter yet.",
          focus_y=0.3)
    panel(base,
          f"{ASSETS}/media-generation-panel-sco-delhi-0-2c42064f-5799-4d3f-b794-f4f167060060.webp",
          (gx + 2 * cw + 2 * gut, gy2, gx + 3 * cw + 2 * gut, gy2 + ch2),
          "NEW DELHI",
          "SCO FORUM OPENS IN DELHI",
          "The Shanghai Cooperation Organisation forum opens in the "
          "Indian capital.",
          # focus_x=1.0 crops the Indian flag's chakra wheel (far left
          # of the source) out of the frame: it used to sit behind the
          # D of DELHI and read as "ODELHI". The right-hand flags and
          # the delegation stay in frame.
          focus_y=0.45, focus_x=1.0, scrim_alpha=215)

    # ---- ticker --------------------------------------------------------
    d.rectangle([(0, 956), (W, H)], fill=(7, 16, 26))
    d.line([(0, 956), (W, 956)], fill=AMBER, width=2)
    d.text((24, 964),
           "ALSO TODAY:   113 new sanctions on Russia",
           font=font(SANS_BOLD, 18), fill=AMBER)
    d.text((24, 989),
           "Ukraine strikes the Crimea bridge again",
           font=font(SANS, 18), fill=SOFT)

    # JPEG bytes in entry.png: the gate reads the format from the magic
    # bytes, and the name stays entry.png either way. JPEG keeps the
    # photographic front page well under the 1 MiB cap; PNG was over
    # 1 MiB for yesterday's page.
    base.save(OUT, format="JPEG", quality=88, optimize=True)
    print(f"wrote {OUT} {base.size}")


if __name__ == "__main__":
    main()
