// Print de um slide do deck pelo data-title, para validar layout antes de publicar.
// Instalação (uma vez por sessão, no scratchpad): npm init -y && npm install puppeteer
// Rodar com a pasta atual = scratchpad: cd <scratchpad> && node <skill>/scripts/shot.js ...
// Uso: node shot.js "/caminho/index.html" "Onde o funil quebrou" saida.png
//      node shot.js "/caminho/index.html" --all shots/s   (todos os slides: shots/s01.png, shots/s02.png...)
// Saída no console: "<nº do slide> <total>". Depois, ler o PNG com a tool Read.
// Resolve o puppeteer a partir da pasta atual (onde foi feito o npm install), não da pasta da skill.
const puppeteer = require('module').createRequire(process.cwd() + '/')('puppeteer');
(async () => {
  const [deck, title, out] = process.argv.slice(2);
  const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  const p = await b.newPage();
  await p.setViewport({ width: 1600, height: 900 });
  await p.goto('file://' + deck, { waitUntil: 'networkidle0' });
  const titles = await p.$$eval('section.slide', e => e.map(x => x.dataset.title));
  if (title === '--all') {  // node shot.js deck.html --all prefixo  -> prefixo01.png, prefixo02.png...
    for (let i = 0; i < titles.length; i++) {
      await p.evaluate(n => { (window.goTo || window.go)(n); }, i);
      await new Promise(r => setTimeout(r, 700));
      await p.screenshot({ path: `${out}${String(i + 1).padStart(2, '0')}.png` });
    }
    console.log('ok', titles.length); await b.close(); return;
  }
  const n = titles.indexOf(title);
  if (n < 0) { console.log('slide não encontrado:', title); await b.close(); process.exit(1); }
  await p.evaluate(n => { (window.goTo || window.go)(n); }, n);
  await new Promise(r => setTimeout(r, 900));
  await p.screenshot({ path: out });
  console.log(n + 1, titles.length);
  await b.close();
})();
