"""Gera o check-in de quarter (ROPRE do quarter) a partir de um dados.json.

Uso:
    python3 -I build_deck.py <dados.json> <pasta_de_saida>

A pasta de saída recebe index.html, vercel.json, .gitignore e assets/ (fixos copiados da skill;
logo do cliente e prints entram pelo caminho informado no JSON e são copiados para assets/).
Estrutura do JSON: ver assets/exemplo/dados-exemplo.json e a seção 2 do SKILL.md.
Blocos opcionais ausentes no JSON simplesmente não geram slide.
"""
import json, os, shutil, sys, html as _html

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SKILL, 'assets', 'template')
FIX = os.path.join(SKILL, 'assets', 'fixos')
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
import deck_tools as dt  # noqa: E402

# ------------------------------------------------------------------ formatação
def f(x, d=0):
    s = f'{x:,.{d}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')
def brl(x, d=0): return 'R$ ' + f(x, d)
def pct(x, d=2): return f(x, d) + '%'
def esc(t): return _html.escape(str(t), quote=False)
def sgn(x, d=1, suf='%'):
    return ('+' if x >= 0 else '−') + f(abs(x), d) + suf
def var(a, b):  # variação % de a contra b
    return (a / b - 1) * 100 if b else 0.0
def icon(name): return f'<svg class="icon"><use href="#i-{name}"></use></svg>'
def read(p): return open(os.path.join(TPL, p), encoding='utf-8').read()

MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


class Deck:
    def __init__(self, D, out):
        self.D, self.out = D, out
        self.c = D['cliente']; self.q = D['quarter']
        self.Q, self.QA, self.QN = self.q['nome'], self.q['anterior'], self.q['proximo']  # 'Q3', 'Q2', 'Q4'
        self.ano = self.q['ano']; self.QN_ano = self.q.get('proximo_ano', self.ano)
        self.slides = []
        os.makedirs(os.path.join(out, 'assets'), exist_ok=True)

    # -------------------------------------------------------------- utilidades
    def asset(self, src, nome=None):
        """Copia um arquivo para assets/ e devolve o caminho relativo; None se não existir."""
        if not src:
            return None
        src = os.path.expanduser(src)
        if not os.path.exists(src):
            print(f'  [aviso] arquivo não encontrado: {src}')
            return None
        nome = nome or os.path.basename(src)
        dst = os.path.join(self.out, 'assets', nome)
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copy(src, dst)
        return 'assets/' + nome

    def sec(self, cls, title, body):
        self.slides.append(f'<section class="slide {cls}" data-title="{esc(title)}"><div class="topline"></div>{body}</section>')

    def eyebrow(self, t): return f'<span class="eyebrow">{t}</span>'

    def h2(self, t, size=42, mt=12):
        return f'<h2 style="margin-top:{mt}px;max-width:1380px;font-size:{size}px">{t}</h2>'

    def note(self, t, mt=10):
        return f'<p class="metric-sub" style="font-size:12.5px;color:var(--ink-soft);line-height:1.45;margin-top:{mt}px">{t}</p>'

    def callout(self, t, mt=12): return f'<div class="callout" style="margin-top:{mt}px">{t}</div>'

    def kpi(self, label, big, sub='', cls=''):
        return (f'<div class="card" style="padding:12px 20px"><div class="metric-label" style="margin-top:0">{label}</div>'
                f'<div class="big-number sm">{big}</div><span class="dl {cls}">{sub}</span></div>')

    def print_frame(self, src, alt, legenda, maxh='min(52vh,470px)', link=None, full=False):
        if not src:
            return (f'<div class="pending-banner" style="margin-top:18px;min-height:360px;justify-content:center"><div>'
                    f'<strong>Print a inserir</strong><span>{esc(alt)}</span></div></div>')
        img = (f'<img src="{src}" alt="{esc(alt)}" style="width:100%;height:auto;display:block">' if full else
               f'<img src="{src}" alt="{esc(alt)}" style="max-width:100%;max-height:{maxh};width:auto;height:auto;display:block">')
        frame = 'class="shot-frame" style="display:block;border-radius:14px;overflow:hidden;background:#fff;border:1px solid var(--line)"'
        box = f'<a href="{link}" target="_blank" rel="noopener" {frame}>{img}</a>' if link else f'<div {frame}>{img}</div>'
        wrap = 'width:100%;max-width:1240px' if full else 'width:fit-content;max-width:100%;margin:0 auto'
        return (f'<div style="margin-top:18px;display:flex;justify-content:center"><div style="{wrap}">{box}'
                f'<p class="metric-sub" style="font-size:12px;color:var(--ink-soft);margin-top:8px">{legenda}</p></div></div>')

    # -------------------------------------------------------------- métricas do funil
    @staticmethod
    def funil(x):
        L, M, S, V, I = x['leads'], x['mql'], x['sql'], x['vendas'], x['investimento']
        r = dict(x)
        r.update(lm=M / L if L else 0, ms=S / M if M else 0, sv=V / S if S else 0,
                 cpl=I / L if L else 0, cmql=I / M if M else 0, csql=I / S if S else 0, cac=I / V if V else 0)
        if x.get('faturamento') is not None and V:
            r['ticket'] = x.get('ticket') or x['faturamento'] / V
        if x.get('rentabilidade') is not None and x.get('faturamento'):
            r['margem'] = x['rentabilidade'] / x['faturamento'] * 100
            r['roi'] = x['rentabilidade'] / I if I else 0
        return r

    # -------------------------------------------------------------- menus
    def menu(self, ativo, titulo, subs, data_title=None):
        blocos = ['Resultados', 'Objetivos', 'Premissas e riscos', 'Entregas', f'Planos de Ação {self.QN}']
        rows = ''
        for i, b in enumerate(blocos, 1):
            on = ' active' if i == ativo else ''
            sb = ''.join(f'<div>{esc(t)}</div>' for t in subs) if i == ativo and subs else ''
            rows += (f'<div class="menu-row"><div class="menu-num{on}">{i:02d}</div><div class="menu-card{on}"><h3>{b}</h3>'
                     + (f'<div class="subs">{sb}</div>' if sb else '') + '</div></div>')
        body = (f'<div style="display:flex;height:100%;align-items:flex-end;justify-content:space-between;gap:60px;padding-bottom:60px">'
                f'<div style="flex:0 0 auto"><span class="menu-hero-eyebrow">Check-in de Quarter · {self.Q} {self.ano}</span>'
                f'<h1 class="menu-hero-title">{titulo}</h1></div><div style="flex:0 0 660px;display:flex;flex-direction:column;gap:13px">{rows}</div></div>')
        self.slides.append(f'<section class="slide dark" data-title="{esc(data_title or titulo)}"><div class="topline"></div>{body}</section>')

    # -------------------------------------------------------------- 1. capa
    def capa(self):
        logo = self.asset(self.c.get('logo'), 'cliente-logo' + os.path.splitext(self.c.get('logo') or '.png')[1])
        lg = f'<span class="eyebrow-logo"><img src="{logo}" alt="{esc(self.c["nome"])}"></span>' if logo else ''
        self.slides.append(
            f'<section class="slide red active" data-title="{esc(self.c["nome"])}, check-in de quarter">'
            '<div class="sphere" style="width:430px;height:430px;right:-80px;top:-115px;opacity:.55"></div>'
            '<div class="sphere" style="width:245px;height:245px;right:285px;top:115px;opacity:.32"></div>'
            '<div class="cover-content"><div class="brand-lockup"><img src="assets/colli-white.png" alt="V4 Company Colli&amp;Co"></div>'
            f'<div>{lg}<h1 class="cover-title">Check-in de Quarter</h1>'
            f'<p class="cover-subtitle">Resultados do {self.Q} {self.ano}, {self.q["meses_extenso"]}: {esc(self.c["nome"])}</p></div></div></section>')

    # -------------------------------------------------------------- 3. funil do quarter
    def funil_quarter(self):
        R, A = self.R, self.A
        k = [self.kpi('Investimento', brl(R['investimento']), f'{sgn(var(R["investimento"], A["investimento"]))} vs {self.QA} ({brl(A["investimento"])})',
                      'g' if R['investimento'] <= A['investimento'] else 'r')]
        if 'faturamento' in R:
            k.append(self.kpi(self.D.get('rotulo_faturamento', 'Faturamento (novas)'), brl(R['faturamento']),
                              f'{sgn(var(R["faturamento"], A.get("faturamento", 0)))} vs {self.QA} ({brl(A.get("faturamento", 0))})',
                              'g' if R['faturamento'] >= A.get('faturamento', 0) else 'r'))
        if 'ticket' in R:
            k.append(self.kpi('Ticket médio', brl(R['ticket']), f'{sgn(var(R["ticket"], A.get("ticket", 0)))} vs {self.QA} ({brl(A.get("ticket", 0))})',
                              'g' if R['ticket'] >= A.get('ticket', 0) else 'r'))
        if 'margem' in R:
            k.append(self.kpi('Rentabilidade', brl(R['rentabilidade']), f'margem {pct(R["margem"], 1)} ({self.QA} {pct(A.get("margem", 0), 1)})',
                              'g' if R['margem'] >= A.get('margem', 0) else 'r'))
            k.append(self.kpi('ROI', f(R['roi'], 2), f'{sgn(var(R["roi"], A.get("roi", 0)))} vs {self.QA} ({f(A.get("roi", 0), 2)})',
                              'g' if R['roi'] >= A.get('roi', 0) else 'r'))
        else:
            k.append(self.kpi('CAC', brl(R['cac'], 2), f'{sgn(var(R["cac"], A["cac"]))} vs {self.QA} ({brl(A["cac"], 2)})', 'g' if R['cac'] <= A['cac'] else 'r'))
        cols = '70px 1fr 300px'
        def row(lab, v, w, minw, grad, cl, cost, ca):
            return (f'<div class="fx-row" style="padding:12px 0;border-bottom:none;grid-template-columns:{cols}"><div class="fx-label">{lab}</div>'
                    f'<div class="fx-bar-wrap" style="height:46px"><div class="fx-bar" style="width:{w}%;min-width:{minw}px;background:linear-gradient(90deg,#7f1d1d,{grad})">{f(v)}</div></div>'
                    f'<div class="fx-cost"><span class="cl">{cl}</span><b>{brl(cost, 2)}</b><span class="dl {"g" if cost <= ca else "r"}">{sgn(var(cost, ca))} ({self.QA} {brl(ca, 2)})</span></div></div>')
        def conn(r, ra, lab):
            d = (r - ra) * 100
            return (f'<div class="fx-conn"><span class="arr">&#9660;</span><b>{pct(r * 100)}</b><span class="cn">{lab}</span>'
                    f'<span class="dl {"g" if d >= 0 else "r"}" style="display:inline;margin:0">{sgn(d, 2, " p.p.")} ({self.QA} {pct(ra * 100)})</span></div>')
        L = R['leads']
        fx = (f'<div class="fx-wrap compact" style="padding-bottom:14px"><div class="fx-head" style="grid-template-columns:{cols}"><div></div>'
              f'<div>Funil de {self.Q} · mídia paga ({self.D.get("canais_rotulo", "Meta + Google")})</div><div>Custo vs {self.QA}<small>investimento ÷ volume da etapa</small></div></div>'
              + row('Leads', L, 100, 0, '#d97706', 'CPL', R['cpl'], A['cpl']) + conn(R['lm'], A['lm'], 'Lead → MQL')
              + row('MQL', R['mql'], R['mql'] / L * 100, 110, '#059669', 'C/MQL', R['cmql'], A['cmql']) + conn(R['ms'], A['ms'], 'MQL → SQL')
              + row('SQL', R['sql'], R['sql'] / L * 100, 80, '#059669', 'C/SQL', R['csql'], A['csql']) + conn(R['sv'], A['sv'], 'SQL → Venda')
              + row('Vendas', R['vendas'], R['vendas'] / L * 100, 46, '#059669', 'CAC', R['cac'], A['cac']) + '</div>')
        six = ' six' if len(k) >= 5 else ''
        body = (self.eyebrow(f'Resultados · {self.Q} {self.ano} (quarter fechado) · comparado ao {self.QA}') + self.h2(f'Funil de vendas do {self.Q}')
                + f'<div class="fill" style="justify-content:flex-start;gap:12px;margin-top:10px"><div class="fx-kpis{six}" style="grid-template-columns:repeat({len(k)},1fr)">{"".join(k)}</div>{fx}'
                + (self.note('ROI = rentabilidade ÷ investimento em mídia.', 6) if 'roi' in R else '') + '</div>')
        self.sec('white vfill', f'Funil de vendas do {self.Q}', body)

    # -------------------------------------------------------------- 4. projetado x realizado
    def proj_real(self):
        R, P = self.R, self.P
        def panel(titulo, x, grad, accent):
            ch = [('Investimento' if not accent else 'Verba de mídia', brl(x['investimento']), ' style="color:var(--v4-red)"')]
            ch.append(('Vendas', f(x['vendas']), ''))
            if 'faturamento' in x: ch.append(('Faturamento', brl(x['faturamento']), ''))
            if 'ticket' in x: ch.append(('Ticket médio', brl(x['ticket']), ''))
            chips = ''.join(f'<div class="df-chip"><span class="cl">{a}</span><span class="cv{" accent" if accent and not st else " "}"{st}>{b}</span></div>' for a, b, st in ch)
            L = x['leads']; rows = ''
            for lab, v, rate, cl, cost in [('Leads', L, None, 'CPL', x['cpl']), ('MQL', x['mql'], x['lm'], 'C/MQL', x['cmql']),
                                          ('SQL', x['sql'], x['ms'], 'C/SQL', x['csql']), ('Vendas', x['vendas'], x['sv'], 'CAC', x['cac'])]:
                w = 100.0 if lab == 'Leads' else v / L * 100
                extra = ''
                if lab == 'Vendas':
                    w = max(w, 3.2); extra = 'min-width:34px;'
                rows += (f'<div class="df-row"><div class="df-label">{lab}</div><div class="df-bar-wrap"><div class="df-bar" style="width:{w:.1f}%;{extra}background:linear-gradient(90deg,#7f1d1d,{grad})">{f(v)}</div></div>'
                         f'<div class="df-rate">{"n/a" if rate is None else pct(rate * 100, 1)}</div><div class="df-cost"><span class="cl">{cl}</span><span class="cv">{brl(cost, 2)}</span></div></div>')
            return f'<div class="df-panel"><h3>{titulo}</h3><div class="df-chips">{chips}</div>{rows}</div>'
        partes = [f'<strong>{pct(R["investimento"] / P["investimento"] * 100, 1)}</strong> da verba', f'<strong>{pct(R["leads"] / P["leads"] * 100, 1)}</strong> dos leads',
                  f'<strong>{pct(R["mql"] / P["mql"] * 100, 1)}</strong> dos MQL', f'<strong>{pct(R["sql"] / P["sql"] * 100, 1)}</strong> dos SQL']
        lede = f'O quarter fechou com {", ".join(partes)} e <strong>{pct(R["vendas"] / P["vendas"] * 100, 1)}</strong> das vendas.'
        if 'faturamento' in R and 'faturamento' in P:
            lede += f' O faturamento chegou a <strong>{pct(R["faturamento"] / P["faturamento"] * 100, 1)}</strong> da meta'
            if 'ticket' in R and 'ticket' in P:
                lede += f', com ticket médio de {brl(R["ticket"])} contra {brl(P["ticket"])} projetado'
            lede += '.'
        lede = self.D.get('textos', {}).get('proj_real_fecho', lede)
        body = (self.eyebrow('Resultados · Geral') + self.h2(f'Projetado x Realizado · {self.Q} {self.ano}', 42, 18)
                + f'<div class="fill"><div class="dual-funnel">{panel(f"{self.Q} · Realizado", R, "#d97706", False)}{panel(f"{self.Q} · Projetado (Breakeven)", P, "#059669", True)}</div>'
                + f'<p class="lede" style="font-size:19px;margin-top:20px;max-width:1380px;line-height:1.45">{lede}</p></div>')
        self.sec('vfill', 'Projetado x Realizado', body)

    # -------------------------------------------------------------- 5. onde o funil quebrou
    def gargalo(self):
        R, P, N = self.R, self.P, self.N
        ponte, steps = dt.ponte_vendas({'leads': P['leads'], 'lm': P['lm'], 'ms': P['ms'], 'sv': P['sv']},
                                       {'leads': R['leads'], 'lm': R['lm'], 'ms': R['ms'], 'sv': R['sv']})
        eff = {s[0]: s[2] for s in steps}
        T = self.D.get('textos', {})
        dl = R['leads'] - P['leads']
        cards = []
        good = dl >= 0
        cards.append(('VOLUME DE ENTRADA', 'Leads', f(R['leads']), f'projetado {f(P["leads"])}',
                      (f'+{f(dl)} LEADS ACIMA' if good else f'FALTARAM {f(-dl)} LEADS ({sgn(var(R["leads"], P["leads"]))})'), good,
                      T.get('gargalo_leads', f'Verba investida: {pct(R["investimento"] / P["investimento"] * 100, 1)} do previsto.')))
        etapas = [('Lead → MQL', 'lm', 'MQL', R['leads'], 'leads'), ('MQL → SQL', 'ms', 'SQL', R['mql'], 'MQL reais'), ('SQL → Venda', 'sv', 'vendas', R['sql'], 'SQL reais')]
        efeitos = sorted(etapas, key=lambda e: eff.get(e[0], 0))
        rot_neg = ['GARGALO PRINCIPAL', 'SEGUNDA FRENTE', 'TERCEIRA FRENTE']; i_neg = 0
        for lab, k, nome, base, basenome in efeitos:
            r, p = R[k] * 100, P[k] * 100; d = r - p
            if d < 0:
                rot = rot_neg[i_neg]; i_neg += 1; pill = f'FALTAM +{f(-d, 2)} p.p.'; ok = False
                extra = round(base * (p - r) / 100)
                txt = f'Equivale a +{f(extra)} {nome} com os mesmos {f(base)} {basenome}.'
            else:
                rot = 'PONTO POSITIVO'; pill = f'+{f(d, 2)} p.p. ACIMA'; ok = True
                txt = 'A etapa converteu acima da régua do Breakeven.'
            if N:
                rn = N[k] * 100
                txt += f' Régua do {self.QN}: {pct(rn)}' + (f', ou {sgn(rn - r, 2, " p.p.")} sobre o {self.Q}.' if True else '.')
            cards.append((rot, lab, pct(r), f'projetado {pct(p)}', pill, ok, T.get('gargalo_' + k, txt)))
        html_cards = ''
        for rot, lab, val, proj, pill, ok, txt in cards:
            cor = 'var(--safe)' if ok else 'var(--v4-red)'
            borda = 'border:2px solid var(--v4-red);' if rot == 'GARGALO PRINCIPAL' else ''
            html_cards += (f'<div class="card" style="{borda}padding:16px 20px"><div class="mono" style="font-size:11px;font-weight:700;letter-spacing:.09em;color:{cor}">{rot}</div>'
                           f'<h3 style="font-size:22px;margin:4px 0 6px">{lab}</h3><div style="display:flex;align-items:baseline;gap:10px">'
                           f'<span class="big-number sm" style="font-size:40px;color:{cor}">{val}</span><span class="mono" style="font-size:12px;color:var(--ink-soft)">{proj}</span></div>'
                           f'<div style="margin:10px 0 8px"><span class="gap-pill {"g" if ok else "r"}">{pill}</span></div>'
                           f'<p style="font-size:13px;line-height:1.4;color:var(--ink-soft);margin:0">{txt}</p></div>')
        dm = P['mql'] - R['mql']
        if 'gargalo_conclusao' in T:
            concl = T['gargalo_conclusao']
        else:
            vol = (P['leads'] - R['leads']) * P['lm']; tx = R['leads'] * (P['lm'] - R['lm'])
            falt = [f'<strong>+{f((P[k] - R[k]) * 100, 2)} p.p. em {lab}</strong>' for lab, k, *_ in etapas if R[k] < P[k]]
            concl = (f'<strong>Onde o funil perdeu mais vendas: {min(eff, key=eff.get)}.</strong> '
                     + (f'Do déficit de {f(dm)} MQL, {f(vol)} vieram de menos leads e {f(tx)} da taxa Lead → MQL abaixo da régua. ' if dm > 0 else '')
                     + (f'Para voltar à régua projetada faltam {" e ".join(falt)}.' if falt else 'Todas as taxas ficaram acima da régua.'))
        body = (self.eyebrow('Resultados · Diagnóstico de gargalo · realizado x projetado') + self.h2('Onde o funil quebrou e quanto precisamos melhorar')
                + f'<div class="grid-4" style="margin-top:12px;gap:14px">{html_cards}</div>{ponte}' + self.callout(concl, 14))
        self.sec('white vfill', 'Onde o funil quebrou', body)

    # -------------------------------------------------------------- 6. breakeven realizado
    def breakeven_realizado(self):
        B = self.D.get('breakeven', {}); src = self.asset(B.get('print_realizado'), 'print-breakeven-realizado.png')
        link = B.get('link_realizado', '#')
        calls = ''.join(f'<div class="callout" style="margin-top:0px">{t}</div>' for t in B.get('callouts_realizado', []))
        img = (f'<a href="{link}" target="_blank" rel="noopener" class="shot-frame" style="flex:0 0 auto;display:block"><img src="{src}" alt="Breakeven realizado" style="height:588px;width:auto;display:block"></a>'
               if src else '<div class="pending-banner" style="flex:0 0 640px;height:588px;justify-content:center"><div><strong>Print a inserir</strong><span>Aba "Breakeven - Realizado" da planilha de Break-even.</span></div></div>')
        body = (self.eyebrow('Resultados · Geral · evolução mensal · Breakeven realizado') + self.h2(f'Breakeven realizado: {B.get("periodo_realizado", self.q["meses_extenso"])}')
                + '<div style="display:flex;gap:46px;margin-top:10px;align-items:center;justify-content:space-between"><div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:14px">'
                + calls + f'<div><a href="{link}" target="_blank" rel="noopener" style="display:inline-block;background:var(--v4-red);color:#fff;text-decoration:none;font:700 14px IBM Plex Sans,sans-serif;padding:12px 22px;border-radius:999px">Abrir planilha de Break-even realizado ↗</a></div>'
                + self.note('Fonte: planilha de Break-even, aba de Realizado (investimento, leads, MQL, SQL e vendas do Growth Pack). Faixas vermelhas = taxas de conversão do funil; amarelas = metas.', 0)
                + f'</div>{img}</div>')
        self.sec('white vfill', 'Breakeven realizado', body)

    # -------------------------------------------------------------- 7-12. análises opcionais
    def analise_margem(self, a):
        meses = a['meses']; prem = a.get('premissa'); mx = max([m['margem'] for m in meses] + [prem or 0]) * 1.15
        W, base, top = 1408, 272.0, 40.0; n = len(meses); slot = (W - 60) / n; bw = slot * 0.64; sc = (base - top) / mx
        svg = ('<defs><linearGradient id="gb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff481f"/><stop offset="1" stop-color="#b00610"/></linearGradient>'
               '<linearGradient id="gm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfc9c9"/><stop offset="1" stop-color="#a9a2a2"/></linearGradient></defs>'
               f'<line x1="30" x2="1378" y1="{base}" y2="{base}" stroke="rgba(20,20,20,.22)" stroke-width="1"/>')
        for i, m in enumerate(meses):
            x = 30 + i * slot + (slot - bw) / 2; h = max(m['margem'] * sc, 2); cx = x + bw / 2
            svg += (f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="7" fill="url(#{"gb" if m.get("quarter") else "gm"})"/>'
                    f'<text x="{cx:.1f}" y="{base - h - 9:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-weight="700" font-size="18" fill="#141414">{pct(m["margem"], 1)}</text>'
                    f'<text x="{cx:.1f}" y="298" text-anchor="middle" font-family="IBM Plex Mono" font-weight="700" font-size="15" fill="#141414">{esc(m["mes"])}</text>')
        if prem:
            y = base - prem * sc
            svg += (f'<line x1="30" x2="1378" y1="{y:.1f}" y2="{y:.1f}" stroke="#e50914" stroke-width="2" stroke-dasharray="8 7"/>'
                    f'<text x="1378" y="{y - 8:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-weight="700" font-size="14" fill="#e50914">Premissa de margem do Breakeven: {pct(prem, 0)}</text>')
        ks = ''.join(self.kpi(k['label'], k['valor'], k.get('sub', ''), k.get('cls', '')) for k in a.get('kpis', []))
        body = (self.eyebrow('Resultados · Margem ops · planilha de vendas do cliente') + self.h2(a.get('titulo', 'Margem ops do quarter'), 46)
                + (f'<div style="margin-top:6px"><div class="fx-kpis" style="grid-template-columns:repeat({len(a["kpis"])},1fr)">{ks}</div></div>' if ks else '')
                + f'<div class="card" style="margin-top:12px;padding:14px 22px 10px"><svg viewBox="0 0 1408 330" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;max-height:100%;display:block">{svg}</svg>'
                + f'<div style="display:flex;gap:24px;margin-top:4px;font:600 13px IBM Plex Mono,monospace;color:var(--ink-soft)"><span><i style="display:inline-block;width:12px;height:12px;background:#d4381a;border-radius:3px;margin-right:7px"></i>{self.Q}</span>'
                + '<span><i style="display:inline-block;width:12px;height:12px;background:#b9b3b3;border-radius:3px;margin-right:7px"></i>Meses anteriores</span><span>Margem ops no mês = rentabilidade ÷ faturamento</span></div></div>'
                + (self.note(a['nota']) if a.get('nota') else ''))
        self.sec('white vfill', 'Margem', body)

    def analise_concentracao(self, a):
        vendas = sorted(a['vendas'], key=lambda v: -v['valor']); tot = sum(v['valor'] for v in vendas); mx = vendas[0]['valor']
        bars = ''.join(f'<div class="hbar"><div class="hl">{esc(v["cliente"])}' + (f' <span class="hs">{esc(v["produto"])}</span>' if v.get('produto') else '')
                       + f'</div><div class="ht"><i style="width:{max(v["valor"] / mx * 100, .6):.1f}%;background:linear-gradient(90deg,#7f1d1d,var(--v4-red))"></i></div><div class="hv">{brl(v["valor"])} · {pct(v["valor"] / tot * 100, 1)}</div></div>' for v in vendas)
        css = ('<style>.hb-all .hbar{grid-template-columns:420px 1fr 140px;margin:5px 0}.hb-all .hl{font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
               '.hb-all .hl .hs{display:inline;margin-left:6px;font-size:12px}.hb-all .ht{height:16px;border-radius:5px}.hb-all .ht i{border-radius:5px}</style>')
        top3 = sum(v['valor'] for v in vendas[:3])
        right = ''
        if a.get('vendedores'):
            rows = ''.join(f'<tr><td><strong>{esc(v["nome"])}</strong></td><td class="num r">{f(v["vendas"])}</td><td class="num r">{brl(v["faturamento"])}</td>'
                           + (f'<td class="num r">{pct(v["margem"], 1)}</td>' if 'margem' in v else '') + '</tr>' for v in a['vendedores'])
            mh = '<th class="r">Margem</th>' if 'margem' in a['vendedores'][0] else ''
            right += f'<div class="card" style="padding:4px 18px"><table class="data-table tight"><thead><tr><th>Vendedor</th><th class="r">Vendas</th><th class="r">Faturamento</th>{mh}</tr></thead><tbody>{rows}</tbody></table></div>'
        right += self.callout(a.get('callout', f'As <strong>3 maiores vendas somam {pct(top3 / tot * 100, 0)}</strong> do faturamento; as outras {len(vendas) - 3} somam {brl(tot - top3)}.'), 14)
        titulo = a.get('titulo', f'Uma venda concentra {pct(mx / tot * 100, 0)} do faturamento')
        body = (self.eyebrow('Resultados · Vendas · concentração') + self.h2(titulo)
                + f'<div style="display:grid;grid-template-columns:1.5fr 1fr;gap:22px;margin-top:10px"><div><div class="card" style="padding:18px 24px"><div class="metric-label" style="margin:0 0 8px">Faturamento por venda ({len(vendas)} vendas do {self.Q})</div>{css}<div class="hb-all">{bars}</div></div></div><div>{right}</div></div>')
        self.sec('white vfill', 'Concentração das vendas', body)

    def analise_recompra(self, a):
        ms = a['meses']; tot = lambda m: m['aquisicao'] + m['recompra']
        th = ''.join(f'<th class="r{" q3" if m.get("quarter") else ""}">{esc(m["mes"])}</th>' for m in ms)
        def tr(lab, fn, strong=False):
            cells = ''.join(f'<td class="num r{" q3" if m.get("quarter") else ""}">{fn(m)}</td>' for m in ms)
            return f'<tr><td>{"<strong>" + lab + "</strong>" if strong else lab}</td>{cells}</tr>'
        rows = (tr('Aquisição (1ª compra)', lambda m: brl(m['aquisicao']), True) + tr('Recompra', lambda m: brl(m['recompra']))
                + tr('Receita total', lambda m: brl(tot(m)), True) + tr('% de recompra', lambda m: pct(m['recompra'] / tot(m) * 100 if tot(m) else 0, 1)))
        n = len(ms); W, base, top = 1408, 196.0, 30.0; slot = (W - 40) / n; bw = slot * 0.56; mx = max(tot(m) for m in ms) or 1; sc = (base - top) / mx
        svg = ''
        qi = [i for i, m in enumerate(ms) if m.get('quarter')]
        if qi:
            x0 = 20 + qi[0] * slot; x1 = 20 + (qi[-1] + 1) * slot
            svg += (f'<rect x="{x0:.1f}" y="2" width="{x1 - x0:.1f}" height="258" rx="14" fill="rgba(229,9,20,.06)"/>'
                    f'<text x="{(x0 + x1) / 2:.1f}" y="18" text-anchor="middle" font-family="IBM Plex Mono" font-weight="700" font-size="13" fill="#e50914">{self.Q}</text>')
        svg += f'<line x1="20" x2="1388" y1="{base}" y2="{base}" stroke="rgba(20,20,20,.22)"/>'
        for i, m in enumerate(ms):
            x = 20 + i * slot + (slot - bw) / 2; cx = x + bw / 2; ha = m['aquisicao'] * sc; hr = m['recompra'] * sc; t = tot(m)
            svg += (f'<rect x="{x:.1f}" y="{base - ha:.1f}" width="{bw:.1f}" height="{ha:.1f}" fill="#e50914"/>'
                    f'<rect x="{x:.1f}" y="{base - ha - hr:.1f}" width="{bw:.1f}" height="{hr:.1f}" fill="#b9b4b4"/>'
                    f'<text x="{cx:.1f}" y="{base - ha - hr - 8:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-weight="700" font-size="13" fill="#141414">{f(t / 1000)} mil</text>'
                    f'<text x="{cx:.1f}" y="218" text-anchor="middle" font-family="IBM Plex Mono" font-weight="700" font-size="14" fill="#141414">{esc(m["mes"])}</text>'
                    f'<text x="{cx:.1f}" y="238" text-anchor="middle" font-family="IBM Plex Mono" font-weight="700" font-size="13" fill="#6b6666">{pct(m["recompra"] / t * 100 if t else 0, 0)} recompra</text>')
        chart = (f'<div class="card" style="margin-top:10px;padding:12px 22px 6px"><svg viewBox="0 0 1408 262" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">{svg}</svg>'
                 '<div style="display:flex;gap:24px;margin-top:2px;font:600 12.5px IBM Plex Mono,monospace;color:var(--ink-soft)"><span><i style="display:inline-block;width:12px;height:12px;background:#e50914;border-radius:3px;margin-right:7px"></i>Aquisição (1ª compra)</span>'
                 '<span><i style="display:inline-block;width:12px;height:12px;background:#b9b4b4;border-radius:3px;margin-right:7px"></i>Recompra de clientes já ativos</span><span>Total mensal acima de cada barra</span></div></div>')
        body = (self.eyebrow('Resultados · Receita dos clientes de origem inbound · aquisição x recompra') + self.h2(a.get('titulo', 'Aquisição e recompra: faturamento mês a mês'))
                + chart + f'<div class="card" style="padding:4px 14px;margin-top:12px"><table class="data-table tight monthly"><thead><tr><th></th>{th}</tr></thead><tbody>{rows}</tbody></table></div>'
                + (self.callout(a['callout'], 14) if a.get('callout') else ''))
        self.sec('white vfill', 'Aquisição x recompra', body)

    def analise_ciclo_mensal(self, a):
        cores = ['#1e8a4c', '#8bbf6a', '#d9a441', '#e50914']; faixas = ['≤ 30 dias', '31 a 90', '91 a 180', '> 180 dias']
        rows = ''
        for m in a['meses']:
            b = m['faixas']; t = sum(b) or 1
            sp = ''.join(f'<span style="width:{v / t * 100:.1f}%;background:{cores[i]}">{v if v else ""}</span>' for i, v in enumerate(b))
            rows += f'<div class="stkrow" style="margin:8px 0"><div class="stkl" style="color:{"var(--v4-red)" if m.get("quarter") else "var(--ink)"}">{esc(m["mes"])}</div><div class="stk" style="height:34px">{sp}</div></div>'
        leg = ''.join(f'<span><i style="background:{cores[i]}"></i>{faixas[i]}</span>' for i in range(4))
        body = (self.eyebrow('Resultados · Ciclo de vendas · planilha de vendas do cliente') + self.h2('Ciclo de vendas mês a mês')
                + f'<div style="margin-top:10px"><div class="card" style="padding:14px 22px;flex-shrink:0"><div class="metric-label" style="margin:0 0 6px">Distribuição das vendas por tempo de ciclo, mês a mês</div>{rows}<div class="stkleg" style="margin-top:8px">{leg}</div></div></div>'
                + self.note(a.get('nota', 'Ciclo = dias entre o 1º contato e a 1ª venda, por mês da 1ª venda.')))
        self.sec('white vfill', 'Ciclo de vendas', body)

    def analise_ciclo_quarter(self, a):
        qs = a['quarters']
        th = ''.join(f'<th class="r{" q3" if q.get("atual") else ""}">{esc(q["nome"])}</th>' for q in qs)
        def tr(lab, fn):
            return f'<tr><td><strong>{lab}</strong></td>' + ''.join(f'<td class="num r{" q3" if q.get("atual") else ""}">{fn(q)}</td>' for q in qs) + '</tr>'
        rows = (tr('Vendas fechadas', lambda q: f(q['vendas'])) + tr('Fechadas em até 30 dias', lambda q: f'{f(q["ate30"])} <span class="qp">({pct(q["ate30"] / q["vendas"] * 100, 0)})</span>')
                + tr('Fechadas com mais de 90 dias', lambda q: f'{f(q["mais90"])} <span class="qp">({pct(q["mais90"] / q["vendas"] * 100, 0)})</span>')
                + tr('Mediana do ciclo', lambda q: f'{f(q["mediana"])} dias'))
        body = (self.eyebrow('Resultados · Ciclo de vendas · por quarter · só primeira compra') + self.h2('Ciclo de vendas por quarter')
                + f'<div class="card" style="padding:6px 22px;margin-top:16px"><table class="data-table qtab"><thead><tr><th></th>{th}</tr></thead><tbody>{rows}</tbody></table></div>'
                + self.note('Ciclo = dias entre o 1º contato e a 1ª venda, por trimestre da 1ª venda. Considera só a primeira compra dos clientes novos; recompra não entra.', 12))
        self.sec('white vfill', 'Ciclo de vendas por quarter', body)

    def analise_motivos(self, a):
        ms = sorted(a['motivos'], key=lambda m: -m['qtd']); tot = sum(m['qtd'] for m in ms); mx = ms[0]['qtd']
        bars = ''.join(f'<div class="hbar"><div class="hl">{esc(m["motivo"])}</div><div class="ht"><i style="width:{m["qtd"] / mx * 100:.1f}%;background:linear-gradient(90deg,#7f1d1d,var(--v4-red))"></i></div><div class="hv">{f(m["qtd"])} · {pct(m["qtd"] / tot * 100, 1)}</div></div>' for m in ms)
        body = (self.eyebrow('Resultados · Qualidade dos leads · motivos') + self.h2(a.get('titulo', f'Por que {f(tot)} leads não qualificaram'))
                + f'<div style="margin-top:10px"><div class="card" style="padding:18px 24px"><div class="metric-label" style="margin:0 0 8px">Motivo registrado pelo comercial · {self.Q} {self.ano} · % dos não qualificados</div>{bars}</div></div>'
                + ''.join(self.callout(c) for c in a.get('callouts', [])))
        self.sec('white vfill', 'Motivos de desqualificação', body)

    # -------------------------------------------------------------- 13-15. canais
    def canal_google(self, g):
        ga = g.get('anterior', {})
        ks = [self.kpi('Investimento', brl(g['investimento']), f'{sgn(var(g["investimento"], ga.get("investimento", 0)))} vs {self.QA} ({brl(ga.get("investimento", 0))})' if ga else '', 'g' if ga and g['investimento'] <= ga['investimento'] else 'r'),
              self.kpi('Leads (conversões)', f(g['leads']), f'{sgn(var(g["leads"], ga.get("leads", 0)))} vs {self.QA} ({f(ga.get("leads", 0))})' if ga else '', 'g' if ga and g['leads'] >= ga['leads'] else 'r')]
        cpl = g['investimento'] / g['leads']; cpla = ga['investimento'] / ga['leads'] if ga.get('leads') else 0
        ks.append(self.kpi('Custo por lead', brl(cpl, 2), f'{sgn(var(cpl, cpla))} vs {self.QA} ({brl(cpla, 2)})' if cpla else '', 'g' if cpl <= cpla else 'r'))
        if g.get('cliques'):
            ctr = g['cliques'] / g['impressoes'] * 100 if g.get('impressoes') else None
            big = f(g['cliques']) + (f' <span style="font-size:16px;color:var(--ink-soft);letter-spacing:0">· {pct(ctr)}</span>' if ctr else '')
            ks.append(self.kpi('Cliques · CTR', big, f'{self.QA}: {f(ga["cliques"])} cliques' if ga.get('cliques') else ''))
        src = self.asset(g.get('print'), 'print-google-campanhas.png')
        logo = read('logo-google.svg.html')
        body = (self.eyebrow(f'Google Ads · {self.Q} {self.ano} · Growth Pack') + f'<h2 style="margin-top:14px;max-width:1380px">{logo}Google Ads no quarter</h2>'
                + f'<div style="margin-top:6px"><div class="fx-kpis" style="grid-template-columns:repeat({len(ks)},1fr)">{"".join(ks)}</div></div>'
                + self.print_frame(src, f'Print do painel de campanhas do Google Ads, {self.Q} {self.ano}', f'Painel de campanhas do Google Ads, {self.Q} {self.ano}.'))
        self.sec('white vfill', 'Google Ads no quarter', body)

    def canal_otimizacao(self, o):
        src = self.asset(o.get('print'), 'print-otimizacao-campanhas.png')
        body = (self.eyebrow(f'Google Ads · {self.Q} {self.ano} · Otimização de campanhas') + self.h2('Campanhas por volume de qualificação', 44, 14)
                + self.print_frame(src, f'Painel de otimização de campanhas do {self.Q}', f'Painel de otimização de campanhas do {self.Q}. Clique na imagem para abrir o relatório completo.',
                                   'min(58vh,540px)', o.get('link')))
        self.sec('white vfill', 'Campanhas por volume de qualificação', body)

    def canal_meta(self, m):
        ma = m.get('anterior', {}); R = self.R
        cpl = m['investimento'] / m['leads'] if m['leads'] else 0; cpla = ma['investimento'] / ma['leads'] if ma.get('leads') else 0
        ks = [self.kpi('Investimento', brl(m['investimento'], 2), f'{sgn(var(m["investimento"], ma.get("investimento", 0)))} vs {self.QA} ({brl(ma.get("investimento", 0))})' if ma else '', 'g' if ma and m['investimento'] <= ma['investimento'] else 'r'),
              self.kpi('Leads', f(m['leads']), f'{sgn(var(m["leads"], ma.get("leads", 0)))} vs {self.QA} ({f(ma.get("leads", 0))})' if ma else '', 'g' if ma and m['leads'] >= ma['leads'] else 'r'),
              self.kpi('Custo por lead', brl(cpl, 2), f'{self.QA}: {brl(cpla, 2)}' if cpla else '', 'g' if cpl <= cpla else 'r'),
              self.kpi('Peso no investimento', pct(m['investimento'] / R['investimento'] * 100, 1), f'{pct(m["leads"] / R["leads"] * 100, 1)} dos leads')]
        src = self.asset(m.get('print'), 'print-meta-campanhas.png')
        logo = read('logo-meta.svg.html')
        body = (self.eyebrow(f'Meta Ads · {self.Q} {self.ano} · Growth Pack') + f'<h2 style="margin-top:14px;max-width:1380px">{logo}Meta Ads no quarter</h2>'
                + f'<div style="margin-top:6px"><div class="fx-kpis" style="grid-template-columns:repeat(4,1fr)">{"".join(ks)}</div></div>'
                + self.print_frame(src, f'Print do Gerenciador de Anúncios do Meta, {self.Q} {self.ano}', f'Gerenciador de Anúncios do Meta, {self.q["periodo"]}.', full=True))
        self.sec('vfill', 'Meta Ads no quarter', body)

    # -------------------------------------------------------------- 17-19. objetivos
    def bateu(self):
        R, P = self.R, self.P; it = []
        if 'ticket' in R and 'ticket' in P: it.append(('Ticket médio', R['ticket'] / P['ticket'] * 100, f'{brl(R["ticket"])} de {brl(P["ticket"])}'))
        if 'faturamento' in R and 'faturamento' in P: it.append((self.D.get('rotulo_faturamento', 'Faturamento (novas)'), R['faturamento'] / P['faturamento'] * 100, f'{brl(R["faturamento"])} de {brl(P["faturamento"])}'))
        for lab, k in [('Taxa Lead → MQL', 'lm'), ('Taxa MQL → SQL', 'ms'), ('Taxa SQL → Venda', 'sv')]:
            it.append((lab, R[k] / P[k] * 100, f'{pct(R[k] * 100)} de {pct(P[k] * 100)}'))
        it.append(('Custo por lead (menor é melhor)', P['cpl'] / R['cpl'] * 100, f'{brl(R["cpl"], 2)} contra {brl(P["cpl"], 2)}'))
        for lab, k in [('Leads', 'leads'), ('MQL', 'mql'), ('SQL', 'sql'), ('Vendas', 'vendas')]:
            it.append((lab, R[k] / P[k] * 100, f'{f(R[k])} de {f(P[k])}'))
        if 'margem' in R and P.get('margem_premissa'):
            it.append(('Margem das vendas', R['margem'] / P['margem_premissa'] * 100, f'{pct(R["margem"], 1)} de {pct(P["margem_premissa"], 0)}'))
        it.sort(key=lambda x: -x[1])
        body = (self.eyebrow(f'Objetivos · {self.Q} {self.ano} fechado · % da meta do Breakeven') + self.h2('O que bateu e o que ficou devendo', 46) + dt.goal_rows(it))
        self.sec('white vfill', 'O que bateu e o que ficou devendo', body)

    def smart(self):
        R, N = self.R, self.N; S = self.D.get('smart', {})
        frase = S.get('frase') or (f'Fechar o {self.QN} com <strong class="accent">{f(N["vendas"])} vendas novas</strong>'
                                   + (f' e faturamento de <strong class="accent">{brl(N["faturamento"])}</strong>' if 'faturamento' in N else '')
                                   + f', com <strong>{f(N["sql"])} SQL</strong>, investindo {brl(N["investimento"])} em mídia paga.')
        krs = S.get('krs') or [
            (f'KR1 · Gerar {f(N["leads"])} leads no quarter, com custo por lead médio de até {brl(N["cpl"], 2)}', f'No {self.Q} foram {f(R["leads"])} leads a {brl(R["cpl"], 2)}.'),
            (f'KR2 · {"Elevar" if N["lm"] > R["lm"] else "Sustentar"} a taxa Lead → MQL {"para" if N["lm"] > R["lm"] else "em pelo menos"} {pct(N["lm"] * 100, 1)}, chegando a {f(N["mql"])} MQL', f'No {self.Q} a taxa foi de {pct(R["lm"] * 100, 1)} ({f(R["mql"])} MQL).'),
            (f'KR3 · {"Elevar" if N["ms"] > R["ms"] else "Sustentar"} a taxa MQL → SQL {"para" if N["ms"] > R["ms"] else "em pelo menos"} {pct(N["ms"] * 100, 1)}, chegando a {f(N["sql"])} SQL', f'No {self.Q} a taxa foi de {pct(R["ms"] * 100, 1)} ({f(R["sql"])} SQL).'),
            (f'KR4 · {"Elevar" if N["sv"] > R["sv"] else "Sustentar"} a taxa SQL → Venda {"para" if N["sv"] > R["sv"] else "em pelo menos"} {pct(N["sv"] * 100, 1)}, fechando {f(N["vendas"])} vendas', f'No {self.Q} a taxa foi de {pct(R["sv"] * 100, 1)} ({f(R["vendas"])} vendas).')]
        if not S.get('krs') and 'margem' in R and N.get('margem_premissa'):
            krs.append((f'KR5 · Levar a margem das vendas em direção aos {pct(N["margem_premissa"], 0)} do Breakeven', f'No {self.Q} a margem foi de {pct(R["margem"], 1)}.'))
        lis = ''.join(f'<li><div class="icon-box small">{icon("target")}</div><div class="bullet-text"><strong>{a}</strong><span>{b}</span></div></li>' for a, b in krs)
        body = (self.eyebrow(f'Objetivos · SMART · base: Breakeven de {self.q["proximo_meses"]} · proposta a validar') + f'<h2 style="margin-top:16px;max-width:1380px">Objetivo SMART do {self.QN} {self.QN_ano}</h2>'
                + f'<div class="fill" style="justify-content:flex-start"><div class="card" style="margin-top:12px;padding:16px 28px;flex-shrink:0"><p style="font-size:21px;line-height:1.4;color:var(--ink);margin:0">{frase}</p></div>'
                + f'<ul class="bullet-list smart-kr" style="margin-top:14px;gap:8px">{lis}</ul></div>')
        self.sec('white vfill', f'Objetivo SMART do {self.QN}', body)

    def projecao(self):
        R, N = self.R, self.N; B = self.D.get('breakeven', {}); link = B.get('link_projecao', '#')
        src = self.asset(B.get('print_projecao'), 'print-breakeven-projecao.png')
        cards = ''
        for lab, k in [('Lead → MQL', 'lm'), ('MQL → SQL', 'ms'), ('SQL → Venda', 'sv')]:
            r, n = R[k] * 100, N[k] * 100; ok = r >= n; cor = 'var(--safe)' if ok else 'var(--v4-red)'
            cards += (f'<div class="card" style="padding:16px 22px"><div class="metric-label" style="margin-top:0">{lab} · realizado {self.Q}</div>'
                      f'<h3 style="margin-top:4px;font-size:30px;color:{cor}">{pct(r, 1)} <span style="font-size:18px">{"&#9650;" if ok else "&#9660;"}</span></h3>'
                      f'<div class="mono" style="font-size:11.5px;color:{cor}">{sgn(r - n, 2, " p.p.")} vs. projetado {self.QN} ({pct(n, 1)})</div></div>')
        img = (f'<a href="{link}" target="_blank" rel="noopener" class="shot-frame" style="flex:0 0 auto;display:block;margin:-8px auto 0 auto"><img src="{src}" alt="Projeção Breakeven {self.QN}" style="height:712px;width:auto;display:block"></a>'
               if src else '<div class="pending-banner" style="flex:1;height:712px;justify-content:center"><div><strong>Print a inserir</strong><span>Aba de projeção do Break-even do próximo quarter.</span></div></div>')
        body = ('<div style="display:flex;gap:40px;height:100%;align-items:flex-start"><div style="flex:0 0 400px;display:flex;flex-direction:column;gap:12px">'
                + f'<div><span class="eyebrow">Objetivos · Projeção Breakeven</span></div><h2 style="margin-top:2px;max-width:1380px;font-size:42px">Projeção {self.QN} {self.QN_ano}</h2>{cards}'
                + f'<a href="{link}" target="_blank" rel="noopener" style="align-self:flex-start;background:var(--v4-red);color:#fff;text-decoration:none;font:700 14px IBM Plex Sans,sans-serif;padding:12px 22px;border-radius:999px;margin-top:4px">Abrir planilha de Break-even ↗</a>'
                + f'<p class="metric-sub" style="margin:0;font-size:12.5px;color:var(--ink-soft);line-height:1.45">{B.get("fonte_projecao", "Fonte: Breakeven, projeção de " + self.q["proximo_meses"] + ".")}</p></div>{img}</div>')
        self.slides.append(f'<section class="slide vfill" data-title="Projeção {self.QN} {self.QN_ano}"><div class="topline"></div>{body}</section>')

    # -------------------------------------------------------------- premissas
    def premissas(self, pr):
        def col(t, its, cor):
            lis = ''.join(f'<li style="font-size:15px;margin-bottom:9px"><span class="dot{" r" if cor == "r" else ""}"></span><span>{esc(x)}</span></li>' for x in its)
            return f'<div class="card" style="padding:18px 24px"><div class="mono" style="font-size:12px;font-weight:700;letter-spacing:.08em;color:{"var(--v4-red)" if cor == "r" else "var(--safe)"};margin-bottom:12px">{t}</div><ul class="tick-list" style="margin:0">{lis}</ul></div>'
        body = (self.eyebrow(f'Premissas e riscos · {self.QN} {self.QN_ano}') + self.h2(pr.get('titulo', 'Premissas e riscos do próximo quarter'), 46)
                + f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:18px">{col("PREMISSAS", pr.get("premissas", []), "g")}{col("RISCOS", pr.get("riscos", []), "r")}</div>')
        self.sec('white vfill', f'Premissas e riscos do {self.QN}', body)

    # -------------------------------------------------------------- entregas
    def entregas(self, E):
        cards = ''
        for c in E['categorias']:
            lis = ''.join(f'<li>{esc(x)}</li>' for x in c['itens'])
            cards += (f'<div class="card ent-card"><div class="ent-head"><span class="icon-box small safe">{icon(c.get("icone", "check"))}</span>'
                      f'<div><div class="ent-n">{f(c["n"])}</div><div class="ent-name">{esc(c["nome"])}</div></div></div><ul>{lis}</ul></div>')
        if E.get('destaques'):
            lis = ''.join(f'<li><strong>{esc(d["titulo"])}:</strong> {esc(d["texto"])}</li>' for d in E['destaques'])
            cards += (f'<div class="card ent-card" style="background:rgba(229,9,20,.05);border-color:rgba(229,9,20,.25)"><div class="ent-name" style="color:var(--v4-red);font:700 12px IBM Plex Mono,monospace;letter-spacing:.08em;margin-bottom:8px">DESTAQUES DO QUARTER</div><ul>{lis}</ul></div>')
        total = sum(c['n'] for c in E['categorias'])
        body = (self.eyebrow(f'Entregas · Ekyte · {self.q["meses_extenso"]} de {self.ano}') + self.h2(f'{f(total)} entregas no quarter', 46) + f'<div class="ent-grid">{cards}</div>')
        self.sec('white vfill', f'{total} entregas no quarter', body)

    # -------------------------------------------------------------- planos de ação
    def plano(self, k, p):
        tipo = p.get('tipo', '5w'); eb = self.eyebrow(f'Planos de Ação {self.QN} · Plano {k} · {esc(p.get("tema", ""))}')
        if tipo == 'livre':
            body = eb + self.h2(p['titulo'], p.get('tamanho_titulo', 40)) + p['html']
        else:
            rows = ''.join(f'<div class="pa-row"><div class="pa-k">{esc(a)}</div><div class="pa-v">{b}</div></div>' for a, b in p['linhas'])
            src = self.asset(p.get('print'))
            if src:
                img = f'<img src="{src}" alt="{esc(p.get("legenda", ""))}" style="width:100%;height:auto;display:block">'
                img = f'<a href="{p["link"]}" target="_blank" rel="noopener" class="shot-frame" style="display:block">{img}</a>' if p.get('link') else f'<div class="shot-frame">{img}</div>'
                right = f'<div>{img}<p class="metric-sub" style="font-size:12px;color:var(--ink-soft);margin-top:8px">{p.get("legenda", "")}</p></div>'
                grid = '0.72fr 1.6fr'
            else:
                right, grid = '', '1fr'
            body = eb + self.h2(p['titulo'], p.get('tamanho_titulo', 34)) + f'<div style="display:grid;grid-template-columns:{grid};gap:24px;margin-top:12px;align-items:center"><div class="card" style="padding:6px 22px">{rows}</div>{right}</div>'
        self.sec('white vfill', p.get('data_title', f'Plano de ação {k}' + (f': {p["slide"]}' if p.get('slide') else '')), body)

    # -------------------------------------------------------------- fechamento
    def colli_conecta(self):
        for a in ('colli-conecta-flavio.jpg', 'qr-colli-conecta.png'):
            shutil.copy(os.path.join(FIX, a), os.path.join(self.out, 'assets', a))
        self.slides.append(read('colli-conecta.html'))

    def csat(self):
        """Gera assets/qr-pesquisa.png a partir de csat_url (precisa de node + pacote qrcode; ver SKILL.md)."""
        url = self.D.get('csat_url')
        if url and '<' not in url:
            import subprocess
            dst = os.path.join(self.out, 'assets', 'qr-pesquisa.png')
            env = dict(os.environ)
            try:
                subprocess.run(['node', os.path.join(SKILL, 'scripts', 'qr.js'), 'gerar', dst, url], check=True, env=env,
                               cwd=os.environ.get('CHECKIN_NODE_DIR', os.getcwd()), capture_output=True)
                print('  QR da pesquisa gerado:', url)
            except Exception as e:
                print('  [pendente] não gerei o QR automaticamente (', type(e).__name__, '): rode scripts/qr.js gerar')
        self.slides.append(read('csat.html'))

    # -------------------------------------------------------------- montagem
    def build(self):
        D = self.D
        self.R = self.funil(D['realizado']); self.A = self.funil(D['anterior']); self.P = self.funil(D['projetado'])
        if D['projetado'].get('margem_premissa'): self.P['margem_premissa'] = D['projetado']['margem_premissa']
        self.N = self.funil(D['proximo']) if D.get('proximo') else None
        if self.N is not None and D['proximo'].get('margem_premissa'): self.N['margem_premissa'] = D['proximo']['margem_premissa']
        an = D.get('analises', {})
        subs = ['Funil do quarter e Projetado x Realizado']
        if any(k in an for k in ('margem', 'concentracao', 'recompra', 'ciclo_mensal', 'ciclo_quarter')): subs.append('Vendas, margem e ciclo de vendas')
        if 'motivos' in an: subs.append('Qualidade dos leads')
        cn = [n for n, k in (('Google Ads', 'google'), ('Meta Ads', 'meta')) if k in D.get('canais', {})]
        if cn: subs.append(' e '.join(cn))
        self.capa(); self.menu(1, 'Resultados', subs, 'Sumário')
        self.funil_quarter(); self.proj_real(); self.gargalo(); self.breakeven_realizado()
        for k, fn in [('margem', self.analise_margem), ('concentracao', self.analise_concentracao), ('recompra', self.analise_recompra),
                      ('ciclo_mensal', self.analise_ciclo_mensal), ('ciclo_quarter', self.analise_ciclo_quarter), ('motivos', self.analise_motivos)]:
            if k in an: fn(an[k])
        C = D.get('canais', {})
        if 'google' in C: self.canal_google(C['google'])
        if 'otimizacao' in C: self.canal_otimizacao(C['otimizacao'])
        if 'meta' in C: self.canal_meta(C['meta'])
        self.menu(2, 'Objetivos', ['O que bateu e o que ficou devendo', f'Objetivo SMART e projeção do {self.QN}'])
        self.bateu()
        if self.N: self.smart(); self.projecao()
        if D.get('premissas'):
            self.menu(3, 'Premissas e riscos', []); self.premissas(D['premissas'])
        if D.get('entregas'):
            self.menu(4, 'Entregas', []); self.entregas(D['entregas'])
        self.menu(5, f'Planos de Ação {self.QN}', [p['titulo_menu'] for p in D.get('planos', []) if p.get('titulo_menu')])
        k = 0
        for p in D.get('planos', []):  # slides do mesmo plano repetem o mesmo "plano": n
            k = p.get('plano', k + 1)
            self.plano(k, p)
        self.colli_conecta(); self.csat()
        for a in ('colli-red.png', 'colli-white.png'):
            shutil.copy(os.path.join(FIX, a), os.path.join(self.out, 'assets', a))
        head = read('head.html').replace('{{TITLE}}', f'{esc(self.c["nome"])} | Check-in de Quarter {self.Q} {self.ano}')
        tail = read('tail.html').replace('01 / 33', f'01 / {len(self.slides):02d}')
        open(os.path.join(self.out, 'index.html'), 'w', encoding='utf-8').write(head + '\n      '.join(self.slides) + tail)
        open(os.path.join(self.out, 'vercel.json'), 'w').write('{"public": true}\n')
        open(os.path.join(self.out, '.gitignore'), 'w').write('.vercel\n')
        print(f'ok: {len(self.slides)} slides -> {self.out}/index.html')
        if not os.path.exists(os.path.join(self.out, 'assets', 'qr-pesquisa.png')):
            print('  [pendente] gerar assets/qr-pesquisa.png com scripts/qr.js (link CSAT do cliente, mês do disparo)')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    D = json.load(open(sys.argv[1], encoding='utf-8'))
    Deck(D, sys.argv[2]).build()
