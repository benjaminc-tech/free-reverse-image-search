import { readFileSync } from 'fs';
const parserSrc = readFileSync('/tmp/exif_extracted.js','utf8');
// The parser is plain JS with no DOM use; evaluate it and grab parseExif.
const factory = new Function(parserSrc + '\n return { parseExif, dmsToDecimal, findExifSegment };');
const { parseExif } = factory();

function check(label, actual, expected) {
  const ok = String(actual) === String(expected);
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}`);
  if (!ok) console.log(`        got: ${actual}\n   expected: ${expected}`);
  return ok;
}

let fails = 0;
const buf = readFileSync(process.argv[2]);
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const r = parseExif(ab);

if (!r) { console.log('FAIL  parseExif returned null'); process.exit(1); }
console.log('--- parsed fields ---');
for (const [k,v] of Object.entries(r.fields)) console.log(`  ${k}: ${v}`);
console.log('  GPS:', r.gps ? `${r.gps.lat.toFixed(6)}, ${r.gps.lon.toFixed(6)}` : null);
console.log('--- assertions ---');

fails += !check('Camera make',        r.fields['Camera make'],  'TestCam Industries');
fails += !check('Camera model',       r.fields['Camera model'], 'Model X100');
fails += !check('Software',           r.fields['Software'],     'Adobe Photoshop 2026');
fails += !check('Copyright',          r.fields['Copyright'],    '(c) Ben Goldberger');
fails += !check('Orientation',        r.fields['Orientation'],  '1');
fails += !check('Taken (original)',   r.fields['Taken (original)'], '2026:07:27 14:05:33');
fails += !check('ISO (sub-IFD)',      r.fields['ISO'],          '400');
fails += !check('F number (rational)',r.fields['F number'],     '2.8');
fails += !check('Focal length',       r.fields['Focal length'], '35');
fails += !check('Lens model',         r.fields['Lens model'],   'TestCam 35mm f/1.8');
fails += !check('GPS latitude',       r.gps.lat.toFixed(6),     '37.774900');
fails += !check('GPS longitude',      r.gps.lon.toFixed(6),     '-122.419439');

// negative cases
const noexif = readFileSync('_base.jpg');
const ab2 = noexif.buffer.slice(noexif.byteOffset, noexif.byteOffset + noexif.byteLength);
fails += !check('JPEG without EXIF -> null', parseExif(ab2), 'null');
fails += !check('Non-JPEG bytes -> null', parseExif(new Uint8Array([1,2,3,4,5,6,7,8]).buffer), 'null');
fails += !check('Empty buffer -> null', parseExif(new ArrayBuffer(0)), 'null');
// truncated file must not throw
try {
  const t = buf.slice(0, 300);
  parseExif(t.buffer.slice(t.byteOffset, t.byteOffset + t.byteLength));
  console.log('PASS  truncated file does not throw');
} catch (e) { console.log('FAIL  truncated file threw:', e.message); fails++; }

console.log(fails === 0 ? '\nALL PASSED' : `\n${fails} FAILURE(S)`);
process.exit(fails ? 1 : 0);
