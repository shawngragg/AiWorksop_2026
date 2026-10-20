# RefView Test Images

Fictional, synthetic CT-like images for the workshop; **not for clinical use**.

## Format

| Property | Value |
|---|---|
| Size | 512 × 512 |
| Pixel type | `uint16`, little-endian, rows top-to-bottom, no header |
| HU conversion | `HU = stored + rescale_intercept` (intercept −1024, slope 1) |
| HU range | −1024 to +3071 (stored 0–4095) |
| Missing pixels | stored `65535` (`pixel_padding_value`); not an HU value |

Each `<name>.raw` has a `<name>.json` sidecar with the format fields, a
description, expected file size, padding count, and HU min/max and nearest-rank
5th/95th percentiles excluding padding. Readers should check the actual file size
against `width × height × 2` before using the data.

`<name>.png` is an 8-bit preview rendered with the Packet 1 (D1E2) window/level
formula using the window recorded in the sidecar. Padding pixels are shown as a
checkerboard. Previews are for viewing only; the `.raw` files are the test data.

## Images

| Image | Purpose |
|---|---|
| `ramp` | Linear −1024 → +3071 HU across columns; window/level visual check |
| `uniform_water` | 0 HU water cylinder, noise SD 12 HU (Packet 2 uniform phantom) |
| `material_phantom` | Noise-free 0, −100, +100 HU inserts (Packet 2 material phantom) |
| `resolution_edge` | Noise-free 5° slanted 0/1000 HU edge (Packet 2 resolution phantom) |
| `typical_body` | Ordinary image: fat, soft tissue, lungs, vertebra in air |
| `large_air` | Mostly air; 5th and 95th percentiles are both −1000 HU |
| `extreme_high` | Soft tissue with a +3071 HU object |
| `metal_artifact` | +3071 HU metal disc with radial bright/dark streaks |
| `nearly_uniform` | 40 ± 1 HU everywhere |
| `missing_data` | `typical_body` anatomy with a padding block |
| `corrupted_truncated` | Truncated to 200,001 bytes (odd, mid-row); must be rejected |

The challenging cases follow the Packet 3 (D1E2) list of known challenging images.

## Regenerating

```powershell
py TestImages\generate_test_images.py
```

The generator uses only the Python standard library and a fixed seed, so output is
byte-identical across runs. It checks the preview formula against the handout's
worked example, then rereads every file to verify its size, padding count, and HU
range.
