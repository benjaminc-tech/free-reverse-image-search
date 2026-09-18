#!/bin/bash
# Verifies the EXIF parser and the three perceptual hashes against independent
# reference implementations. Extracts the real code out of index.html so the
# tests cannot drift away from what actually ships.
set -e
cd "$(dirname "$0")/.."

echo "== building fixtures =="
python3 tests/make_fixtures.py

echo
echo "== extracting shipped code =="
python3 - <<'PY'
src = open('index.html').read()
a = src.index('  const TAGS = {')
b = src.index('  // =========================================================================\n  //  Perceptual hashing')
open('/tmp/exif_extracted.js','w').write(src[a:b])
c = src.index('  const bitsToHex = (bits) => {')
d = src.index('  // =========================================================================\n  //  Search engines')
open('/tmp/hash_extracted.js','w').write(src[c:d])
import re
# There are THREE plain <script> blocks (an /#internal opt-out, the PostHog
# snippet, and the app). A non-greedy match grabs the FIRST, which is seven
# lines long, so the syntax check below was passing on the wrong code and
# would never have caught a break in the app. Take the largest block.
blocks = re.findall(r'<script>\n(.*?)\n</script>', src, re.S)
assert blocks, "no <script> blocks found in index.html"
main = max(blocks, key=len)
assert 'use strict' in main and len(main.splitlines()) > 200, \
    f"largest script block looks wrong: {len(main.splitlines())} lines"
open('/tmp/full_script.js','w').write(main)
print(f"ok (app block: {len(main.splitlines())} lines of {len(blocks)} blocks)")
PY

echo
echo "== syntax =="
node --check /tmp/full_script.js && echo "SYNTAX OK"

echo
echo "== EXIF parser =="
node tests/test_exif.mjs test-exif.jpg

echo
echo "== perceptual hashes =="
node tests/test_hash.mjs

echo
echo "== hash robustness =="
python3 tests/test_robustness.py
