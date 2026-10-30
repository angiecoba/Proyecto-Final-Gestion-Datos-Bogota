"""Maqueta del tablero Power BI (datos reales) → PNG."""
import pandas as pd, json
T = pd.read_pickle('out/tablas.pkl')
f = (T['Hechos_Compromisos'].merge(T['Rubro'], on='rubro_sk').merge(T['Entidad'], on='entidad_cod')
     .merge(T['Programa'], on='programa_sk'))
INV, FUN, DEU = '#0089A0', '#D9822B', '#7A5CB8'
YC = {2022: '#C2E5E9', 2023: '#7CC3CD', 2024: '#2F98A8', 2025: '#0F5C63'}
VIG = [2022, 2023, 2024, 2025]
INK, MUT, GRID = '#1F2A37', '#5B6676', '#E6E9EE'
B = 1e12
def bn(x, d=1): return f'{x:,.{d}f}'.replace('.', ',')
def pct(x, d=1): return f'{100*x:,.{d}f}%'.replace('.', ',')
tot = f.groupby('vigencia').compromiso_mes.sum() / B
tg = (f.groupby(['vigencia', 'tipo_gasto']).compromiso_mes.sum() / B).unstack()
acc = f.groupby(['vigencia', 'mes']).compromiso_acumulado.sum().unstack(0); curva = acc / acc.iloc[-1]
mes = f.groupby(['vigencia', 'mes']).compromiso_mes.sum().unstack(0)
e = f.groupby(['vigencia', 'sigla']).compromiso_mes.sum().unstack(0) / 1e9
e['var'] = e[2025] / e[2024] - 1
top = e.sort_values(2025, ascending=False).head(10)
top5 = e[2025].sort_values(ascending=False).head(5).sum() / e[2025].sum()
inv24 = f[(f.vigencia == 2024) & (f.tipo_programa == 'Proyecto de inversión')]
pdd = (inv24.groupby(['mes', 'plan_desarrollo']).compromiso_mes.sum() / B).unstack().fillna(0)
OLD, NEW = 'Un Nuevo Contrato Social y Ambiental (2020–2024)', 'Bogotá Camina Segura (2024–2027)'
kpis = [('Compromisos 2025', f'${bn(tot[2025])} bill.', f'2022: ${bn(tot[2022])} · 2024: ${bn(tot[2024])}'),
        ('Variación 2025 vs. 2024', f'+{pct(tot[2025]/tot[2024]-1)}', f'2022–2025: +{pct(tot[2025]/tot[2022]-1)}'),
        ('Peso de la inversión', pct(tg.loc[2025, 'Inversión'] / tot[2025]), 'del total comprometido 2025'),
        ('Concentración', pct(top5), '5 entidades del total 2025'),
        ('Comprometido en diciembre', pct(mes.loc[12, 2025] / mes[2025].sum()), f'2022: {pct(mes.loc[12,2022]/mes[2022].sum())}')]

def stacked_cols(w=400, h=270):
    mt, mb, ml = 16, 26, 10; H = h - mt - mb; mx = tot.max() * 1.12; bw = 66; gap = (w - ml * 2 - 4 * bw) / 4
    o = [f'<svg width="{w}" height="{h}" font-family="Inter" font-size="11">']
    for i, v in enumerate(VIG):
        x = ml + gap / 2 + i * (bw + gap); y = mt + H
        for k, col in (('Inversión', INV), ('Funcionamiento', FUN), ('Servicio de la deuda', DEU)):
            hh = H * tg.loc[v, k] / mx; y -= hh
            o.append(f'<rect x="{x:.1f}" y="{y+1:.1f}" width="{bw}" height="{max(hh-2,1):.1f}" rx="2" fill="{col}"/>')
            if hh > 22: o.append(f'<text x="{x+bw/2:.1f}" y="{y+hh/2+4:.1f}" text-anchor="middle" fill="#fff" font-weight="600">{bn(tg.loc[v,k])}</text>')
        o.append(f'<text x="{x+bw/2:.1f}" y="{y-6:.1f}" text-anchor="middle" fill="{INK}" font-weight="700">{bn(tot[v])}</text>')
        o.append(f'<text x="{x+bw/2:.1f}" y="{h-6}" text-anchor="middle" fill="{MUT}">{v}</text>')
    o.append('</svg>'); return ''.join(o)

def curve_svg(w=400, h=250):
    ml, mr, mt, mb = 40, 46, 10, 26; W, H = w - ml - mr, h - mt - mb
    sx = lambda m: ml + W * (m - 1) / 11; sy = lambda v: mt + H * (1 - v)
    o = [f'<svg width="{w}" height="{h}" font-family="Inter" font-size="10.5">']
    for t in (0, .25, .5, .75, 1):
        o.append(f'<line x1="{ml}" x2="{w-mr}" y1="{sy(t)}" y2="{sy(t)}" stroke="{GRID}"/><text x="{ml-6}" y="{sy(t)+4}" text-anchor="end" fill="{MUT}">{int(t*100)}%</text>')
    for m in range(1, 13):
        o.append(f'<text x="{sx(m):.1f}" y="{h-8}" text-anchor="middle" fill="{MUT}">{"EFMAMJJASOND"[m-1]}</text>')
    for v in VIG:
        pts = ' '.join(f'{sx(m):.1f},{sy(curva.loc[m, v]):.1f}' for m in range(1, 13))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{YC[v]}" stroke-width="2.5"/>')
    o.append(f'<line x1="{sx(6)}" x2="{sx(6)}" y1="{mt}" y2="{mt+H}" stroke="{MUT}" stroke-dasharray="3 3"/>')
    o.append('</svg>'); return ''.join(o)

def pdd_svg(w=400, h=270):
    ml, mt, mb = 34, 12, 26; W, H = w - ml - 10, h - mt - mb; mx = (pdd[OLD] + pdd[NEW]).clip(lower=0).max() * 1.1
    bw = W / 12 - 8; sy = lambda v: mt + H * (1 - v / mx)
    o = [f'<svg width="{w}" height="{h}" font-family="Inter" font-size="10.5">']
    for t in (0, 1, 2, 3):
        if t <= mx: o.append(f'<line x1="{ml}" x2="{w-10}" y1="{sy(t):.1f}" y2="{sy(t):.1f}" stroke="{GRID}"/><text x="{ml-6}" y="{sy(t)+4:.1f}" text-anchor="end" fill="{MUT}">{t}</text>')
    for m in range(1, 13):
        x = ml + (m - 1) * W / 12 + 4; base = mt + H
        for k, col in ((OLD, FUN), (NEW, INV)):
            v = max(pdd.loc[m, k], 0); hh = H * v / mx
            if hh > 0.5:
                o.append(f'<rect x="{x:.1f}" y="{base-hh:.1f}" width="{bw:.1f}" height="{max(hh-1,0.5):.1f}" rx="2" fill="{col}"/>'); base -= hh
        o.append(f'<text x="{x+bw/2:.1f}" y="{h-8}" text-anchor="middle" fill="{MUT}">{"EFMAMJJASOND"[m-1]}</text>')
    x6 = ml + 5 * W / 12 + 4
    o.append(f'<text x="{x6+bw/2:.1f}" y="{mt+H-8:.1f}" text-anchor="middle" fill="{INK}" font-weight="700">$0</text>')
    o.append('</svg>'); return ''.join(o)

def top_svg(w=470, h=300):
    x0 = 96; bw = w - x0 - 120; lh = h / len(top); mx = top[2025].max()
    o = [f'<svg width="{w}" height="{h}" font-family="Inter" font-size="11">']
    for i, (s, r) in enumerate(top.iterrows()):
        y = i * lh + 3
        o.append(f'<text x="{x0-8}" y="{y+13}" text-anchor="end" fill="{INK}">{s}</text>')
        o.append(f'<rect x="{x0}" y="{y}" width="{bw*r[2025]/mx:.1f}" height="17" rx="3" fill="{INV}"/>')
        sign = '+' if r['var'] >= 0 else '−'
        o.append(f'<text x="{x0+bw*r[2025]/mx+6:.1f}" y="{y+13}" fill="{MUT}">{bn(r[2025]/1000,2)} · <tspan fill="{INK}" font-weight="600">{sign}{pct(abs(r["var"]),0)}</tspan></text>')
    o.append('</svg>'); return ''.join(o)

css = f'''body{{margin:0;font-family:Inter;background:#EEF1F4;color:{INK};width:1600px;height:900px}}
.page{{display:grid;grid-template-columns:210px 1fr;height:900px}} .side{{background:#0F5C63;color:#fff;padding:22px 18px;position:relative}}
.side h3{{font-size:12px;letter-spacing:.06em;text-transform:uppercase;opacity:.75;margin:22px 0 8px}}
.sl{{background:rgba(255,255,255,.12);border-radius:6px;padding:8px 10px;font-size:12.5px;margin-bottom:6px;display:flex;justify-content:space-between}}
.main{{padding:18px 22px;display:flex;flex-direction:column;gap:12px;min-width:0;overflow:hidden}} .row>div, .kpis>div{{min-width:0;overflow:hidden}} h1{{font-size:22px;margin:0}} .sub{{color:{MUT};font-size:12.5px;margin-top:3px}}
.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}} .card{{background:#fff;border-radius:8px;padding:12px 14px;box-shadow:0 1px 2px rgba(0,0,0,.06)}}
.k .l{{font-size:12px;color:{MUT}}} .k .v{{font-size:26px;font-weight:700;margin:2px 0}} .k .s{{font-size:11.5px;color:{MUT}}}
.row{{display:grid;gap:12px}} .r1{{grid-template-columns:1fr 1fr 1fr;height:330px}} .r2{{grid-template-columns:1.1fr 1fr;height:330px}}
.t{{font-size:13.5px;font-weight:600;margin-bottom:4px}} .lg{{font-size:11px;color:{MUT};display:flex;gap:12px;margin-bottom:4px;flex-wrap:wrap}}
.sw{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}}
table{{width:100%;border-collapse:collapse;font-size:12px}} th{{text-align:left;color:{MUT};font-weight:500;border-bottom:1px solid {GRID};padding:5px 4px}}
td{{padding:6px 4px;border-bottom:1px solid {GRID}}} .n{{text-align:right}}'''
cg = (f.groupby(['vigencia', 'concepto_gasto']).compromiso_mes.sum() / B).unstack(0).sort_values(2025, ascending=False).head(6)
trs = ''.join(f'<tr><td>{c}</td>' + ''.join(f'<td class="n">{bn(r[v],2)}</td>' for v in VIG) +
              f'<td class="n">{"+" if r[2025]>=r[2022] else "−"}{pct(abs(r[2025]/r[2022]-1),0) if r[2022]>0.01 else "—"}</td></tr>' for c, r in cg.iterrows())
html = f'''<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="page">
<div class="side"><div style="font-weight:700;font-size:15px">Presupuesto<br>Bogotá D.C.</div><div style="font-size:11px;opacity:.75;margin-top:4px">Compromisos 2022–2025</div>
<h3>Vigencia</h3><div class="sl">2022</div><div class="sl">2023</div><div class="sl">2024</div><div class="sl" style="background:rgba(255,255,255,.28)">2025 ✓</div>
<h3>Tipo de entidad</h3><div class="sl">Todas <span>▾</span></div><h3>Tipo de gasto</h3><div class="sl">Todos <span>▾</span></div>
<h3>Entidad</h3><div class="sl">Buscar… <span>⌕</span></div>
<div style="position:absolute;bottom:20px;font-size:10.5px;opacity:.7;width:175px">Fuente: SDH · Informe de Gastos e Inversiones · datosabiertos.bogota.gov.co · Cifras en billones de pesos corrientes</div></div>
<div class="main"><div><h1>¿En qué y a qué ritmo compromete el Distrito su presupuesto?</h1><div class="sub">Compromisos presupuestales de 44 entidades · Administración Central, Establecimientos Públicos y Órganos de Control · Propuesta de tablero en Power BI</div></div>
<div class="kpis">{''.join(f'<div class="card k"><div class="l">{a}</div><div class="v">{b}</div><div class="s">{s}</div></div>' for a,b,s in kpis)}</div>
<div class="row r1">
<div class="card"><div class="t">Compromisos por tipo de gasto (billones)</div><div class="lg"><span><i class="sw" style="background:{INV}"></i>Inversión</span><span><i class="sw" style="background:{FUN}"></i>Funcionamiento</span><span><i class="sw" style="background:{DEU}"></i>Deuda</span></div>{stacked_cols()}</div>
<div class="card"><div class="t">Ritmo: % del total anual comprometido</div><div class="lg">{''.join(f'<span><i class="sw" style="background:{YC[v]}"></i>{v}</span>' for v in VIG)}</div><div class="lg">A junio: {' · '.join(f'{v} {pct(curva.loc[6,v],0)}' for v in VIG)}</div>{curve_svg()}</div>
<div class="card"><div class="t">2024: inversión por Plan de Desarrollo (bill./mes)</div><div class="lg"><span><i class="sw" style="background:{FUN}"></i>Un Nuevo Contrato Social</span><span><i class="sw" style="background:{INV}"></i>Bogotá Camina Segura</span></div>{pdd_svg()}</div>
</div>
<div class="row r2">
<div class="card"><div class="t">Top 10 entidades 2025 · billones y variación vs. 2024</div>{top_svg(w=600,h=290)}</div>
<div class="card"><div class="t">Compromisos por concepto de gasto (billones)</div><table><tr><th>Concepto</th><th class="n">2022</th><th class="n">2023</th><th class="n">2024</th><th class="n">2025</th><th class="n">Var. 22–25</th></tr>{trs}</table></div>
</div></div></div></body></html>'''
open('out/dashboard_mockup.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1600, 'height': 900}, device_scale_factor=2)
    pg.goto('file:///root/fin/out/dashboard_mockup.html'); pg.wait_for_timeout(400)
    pg.screenshot(path='out/img/fin_dashboard.png'); b.close()
json.dump(dict(tot=tot.round(4).to_dict(), curva6={int(k): float(v) for k, v in curva.loc[6].items()}, top5=float(top5)), open('out/mock.json', 'w'))
print('ok')
