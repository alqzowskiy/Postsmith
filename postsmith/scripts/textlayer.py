import io
import os
import re


NAMED_COLORS = {
    "white": "#FFFFFF",
    "black": "#0E0E10",
    "ink": "#0E0E10",
}


def available():
    try:
        from PIL import Image, ImageDraw, ImageFont

        return bool(Image and ImageDraw and ImageFont)
    except ImportError:
        return False


def hex_to_rgb(value):
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(channel * 2 for channel in value)
    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 255, 255)


def resolve_color(value, brand, default):
    if not value:
        value = default
    palette = brand.get("palette", {}) if isinstance(brand, dict) else {}
    if value in palette:
        value = palette[value]
    elif value in NAMED_COLORS:
        value = NAMED_COLORS[value]
    return hex_to_rgb(value)


def find_font(fonts_dir, display_name):
    candidates = []
    if fonts_dir and os.path.isdir(fonts_dir):
        for name in sorted(os.listdir(fonts_dir)):
            if name.lower().endswith((".ttf", ".otf")):
                candidates.append(os.path.join(fonts_dir, name))
    wanted = re.sub(r"[^a-z0-9]", "", (display_name or "").lower())
    for path in candidates:
        stem = re.sub(r"[^a-z0-9]", "", os.path.basename(path).lower())
        if wanted and wanted in stem:
            return path
    if candidates:
        return candidates[0]
    for path in (
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(path):
            return path
    return None


def load_font(path, size):
    from PIL import ImageFont

    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap(draw, text, font, max_width):
    words = text.split()
    if not words:
        return []
    lines = []
    line = words[0]
    for word in words[1:]:
        candidate = line + " " + word
        if text_width(draw, candidate, font) <= max_width:
            line = candidate
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def apply(png_bytes, caption, brand, fonts_dir):
    from PIL import Image, ImageDraw

    image = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    width, height = image.size
    draw = ImageDraw.Draw(image)

    margin = round(width * 0.07)
    max_width = width - 2 * margin
    head_size = max(18, round(width * 0.075))
    sub_size = max(12, round(width * 0.030))
    shadow = max(1, round(width * 0.004))

    fonts = brand.get("fonts", {}) if isinstance(brand, dict) else {}
    head_font = load_font(find_font(fonts_dir, fonts.get("display", "")), head_size)
    sub_font = load_font(find_font(fonts_dir, fonts.get("body", "")), sub_size)

    head_color = resolve_color(caption.get("color"), brand, "white")
    accent = brand.get("palette", {}).get("accent") if isinstance(brand, dict) else None
    sub_color = resolve_color(caption.get("subcolor") or accent, brand, "white")
    shadow_color = (0, 0, 0, 150)

    head_lines = wrap(draw, caption.get("headline", ""), head_font, max_width)
    sub_lines = wrap(draw, caption.get("subhead", ""), sub_font, max_width)

    blocks = []
    for line in head_lines:
        blocks.append((line, head_font, head_color, round(head_size * 1.06)))
    if head_lines and sub_lines:
        blocks.append(("", sub_font, sub_color, round(sub_size * 0.7)))
    for line in sub_lines:
        blocks.append((line, sub_font, sub_color, round(sub_size * 1.35)))

    total = sum(height_step for _, _, _, height_step in blocks)
    position = caption.get("position", "top-left")
    if "bottom" in position:
        y = height - margin - total
    elif "center" in position:
        y = round((height - total) / 2)
    else:
        y = margin

    for line, font, color, step in blocks:
        if line:
            draw.text((margin + shadow, y + shadow), line, font=font, fill=shadow_color)
            draw.text((margin, y), line, font=font, fill=color + (255,))
        y += step

    out = io.BytesIO()
    image.convert("RGB").save(out, format="PNG")
    return out.getvalue()
