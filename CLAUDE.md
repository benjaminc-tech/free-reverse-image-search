# Free Reverse Image Search

Single-file HTML tool: multi-engine launcher, from-scratch EXIF parser,
aHash/dHash/pHash. No server, nothing uploaded.

## Gates
- Test: `./tests/run.sh`
- Deploy: copy files into `publish/` first, then
  `netlify deploy --prod --dir=publish`

## Traps
- There are THREE plain `<script>` blocks. A non-greedy regex grabs the first,
  a seven-line opt-out snippet, so the harness syntax check used to validate the
  wrong code. `tests/run.sh` now takes the largest block. Keep it that way.
- Tests extract the real code out of `index.html` rather than duplicating it, so
  they cannot drift from what ships.
- ChatGPT drives most traffic and strips the referrer. Attribute it on
  `utm_source=chatgpt.com`, never on `$referring_domain`.
- Contrast was re-measured 2026-09-17 across 98 elements in both themes, and
  again for the ui v2 pass (2026-10-09). Engine cards are now one style: ink on
  panel with an accent outline (3.47:1 on the dark panel, the tightest pair).
  If you change a card or surface color, re-measure.
- ui v2 (2026-10-09) puts the engine buttons right under a small thumbnail so
  they are on the first phone screen after a load. Every event carries `ui`,
  and `metadata_read` carries `scrolled`; compare across versions on those,
  not raw counts.
