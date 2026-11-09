"""
Constrói painel consolidado municipal (anos eleitorais 2006, 2010, 2014, 2018, 2022)

Fontes:
  painel_polarizacao_municipal_2006_2022.csv  → base (codigo_tse × ano)
  municipios_anatel_consolidado.csv           → 3G/4G, ERBs, BL, área (codigo_tse)
  pib_percapita_municipal.csv                 → PIB e população anual (cod_municipio × ano)
  controles_educacao_censo2010.csv            → escolaridade (CO_MUNICIPIO, Censo 2010)

Saída: painel_consolidado_2006_2022.csv
"""

import numpy as np
import pandas as pd

POL_FILE    = "painel_polarizacao_municipal_2006_2022.csv"
ANATEL_FILE = "municipios_anatel_consolidado.csv"
PIB_FILE    = "pib_percapita_municipal.csv"
EDU_FILE    = "controles_educacao_censo2010.csv"
OUTPUT_FILE = "painel_consolidado_2006_2022.csv"

print("\n" + "=" * 70)
print("BUILD PAINEL CONSOLIDADO 2006–2022")
print("=" * 70 + "\n")

# ─────────────────────────────────────────────────────────────────────
# 1. Carregamento
# ─────────────────────────────────────────────────────────────────────
pol    = pd.read_csv(POL_FILE)
anatel = pd.read_csv(ANATEL_FILE)
pib    = pd.read_csv(PIB_FILE)
edu    = pd.read_csv(EDU_FILE)

print(f"Polarizacao : {len(pol):,} linhas | {pol['ano'].nunique()} anos | {pol['codigo_tse'].nunique():,} municipios")
print(f"Anatel      : {len(anatel):,} municipios")
print(f"PIB         : {len(pib):,} linhas")
print(f"Educacao    : {len(edu):,} municipios\n")

# ─────────────────────────────────────────────────────────────────────
# 2. Normalização de chaves
# ─────────────────────────────────────────────────────────────────────
pol["codigo_tse"]    = pol["codigo_tse"].astype(int)
anatel["codigo_tse"] = anatel["codigo_tse"].astype(int)

# Chave de 6 dígitos IBGE: remove o dígito verificador (÷10) para join com PIB
anatel["cod_municipio"] = (anatel["codigo_ibge"] // 10).astype(int)

pib["ano"]           = pib["ano"].astype(int)
pib["cod_municipio"] = pib["cod_municipio"].astype(int)

# ─────────────────────────────────────────────────────────────────────
# 3. Renomeações no Anatel antes do merge (evita colisão com PIB)
# ─────────────────────────────────────────────────────────────────────
anatel = anatel.rename(columns={
    "populacao":     "populacao_anatel",   # PIB trará pop anual
    "n_estacoes_3g": "n_estacoes_3g_total",
    "erbs_per_area": "erbs_per_km2",
    "municipio_tse": "nome_municipio",
    "anos_4g_2014":  "anos_com_4g_2014",
    "anos_4g_2018":  "anos_com_4g_2018",
    "anos_4g_2022":  "anos_com_4g_2022",
    "anos_3g_2014":  "anos_com_3g_2014",
    "anos_3g_2018":  "anos_com_3g_2018",
    "anos_3g_2022":  "anos_com_3g_2022",
})

# ─────────────────────────────────────────────────────────────────────
# 4. Merge base: polarizacao × anatel  (many-to-1 via codigo_tse)
# ─────────────────────────────────────────────────────────────────────
df = pol.merge(anatel, on="codigo_tse", how="left")
n_sem_anatel = df["codigo_ibge"].isna().sum()
print(f"Merge pol x anatel: {len(df):,} linhas | sem match Anatel: {n_sem_anatel:,}")

# ─────────────────────────────────────────────────────────────────────
# 5. Variável estática: tem_4g_2010
#    (4G no Brasil chegou em 2013; praticamente zero em 2010)
# ─────────────────────────────────────────────────────────────────────
df["tem_4g_2010"] = np.where(
    df["ano_primeira_4g"].notna() & (df["ano_primeira_4g"] <= 2010), 1, 0
)

# ─────────────────────────────────────────────────────────────────────
# 6. Variáveis de painel: tem_4g, anos_4g, tem_3g, anos_3g
#    Cada eleição usa o snapshot do ano correspondente no Anatel
# ─────────────────────────────────────────────────────────────────────
def panel_var(df, year_col_map, default=0.0):
    """Seleciona a coluna correta do Anatel para cada ano eleitoral."""
    anos = sorted(year_col_map)
    return np.select(
        [df["ano"] == a for a in anos],
        [df[year_col_map[a]].fillna(default) for a in anos],
        default=default,
    )

df["tem_4g"]  = panel_var(df, {2014: "tem_4g_2014", 2018: "tem_4g_2018", 2022: "tem_4g_2022"}, 0)
df["anos_4g"] = panel_var(df, {2014: "anos_com_4g_2014", 2018: "anos_com_4g_2018", 2022: "anos_com_4g_2022"}, 0.0)
df["tem_3g"]  = panel_var(df, {2006: "tem_3g_2006", 2010: "tem_3g_2010", 2014: "tem_3g_2014",
                                2018: "tem_3g_2018", 2022: "tem_3g_2022"}, 0)
df["anos_3g"] = panel_var(df, {2006: "anos_3g_2006", 2010: "anos_3g_2010", 2014: "anos_com_3g_2014",
                                2018: "anos_com_3g_2018", 2022: "anos_com_3g_2022"}, 0.0)

# ─────────────────────────────────────────────────────────────────────
# 7. Variáveis DiD: cohort e tempo_relativo
#    Cohorts definidos pelos marcos regulatórios do 4G no Brasil:
#      2012 = 1º leilão 4G (Copa 2014), 2014/2018/2022 = eleições gerais
# ─────────────────────────────────────────────────────────────────────
ap4 = df["ano_primeira_4g"]
df["cohort"] = np.select(
    [
        ap4.notna() & (ap4 <= 2012),
        ap4.notna() & (ap4 > 2012) & (ap4 <= 2014),
        ap4.notna() & (ap4 > 2014) & (ap4 <= 2018),
        ap4.notna() & (ap4 > 2018) & (ap4 <= 2022),
    ],
    ["cohort_2010_2012", "cohort_2012_2014", "cohort_2014_2018", "cohort_2018_2022"],
    default="never_treated",
)

df["tempo_relativo"] = np.where(
    df["cohort"] != "never_treated",
    df["ano"] - df["ano_primeira_4g"],
    np.nan,
)

# ─────────────────────────────────────────────────────────────────────
# 8. Outras variáveis derivadas do Anatel
# ─────────────────────────────────────────────────────────────────────
# Frequência da 1ª estação 4G (700 MHz = cobertura rural, 2500 MHz = capacidade)
df["faixa_primeira"] = np.select(
    [
        (df["cohort"] != "never_treated") & (df["erbs_700mhz"].fillna(0) > 0),
        (df["cohort"] != "never_treated") & (df["erbs_2500mhz"].fillna(0) > 0),
    ],
    [700, 2500],
    default=np.nan,
)

# Mês da primeira estação 3G
df["mes_primeira_3g"] = (
    pd.to_datetime(df["primeira_estacao_3g"], errors="coerce").dt.month
)

# Categoria de intensidade 4G — calibrada pela distribuição do painel de referência
# (~6% Baixa, ~70% Média, ~24% Alta entre municípios com 4G; "Sem 4G" para os demais)
_mask_4g = df["intensidade_4g_norm"].notna() & (df["intensidade_4g_norm"] > 0)
p06 = df.loc[_mask_4g, "intensidade_4g_norm"].quantile(0.06)
p76 = df.loc[_mask_4g, "intensidade_4g_norm"].quantile(0.76)
df["categoria_4g"] = np.select(
    [
        ~_mask_4g,
        _mask_4g & (df["intensidade_4g_norm"] <  p06),
        _mask_4g & (df["intensidade_4g_norm"] >= p06) & (df["intensidade_4g_norm"] < p76),
        _mask_4g & (df["intensidade_4g_norm"] >= p76),
    ],
    ["Sem 4G", "Baixa", "Média", "Alta"],
    default="Sem 4G",
)

# BL densidade 2010 winsorizada (1%-99%)
_bl = df["bl_densidade_2010"]
df["bl_densidade_2010_win"] = _bl.clip(lower=_bl.quantile(0.01), upper=_bl.quantile(0.99))

# esteban_ray_corr (placeholder — substitua pela fórmula corrigida se disponível)
df["esteban_ray_corr"] = df["esteban_ray"]

# ─────────────────────────────────────────────────────────────────────
# 9. Merge com PIB per capita  (painel: cod_municipio × ano)
# ─────────────────────────────────────────────────────────────────────
pib_sel = pib[["cod_municipio", "ano", "pib_corrente_mil", "populacao",
               "pib_percapita", "pop_interpolada"]].copy()

df = df.merge(pib_sel, on=["cod_municipio", "ano"], how="left")

df["pib_total"]      = df["pib_corrente_mil"] * 1_000
df["pib_per_capita"] = df["pib_percapita"]
df["log_pib_pc"]     = np.log(df["pib_percapita"])

n_sem_pib = df["pib_percapita"].isna().sum()
print(f"Merge x PIB: {n_sem_pib:,} linhas sem dados de PIB")

# ─────────────────────────────────────────────────────────────────────
# 10. Merge com educação  (CO_MUNICIPIO = codigo_ibge, Censo 2010)
# ─────────────────────────────────────────────────────────────────────
edu_sel = (
    edu[["CO_MUNICIPIO", "prop_medio_mais", "prop_baixa_instrucao"]]
    .rename(columns={"CO_MUNICIPIO": "codigo_ibge"})
)
df = df.merge(edu_sel, on="codigo_ibge", how="left")

n_sem_edu = df["prop_medio_mais"].isna().sum()
print(f"Merge x Educacao: {n_sem_edu:,} linhas sem dados de educacao\n")

# ─────────────────────────────────────────────────────────────────────
# 11. Seleção e ordenação das colunas
#     Ordem espelha painel de referência; variáveis extras do novo painel
#     (2006, wolfson, bl anuais, metadados) ficam ao final
# ─────────────────────────────────────────────────────────────────────
COLUNAS = [
    # — Identificadores —
    "codigo_tse", "ano",
    # — Polarização (Esteban-Ray et al.) —
    "esteban_ray", "herfindahl", "concentracao_bipartidaria", "enp",
    # — 4G estático —
    "tem_4g_2010", "tem_4g_2014", "tem_4g_2018", "tem_4g_2022",
    "anos_com_4g_2014", "anos_com_4g_2018", "anos_com_4g_2022",
    "ano_primeira_4g", "uf", "faixa_primeira",
    # — 4G de painel (varia por ano eleitoral) —
    "tem_4g", "anos_4g",
    # — DiD —
    "cohort", "tempo_relativo",
    # — 3G —
    "primeira_estacao_3g", "ano_primeira_3g", "mes_primeira_3g", "n_estacoes_3g_total",
    "tem_3g_2010", "tem_3g_2014", "tem_3g_2018", "tem_3g_2022",
    "anos_com_3g_2014", "anos_com_3g_2018", "anos_com_3g_2022",
    "tem_3g", "anos_3g",
    # — Infraestrutura 4G —
    "total_erbs_4g", "erbs_700mhz", "erbs_2500mhz",
    "erbs_per_1000hab", "erbs_per_km2",
    "intensidade_4g_norm", "categoria_4g", "alta_intensidade_4g",
    # — Socioeconômico —
    "populacao", "pib_total", "nome_municipio",
    "pib_per_capita", "log_pib_pc",
    # — Educação (Censo 2010, fixo em todos os anos) —
    "prop_medio_mais", "prop_baixa_instrucao",
    # — Banda larga —
    "bl_densidade_2010", "bl_densidade_2010_win",
    # — Outras medidas de polarização —
    "esteban_ray_corr", "dalton", "dist_bipolar", "reynal_querol",
    # — Variáveis extras do painel estendido (2006 + anuais) —
    "tem_3g_2006", "anos_3g_2006",            # 3G em 2006
    "bl_densidade_2014", "bl_densidade_2018", "bl_densidade_2022",  # BL anual
    "wolfson", "wolfson_norm",                 # medidas adicionais de polarização
    "pop_interpolada",                         # flag: pop estimada por interpolação
    # — Chaves de ligação (mantidas para referência cruzada) —
    "cod_municipio", "codigo_ibge",
]

colunas_ok = [c for c in COLUNAS if c in df.columns]
df_out = (
    df[colunas_ok]
    .sort_values(["codigo_tse", "ano"])
    .reset_index(drop=True)
)

# ─────────────────────────────────────────────────────────────────────
# 12. Salvar
# ─────────────────────────────────────────────────────────────────────
df_out.to_csv(OUTPUT_FILE, index=False)

print("=" * 70)
print("CONCLUÍDO")
print("=" * 70)
print(f"Arquivo  : {OUTPUT_FILE}")
print(f"Linhas   : {len(df_out):,}")
print(f"Colunas  : {len(df_out.columns)}")
print(f"Anos     : {sorted(df_out['ano'].unique())}")
print(f"Municípios: {df_out['codigo_tse'].nunique():,}")
print()
print("Cohort (ano=2010):")
print(df_out[df_out["ano"] == 2010]["cohort"].value_counts().to_string())
print()
print("Missings relevantes:")
cols_check = ["log_pib_pc", "prop_medio_mais", "bl_densidade_2010",
              "tem_4g", "tem_3g", "esteban_ray"]
for c in cols_check:
    if c in df_out.columns:
        n = df_out[c].isna().sum()
        print(f"  {c:<25}: {n:,}")
print()
