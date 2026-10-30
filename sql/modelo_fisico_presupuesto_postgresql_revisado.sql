-- PROPUESTA REVISADA, NO DESPLEGADA NI VALIDADA EN POSTGRESQL.
-- Revisar estabilidad de linea_id y claves foraneas antes de la carga.
-- =====================================================================
-- Modelo físico — Informe de Gastos e Inversiones de Bogotá D.C. (SDH)
-- Motor: PostgreSQL 15+  |  Esquema transaccional (3FN) + esquema analítico (estrella)
-- Proyecto final · Herramientas de Gestión de Datos
-- Fuente: datosabiertos.bogota.gov.co/dataset/informe-de-gastos-e-inversiones-bogota
-- Valores en pesos colombianos corrientes (COP)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS presupuesto;   -- capa transaccional normalizada
CREATE SCHEMA IF NOT EXISTS dw;            -- capa analítica para Power BI

-- ---------------------------------------------------------------------
-- 1. CAPA TRANSACCIONAL (modelo lógico en 3FN)
-- ---------------------------------------------------------------------
CREATE TABLE presupuesto.tipo_entidad (
    tipo_entidad_id SMALLSERIAL PRIMARY KEY,
    sigla           VARCHAR(5)  NOT NULL UNIQUE,      -- AC, EP, OC, EAU
    nombre          VARCHAR(60) NOT NULL
);

CREATE TABLE presupuesto.entidad (
    entidad_cod     CHAR(4)      PRIMARY KEY,         -- 0111 = Secretaría Distrital de Hacienda
    nombre          VARCHAR(200) NOT NULL,
    sigla           VARCHAR(20),
    tipo_entidad_id SMALLINT     NOT NULL REFERENCES presupuesto.tipo_entidad
);

CREATE TABLE presupuesto.unidad_ejecutora (
    unidad_cod      VARCHAR(10)  PRIMARY KEY,         -- 0111-01, 0111-02 ...
    entidad_cod     CHAR(4)      NOT NULL REFERENCES presupuesto.entidad,
    nombre          VARCHAR(200)
);

CREATE TABLE presupuesto.periodo (
    periodo_id      INT          PRIMARY KEY,         -- AAAAMM
    vigencia        SMALLINT     NOT NULL CHECK (vigencia BETWEEN 2000 AND 2100),
    mes             SMALLINT     NOT NULL CHECK (mes BETWEEN 1 AND 12),
    UNIQUE (vigencia, mes)
);

CREATE TABLE presupuesto.plan_desarrollo (
    pdd_cod         CHAR(2)      PRIMARY KEY,         -- 16, 17 (dígitos 6-7 del código de proyecto)
    nombre          VARCHAR(120) NOT NULL,
    anio_inicio     SMALLINT,
    anio_fin        SMALLINT
);

CREATE TABLE presupuesto.programa (
    programa_cod    VARCHAR(25)  PRIMARY KEY,         -- programa de financiación / proyecto de inversión
    nombre          VARCHAR(300) NOT NULL,
    tipo_programa   VARCHAR(30)  NOT NULL CHECK (tipo_programa IN ('Funcionamiento','Proyecto de inversión','No publicado','Transferencias de inversión','Servicio de la deuda','Genérico')),
    pdd_cod         CHAR(2)      REFERENCES presupuesto.plan_desarrollo
);

CREATE TABLE presupuesto.tipo_gasto (
    tipo_gasto_cod  CHAR(3)      PRIMARY KEY,         -- O21 Funcionamiento, O22 Deuda, O23 Inversión
    nombre          VARCHAR(40)  NOT NULL
);

CREATE TABLE presupuesto.concepto_gasto (
    concepto_cod    CHAR(4)      PRIMARY KEY,         -- O211 Gastos de personal, O232 Adquisición de bienes y servicios...
    nombre          VARCHAR(80)  NOT NULL,
    tipo_gasto_cod  CHAR(3)      NOT NULL REFERENCES presupuesto.tipo_gasto
);

CREATE TABLE presupuesto.rubro (
    rubro_cod       VARCHAR(25)  PRIMARY KEY,         -- hoja del catálogo CCPET
    descripcion     VARCHAR(300) NOT NULL,
    concepto_cod    CHAR(4)      NOT NULL REFERENCES presupuesto.concepto_gasto
);

-- Hecho: compromiso mensual (el CSV fuente publica el ACUMULADO; valor_mes = acumulado_m - acumulado_m-1)
CREATE TABLE presupuesto.compromiso_mensual (
    linea_id        INT          NOT NULL,            -- identificador de linea de origen por vigencia
    unidad_cod      VARCHAR(10)  NOT NULL REFERENCES presupuesto.unidad_ejecutora,
    programa_cod    VARCHAR(25)  NOT NULL REFERENCES presupuesto.programa,
    rubro_cod       VARCHAR(25)  NOT NULL REFERENCES presupuesto.rubro,
    periodo_id      INT          NOT NULL REFERENCES presupuesto.periodo,
    valor_acumulado NUMERIC(18,2) NOT NULL CHECK (valor_acumulado >= 0),
    valor_mes       NUMERIC(18,2) NOT NULL,           -- negativo = liberación de compromisos
    PRIMARY KEY (periodo_id, linea_id)            -- linea_id debe ser unica por vigencia
);

CREATE INDEX ix_comp_periodo ON presupuesto.compromiso_mensual (periodo_id);
CREATE INDEX ix_comp_rubro   ON presupuesto.compromiso_mensual (rubro_cod);

-- ---------------------------------------------------------------------
-- 2. CAPA ANALÍTICA (modelo estrella que se carga en Power BI)
-- ---------------------------------------------------------------------
CREATE TABLE dw.dim_entidad (
    entidad_cod  CHAR(4) PRIMARY KEY, entidad VARCHAR(200), sigla VARCHAR(20), tipo_entidad VARCHAR(60)
);
CREATE TABLE dw.dim_rubro (
    rubro_sk INT PRIMARY KEY, rubro_cod VARCHAR(25) UNIQUE, rubro VARCHAR(300),
    nivel1_cod CHAR(3), tipo_gasto VARCHAR(40), nivel2_cod CHAR(4), concepto_gasto VARCHAR(80)
);
CREATE TABLE dw.dim_programa (
    programa_sk INT PRIMARY KEY, programa_cod VARCHAR(25) UNIQUE, programa VARCHAR(300),
    tipo_programa VARCHAR(30), pdd_cod CHAR(2), plan_desarrollo VARCHAR(120), num_proyecto VARCHAR(6), nombre_corto VARCHAR(300)
);
CREATE TABLE dw.dim_calendario (
    fecha DATE PRIMARY KEY, vigencia SMALLINT, mes SMALLINT, nombre_mes VARCHAR(12), trimestre CHAR(2), semestre CHAR(2)
);
-- Grano: vigencia × unidad ejecutora × programa × rubro × mes
CREATE TABLE dw.fact_compromiso (
    vigencia              SMALLINT,
    mes                   SMALLINT,
    fecha                 DATE        REFERENCES dw.dim_calendario,
    entidad_cod           CHAR(4)     REFERENCES dw.dim_entidad,
    unidad_ejecutora      VARCHAR(10),                 -- dimensión degenerada
    programa_sk           INT         REFERENCES dw.dim_programa,
    rubro_sk              INT         REFERENCES dw.dim_rubro,
    linea_id              INT,                         -- fila de origen en el CSV
    compromiso_acumulado  NUMERIC(18,2),
    compromiso_mes        NUMERIC(18,2)
);
CREATE INDEX ix_fact_fecha ON dw.fact_compromiso (fecha);

-- Vista de ejemplo: composición anual del gasto comprometido
CREATE VIEW dw.v_compromiso_anual AS
SELECT f.vigencia, r.tipo_gasto, e.sigla,
       SUM(f.compromiso_mes) / 1e9 AS compromiso_miles_millones
FROM dw.fact_compromiso f
JOIN dw.dim_rubro   r USING (rubro_sk)
JOIN dw.dim_entidad e USING (entidad_cod)
GROUP BY f.vigencia, r.tipo_gasto, e.sigla;
