"""Generate deterministic CT-like test images for the RefView workshop.

Fictional sandbox data; not for clinical use. Standard library only.

Each image is 512 x 512, uint16 little-endian, stored = HU + 1024.
A JSON sidecar records the format, description, and expected properties.
An 8-bit PNG preview is rendered using the D1E2 window/level formula.
"""

import json
import math
import random
import struct
import zlib
from pathlib import Path

WIDTH = 512
HEIGHT = 512
PIXELS = WIDTH * HEIGHT
INTERCEPT = -1024
PADDING = 65535
HU_MIN = -1024
HU_MAX = 3071
SEED = 20261020
OUT = Path(__file__).resolve().parent


def clamp_hu(value):
    return max(HU_MIN, min(HU_MAX, int(math.floor(value + 0.5))))


def new_image(value):
    return [value] * PIXELS


def ellipse_rows(cx, cy, rx, ry):
    for y in range(max(0, math.floor(cy - ry)), min(HEIGHT - 1, math.ceil(cy + ry)) + 1):
        dy = (y - cy) / ry
        if abs(dy) > 1:
            continue
        half = rx * math.sqrt(1 - dy * dy)
        x0 = max(0, math.ceil(cx - half))
        x1 = min(WIDTH - 1, math.floor(cx + half))
        if x0 <= x1:
            yield y, x0, x1


def fill_ellipse(img, cx, cy, rx, ry, value):
    for y, x0, x1 in ellipse_rows(cx, cy, rx, ry):
        row = y * WIDTH
        for x in range(x0, x1 + 1):
            img[row + x] = value


def ellipse_mask(cx, cy, rx, ry):
    mask = [False] * PIXELS
    fill_ellipse(mask, cx, cy, rx, ry, True)
    return mask


def add_noise(img, rng, sd, mask):
    for i in range(PIXELS):
        if mask[i]:
            img[i] += rng.gauss(0.0, sd)


def finalize(img):
    return [clamp_hu(v) for v in img]


# ---- Image definitions (all values in HU) ---------------------------------

def make_ramp():
    row = [HU_MIN + (x * (HU_MAX - HU_MIN) + (WIDTH - 1) // 2) // (WIDTH - 1) for x in range(WIDTH)]
    return row * HEIGHT


def make_uniform_water(rng):
    img = new_image(-1000.0)
    fill_ellipse(img, 255.5, 255.5, 240, 240, 0.0)
    add_noise(img, rng, 12.0, ellipse_mask(255.5, 255.5, 240, 240))
    return finalize(img)


def make_material_phantom():
    img = new_image(-1000)
    fill_ellipse(img, 255.5, 255.5, 240, 240, 0)
    for angle, value in ((90, 0), (210, -100), (330, 100)):
        a = math.radians(angle)
        fill_ellipse(img, 255.5 + 130 * math.cos(a), 255.5 - 130 * math.sin(a), 40, 40, value)
    return img


def make_resolution_edge():
    img = new_image(0)
    slope = math.tan(math.radians(5))
    for y in range(HEIGHT):
        edge = 255.5 + slope * (y - 255.5)
        row = y * WIDTH
        for x in range(WIDTH):
            if x > edge:
                img[row + x] = 1000
    return img


def make_body(rng):
    img = new_image(-1000.0)
    fill_ellipse(img, 255.5, 255.5, 220, 160, -100.0)   # fat rim
    fill_ellipse(img, 255.5, 255.5, 208, 148, 40.0)     # soft tissue
    fill_ellipse(img, 175, 235, 60, 80, -850.0)         # left lung
    fill_ellipse(img, 336, 235, 60, 80, -850.0)         # right lung
    fill_ellipse(img, 255.5, 360, 28, 24, 700.0)        # vertebra
    add_noise(img, rng, 10.0, ellipse_mask(255.5, 255.5, 220, 160))
    return finalize(img)


def make_large_air(rng):
    img = new_image(-1000.0)
    fill_ellipse(img, 255.5, 255.5, 30, 30, 40.0)
    add_noise(img, rng, 10.0, ellipse_mask(255.5, 255.5, 30, 30))
    return finalize(img)


def make_extreme_high(rng):
    img = new_image(-1000.0)
    fill_ellipse(img, 255.5, 255.5, 200, 200, 40.0)
    add_noise(img, rng, 10.0, ellipse_mask(255.5, 255.5, 200, 200))
    fill_ellipse(img, 300, 220, 20, 20, float(HU_MAX))
    return finalize(img)


def make_metal_artifact(rng):
    img = new_image(-1000.0)
    fill_ellipse(img, 255.5, 255.5, 220, 160, 40.0)
    mask = ellipse_mask(255.5, 255.5, 220, 160)
    add_noise(img, rng, 10.0, mask)
    mx, my = 300.0, 240.0
    for i in range(PIXELS):
        if not mask[i]:
            continue
        dx, dy = i % WIDTH - mx, i // WIDTH - my
        r = math.hypot(dx, dy)
        if r < 1:
            continue
        theta = math.atan2(dy, dx)
        streak = math.cos(8 * theta) ** 16
        amplitude = 800.0 if math.cos(4 * theta) > 0 else -600.0
        img[i] += amplitude * streak * math.exp(-r / 120.0)
    fill_ellipse(img, mx, my, 12, 12, float(HU_MAX))
    return finalize(img)


def make_nearly_uniform(rng):
    return [40 + rng.choice((-1, 0, 1)) for _ in range(PIXELS)]


MISSING_BLOCK = (150, 200, 362, 312)  # x0, y0, x1 (exclusive), y1 (exclusive)
TRUNCATED_BYTES = 200001


# ---- Encoding and metadata -------------------------------------------------

def percentile(sorted_values, p):
    # Nearest-rank percentile.
    rank = max(1, math.ceil(p / 100.0 * len(sorted_values)))
    return sorted_values[rank - 1]


def window_level(pixel, center, width):
    # D1E2 Packet 1 formula, mirroring RefView::WindowLevelTransform.
    if width <= 1:
        raise ValueError("width must be greater than 1")
    lower = center - 0.5 - (width - 1) / 2
    upper = center - 0.5 + (width - 1) / 2
    if pixel <= lower:
        return 0
    if pixel > upper:
        return 255
    value = ((pixel - (center - 0.5)) / (width - 1) + 0.5) * 255
    return max(0, min(255, int(math.floor(value + 0.5))))


def write_png(path, gray):
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)
        raw.extend(gray[y * WIDTH:(y + 1) * WIDTH])

    def chunk(tag, data):
        content = tag + data
        return struct.pack(">I", len(data)) + content + struct.pack(">I", zlib.crc32(content) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def write_image(name, description, category, hu, window, padding=None, truncate_to=None, notes=None):
    if len(hu) != PIXELS:
        raise AssertionError(f"{name}: wrong pixel count")
    stored = [PADDING if padding and padding[i] else v - INTERCEPT for i, v in enumerate(hu)]
    data = struct.pack("<%dH" % PIXELS, *stored)
    expected_bytes = len(data)
    if truncate_to is not None:
        data = data[:truncate_to]
    (OUT / f"{name}.raw").write_bytes(data)

    valid = sorted(v for i, v in enumerate(hu) if not (padding and padding[i]))
    center, width = window
    meta = {
        "name": name,
        "description": description,
        "category": category,
        "file": f"{name}.raw",
        "width": WIDTH,
        "height": HEIGHT,
        "data_type": "uint16",
        "byte_order": "little-endian",
        "row_order": "top-to-bottom",
        "expected_file_bytes": expected_bytes,
        "actual_file_bytes": len(data),
        "rescale_slope": 1,
        "rescale_intercept": INTERCEPT,
        "pixel_padding_value": PADDING,
        "padding_pixel_count": sum(padding) if padding else 0,
        "hu_statistics_excluding_padding": {
            "min": valid[0],
            "max": valid[-1],
            "p05_nearest_rank": percentile(valid, 5),
            "p95_nearest_rank": percentile(valid, 95),
        },
        "preview": {
            "file": None if truncate_to is not None else f"{name}.png",
            "window_center": center,
            "window_width": width,
        },
        "seed": SEED,
    }
    if notes:
        meta["notes"] = notes
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    if truncate_to is None:
        gray = bytes(checker(i) if padding and padding[i] else window_level(v, center, width)
                     for i, v in enumerate(hu))
        write_png(OUT / f"{name}.png", gray)
    return meta


def checker(i):
    # Padding is shown as an 8 px black/white checkerboard so it is not mistaken for air.
    return 255 if ((i % WIDTH) // 8 + (i // WIDTH) // 8) % 2 else 0


def self_check():
    expected = {-100: 0, -1: 0, 0: 1, 50: 129, 99: 254, 100: 255, 500: 255}
    for pixel, value in expected.items():
        actual = window_level(pixel, 50, 101)
        if actual != value:
            raise AssertionError(f"window_level({pixel}) = {actual}, expected {value}")


def verify(meta):
    data = (OUT / meta["file"]).read_bytes()
    if len(data) != meta["actual_file_bytes"]:
        raise AssertionError(f"{meta['file']}: size mismatch")
    if meta["actual_file_bytes"] != meta["expected_file_bytes"]:
        if meta["name"] != "corrupted_truncated":
            raise AssertionError(f"{meta['file']}: unexpected truncation")
        return
    values = struct.unpack("<%dH" % PIXELS, data)
    if sum(1 for v in values if v == PADDING) != meta["padding_pixel_count"]:
        raise AssertionError(f"{meta['file']}: padding count mismatch")
    hu = [v + INTERCEPT for v in values if v != PADDING]
    stats = meta["hu_statistics_excluding_padding"]
    if (min(hu), max(hu)) != (stats["min"], stats["max"]) or min(hu) < HU_MIN or max(hu) > HU_MAX:
        raise AssertionError(f"{meta['file']}: HU range mismatch")
    if meta["preview"]["file"] and not (OUT / meta["preview"]["file"]).read_bytes().startswith(b"\x89PNG"):
        raise AssertionError(f"{meta['file']}: invalid preview")


def main():
    self_check()
    rng = random.Random(SEED)
    soft = (40, 400)
    x0, y0, x1, y1 = MISSING_BLOCK
    missing = [x0 <= i % WIDTH < x1 and y0 <= i // WIDTH < y1 for i in range(PIXELS)]

    specs = [
        ("ramp", "Horizontal ramp from -1024 HU (left) to +3071 HU (right).",
         "normal", make_ramp(), (1024, 4096), {}),
        ("uniform_water", "Water cylinder (0 HU, noise SD 12 HU, radius 240 px) in air.",
         "phantom", make_uniform_water(rng), (0, 100),
         {"notes": "Measure mean and noise inside the central water region, away from the edge."}),
        ("material_phantom", "Water cylinder with noise-free inserts at 0, -100 and +100 HU.",
         "phantom", make_material_phantom(), (0, 400),
         {"notes": "Inserts (radius 40 px): top 0 HU, lower-left -100 HU, lower-right +100 HU."}),
        ("resolution_edge", "Noise-free 5-degree slanted edge between 0 HU (left) and 1000 HU (right).",
         "phantom", make_resolution_edge(), (500, 1200), {}),
        ("typical_body", "Body-like ellipse with fat, soft tissue, lungs and vertebra in air.",
         "normal", make_body(rng), soft, {}),
        ("large_air", "Mostly air (-1000 HU) with a small 40 HU object (radius 30 px).",
         "challenging", make_large_air(rng), soft, {}),
        ("extreme_high", "Soft-tissue disc with a +3071 HU object (radius 20 px).",
         "challenging", make_extreme_high(rng), soft, {}),
        ("metal_artifact", "Body-like ellipse with a +3071 HU metal disc and radial bright/dark streaks.",
         "challenging", make_metal_artifact(rng), soft, {}),
        ("nearly_uniform", "All pixels 40 HU with -1, 0 or +1 HU variation.",
         "challenging", make_nearly_uniform(rng), soft, {}),
        ("missing_data", "Typical body with a rectangular block of missing (padding) pixels.",
         "challenging", make_body(rng), soft,
         {"padding": missing,
          "notes": f"Padding block x=[{x0},{x1}), y=[{y0},{y1}); shown as a checkerboard in the preview."}),
        ("corrupted_truncated", "Typical body truncated mid-row; metadata declares 512 x 512.",
         "challenging", make_body(rng), soft,
         {"truncate_to": TRUNCATED_BYTES,
          "notes": "File is shorter than expected with an odd byte count; readers must reject it."}),
    ]

    metas = [write_image(name, desc, cat, hu, window, **extra)
             for name, desc, cat, hu, window, extra in specs]
    for meta in metas:
        verify(meta)
    print(f"Generated and verified {len(metas)} images in {OUT}")


if __name__ == "__main__":
    main()
