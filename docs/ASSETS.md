# Asset provenance

- `assets/original.mp4`: user-supplied Invitation_2.mp4, 2026-09-26. Original audio is copied without tempo changes or extra fades.
- `assets/background.mp4`: existing approved 1080×1920, 268-frame background; final 0.1 seconds extended to 3 seconds. Its audio is ignored.
- `assets/kbw.png`, `assets/upbit.png`, `assets/renaiss-mark.png`: unchanged PNG bytes from Harry's `invitation_logo.zip`, Discord message `1553424336885383320` (2026-09-26). ZIP entries map from `invitation logo/KBW.png`, `invitation logo/upbit.png`, and `invitation logo/cmty.png`, respectively. All have real alpha transparency and visible artwork. Native sizes are 191×36, 138×73, and 109×123; these are small raster sources, not native HD. The renderer trims transparent margins and fits each mark proportionally inside its configured placement. Upbit's nontransparent artwork is 89×24. These replace the previous Canva-preview-derived rendering assets.
- `examples/winchman.jpg`: public profile avatar for @Plus_Ultra_715, retrieved 2026-09-26; 400×400 source.
- `assets/fonts/Inter[opsz,wght].ttf`, `OFL.txt`: https://github.com/google/fonts/tree/main/ofl/inter ; SIL Open Font License 1.1. Used instead of redistributing system fonts.

Company media and brand assets remain subject to their owners' rights. Keep this repository private and use for authorized invitations.

- `assets/supplied/2026-09-26/`: three unchanged user-supplied PNG attachments from Discord message `1553423495461871708`. Archived for traceability; rejected for active rendering because transparency and source-quality checks failed. See the folder README and inspection.json.
