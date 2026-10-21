---
name: checkin-ropre-quarter
description: Monta o check-in de quarter (ROPRE do quarter) de qualquer cliente em HTML, a partir das fontes de dados do projeto, e publica no Vercel. Antes de montar, pede o checklist de dados (guarda-rails). Estrutura padrão — capa, sumário, 01 Resultados (funil do quarter, Projetado x Realizado, Onde o funil quebrou com a ponte de vendas, Breakeven realizado com print, análises opcionais de vendas e leads, Google Ads e Meta Ads com print), 02 Objetivos (o que bateu e o que ficou devendo, SMART, projeção com print), 03 Premissas e riscos (opcional), 04 Entregas, 05 Planos de Ação do próximo quarter na narrativa que o usuário trouxer, Colli Conecta no penúltimo slide e QR da pesquisa CSAT no último. Gera o deck por um script (build_deck.py) a partir de um dados.json. Use quando pedirem "check-in de quarter", "ROPRE do quarter", "hopper do quarter", "apresentação do quarter", "check-in trimestral" ou "monta o check-in do Q<n>" de um cliente. Projeto com menos dados recebe um deck mais enxuto, no mesmo formato. Check-in MENSAL não é aqui (usa apresentacoes-em-html, formato V2).
---

# Check-in de quarter (ROPRE do quarter)

Monta o check-in de quarter de **qualquer projeto** no mesmo formato, sem começar do zero: você coleta os dados
do cliente, preenche um `dados.json` e o script `scripts/build_deck.py` gera o deck inteiro (HTML 1600×900,
identidade vermelho V4 + branco/cinza, IBM Plex Sans/Mono, navegação por setas, logo Colli&Co no rodapé).
Cada projeto tem suas particularidades: blocos sem dado simplesmente não geram slide, e o deck fica mais enxuto.

A narrativa é sempre a mesma: **resultado do quarter → onde travou → por quê → o que bateu → meta do próximo
quarter → o que entregamos → o que vamos fazer**. Cada slide responde a uma pergunta só, com um título que já é a
conclusão ("Uma venda concentra 37% do faturamento", "A receita aumentou, mas a margem ops caiu"), não o nome da métrica.

---

## 1. Primeiro passo, sempre: pedir o checklist de dados (guarda-rails)

Antes de qualquer cálculo ou HTML, mandar para o usuário o checklist abaixo **preenchido com o que já foi
encontrado** (procurar primeiro no `links.md` da pasta do cliente) e marcar o que falta. Só montar quando os
itens **obrigatórios** estiverem respondidos. Os opcionais que faltarem viram slide a menos, não bloqueiam.

**Obrigatórios**
| # | Dado | Fonte esperada | Para qual slide |
|---|---|---|---|
| 1 | Cliente, quarter fechado e próximo quarter (ex.: Q3 2026 = jul a set; próximo Q4 = out a dez) | usuário | todos |
| 2 | Realizado do quarter: investimento em mídia, leads, MQL, SQL, vendas (mídia paga) | **Growth Pack** (nunca CRM bruto) | Funil, Projetado x Realizado, Gargalo, O que bateu |
| 3 | Mesmos números do quarter anterior | Growth Pack | comparativos "vs Q anterior" |
| 4 | Projetado do quarter: verba, leads, MQL, SQL, vendas, ticket, faturamento | **Planilha de Break-even** (aba de projeção) | Projetado x Realizado, Gargalo, O que bateu |
| 5 | Projetado do próximo quarter (mesmos campos) | Planilha de Break-even | SMART, Projeção |
| 6 | Print da aba "Breakeven - Realizado" e link da aba | usuário manda o print | Breakeven realizado |
| 7 | Print da projeção do próximo quarter e link da aba | usuário manda o print | Projeção (mesmo tamanho e posição sempre) |
| 8 | Link do formulário da pesquisa CSAT do cliente (Pipefy) | check-in anterior do cliente ou usuário | último slide (QR) |
| 9 | Planos de ação do próximo quarter e a narrativa de cada um | usuário | bloco 05 |

**Quando o cliente roda o canal (obrigatório para aquele canal)**
| # | Dado | Fonte | Slide |
|---|---|---|---|
| 10 | Google Ads no quarter e no anterior: investimento, conversões, cliques, impressões + **print do painel de campanhas do quarter** (colunas Custo, Conversões, Custo/conv., Cliques) | Google Ads / NEKT-Flow + usuário | Google Ads |
| 11 | Meta Ads no quarter e no anterior: investimento, leads + **print do Gerenciador do quarter** | Meta / NEKT-Flow + usuário | Meta Ads |

**Opcionais (cada um vira um slide de análise)**
| # | Dado | Fonte | Slide |
|---|---|---|---|
| 12 | Faturamento e rentabilidade das vendas novas (por mês) + premissa de margem do Breakeven | planilha comercial do cliente | KPIs de rentabilidade/ROI, Margem ops |
| 13 | Lista das vendas do quarter (cliente, produto, valor) e vendedor | planilha comercial / CRM | Concentração das vendas |
| 14 | Faturamento de aquisição x recompra por mês | planilha comercial / CRM | Aquisição x recompra |
| 15 | Data do 1º contato e da 1ª venda de cada venda | planilha comercial / CRM | Ciclo mês a mês e por quarter |
| 16 | Motivo de desqualificação dos leads | CRM / planilha de qualificação | Motivos de desqualificação |
| 17 | Relatório de otimização de campanhas do quarter (print + link) | skill `otimizacao-campanhas` | Campanhas por volume de qualificação |
| 18 | Entregas do quarter (tarefas concluídas) | **Ekyte** | Entregas |
| 19 | Premissas e riscos do próximo quarter | usuário | Premissas e riscos |

Regras de dado:
- Realizado = Growth Pack; projetado = Break-even. Não usar `cockpit_breakeven_*` nem CRM bruto para isso.
- Conferir a base de faturamento (vendas novas x novas + recompra) mês a mês; se algum mês misturar, usar a base
  consistente e avisar o usuário.
- Print chegando como caminho temporário (`/var/folders/.../screencaptureui_...png`): **copiar na hora** para o
  projeto, porque o arquivo some.
- Nunca inventar print, número ou plano. Se faltar, o gerador mostra "Print a inserir" e você avisa.

---

## 2. Montar o `dados.json`

Copiar `assets/exemplo/dados-exemplo.json` (cliente fictício, todos os blocos preenchidos) para a pasta do
projeto e trocar pelos dados reais. Valores em número puro (sem "R$" e sem "%"); taxas, custos, variações e
percentuais da meta são calculados pelo gerador. Apagar os blocos opcionais que não tiver.

| Bloco | Obrigatório | Conteúdo |
|---|---|---|
| `cliente` | sim | `nome`, `logo` (caminho do PNG) |
| `quarter` | sim | `nome` (Q3), `anterior` (Q2), `proximo` (Q4), `ano`, `proximo_ano`, `meses_extenso`, `periodo` (dd/mm a dd/mm/aaaa), `proximo_meses` |
| `realizado`, `anterior` | sim | `investimento`, `leads`, `mql`, `sql`, `vendas`, `faturamento`; `rentabilidade` se houver |
| `projetado`, `proximo` | sim | mesmos campos + `ticket`, `margem_premissa` (se o Breakeven tiver) |
| `breakeven` | sim | `print_realizado`, `link_realizado`, `periodo_realizado`, `callouts_realizado` (2 frases), `print_projecao`, `link_projecao`, `fonte_projecao` |
| `canais.google` / `canais.meta` | se roda | números do quarter + `anterior` + `print` |
| `canais.otimizacao` | não | `print`, `link` |
| `analises.margem` / `concentracao` / `recompra` / `ciclo_mensal` / `ciclo_quarter` / `motivos` | não | ver exemplo |
| `premissas` | não | `premissas`, `riscos` |
| `entregas` | recomendado | `categorias` (`nome`, `icone`, `n`, `itens`), `destaques` |
| `planos` | sim | lista de slides (ver seção 4) |
| `textos` | não | sobrescreve frases automáticas: `gargalo_leads`, `gargalo_lm`, `gargalo_ms`, `gargalo_sv`, `gargalo_conclusao`, `proj_real_fecho` |
| `csat_url` | sim | link do Pipefy do cliente (ver seção 5) |

Ícones disponíveis: arrow-left, arrow-right, chart, target, route, database, brush, page, users, check, calendar,
sale, search, message, bolt, trend, swap, alert, clock, filter, globe, link, spark.

---

## 3. O que cada slide mostra (o gerador já faz assim, não mudar o formato)

**Abertura**
1. **Capa**: logo do cliente acima de "Check-in de Quarter"; subtítulo "Resultados do Q<n> <ano>, <meses>: <cliente>".
2. **Sumário**: menu com 01 a 05 (01 ativo, subtópicos do que entrou). O menu sempre lista os 5 blocos, inclusive
   "03 Premissas e riscos" quando não houver slide.

**01 Resultados**
3. **Funil de vendas do quarter**: KPIs Investimento, Faturamento, Ticket médio, Rentabilidade (margem) e ROI
   (ROI = rentabilidade ÷ investimento; sem rentabilidade, entra CAC), cada um vs quarter anterior. Funil
   **Leads → MQL → SQL → Vendas** com a taxa entre as etapas (variação em p.p.) e o custo de cada etapa.
   **Sem impressões e cliques no funil. Sem ROAS.**
4. **Projetado x Realizado**: dois funis lado a lado (realizado do Growth Pack x projetado do Breakeven) e uma frase
   com o % de verba, leads, MQL, SQL, vendas e faturamento atingidos.
5. **Onde o funil quebrou e quanto precisamos melhorar** — o slide mais importante do deck:
   - 4 cards: VOLUME DE ENTRADA (leads x projetado), GARGALO PRINCIPAL (borda vermelha, a taxa que mais tirou
     vendas), SEGUNDA FRENTE e PONTO POSITIVO (verde), cada um com o gap em p.p., o equivalente em volume e a régua
     do próximo quarter. A ordem sai da ponte, não de opinião.
   - **Ponte de vendas**: Projetado → Menos leads → Lead→MQL → MQL→SQL → SQL→Venda → Realizado, por substituição
     sequencial (a soma dos efeitos fecha exatamente projetado → realizado). Vermelho tirou vendas, verde somou.
   - Callout com a conclusão: onde quebrou primeiro, quanto do déficit de MQL veio de volume e quanto de taxa, e
     quantos p.p. faltam em cada taxa. Reescrever em `textos.gargalo_conclusao` se o contexto pedir.
6. **Breakeven realizado**: 2 callouts à esquerda (mês atípico e leitura do último mês), botão "Abrir planilha de
   Break-even realizado ↗", e o print da aba Realizado à direita, clicável, `height:588px`.
7–12. **Análises opcionais** (só com dado): Margem ops mês a mês com a premissa tracejada (usar o termo
   "margem ops"); Concentração com **todas** as vendas em barras + vendedores + callout das 3 maiores; Aquisição x
   recompra (barras empilhadas + tabela); Ciclo de vendas mês a mês (faixas ≤30, 31-90, 91-180, >180 dias); Ciclo
   por quarter (tabela); Motivos de desqualificação (barras + callouts com o achado).
13. **Google Ads no quarter**: 4 KPIs (Investimento, Leads, Custo por lead, Cliques · CTR) vs quarter anterior +
   **só o print** do painel de campanhas do quarter. Sem tabela e sem parágrafo.
14. **Campanhas por volume de qualificação** (opcional): print do relatório de otimização, clicável.
15. **Meta Ads no quarter**: 4 KPIs (Investimento, Leads, Custo por lead, Peso no investimento) + **só o print** do
   Gerenciador do quarter. Sem tabela e sem parágrafo.

**02 Objetivos**
16. Divisor com 02 ativo.
17. **O que bateu e o que ficou devendo**: barras de % da meta do Breakeven, da maior para a menor (verde ≥ 100%,
   amarelo ≥ 90%, vermelho < 90%, linha tracejada = 100%). Custo por lead entra invertido (menor é melhor).
18. **Objetivo SMART do próximo quarter**: frase-objetivo + 5 KRs (leads e CPL, Lead→MQL, MQL→SQL, SQL→Venda,
   margem), números do Breakeven do próximo quarter, cada KR comparado ao quarter que fechou. Pode ser sobrescrito
   em `smart.frase` / `smart.krs`, mantendo o formato.
19. **Projeção do próximo quarter**: coluna de 400px com 3 cards (taxas realizadas x projetadas), botão da planilha e
   fonte; à direita o print da projeção, **`height:712px`, mesma posição sempre**. Só troca o print.

**03 Premissas e riscos** (opcional): divisor + slide com duas colunas (premissas e riscos).

**04 Entregas**: divisor + "<N> entregas no quarter" com cards por categoria (número + itens) e o card de destaques.
Fonte: Ekyte, tarefas concluídas no quarter, **sem os atendimentos recorrentes de WhatsApp**. Revisar com o usuário o
que de fato foi feito antes de publicar; o total do título é a soma das categorias.

**05 Planos de Ação** (seção 4).

**Fechamento fixo**
- **Penúltimo: Colli Conecta** (programa de indicação: foto do Flávio Augusto, 3 indicações válidas = 1 ano de
  mentoria online, 3 passos e QR para https://colli-conecta.vercel.app/). Não muda entre clientes.
- **Último: "Como foi esse quarter pra você?"** com o QR da pesquisa CSAT do cliente.

---

## 4. Planos de ação: na narrativa que o usuário trouxer

Perguntar quais planos entram e a história de cada um; com ou sem proposta comercial. Cada item de `planos` vira um
slide; slides do mesmo plano repetem o mesmo `"plano": n`. Dois tipos:

- **`"tipo": "5w"`** (padrão): `titulo`, `tema`, `linhas` = [Por quê, O quê, Como, Quem, Quando] e, se houver,
  `print` + `legenda` + `link` à direita.
- **`"tipo": "livre"`**: `titulo`, `tema` e `html` com o corpo do slide montado para a narrativa, usando os
  componentes do motor (`card`, `callout`, `pa-row`, `cx-flow`/`cx-step`, `cx-card`, `deliver-grid`/`deliver-card`,
  `tick-list`, `data-table`, `big-number`, `status-pill`, `goal-row`).

Sequências que já funcionaram e servem de modelo:
- **Problema → solução → valor → proposta** (ex.: implantar uma ferramenta): Contexto (fluxo atual em etapas,
  4 cards de impacto, onde o processo se perde) → Solução (fluxo novo + tabela "Hoje x Com a solução" + o que passa a
  ser visível) → Ancoragem (linhas de valor gerado por ano + total + callout) → Proposta (entregáveis + card de
  investimento com a parcela em destaque e a mensalidade em linha separada).
- **Mais verba e novos canais**: contexto da dependência de um canal (cards + leads por mês + mix de verba) e a
  jornada em setas Descoberta → Consideração → Intenção, com cada canal mostrando "Como chega" e "No próximo ano".
- **Canal novo aplicado ao cliente**: "mesma compra, duas lógicas" — termos reais da conta no Google com leads e
  qualificados x a conversa de um comprador no canal novo, com etiquetas do que o contexto revela. Avisar quando a
  conversa for ilustrativa.
- **Ferramenta nova**: 3 cards de contexto + tabela "Hoje x Com a ferramenta" + preço + imagem do produto.

Um plano com vários aspectos ganha vários slides; nunca espremer tudo em um só.

---

## 5. QR da pesquisa CSAT

Link por cliente e por mês:
```
https://app.pipefy.com/public/form/dUzDZw_-?&selecione_o_cliente_database=<ID_CLIENTE>&selecione_o_projeto_central_de_projetos=<ID_PROJETO>&selecione_o_franqueado=11327230&pesquisa_automatica=Sim&pesquisa_a_ser_realizada=MENSAL&identificador_da_pesquisa=disparo_fr_M<MÊS>_<ANO>
```
- `<ID_CLIENTE>` e `<ID_PROJETO>`: ler o QR do check-in anterior do cliente (`node scripts/qr.js ler <png>`) ou pedir.
- `M<MÊS>` = mês em que o check-in é apresentado (outubro = `M10`).
- Com `csat_url` no JSON, o gerador cria `assets/qr-pesquisa.png` sozinho. Sempre ler o QR de volta antes de publicar.

---

## 6. Passo a passo

1. Pedir o checklist (seção 1) e esperar os obrigatórios.
2. Preparar o ambiente no scratchpad (uma vez por sessão): `npm init -y && npm install puppeteer qrcode jsqr pngjs`.
3. Montar o `dados.json` (seção 2) com os dados do cliente.
4. Gerar, com a pasta atual no scratchpad (para o Node achar os pacotes):
   `python3 -I <skill>/scripts/build_deck.py dados.json "<pasta do cliente>/<cliente>-checkin-quarter-q<n>-<ano>-deploy"`
5. Validar **todos** os slides com print real: `node <skill>/scripts/shot.js "<deploy>/index.html" --all shots/s` e ler
   os PNGs. Nada pode encostar no rodapé (logo e contador), tabela não pode quebrar linha, print tem que ser legível.
6. Ajustes finos de um slide: `scripts/deck_tools.py` (`get`, `replace`, `remove`, `insert_after`, `move_before`,
   `check`) ou mudar o JSON e gerar de novo.
7. Publicar direto, sem perguntar: `cd <deploy> && vercel --prod --yes`; conferir o alias
   `https://<cliente>-checkin-quarter-q<n>-<ano>.vercel.app` com `curl`.
8. A cada pedido do usuário: editar, printar o slide, publicar na mesma URL e responder curto com o número do slide.
   Inseriu ou removeu slide? Avisar que a numeração andou.

## 7. Regras de estilo (pedidos que já vieram do usuário)
- Título é conclusão. Sem parágrafo de "leitura" embaixo de gráfico ou print que já fala sozinho.
- Fonte só onde for indispensável (Breakeven, estimativas); nada de nota longa.
- "V4" no texto dos slides; a logo do rodapé é a Colli&Co do motor.
- Print do período do quarter no lugar de tabela que repetiria o mesmo dado.
- Números em pt-BR (R$ 1.094.303; 22,70%; −9,35 p.p.); taxas em p.p. calculadas com os valores já arredondados.
- Removeu item de uma lista com contador (entregas)? Recalcular o número e o título.
- Mudou a ordem de canais num slide? O título acompanha a mesma ordem.

## 8. Arquivos
- `scripts/build_deck.py`: gerador (dados.json → deck completo).
- `scripts/deck_tools.py`: edição por título, `ponte_vendas()`, `goal_rows()`.
- `scripts/shot.js`: print de um slide ou de todos (`--all`).
- `scripts/qr.js`: ler e gerar QR.
- `assets/template/`: motor (CSS + navegação), logos de Google e Meta, Colli Conecta e slide do QR.
- `assets/fixos/`: logos Colli&Co, foto e QR do Colli Conecta.
- `assets/exemplo/dados-exemplo.json`: cliente fictício com todos os blocos.
- Skills relacionadas: `otimizacao-campanhas` (print do slide 14), `cs-retrospectiva-ropre-quarter` e
  `growth-retrospectiva-quarter` (insumos do quarter), `apresentacoes-em-html` (check-in mensal V2).
