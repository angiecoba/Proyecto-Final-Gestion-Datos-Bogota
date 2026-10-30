# Verificación final de coherencia — 30 de octubre de 2026

## Material contrastado

- `datos/originales/Hechos_Compromisos.csv`: archivo de hechos integrado, inspeccionado directamente.
- `sql/modelo_fisico_presupuesto_postgresql.sql`: definición DDL entregada.
- `scripts/build.py` y `scripts/export.py`: transformación y exportación del kit.
- `modelos/fin_conceptual.png`, `fin_logico.png` y `fin_estrella.png`: diagramas entregados.
- Imagen compartida del modelo Power BI: `Entidad`, `Rubro`, `Programa`, `Calendario`, `Hechos` y tabla de medidas; las cuatro dimensiones tienen relaciones 1:N con hechos.
- `dashboard/Proyecto final HD Final.pbix`: artefacto recibido; no se ha ejecutado Power BI Desktop ni validado visualmente cada medida DAX dentro de esta revisión.

## Resultado de pruebas sobre el CSV de hechos

| Comprobación | Resultado | Estado |
|---|---:|---|
| Filas | 514.968 | Confirmado |
| Columnas | 10 | Confirmado |
| Vigencias | 2022, 2023, 2024, 2025 | Confirmado |
| Meses por vigencia | 12 | Confirmado |
| Duplicados exactos | 0 | Confirmado |
| Nulos en compromiso acumulado y mensual | 0 | Confirmado |
| Duplicados de `vigencia, unidad_ejecutora, programa_sk, rubro_sk, mes` | **3.132** | **Incompatibilidad con PK del SQL original** |
| Duplicados de `vigencia, linea_id, mes` | **0** | Clave técnica candidata válida en el CSV revisado |
| Valores mensuales negativos | **5.418** | Permitidos en la lógica de liberaciones/ajustes |
| Valores acumulados negativos | 0 | Compatible con CHECK original |

## Hallazgos y acciones

### 1. Clave primaria del hecho transaccional — crítico

El SQL original declara `PRIMARY KEY (unidad_cod, programa_cod, rubro_cod, periodo_id)`; el ETL genera más de una línea de origen con la misma combinación. En el archivo integrado se identificaron 3.132 registros duplicados bajo su equivalente analítico. **La carga del hecho transaccional fallaría por violación de clave primaria si se cargara una fila por línea sin agregar o preservar identificador.**

**Acción propuesta:** añadir `linea_id` a `presupuesto.compromiso_mensual` y usar `PRIMARY KEY (periodo_id, linea_id)`, siempre que la numeración de `linea_id` sea estable y única dentro de cada año; alternativamente, consolidar explícitamente las líneas con igual clave de negocio antes de cargar. En el CSV revisado `vigencia + linea_id + mes` no presenta duplicados. Se entrega SQL revisado como propuesta, **no como ejecución verificada**.

### 2. Valores posibles de tipo de programa — crítico

`build.py` genera categorías adicionales: `Transferencias de inversión`, `Servicio de la deuda` y `Genérico`. El CHECK de `presupuesto.programa.tipo_programa` solo acepta `Funcionamiento`, `Proyecto de inversión` y `No publicado`. **Una carga de esas categorías fallaría.** La versión SQL revisada amplía la lista.

### 3. Rutas y codificaciones ETL — pendiente de reproducibilidad

`build.py` espera `raw/g20*.csv` y abre los archivos con `utf-8-sig`; la auditoría local de 2025 requirió `cp1252`. El repositorio usa `datos/originales/`. Los scripts históricos se conservan sin reescritura para no alterar resultados existentes; hay que ajustar rutas y codificaciones o preparar el directorio de ejecución. Los CSV 2022, 2023 y 2024 deben quedar publicados si se desea reproducir toda la integración histórica desde fuentes.

### 4. Diagrama lógico frente a SQL revisado — pendiente gráfico

El diagrama lógico muestra la clave compuesta original del hecho (`unidad_cod`, `programa_cod`, `rubro_cod`, `periodo_id`). Si se adopta la propuesta SQL revisada, **el diagrama lógico deberá actualizarse para incluir `linea_id` como parte de la clave técnica**. Hasta entonces se conserva como representación del diseño original, con esta salvedad explícita.

### 5. Esquema estrella y Power BI — consistente en estructura, con cautelas

La tabla de hechos contiene `entidad_cod`, `programa_sk`, `rubro_sk`, `fecha`, `unidad_ejecutora`, `linea_id`, `vigencia`, `mes`, `compromiso_acumulado`, `compromiso_mes`, coincidentes con la estructura del SQL analítico. Las dimensiones `Entidad`, `Rubro`, `Programa` y `Calendario` corresponden al diagrama estrella y a la captura del modelo Power BI. El SQL analítico no declara una PK para la tabla de hechos; es recomendable incluir una clave técnica o restricción única tras verificar el grano de origen. Las medidas DAX y la integridad de todas las claves foráneas no han sido auditadas mediante ejecución en Power BI.

### 6. Semántica y cobertura — importante para las conclusiones

El dato de origen es acumulado y el flujo mensual se deriva por diferencia. No sumar acumulados de enero a diciembre. El conjunto no contiene apropiaciones ni giros; no presentar los compromisos como tasa de ejecución. El detalle de programas de 2025 es más limitado, por lo que las comparaciones por plan de desarrollo entre años deben declararse como parciales.

## Conclusión de auditoría

**Coherencia conceptual y analítica: favorable**, porque el modelo estrella y las relaciones mostradas en Power BI coinciden en su estructura general. **Coherencia física y reproducibilidad integral: condicionadas** por la clave primaria del hecho, el CHECK de programas, las rutas de ETL y la ausencia de prueba de despliegue PostgreSQL. Se recomienda documentar estos puntos como hallazgos y no afirmar que todo el sistema está implementado y ejecutado de extremo a extremo.
