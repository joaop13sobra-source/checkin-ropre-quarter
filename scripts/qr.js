// Lê e gera QR Codes do deck (pesquisa CSAT e Colli Conecta).
// Instalação (uma vez por sessão, no scratchpad): npm init -y && npm install qrcode jsqr pngjs
// Rodar com a pasta atual = scratchpad: cd <scratchpad> && node <skill>/scripts/qr.js ...
// Ler:   node qr.js ler  "/caminho/qr.png"        (se der erro de PNG, converter antes: sips -s format png in.png --out t.png)
// Gerar: node qr.js gerar "/caminho/qr-pesquisa.png" "https://app.pipefy.com/..."
const fs = require('fs');
// Resolve os pacotes a partir da pasta atual (onde foi feito o npm install), não da pasta da skill.
const req = require('module').createRequire(process.cwd() + '/');
const [cmd, file, url] = process.argv.slice(2);
if (cmd === 'ler') {
  const { PNG } = req('pngjs'), jsQR = req('jsqr');
  const p = PNG.sync.read(fs.readFileSync(file));
  const r = jsQR(new Uint8ClampedArray(p.data), p.width, p.height);
  console.log(r ? r.data : 'não decodificou');
} else if (cmd === 'gerar') {
  req('qrcode').toFile(file, url, { width: 828, margin: 1, errorCorrectionLevel: 'M' }, e => { if (e) throw e; console.log('ok', file); });
} else {
  console.log('uso: node qr.js ler <png> | node qr.js gerar <png> <url>');
}
