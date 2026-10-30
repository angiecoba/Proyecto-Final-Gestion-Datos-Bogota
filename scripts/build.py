"""ETL — Informe de Gastos e Inversiones (SDH, Bogotá) → modelo estrella para Power BI.
Lee los CSV anuales de raw/ (compromisos mensuales ACUMULADOS por entidad, proyecto y rubro),
los normaliza a una tabla de hechos mensual y genera dimensiones."""
import csv, glob, re, os, json, collections
import pandas as pd

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto',
         'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
TIPO = {'AC': 'Administración Central', 'EP': 'Establecimientos Públicos',
        'OC': 'Organismo de Control', 'EAU': 'Ente Autónomo Universitario'}
NIVEL1 = {'O21': 'Funcionamiento', 'O22': 'Servicio de la deuda', 'O23': 'Inversión'}
# Clasificación CCPET (Catálogo de Clasificación Presupuestal para Entidades Territoriales)
NIVEL2 = {'1': 'Gastos de personal', '2': 'Adquisición de bienes y servicios', '3': 'Transferencias corrientes',
          '4': 'Transferencias de capital', '5': 'Gastos de comercialización y producción',
          '6': 'Adquisición de activos financieros', '7': 'Disminución de pasivos',
          '8': 'Tributos, tasas, contribuciones, multas y sanciones', '9': 'Sentencias, conciliaciones y otros'}
DEUDA2 = {'O221': 'Deuda pública externa', 'O222': 'Deuda pública interna'}
SIGLA = {'0100': 'Concejo', '0102': 'Personería', '0104': 'Sec. General', '0105': 'Veeduría', '0110': 'SDG', '0111': 'SDH',
         '0112': 'SED', '0113': 'SDM', '0114': 'SDS', '0117': 'SDDE', '0118': 'SDHT', '0119': 'SCRD', '0120': 'SDP',
         '0121': 'SDMujer', '0122': 'SDIS', '0125': 'DASCD', '0126': 'SDA', '0127': 'DADEP', '0131': 'UAECOB', '0136': 'SJD',
         '0137': 'SDSCJ', '0200': 'IPES', '0201': 'FFDS', '0203': 'IDIGER', '0204': 'IDU', '0206': 'FONCEP', '0208': 'CVP',
         '0211': 'IDRD', '0213': 'IDPC', '0214': 'IDIPRON', '0215': 'FUGA', '0216': 'OFB', '0218': 'JBB', '0219': 'IDEP',
         '0220': 'IDPAC', '0221': 'IDT', '0222': 'IDARTES', '0226': 'UAECD', '0227': 'UAERMV', '0228': 'UAESP',
         '0229': 'IDPYBA', '0230': 'UDFJC', '0235': 'Contraloría', '0501': 'ATENEA'}
PDD = {'16': 'Un Nuevo Contrato Social y Ambiental (2020–2024)', '17': 'Bogotá Camina Segura (2024–2027)'}

def num(s):
    s = (s or '').strip()
    if s in ('', '-'):
        return 0.0
    neg = s.startswith('(') or s.startswith('-')
    s = s.strip('()-').strip().replace('.', '').replace(',', '.')
    return -float(s) if neg else float(s)

def leer(path):
    rows = list(csv.reader(open(path, encoding='utf-8-sig'), delimiter=';'))
    h = [x.strip() for x in rows[0]]
    idx = {k: h.index(k) for k in h if k}
    out, trunc = [], 0
    for r in rows[1:]:
        if not r or not r[0].strip() or r[0].startswith('Fuente'):
            continue
        if len(r) != len(rows[0]):
            trunc += 1; continue
        g = lambda k: r[idx[k]].strip() if k in idx else ''
        vig = int(re.match(r'(\d{4})', g('Vigencia')).group(1))
        cod = g('Codigo Entidad')
        out.append(dict(vigencia=vig, tipo=TIPO.get(g('Tipo de entidad'), g('Tipo de entidad')),
                        entidad_cod=cod[:4], unidad_ejecutora=cod if '-' in cod else f'{cod}-NA',
                        entidad=re.sub(r'\s*-\s*Unidad \d+$', '', g('Nombre de la Entidad')).strip(),
                        programa_cod=g('Programa de financiación') or 'NO_PUBLICADO',
                        programa=g('Descripcion del Programa') or 'No publicado en este archivo',
                        rubro_cod=g('Código Rubro'), rubro=g('Descripción Rubro'),
                        acum=[num(r[idx[m]]) for m in MESES]))
    return out, trunc, h

def main():
    regs, log = [], {}
    for p in sorted(glob.glob('raw/g20*.csv')):
        rr, tr, h = leer(p)
        log[os.path.basename(p)] = dict(filas=len(rr), filas_truncadas=tr, columnas=len(h),
                                        tiene_programa='Programa de financiación' in h)
        regs += rr
    df = pd.DataFrame(regs)
    # ----- dimensiones -----
    ent = (df.sort_values('vigencia').groupby('entidad_cod').agg(entidad=('entidad', 'last'), tipo_entidad=('tipo', 'last'))
           .reset_index())
    ent['sigla'] = ent.entidad_cod.map(SIGLA).fillna(ent.entidad.str[:20])
    rub = df.sort_values('vigencia').groupby('rubro_cod').rubro.last().reset_index()
    rub['nivel1_cod'] = rub.rubro_cod.str[:3]
    rub['tipo_gasto'] = rub.nivel1_cod.map(NIVEL1)
    rub['nivel2_cod'] = rub.rubro_cod.str[:4]
    rub['concepto_gasto'] = [DEUDA2.get(c) if c.startswith('O22') else NIVEL2.get(c[3], 'Otro') for c in rub.nivel2_cod]
    rub.insert(0, 'rubro_sk', range(1, len(rub) + 1))
    prog = df.sort_values('vigencia').groupby('programa_cod').programa.last().reset_index()
    def clasif(c, n):
        if c == 'NO_PUBLICADO': return ('No publicado', None, 'Sin detalle (2025)')
        if 'Programa Funcionamiento' in n: return ('Funcionamiento', None, 'No aplica')
        if 'Transferencias de Inversi' in n: return ('Transferencias de inversión', None, 'No aplica')
        if 'Servicio Deuda' in n: return ('Servicio de la deuda', None, 'No aplica')
        if n.strip().upper() == 'GENERICO': return ('Genérico', None, 'No aplica')
        m = re.match(r'(?:O2301|13301)(\d{2})', c)
        pdd = m.group(1) if m else None
        return ('Proyecto de inversión', pdd, PDD.get(pdd, 'Otro / sin identificar'))
    cl = [clasif(c, n) for c, n in zip(prog.programa_cod, prog.programa)]
    prog['tipo_programa'] = [x[0] for x in cl]; prog['pdd_cod'] = [x[1] for x in cl]
    prog['plan_desarrollo'] = [x[2] for x in cl]
    prog['nombre_corto'] = [n if t == 'Proyecto de inversión' else t for n, t in zip(prog.programa, prog.tipo_programa)]
    prog.insert(0, 'programa_sk', range(1, len(prog) + 1))
    # ----- hechos (grano: vigencia × unidad × programa × rubro × mes) -----
    rsk = dict(zip(rub.rubro_cod, rub.rubro_sk)); psk = dict(zip(prog.programa_cod, prog.programa_sk))
    filas = []
    for i, r in enumerate(df.itertuples(index=False), start=1):
        prev = 0.0
        for m, a in enumerate(r.acum, start=1):
            flujo = a - prev; prev = a
            filas.append((r.vigencia, m, f'{r.vigencia}-{m:02d}-01', r.entidad_cod, r.unidad_ejecutora,
                          psk[r.programa_cod], rsk[r.rubro_cod], i, round(a, 2), round(flujo, 2)))
    fact = pd.DataFrame(filas, columns=['vigencia', 'mes', 'fecha', 'entidad_cod', 'unidad_ejecutora', 'programa_sk',
                                        'rubro_sk', 'linea_id', 'compromiso_acumulado', 'compromiso_mes'])
    cal = pd.DataFrame({'fecha': pd.date_range(f'{fact.vigencia.min()}-01-01', f'{fact.vigencia.max()}-12-01', freq='MS')})
    cal['vigencia'] = cal.fecha.dt.year; cal['mes'] = cal.fecha.dt.month
    cal['nombre_mes'] = cal.mes.map(lambda m: MESES[m - 1]); cal['trimestre'] = 'T' + cal.fecha.dt.quarter.astype(str)
    cal['semestre'] = cal.mes.map(lambda m: 'S1' if m <= 6 else 'S2'); cal['fecha'] = cal.fecha.dt.date
    os.makedirs('out', exist_ok=True)
    T = dict(Hechos_Compromisos=fact, Entidad=ent, Rubro=rub, Programa=prog, Calendario=cal)
    pd.to_pickle(dict(T, lineas=df), 'out/tablas.pkl')
    json.dump(log, open('out/log_carga.json', 'w'), ensure_ascii=False, indent=1)
    print(log); print({k: v.shape for k, v in T.items()})

if __name__ == '__main__':
    main()
