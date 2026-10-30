"""Exporta el kit para Power BI: dimensiones en Excel + hechos en CSV."""
import json, os, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

T = pd.read_pickle('out/tablas.pkl'); log = json.load(open('out/log_carga.json'))
F = 'Arial'; os.makedirs('out/kit', exist_ok=True)
fact = T['Hechos_Compromisos']
fact.to_csv('out/kit/Hechos_Compromisos.csv', index=False, encoding='utf-8-sig')
vig = sorted(fact.vigencia.unique())

wb = Workbook(); ws = wb.active; ws.title = 'Leeme'
ws['A1'] = 'Kit Power BI · Informe de Gastos e Inversiones de Bogotá D.C.'; ws['A1'].font = Font(name=F, size=14, bold=True)
ws['A2'] = f'Fuente: Secretaría Distrital de Hacienda, datosabiertos.bogota.gov.co · vigencias {", ".join(map(str, vig))} · valores en pesos corrientes'
ws['A2'].font = Font(name=F, size=10, italic=True, color='5B6676')
info = [
    ('Tablas del modelo', None),
    ('Hechos_Compromisos.csv', f'Hecho (archivo aparte por tamaño, {len(fact):,} filas). Grano: vigencia × unidad ejecutora × programa × rubro × mes.'.replace(',', '.')),
    ('Entidad', 'Dimensión. 44 entidades del Presupuesto Anual (Administración Central, Establecimientos Públicos, Organismo de Control, Ente Autónomo).'),
    ('Rubro', 'Dimensión. Rubro presupuestal hoja del catálogo CCPET, con tipo de gasto (nivel 1) y concepto de gasto (nivel 2).'),
    ('Programa', 'Dimensión. Programa de financiación: "Funcionamiento" o proyecto de inversión con su Plan de Desarrollo.'),
    ('Calendario', 'Dimensión mensual (primer día de cada mes).'),
    ('Reglas de negocio', None),
    ('compromiso_acumulado', 'Valor publicado por la SDH: compromisos acumulados de enero al mes indicado.'),
    ('compromiso_mes', 'Calculado: acumulado del mes − acumulado del mes anterior. Negativo = liberación o anulación de compromisos. Sumar esta columna da el total anual sin doble conteo.'),
    ('tipo_gasto', 'Tercer carácter del código de rubro: O21 Funcionamiento, O22 Servicio de la deuda, O23 Inversión.'),
    ('concepto_gasto', 'Cuarto carácter según CCPET: 1 personal, 2 bienes y servicios, 3 transferencias corrientes… En deuda: O221 externa, O222 interna.'),
    ('plan_desarrollo', 'Dígitos 6-7 del código de proyecto (O2301XX…): 16 = Un Nuevo Contrato Social y Ambiental (2020–2024); 17 = Bogotá Camina Segura (2024–2027).'),
    ('Limitación', 'El archivo solo trae compromisos: no incluye apropiación ni giros, por lo que no permite calcular % de ejecución. 2025 se publicó sin las columnas de programa/proyecto.'),
    ('Calidad de la carga', '; '.join(f"{k}: {v['filas']} filas, {v['filas_truncadas']} truncadas" for k, v in log.items())),
]
r = 4
for k, v in info:
    if v is None:
        ws.cell(r, 1, k).font = Font(name=F, size=11, bold=True, color='0F5C63')
    else:
        ws.cell(r, 1, k).font = Font(name=F, size=10, bold=True)
        c = ws.cell(r, 2, v); c.font = Font(name=F, size=10); c.alignment = Alignment(wrap_text=True, vertical='top')
    r += 1
ws.column_dimensions['A'].width = 26; ws.column_dimensions['B'].width = 120
for name in ['Entidad', 'Rubro', 'Programa', 'Calendario']:
    df = T[name]; s = wb.create_sheet(name); s.append(list(df.columns))
    for row in df.itertuples(index=False):
        s.append([None if (isinstance(v, float) and pd.isna(v)) else v for v in row])
    for c in s[1]:
        c.font = Font(name=F, size=10, bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='0F5C63')
    for row in s.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=F, size=10)
            if hasattr(c.value, 'year'): c.number_format = 'yyyy-mm-dd'
    t = Table(displayName=f't{name}', ref=f'A1:{get_column_letter(df.shape[1])}{df.shape[0] + 1}')
    t.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True); s.add_table(t)
    for i, col in enumerate(df.columns, 1):
        s.column_dimensions[get_column_letter(i)].width = min(max(len(str(col)), *(len(str(v)) for v in df[col].head(300))) + 2, 60)
    s.freeze_panes = 'A2'
wb.save('out/kit/Presupuesto_Dimensiones_PowerBI.xlsx')
print('ok', os.listdir('out/kit'))
