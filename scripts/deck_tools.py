"""Ferramentas para editar o deck de check-in de quarter slide a slide, pelo data-title.

Uso (sempre com python3 -I):
    import sys; sys.path.insert(0, '<skill>/scripts'); import deck_tools as dt
    dt.titles(DECK)                          # lista numerada dos slides
    html = dt.get(DECK, 'Onde o funil quebrou')
    dt.replace(DECK, 'Onde o funil quebrou', novo_html)
    dt.remove(DECK, 'Concentração das vendas')
    dt.insert_after(DECK, 'Google Ads no quarter', html_do_slide_novo)
    dt.move_before(DECK, 'Colli Conecta', 'Antes de fechar')
    dt.check(DECK)                           # confere <div> abertos x fechados

Geradores (devolvem HTML pronto para colar dentro do slide):
    dt.ponte_vendas(proj, real)              # gráfico "ponte de vendas" do slide Onde o funil quebrou
    dt.goal_rows(itens)                      # barras do slide O que bateu e o que ficou devendo
"""
import re

SEC_RE = re.compile(r'<section\b.*?</section>', re.S)


def _read(p):
    return open(p, encoding='utf-8').read()


def _write(p, s):
    open(p, 'w', encoding='utf-8').write(s)


def _span(s, title):
    k = s.find(f'data-title="{title}"')
    if k < 0:
        raise KeyError(f'slide não encontrado: {title}')
    i = s.rfind('<section', 0, k)
    j = s.find('</section>', k) + len('</section>')
    return i, j


def titles(p):
    s = _read(p)
    out = re.findall(r'<section\b[^>]*data-title="([^"]*)"', s)
    for n, t in enumerate(out, 1):
        print(f'{n:>2}  {t}')
    return out


def get(p, title):
    s = _read(p); i, j = _span(s, title); return s[i:j]


def replace(p, title, new_html):
    s = _read(p); i, j = _span(s, title); _write(p, s[:i] + new_html + s[j:])


def remove(p, title):
    s = _read(p); i, j = _span(s, title)
    _write(p, s[:i].rstrip() + '\n      ' + s[j:].lstrip())


def insert_after(p, title, new_html):
    s = _read(p); i, j = _span(s, title)
    _write(p, s[:j] + '\n      ' + new_html + s[j:])


def insert_before(p, title, new_html):
    s = _read(p); i, j = _span(s, title)
    _write(p, s[:i] + new_html + '\n      ' + s[i:])


def move_before(p, title, before_title):
    s = _read(p); i, j = _span(s, title); block = s[i:j]
    s = s[:i].rstrip() + '\n      ' + s[j:].lstrip()
    k, _ = _span(s, before_title)
    _write(p, s[:k] + block + '\n      ' + s[k:])


def check(p):
    s = _read(p)
    a, b = s.count('<div'), s.count('</div>')
    n = len(SEC_RE.findall(s))
    print(f'slides: {n} | <div {a} x </div> {b}' + ('' if a == b else '  <-- DESBALANCEADO'))
    return a == b


# ------------------------------------------------------------------ formatação pt-BR
def f(x, d=0):
    s = f'{x:,.{d}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def pct(x, d=2):
    return f(x, d) + '%'


# ------------------------------------------------------------------ ponte de vendas
def ponte_vendas(proj, real, titulo=None):
    """Waterfall de vendas: projetado -> efeito de cada etapa -> realizado.

    proj/real = {'leads': int, 'lm': taxa Lead->MQL (0-1), 'ms': MQL->SQL, 'sv': SQL->Venda}
    Decomposição por substituição sequencial: troca uma variável projetada pela realizada
    de cada vez (leads, depois Lead->MQL, MQL->SQL, SQL->Venda). A soma dos efeitos fecha
    exatamente projetado -> realizado.
    """
    order = [('leads', 'Menos leads' , 'Mais leads'), ('lm', 'Lead → MQL', 'Lead → MQL'),
             ('ms', 'MQL → SQL', 'MQL → SQL'), ('sv', 'SQL → Venda', 'SQL → Venda')]
    cur = dict(proj)
    v = lambda d: d['leads'] * d['lm'] * d['ms'] * d['sv']
    v0 = v(cur); steps = []
    for k, neg, pos in order:
        before = v(cur); cur[k] = real[k]; after = v(cur)
        if k == 'leads':
            lab, sub = (neg if after < before else pos), f'{f(real["leads"])} contra {f(proj["leads"])}'
        else:
            lab, sub = neg, f'{pct(real[k] * 100)} contra {pct(proj[k] * 100)}'
        steps.append((lab, sub, after - before))
    v1 = v(cur)
    W, H, base, top = 1408, 196, 134.0, 34.3
    vmax = max(v0, v1, *(v0 + sum(d for *_, d in steps[:i + 1]) for i in range(len(steps))))
    sc = (base - top) / vmax
    n = len(steps) + 2; slot = W / n; bw = slot * 0.6
    out = [f'<line x1="0" x2="{W}" y1="{base}" y2="{base}" stroke="rgba(20,20,20,.18)"/>']

    def bar(i, y0, y1, color, val, lab, sub, valcolor):
        x = i * slot + (slot - bw) / 2; cx = x + bw / 2
        y, h = min(y0, y1), max(abs(y1 - y0), 3)
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="6" fill="{color}"/>')
        out.append(f'<text x="{cx:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-weight="700" font-size="17" fill="{valcolor}">{val}</text>')
        out.append(f'<text x="{cx:.1f}" y="158.0" text-anchor="middle" font-family="IBM Plex Sans" font-weight="700" font-size="15" fill="#141414">{lab}</text>')
        out.append(f'<text x="{cx:.1f}" y="177.0" text-anchor="middle" font-family="IBM Plex Mono" font-size="11.5" fill="#5a5a5a">{sub}</text>')
        return x + bw

    y = lambda val: base - val * sc
    end = bar(0, base, y(v0), '#3a3a3a', f(v0, 0), 'Projetado', f'{f(proj["leads"])} leads · {f(v0, 0)} vendas', '#141414')
    acc = v0
    for i, (lab, sub, d) in enumerate(steps, 1):
        nxt = acc + d; x = i * slot + (slot - bw) / 2
        out.append(f'<line x1="{end:.1f}" x2="{x:.1f}" y1="{y(acc):.1f}" y2="{y(acc):.1f}" stroke="rgba(20,20,20,.3)" stroke-dasharray="4 4"/>')
        good = d >= 0; col = '#1e8a4c' if good else '#e50914'
        end = bar(i, y(acc), y(nxt), col, ('+' if good else '−') + f(abs(d), 1), lab, sub, col)
        acc = nxt
    x = (n - 1) * slot + (slot - bw) / 2
    out.append(f'<line x1="{end:.1f}" x2="{x:.1f}" y1="{y(acc):.1f}" y2="{y(acc):.1f}" stroke="rgba(20,20,20,.3)" stroke-dasharray="4 4"/>')
    bar(n - 1, base, y(v1), '#e50914', f(v1, 0), 'Realizado', f'{f(real["leads"])} leads · {f(v1, 0)} vendas', '#e50914')
    titulo = titulo or f'PONTE DE VENDAS: DE {f(v0, 0)} PROJETADAS A {f(v1, 0)} REALIZADAS, ETAPA POR ETAPA'
    return (f'<div class="card" style="padding:12px 24px 8px;margin-top:14px"><div class="mono" style="font-size:11px;font-weight:700;letter-spacing:.09em;color:var(--ink-soft);margin-bottom:2px">{titulo}</div>'
            f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">{"".join(out)}</svg></div>'), steps


# ------------------------------------------------------------------ o que bateu e o que ficou devendo
def goal_rows(itens, escala=220):
    """itens = [(rótulo, %_da_meta, 'detalhe')], já ordenados do maior para o menor.
    % da meta: realizado ÷ meta x 100; em custo (CPL, CAC), use meta ÷ realizado x 100 e
    escreva '(menor é melhor)' no rótulo. Verde >= 100, amarelo >= 90, vermelho < 90.
    """
    mk = 100 / escala * 100; rows = ''
    for lab, p, det in itens:
        cor, var = ('#1e8a4c', 'var(--safe)') if p >= 100 else (('#d9a441', 'var(--care)') if p >= 90 else ('#e50914', 'var(--v4-red)'))
        w = min(p / escala * 100, 100)
        rows += (f'<div class="goal-row"><div class="gl">{lab}</div><div class="gt"><i style="width:{w:.1f}%;background:{cor}"></i>'
                 f'<b class="gm" style="left:{mk:.2f}%"></b></div><div class="gp" style="color:{var}">{pct(p, 1)}</div><div class="gd">{det}</div></div>')
    leg = ('<div style="display:flex;gap:26px;margin-top:8px;font:600 12.5px IBM Plex Mono,monospace;color:var(--ink-soft)">'
           '<span><i style="display:inline-block;width:12px;height:12px;background:#1e8a4c;border-radius:3px;margin-right:7px"></i>bateu a meta</span>'
           '<span><i style="display:inline-block;width:12px;height:12px;background:#d9a441;border-radius:3px;margin-right:7px"></i>a menos de 10% da meta</span>'
           '<span><i style="display:inline-block;width:12px;height:12px;background:#e50914;border-radius:3px;margin-right:7px"></i>ficou devendo</span>'
           '<span>linha tracejada = 100% da meta</span></div>')
    return f'<div class="card" style="margin-top:12px;padding:14px 26px 12px">{rows}{leg}</div>'
