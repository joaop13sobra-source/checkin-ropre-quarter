# checkin-ropre-quarter

Skill do Claude Code que monta o **check-in de quarter (ROPRE do quarter)** de qualquer cliente em HTML, no mesmo
formato, a partir dos dados do projeto, e publica no Vercel.

## Instalar

```bash
git clone https://github.com/joaop13sobra-source/checkin-ropre-quarter.git ~/.claude/skills/checkin-ropre-quarter
```

Pré-requisitos: Python 3, Node.js, Google Chrome (para os prints de validação) e a CLI do Vercel logada.

## Usar

No Claude Code, peça: "monta o check-in do Q4 do cliente X" (ou "ROPRE do quarter do cliente X").
A skill:

1. Pede o **checklist de dados**: o que é obrigatório (Growth Pack, Break-even, prints, link da pesquisa CSAT,
   planos de ação) e o que é opcional (margem, vendas, ciclo, motivos de desqualificação, entregas do Ekyte...).
2. Monta o `dados.json` do cliente (modelo em `assets/exemplo/dados-exemplo.json`).
3. Gera o deck com `scripts/build_deck.py`. Blocos sem dado não viram slide, então projetos com menos dados
   saem com um deck mais enxuto, no mesmo formato.
4. Valida cada slide por print e publica no Vercel.

## Estrutura do deck

Capa → Sumário → **01 Resultados** (funil do quarter, Projetado x Realizado, Onde o funil quebrou com a ponte de
vendas, Breakeven realizado, análises opcionais, Google Ads e Meta Ads com print) → **02 Objetivos** (o que bateu e o
que ficou devendo, SMART, projeção do próximo quarter) → **03 Premissas e riscos** (opcional) → **04 Entregas** →
**05 Planos de Ação** (na narrativa de cada projeto) → Colli Conecta → QR da pesquisa CSAT.

Detalhes completos em [SKILL.md](SKILL.md).

## Testar sem dados reais

```bash
cd /tmp && npm init -y >/dev/null && npm install puppeteer qrcode jsqr pngjs
python3 -I ~/.claude/skills/checkin-ropre-quarter/scripts/build_deck.py \
  ~/.claude/skills/checkin-ropre-quarter/assets/exemplo/dados-exemplo.json /tmp/checkin-exemplo
open /tmp/checkin-exemplo/index.html
```
