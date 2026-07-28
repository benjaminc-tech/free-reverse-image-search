import { readFileSync } from 'fs';
const gray = JSON.parse(readFileSync('/tmp/gray.json','utf8'));
const want = JSON.parse(readFileSync('/tmp/expected_hashes.json','utf8'));
const src  = readFileSync('/tmp/hash_extracted.js','utf8');

// Stub grayscaleAt with the identical pixel arrays Python used, so we are
// comparing the algorithms rather than two different resamplers.
const stub = `
  const el = () => { throw new Error('canvas not needed'); };
  function grayscaleAt(img, w, h) {
    if (w===8  && h===8) return Float64Array.from(${JSON.stringify(gray.g8)});
    if (w===9  && h===8) return Float64Array.from(${JSON.stringify(gray.g98)});
    if (w===32 && h===32) return Float64Array.from(${JSON.stringify(gray.g32)});
    throw new Error('unexpected size ' + w + 'x' + h);
  }
`;
// drop the real grayscaleAt (it needs canvas) and use the stub
const cleaned = src.replace(/\/\/ Draw the image[\s\S]*?\n  }\n/, '');
const f = new Function(stub + cleaned + '\n return { aHash, dHash, pHash };');
const { aHash, dHash, pHash } = f();

let fails = 0;
for (const [name, fn] of [['aHash',aHash],['dHash',dHash],['pHash',pHash]]) {
  const got = fn(null);
  const ok = got === want[name];
  if (!ok) fails++;
  console.log(`${ok?'PASS':'FAIL'}  ${name}  js=${got}  py=${want[name]}`);
}
// sanity: hashes must be 16 hex chars = 64 bits
for (const [name, fn] of [['aHash',aHash],['dHash',dHash],['pHash',pHash]]) {
  const got = fn(null);
  const ok = /^[0-9a-f]{16}$/.test(got);
  if (!ok) fails++;
  console.log(`${ok?'PASS':'FAIL'}  ${name} is 64 bits`);
}
console.log(fails===0 ? '\nALL PASSED' : `\n${fails} FAILURE(S)`);
process.exit(fails?1:0);
