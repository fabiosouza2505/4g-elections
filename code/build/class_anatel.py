# ============================================
# MÓDULOS
# ============================================
import gc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================
# CONFIGURAÇÕES
# ============================================

ARQUIVO_ESTACOES    = 'Estacoes_SMP.csv'
ARQUIVO_DEPARA      = 'depara-ibge-tse.csv'
ARQUIVO_ERB_XLSX    = 'quantitativo_ERB.xlsx'
ARQUIVO_BANDA_LARGA = 'Densidade_Banda_Larga_Fixa.csv'
OUTPUT_CONSOLIDADO  = 'municipios_anatel_consolidado.csv'

ELEICOES_3G = [2006, 2010, 2014, 2018, 2022]
ELEICOES_4G = [2014, 2018, 2022]

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def ibge_to_str(series):
    """IBGE → string de 7 dígitos. Trata int64, float64 e strings com '.0' residual."""
    return (series.astype(str)
            .str.strip()
            .str.replace(r'\.0+$', '', regex=True)   # remove '1100106.0' → '1100106'
            .str.zfill(7))

def parse_br_number(series):
    """Converte números em formato brasileiro (ponto = milhar, vírgula = decimal) para float.

    Exemplos:
        '1.329,847'     → 1329.847
        '64.175.164'    → 64175164.0
        '0,720103884'   → 0.720103884
        '0.720103884'   → 0.720103884   (ponto decimal sem milhar → preservado)
    """
    s = series.astype(str).str.strip()
    # Remove ponto de milhar: ponto seguido de exatamente 3 dígitos não seguidos de dígito
    s = s.str.replace(r'\.(?=\d{3}(?!\d))', '', regex=True)
    # Converte vírgula decimal para ponto
    s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0)

# ============================================
# 1. TABELA DE-PARA IBGE ↔ TSE
# ============================================

print("=== 1. TABELA DE-PARA IBGE-TSE ===")

depara = pd.read_csv(
    ARQUIVO_DEPARA,
    sep=';',
    encoding='latin1',
    dtype={'CD_MUNICIPIO_TSE': str, 'CD_MUNICIPIO_IBGE': str}
)

depara = depara.rename(columns={
    'CD_MUNICIPIO_TSE':  'codigo_tse',
    'CD_MUNICIPIO_IBGE': 'codigo_ibge',
    'NM_MUNICIPIO_TSE':  'municipio_tse',
    'SG_UF':             'uf',
    'NM_UF':             'nome_uf',
})

depara['codigo_tse']  = depara['codigo_tse'].astype(str).str.strip().str.zfill(5)
depara['codigo_ibge'] = ibge_to_str(depara['codigo_ibge'])
depara = depara.drop_duplicates(subset=['codigo_ibge'])

depara_merge = depara[['codigo_tse', 'codigo_ibge', 'municipio_tse', 'uf', 'nome_uf']].copy()

print(f"   Correspondências: {len(depara_merge):,}")
print(f"   Exemplo codigo_ibge: {depara_merge['codigo_ibge'].iloc[0]!r} (tipo: {depara_merge['codigo_ibge'].dtype})")

# ============================================
# 2. ESTAÇÕES SMP — CARGA ÚNICA
# ============================================

print("\n=== 2. CARREGANDO ESTAÇÕES SMP (única vez) ===")

anatel = pd.read_csv(ARQUIVO_ESTACOES, encoding='utf-8', sep=';', low_memory=False)
anatel['data_lic'] = pd.to_datetime(anatel['AnoMesLic'], format='%Y-%m')

print(f"   Total de registros: {len(anatel):,}")
print(f"   Municípios únicos: {anatel['Código IBGE'].nunique():,}")
print(f"   Tipo Código IBGE: {anatel['Código IBGE'].dtype}")

# ============================================
# 3. PROCESSAR 3G
# ============================================

print("\n=== 3. PROCESSANDO 3G (WCDMA, faixas 850/2100 MHz) ===")

anatel_3g = anatel[
    (anatel['Geração'] == '3G') &
    (anatel['Tecnologia'] == 'WCDMA') &
    (anatel['Faixa Estação'].isin([850, 2100])) &
    (anatel['data_lic'] <= '2022-12-31')
].copy()

print(f"   Estações 3G: {len(anatel_3g):,}")

mun_3g = (
    anatel_3g
    .groupby('Código IBGE')
    .agg(
        primeira_estacao_3g=('data_lic', 'min'),
        n_estacoes_3g=('Código IBGE', 'count'),
    )
    .reset_index()
    .rename(columns={'Código IBGE': 'codigo_ibge'})
)

# FIX: Código IBGE pode ser float64 ('1100106.0') após groupby — converter corretamente
mun_3g['codigo_ibge']     = ibge_to_str(mun_3g['codigo_ibge'])
mun_3g['ano_primeira_3g'] = mun_3g['primeira_estacao_3g'].dt.year

for ano in ELEICOES_3G:
    data_el = pd.Timestamp(f'{ano}-10-01')
    mun_3g[f'tem_3g_{ano}'] = (mun_3g['primeira_estacao_3g'] < data_el).astype(int)
    mun_3g[f'anos_3g_{ano}'] = np.where(
        mun_3g[f'tem_3g_{ano}'] == 1,
        (data_el - mun_3g['primeira_estacao_3g']).dt.days / 365.25,
        0.0
    )

print(f"   Municípios com 3G: {len(mun_3g):,}")
print(f"   Exemplo codigo_ibge: {mun_3g['codigo_ibge'].iloc[0]!r}")

# Pré-computar agregados para visualização (antes de liberar memória)
mun_por_ano_3g = mun_3g['ano_primeira_3g'].value_counts().sort_index()
anatel_3g['ano'] = anatel_3g['data_lic'].dt.year
faixa_ano_3g = (anatel_3g
                .groupby(['ano', 'Faixa Estação'])
                .size()
                .unstack(fill_value=0))

del anatel_3g
gc.collect()

# ============================================
# 4. PROCESSAR 4G
# ============================================

print("\n=== 4. PROCESSANDO 4G (LTE, faixas 700/2500 MHz) ===")

anatel_4g = anatel[
    (anatel['Geração'] == '4G') &
    (anatel['Tecnologia'] == 'LTE') &
    (anatel['Faixa Estação'].isin([700, 2500])) &
    (
        ((anatel['Faixa Estação'] == 2500) & (anatel['data_lic'] >= '2012-01-01')) |
        ((anatel['Faixa Estação'] == 700)  & (anatel['data_lic'] >= '2015-01-01'))
    ) &
    (anatel['data_lic'] <= '2022-12-31')
].copy()

print(f"   Estações 4G: {len(anatel_4g):,}")

mun_4g = (
    anatel_4g
    .groupby('Código IBGE')
    .agg(
        primeira_estacao_4g=('data_lic', 'min'),
        n_estacoes_4g=('Código IBGE', 'count'),
    )
    .reset_index()
    .rename(columns={'Código IBGE': 'codigo_ibge'})
)

# FIX: mesma correção de formato de código IBGE
mun_4g['codigo_ibge']     = ibge_to_str(mun_4g['codigo_ibge'])
mun_4g['ano_primeira_4g'] = mun_4g['primeira_estacao_4g'].dt.year

for ano in ELEICOES_4G:
    data_el = pd.Timestamp(f'{ano}-10-01')
    mun_4g[f'tem_4g_{ano}'] = (mun_4g['primeira_estacao_4g'] < data_el).astype(int)
    mun_4g[f'anos_4g_{ano}'] = np.where(
        mun_4g[f'tem_4g_{ano}'] == 1,
        (data_el - mun_4g['primeira_estacao_4g']).dt.days / 365.25,
        0.0
    )

print(f"   Municípios com 4G: {len(mun_4g):,}")

# Pré-computar agregados para visualização (antes de liberar memória)
mun_por_ano_4g = mun_4g['ano_primeira_4g'].value_counts().sort_index()
anatel_4g['ano'] = anatel_4g['data_lic'].dt.year
faixa_ano_4g = (anatel_4g
                .groupby(['ano', 'Faixa Estação'])
                .size()
                .unstack(fill_value=0))

del anatel_4g, anatel
gc.collect()

# ============================================
# 5. INTENSIDADE 4G (ERBs por habitante/km²)
# ============================================

print("\n=== 5. INTENSIDADE 4G (quantitativo_ERB.xlsx) ===")

df_erb = pd.read_excel(ARQUIVO_ERB_XLSX, sheet_name=0, engine='openpyxl')
df_erb.columns = df_erb.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '')

col_ibge = next((c for c in df_erb.columns if 'CÓDIGO' in c.upper() and 'IBGE' in c.upper()), None)
if col_ibge is None:
    raise ValueError("Coluna CÓDIGO IBGE não encontrada em quantitativo_ERB.xlsx")

# FIX: mesmo tratamento de código IBGE
df_erb['codigo_ibge'] = ibge_to_str(df_erb[col_ibge])

df_erb.rename(columns={
    'POPULAÇÃO':                                    'populacao',
    'ÁREA DE ALTA DENSIDADE DE EDIFICAÇÕES':        'area_alta_dens',
    'ÁREA DE BAIXA DENSIDADE DE EDIFICAÇÕES':       'area_baixa_dens',
    'Quantidade de ERBs de cobertura - 700 MHz':    'erbs_700mhz',
    'Quantidade de ERBs de cobertura - 2,5 GHz':   'erbs_2500mhz',
}, inplace=True)

# FIX: colunas de área/população do xlsx podem ser strings com formatação brasileira
# (ex: '64.175.164' = 64.175.164 em m²). parse_br_number trata corretamente.
for col in ['populacao', 'area_alta_dens', 'area_baixa_dens', 'erbs_700mhz', 'erbs_2500mhz']:
    if col in df_erb.columns:
        if df_erb[col].dtype == object:
            df_erb[col] = parse_br_number(df_erb[col])
        else:
            df_erb[col] = pd.to_numeric(df_erb[col], errors='coerce').fillna(0)

df_erb['total_erbs_4g']    = df_erb['erbs_700mhz'] + df_erb['erbs_2500mhz']
df_erb['area_total']       = df_erb['area_alta_dens'] + df_erb['area_baixa_dens']
df_erb['erbs_per_1000hab'] = np.where(df_erb['populacao'] > 0,
                                       df_erb['total_erbs_4g'] / df_erb['populacao'] * 1000, 0)
df_erb['erbs_per_area']    = np.where(df_erb['area_total'] > 0,
                                       df_erb['total_erbs_4g'] / df_erb['area_total'], 0)

max_intens = df_erb['erbs_per_1000hab'].max()
df_erb['intensidade_4g_norm'] = np.where(max_intens > 0, df_erb['erbs_per_1000hab'] / max_intens, 0)

mediana_intens = df_erb.loc[df_erb['total_erbs_4g'] > 0, 'erbs_per_1000hab'].median()
df_erb['alta_intensidade_4g'] = (df_erb['erbs_per_1000hab'] > mediana_intens).astype(int)

intensidade = df_erb[[
    'codigo_ibge', 'total_erbs_4g', 'erbs_700mhz', 'erbs_2500mhz',
    'erbs_per_1000hab', 'erbs_per_area', 'intensidade_4g_norm', 'alta_intensidade_4g',
    'populacao', 'area_total'
]].copy()

print(f"   Municípios no arquivo ERB: {len(intensidade):,}")
print(f"   Municípios com 4G (ERB > 0): {(intensidade['total_erbs_4g'] > 0).sum():,}")
print(f"   erbs_per_1000hab — mediana: {mediana_intens:.3f}")

# ============================================
# 6. BANDA LARGA FIXA
# ============================================

print("\n=== 6. BANDA LARGA FIXA ===")

# FIX: ler tudo como string para tratar formatação brasileira manualmente.
# utf-8-sig remove automaticamente o BOM (corrige o bug ï»¿ano do notebook original).
df_bl = pd.read_csv(
    ARQUIVO_BANDA_LARGA,
    sep=';',
    encoding='utf-8-sig',
    dtype=str,
    low_memory=False
)

# Normalizar nomes: NFKD remove acentos de forma robusta
df_bl.columns = (
    df_bl.columns.str.strip()
    .str.lower()
    .str.normalize('NFKD')
    .str.encode('ascii', errors='ignore')
    .str.decode('ascii')
    .str.replace(' ', '_')
)

# FIX: converter colunas numéricas manualmente (evita ambiguidade decimal=',')
df_bl['ano']       = pd.to_numeric(df_bl['ano'], errors='coerce')
df_bl['mes']       = pd.to_numeric(df_bl['mes'], errors='coerce')
df_bl['densidade'] = parse_br_number(df_bl['densidade'])
df_bl['codigo_ibge'] = df_bl['codigo_ibge'].str.strip().str.zfill(7)

df_bl = df_bl[df_bl['nivel_geografico_densidade'] == 'Municipio'].copy()

# Dezembro de cada ano eleitoral; 2021 como proxy de 2022 (último disponível)
anos_bl = {2010: 12, 2014: 12, 2018: 12, 2021: 12}
bl_wide = None

for ano, mes in anos_bl.items():
    df_ano = (
        df_bl[(df_bl['ano'] == ano) & (df_bl['mes'] == mes)]
        [['codigo_ibge', 'densidade']]
        .rename(columns={'densidade': f'bl_densidade_{ano}'})
    )
    bl_wide = df_ano if bl_wide is None else bl_wide.merge(df_ano, on='codigo_ibge', how='outer')

bl_wide['bl_densidade_2022'] = bl_wide['bl_densidade_2021']

print(f"   Municípios com banda larga: {len(bl_wide):,}")
print(f"   bl_densidade_2010 — mediana: {bl_wide['bl_densidade_2010'].median():.3f}")

del df_bl
gc.collect()

# ============================================
# 7. CONSOLIDAR
# ============================================

print("\n=== 7. CONSOLIDANDO ===")

# Diagnóstico de compatibilidade de chaves antes do merge
print(f"   depara  codigo_ibge exemplo: {depara_merge['codigo_ibge'].iloc[0]!r}")
print(f"   mun_3g  codigo_ibge exemplo: {mun_3g['codigo_ibge'].iloc[0]!r}")
print(f"   mun_4g  codigo_ibge exemplo: {mun_4g['codigo_ibge'].iloc[0]!r}")
print(f"   intens  codigo_ibge exemplo: {intensidade['codigo_ibge'].iloc[0]!r}")
print(f"   bl      codigo_ibge exemplo: {bl_wide['codigo_ibge'].iloc[0]!r}")

# Base: universo de municípios com código TSE
df = depara_merge.copy()

df = df.merge(mun_3g,      on='codigo_ibge', how='left')
df = df.merge(mun_4g,      on='codigo_ibge', how='left')
df = df.merge(intensidade, on='codigo_ibge', how='left')
df = df.merge(bl_wide,     on='codigo_ibge', how='left')

# Municípios sem 3G/4G: dummies = 0, doses = 0
for ano in ELEICOES_3G:
    df[f'tem_3g_{ano}']  = df[f'tem_3g_{ano}'].fillna(0).astype(int)
    df[f'anos_3g_{ano}'] = df[f'anos_3g_{ano}'].fillna(0.0)

for ano in ELEICOES_4G:
    df[f'tem_4g_{ano}']  = df[f'tem_4g_{ano}'].fillna(0).astype(int)
    df[f'anos_4g_{ano}'] = df[f'anos_4g_{ano}'].fillna(0.0)

# Municípios sem dados ERB: intensidade = 0
for col in ['total_erbs_4g', 'erbs_700mhz', 'erbs_2500mhz',
            'erbs_per_1000hab', 'erbs_per_area', 'intensidade_4g_norm', 'alta_intensidade_4g']:
    df[col] = df[col].fillna(0)

print(f"   Municípios no consolidado: {len(df):,}")

# ============================================
# 8. SALVAR E VALIDAR
# ============================================

print("\n=== 8. SALVANDO E VALIDANDO ===")

# FIX: sep=',' explícito para garantir arquivo CSV padrão (separador anterior era ';')
df.to_csv(OUTPUT_CONSOLIDADO, index=False, encoding='utf-8-sig', sep=',')

print(f"\n✅ Arquivo salvo: {OUTPUT_CONSOLIDADO}")
print(f"   Linhas: {len(df):,}")
print(f"   Colunas: {len(df.columns)}")

print("\n=== COBERTURA DE VARIÁVEIS-CHAVE ===")
vars_check = {
    'Com 3G (tem_3g_2022=1)':     (df['tem_3g_2022'] == 1).sum(),
    'Com 4G (tem_4g_2022=1)':     (df['tem_4g_2022'] == 1).sum(),
    'Com intensidade ERB (>0)':    (df['total_erbs_4g'] > 0).sum(),
    'Com banda larga 2010':        df['bl_densidade_2010'].notna().sum(),
    'Com banda larga 2022':        df['bl_densidade_2022'].notna().sum(),
}
for label, n in vars_check.items():
    pct = n / len(df) * 100
    print(f"   {label}: {n:,} ({pct:.1f}%)")

print("\n=== TRATAMENTO 3G POR ELEIÇÃO ===")
for ano in ELEICOES_3G:
    n = df[f'tem_3g_{ano}'].sum()
    print(f"   tem_3g_{ano}: {n:,} ({n/len(df)*100:.1f}%)")

print("\n=== TRATAMENTO 4G POR ELEIÇÃO ===")
for ano in ELEICOES_4G:
    n = df[f'tem_4g_{ano}'].sum()
    print(f"   tem_4g_{ano}: {n:,} ({n/len(df)*100:.1f}%)")

print("\n=== ESTATÍSTICAS DE INTENSIDADE ===")
for col in ['erbs_per_1000hab', 'erbs_per_area', 'bl_densidade_2010', 'bl_densidade_2022']:
    s = df[col].dropna()
    print(f"   {col}: min={s.min():.3f}  mediana={s.median():.3f}  max={s.max():.3f}  dtype={df[col].dtype}")

# ============================================
# 9. Visualizações 3G
# ============================================

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Subplot 1: Histograma temporal
ax1 = fig.add_subplot(gs[0, :])
mun_3g['primeira_estacao_3g'].hist(bins=50, ax=ax1, color='steelblue', edgecolor='white', alpha=0.8)
y_max_3g = ax1.get_ylim()[1]
for ano, label in [(2014, '2014'), (2016, '2016'), (2018, '2018'), (2022, '2022')]:
    ax1.axvline(pd.Timestamp(f'{ano}-10-01'), color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.text(pd.Timestamp(f'{ano}-10-01'), y_max_3g * 0.95, label,
             ha='center', va='top', fontsize=10, fontweight='bold', color='red')
ax1.set_title('Rollout do 3G no Brasil (Faixas 850 e 2100 MHz)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Data', fontsize=11)
ax1.set_ylabel('Número de Municípios', fontsize=11)
ax1.grid(axis='y', alpha=0.3)

# Subplot 2: Acumulado
ax2 = fig.add_subplot(gs[1, :])
mun_3g_sorted = mun_3g.sort_values('primeira_estacao_3g').copy()
mun_3g_sorted['acumulado']    = range(1, len(mun_3g_sorted) + 1)
mun_3g_sorted['pct_acumulado'] = mun_3g_sorted['acumulado'] / len(mun_3g_sorted) * 100

ax2.plot(mun_3g_sorted['primeira_estacao_3g'], mun_3g_sorted['acumulado'],
         linewidth=3, color='steelblue', label='Municípios com 3G')
ax2_twin = ax2.twinx()
ax2_twin.plot(mun_3g_sorted['primeira_estacao_3g'], mun_3g_sorted['pct_acumulado'],
              linewidth=2, color='orange', linestyle='--', alpha=0.7, label='% do Total')
for ano in [2014, 2016, 2018, 2022]:
    ax2.axvline(pd.Timestamp(f'{ano}-10-01'), color='red', linestyle='--', linewidth=1.5, alpha=0.5)
ax2.set_title('Expansão Acumulada do 3G', fontsize=14, fontweight='bold')
ax2.set_xlabel('Data', fontsize=11)
ax2.set_ylabel('Municípios com 3G (acumulado)', fontsize=11, color='steelblue')
ax2_twin.set_ylabel('Percentual do Total (%)', fontsize=11, color='orange')
ax2.tick_params(axis='y', labelcolor='steelblue')
ax2_twin.tick_params(axis='y', labelcolor='orange')
ax2.grid(alpha=0.3)
ax2.legend(loc='upper left')
ax2_twin.legend(loc='lower right')

# Subplot 3: Municípios por ano (primeira estação)
ax3 = fig.add_subplot(gs[2, 0])
mun_por_ano_3g.plot(kind='bar', ax=ax3, color='steelblue', width=0.75)
ax3.set_title('Municípios por Ano (Primeira Estação 3G)', fontsize=12, fontweight='bold')
ax3.set_xlabel('Ano', fontsize=10)
ax3.set_ylabel('Número de Municípios', fontsize=10)
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45)
for i, v in enumerate(mun_por_ano_3g.values):
    if v > 0:
        ax3.text(i, v + mun_por_ano_3g.max() * 0.02, str(v), ha='center', va='bottom', fontsize=8)
ax3.grid(axis='y', alpha=0.3)

# Subplot 4: Estações por faixa ao longo do tempo
ax4 = fig.add_subplot(gs[2, 1])
faixa_ano_3g.plot(kind='bar', stacked=True, ax=ax4, color=['#e74c3c', '#3498db'])
ax4.set_title('Estações 3G por Faixa e Ano', fontsize=12, fontweight='bold')
ax4.set_xlabel('Ano', fontsize=10)
ax4.set_ylabel('Número de Estações', fontsize=10)
ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45)
ax4.legend(title='Faixa (MHz)', labels=[str(c) for c in faixa_ano_3g.columns])
ax4.grid(axis='y', alpha=0.3)

plt.savefig('analise_3g_limpa_final.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico salvo: analise_3g_limpa_final.png")
plt.show()

# ============================================
# 10. Visualizações 4G
# ============================================

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Subplot 1: Histograma temporal
ax1 = fig.add_subplot(gs[0, :])
mun_4g['primeira_estacao_4g'].hist(bins=50, ax=ax1, color='steelblue', edgecolor='white', alpha=0.8)
y_max_4g = ax1.get_ylim()[1]
for ano, label in [(2014, '2014'), (2016, '2016'), (2018, '2018'), (2022, '2022')]:
    ax1.axvline(pd.Timestamp(f'{ano}-10-01'), color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.text(pd.Timestamp(f'{ano}-10-01'), y_max_4g * 0.95, label,
             ha='center', va='top', fontsize=10, fontweight='bold', color='red')
ax1.set_title('Rollout do 4G no Brasil (Faixas 700 e 2500 MHz)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Data', fontsize=11)
ax1.set_ylabel('Número de Municípios', fontsize=11)
ax1.grid(axis='y', alpha=0.3)

# Subplot 2: Acumulado
ax2 = fig.add_subplot(gs[1, :])
mun_4g_sorted = mun_4g.sort_values('primeira_estacao_4g').copy()
mun_4g_sorted['acumulado']    = range(1, len(mun_4g_sorted) + 1)
mun_4g_sorted['pct_acumulado'] = mun_4g_sorted['acumulado'] / len(mun_4g_sorted) * 100

ax2.plot(mun_4g_sorted['primeira_estacao_4g'], mun_4g_sorted['acumulado'],
         linewidth=3, color='steelblue', label='Municípios com 4G')
ax2_twin = ax2.twinx()
ax2_twin.plot(mun_4g_sorted['primeira_estacao_4g'], mun_4g_sorted['pct_acumulado'],
              linewidth=2, color='orange', linestyle='--', alpha=0.7, label='% do Total')
for ano in [2014, 2016, 2018, 2022]:
    ax2.axvline(pd.Timestamp(f'{ano}-10-01'), color='red', linestyle='--', linewidth=1.5, alpha=0.5)
ax2.set_title('Expansão Acumulada do 4G', fontsize=14, fontweight='bold')
ax2.set_xlabel('Data', fontsize=11)
ax2.set_ylabel('Municípios com 4G (acumulado)', fontsize=11, color='steelblue')
ax2_twin.set_ylabel('Percentual do Total (%)', fontsize=11, color='orange')
ax2.tick_params(axis='y', labelcolor='steelblue')
ax2_twin.tick_params(axis='y', labelcolor='orange')
ax2.grid(alpha=0.3)
ax2.legend(loc='upper left')
ax2_twin.legend(loc='lower right')

# Subplot 3: Municípios por ano (primeira estação)
ax3 = fig.add_subplot(gs[2, 0])
mun_por_ano_4g.plot(kind='bar', ax=ax3, color='steelblue', width=0.75)
ax3.set_title('Municípios por Ano (Primeira Estação 4G)', fontsize=12, fontweight='bold')
ax3.set_xlabel('Ano', fontsize=10)
ax3.set_ylabel('Número de Municípios', fontsize=10)
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45)
for i, v in enumerate(mun_por_ano_4g.values):
    if v > 0:
        ax3.text(i, v + mun_por_ano_4g.max() * 0.02, str(v), ha='center', va='bottom', fontsize=8)
ax3.grid(axis='y', alpha=0.3)

# Subplot 4: Estações por faixa ao longo do tempo
ax4 = fig.add_subplot(gs[2, 1])
faixa_ano_4g.plot(kind='bar', stacked=True, ax=ax4, color=['#e74c3c', '#3498db'])
ax4.set_title('Estações 4G por Faixa e Ano', fontsize=12, fontweight='bold')
ax4.set_xlabel('Ano', fontsize=10)
ax4.set_ylabel('Número de Estações', fontsize=10)
ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45)
ax4.legend(title='Faixa (MHz)', labels=[str(c) for c in faixa_ano_4g.columns])
ax4.grid(axis='y', alpha=0.3)

plt.savefig('analise_4g_limpa_final.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico salvo: analise_4g_limpa_final.png")
plt.show()