from diag_base import *

# ---------------- Conceptual ----------------
pos = {'Compromiso presupuestal': (0, 0), 'Unidad ejecutora': (-4.4, 1.6), 'Entidad distrital': (-4.4, 4.2),
       'Tipo de entidad': (-0.6, 4.6), 'Rubro presupuestal': (4.4, 1.6), 'Concepto de gasto': (4.4, 4.2),
       'Tipo de gasto': (8.2, 4.2), 'Programa / proyecto': (4.2, -2.8), 'Plan de desarrollo': (8.2, -2.8),
       'Periodo (vigencia, mes)': (-4.4, -2.8)}
rels = [('Entidad distrital', 'tiene', 'Unidad ejecutora', '1', 'N'),
        ('Entidad distrital', 'se clasifica en', 'Tipo de entidad', 'N', '1'),
        ('Unidad ejecutora', 'registra', 'Compromiso presupuestal', '1', 'N'),
        ('Compromiso presupuestal', 'se imputa a', 'Rubro presupuestal', 'N', '1'),
        ('Rubro presupuestal', 'se agrupa en', 'Concepto de gasto', 'N', '1'),
        ('Concepto de gasto', 'pertenece a', 'Tipo de gasto', 'N', '1'),
        ('Compromiso presupuestal', 'financia', 'Programa / proyecto', 'N', '1'),
        ('Programa / proyecto', 'ejecuta', 'Plan de desarrollo', 'N', '1'),
        ('Compromiso presupuestal', 'ocurre en', 'Periodo (vigencia, mes)', 'N', '1')]
s = ['graph G { layout=neato; overlap=false; splines=true; bgcolor="white"; pad=0.3;',
     f'node [fontname="{FONT}", fontsize=13, color="{TEAL}", fontcolor="{INK}", penwidth=1.6];',
     f'edge [fontname="{FONT}", fontsize=11, color="{LINE}", fontcolor="{MUTED}", penwidth=1.3];']
for e, (x, y) in pos.items():
    fill = TEAL_BG if e == 'Compromiso presupuestal' else 'white'
    s.append(f'"{e}" [shape=box, style="rounded,filled", fillcolor="{fill}", pos="{x},{y}!", margin="0.18,0.1"];')
for i, (a, r, b, ca, cb) in enumerate(rels):
    (xa, ya), (xb, yb) = pos[a], pos[b]
    s.append(f'r{i} [label="{r}", shape=diamond, style=filled, fillcolor="{AMBER_BG}", color="#D98E04", fontsize=10.5, pos="{(xa+xb)/2},{(ya+yb)/2}!", width=0.5, height=0.4, margin=0.02];')
    s.append(f'"{a}" -- r{i} [label=" {ca} "]; r{i} -- "{b}" [label=" {cb} "];')
s.append('}')
render('fin_conceptual', '\n'.join(s))

# ---------------- Lógico 3FN ----------------
L = ['digraph G { rankdir=LR; bgcolor="white"; pad=0.3; nodesep=0.35; ranksep=1.0; splines=ortho;',
     f'node [fontname="{FONT}", fontsize=11.5]; edge [color="{LINE}", arrowhead=crow, arrowtail=tee, dir=both, penwidth=1.2];']
L += [table('tipo_entidad', [('tipo_entidad_id', 'SMALLINT', 'PK'), ('sigla', 'VARCHAR(5)', ''), ('nombre', 'VARCHAR(60)', '')]),
      table('entidad', [('entidad_cod', 'CHAR(4)', 'PK'), ('nombre', 'VARCHAR(200)', ''), ('sigla', 'VARCHAR(20)', ''), ('tipo_entidad_id', 'SMALLINT', 'FK')]),
      table('unidad_ejecutora', [('unidad_cod', 'VARCHAR(10)', 'PK'), ('entidad_cod', 'CHAR(4)', 'FK'), ('nombre', 'VARCHAR(200)', '')]),
      table('periodo', [('periodo_id', 'INT', 'PK'), ('vigencia', 'SMALLINT', ''), ('mes', 'SMALLINT', '')]),
      table('plan_desarrollo', [('pdd_cod', 'CHAR(2)', 'PK'), ('nombre', 'VARCHAR(120)', ''), ('anio_inicio', 'SMALLINT', ''), ('anio_fin', 'SMALLINT', '')]),
      table('programa', [('programa_cod', 'VARCHAR(25)', 'PK'), ('nombre', 'VARCHAR(300)', ''), ('tipo_programa', 'VARCHAR(30)', ''), ('pdd_cod', 'CHAR(2)', 'FK')]),
      table('tipo_gasto', [('tipo_gasto_cod', 'CHAR(3)', 'PK'), ('nombre', 'VARCHAR(40)', '')]),
      table('concepto_gasto', [('concepto_cod', 'CHAR(4)', 'PK'), ('nombre', 'VARCHAR(80)', ''), ('tipo_gasto_cod', 'CHAR(3)', 'FK')]),
      table('rubro', [('rubro_cod', 'VARCHAR(25)', 'PK'), ('descripcion', 'VARCHAR(300)', ''), ('concepto_cod', 'CHAR(4)', 'FK')]),
      table('compromiso_mensual', [('unidad_cod', 'VARCHAR(10)', 'PK'), ('programa_cod', 'VARCHAR(25)', 'PK'), ('rubro_cod', 'VARCHAR(25)', 'PK'),
                                   ('periodo_id', 'INT', 'PK'), ('valor_acumulado', 'NUMERIC(18,2)', ''), ('valor_mes', 'NUMERIC(18,2)', '')], bg=TEAL_BG),
      'tipo_entidad -> entidad; entidad -> unidad_ejecutora; unidad_ejecutora -> compromiso_mensual;',
      'plan_desarrollo -> programa; programa -> compromiso_mensual;',
      'tipo_gasto -> concepto_gasto; concepto_gasto -> rubro; rubro -> compromiso_mensual; periodo -> compromiso_mensual;',
      '{rank=same; tipo_entidad; plan_desarrollo; tipo_gasto}', '{rank=same; entidad; programa; concepto_gasto}',
      '{rank=same; unidad_ejecutora; periodo; rubro}', '}']
render('fin_logico', '\n'.join(L))

# ---------------- Estrella ----------------
def at(t, x, y):
    return t.replace(' [shape=plain', f' [pos="{x},{y}!", shape=plain', 1)
S = ['digraph G { layout=neato; overlap=false; bgcolor="white"; pad=0.3; splines=true;',
     f'node [fontname="{FONT}", fontsize=11]; edge [color="{LINE}", penwidth=1.3, arrowhead=none];']
S += [at(table('fact_compromiso', [('entidad_cod', 'CHAR(4)', 'FK'), ('unidad_ejecutora', 'VARCHAR', ''), ('programa_sk', 'INT', 'FK'),
                                   ('rubro_sk', 'INT', 'FK'), ('fecha', 'DATE', 'FK'), ('vigencia', 'SMALLINT', ''), ('mes', 'SMALLINT', ''),
                                   ('compromiso_acumulado', 'NUMERIC', ''), ('compromiso_mes', 'NUMERIC', '')], color='#B45309', bg=AMBER_BG), 0, 0),
      at(table('dim_entidad', [('entidad_cod', 'CHAR(4)', 'PK'), ('entidad', 'VARCHAR', ''), ('sigla', 'VARCHAR', ''), ('tipo_entidad', 'VARCHAR', '')]), -5, 1.6),
      at(table('dim_calendario', [('fecha', 'DATE', 'PK'), ('vigencia', 'SMALLINT', ''), ('mes', 'SMALLINT', ''), ('nombre_mes', 'VARCHAR', ''), ('semestre', 'CHAR', '')]), -5, -2.0),
      at(table('dim_rubro', [('rubro_sk', 'INT', 'PK'), ('rubro_cod', 'VARCHAR', ''), ('rubro', 'VARCHAR', ''), ('tipo_gasto', 'VARCHAR', ''), ('concepto_gasto', 'VARCHAR', '')]), 5, 1.6),
      at(table('dim_programa', [('programa_sk', 'INT', 'PK'), ('programa_cod', 'VARCHAR', ''), ('programa', 'VARCHAR', ''), ('tipo_programa', 'VARCHAR', ''), ('plan_desarrollo', 'VARCHAR', '')]), 5, -2.0),
      'dim_entidad -> fact_compromiso; dim_calendario -> fact_compromiso; dim_rubro -> fact_compromiso; dim_programa -> fact_compromiso; }']
render('fin_estrella', '\n'.join(S))
print('ok')
