# Supplied logos — 2026-09-26

Original bytes supplied by Harry in Discord message `1553423495461871708`.
Retrieved from the original Discord CDN attachment URLs and compared with the bridge attachments. All three files decode as RGB PNGs, despite the message MIME labels saying WebP. None has an alpha channel or PNG transparency metadata.

These are archived source candidates, **not active rendering assets**. They do not resolve the outstanding logo-quality issue.

- `KBW.png`: 191 × 36; every RGB pixel is (255, 255, 255). No visible logo information is present.
- `upbit.png`: 138 × 73; RGB extrema are R 250–255, G 252–255, B 250–255. The white logo is almost invisible against an opaque white background.
- `renaiss_community_.png`: 109 × 123; visible coloured symbol with an opaque white background, smaller than the current 125 × 134 output placement.

Replacing the live marks with these files would add white rectangles and erase the KBW logo. Existing `assets/kbw.png`, `assets/upbit.png`, and `assets/renaiss-mark.png` remain active and preview quality.

Required replacement: export each original logo separately with **transparent background enabled**, preferably SVG or a PNG with visible artwork at least twice the output placement size (KBW 398 × 90, Upbit 262 × 90, Renaiss 250 × 268). Preserve the original aspect ratio and avoid large empty margins. Package originals in a ZIP if attachment processing removes transparency. Re-export from the original artwork; enlarging these supplied files cannot recover missing detail.
