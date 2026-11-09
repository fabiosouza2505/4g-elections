# ============================================
# MÓDULOS
# ============================================
import gc
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

# ============================================
# Carregar classificações ideológicas
# ============================================

# Carregar classificações ideológicas
with open('ideology_2006.json', 'r', encoding='utf-8') as f:
    ideology_dict_2006 = json.load(f)

with open('ideology_2010.json', 'r', encoding='utf-8') as f:
    ideology_dict_2010 = json.load(f)

with open('ideology_2014.json', 'r', encoding='utf-8') as f:
    ideology_dict_2014 = json.load(f)
    
with open('ideology_2018.json', 'r', encoding='utf-8') as f:
    ideology_dict_2018 = json.load(f)
    
with open('ideology_2022.json', 'r', encoding='utf-8') as f:
    ideology_dict_2022 = json.load(f)


# ============================================
# Definição da função ESTEBAN-RAY (ER)
# ============================================

def calcular_esteban_ray(df_votos_mun, ideology_dict, alpha=1.0):
    """
    Calcula índice de Esteban-Ray de polarização
    
    Parameters:
    -----------
    df_votos_mun : DataFrame
        Votos por partido em um município
        Colunas necessárias: ['sigla_partido', 'votos']
    ideology_dict : dict
        {sigla_partido: ideology_score_01}
    alpha : float
        Parâmetro de identificação (default = 1.0, padrão na literatura)
    
    Returns:
    --------
    float : Índice ER (maior = mais polarizado)
    """
    # Filtrar apenas partidos com classificação ideológica
    df_votos_mun = df_votos_mun[
        df_votos_mun['sigla_partido'].isin(ideology_dict.keys())
    ].copy()
    
    if len(df_votos_mun) == 0:
        return np.nan
    
    # Calcular vote shares
    total_votos = df_votos_mun['votos'].sum()
    
    if total_votos == 0:
        return np.nan
    
    df_votos_mun['vote_share'] = df_votos_mun['votos'] / total_votos
    
    # Adicionar ideologias
    df_votos_mun['ideology'] = df_votos_mun['sigla_partido'].map(ideology_dict)
    
    # Remover partidos sem ideologia (NaN)
    df_votos_mun = df_votos_mun.dropna(subset=['ideology'])
    
    if len(df_votos_mun) == 0:
        return np.nan
    
    # Calcular ER
    er = 0.0
    K = 1.0  # Constante de normalização
    
    for _, row_i in df_votos_mun.iterrows():
        pi_i = row_i['vote_share']
        y_i = row_i['ideology']
        
        for _, row_j in df_votos_mun.iterrows():
            pi_j = row_j['vote_share']
            y_j = row_j['ideology']
            
            identification = pi_i ** (1 + alpha)
            alienation = pi_j
            distance = abs(y_i - y_j)
            
            er += K * identification * alienation * distance
    
    return er

# ============================================
# Índice de Foster-Wolfson (auxiliar)
# ============================================

def _wolfson(s, y):
    """
    Índice de Foster-Wolfson adaptado à escala de ideologia 0-1 (mediana empírica).
    Bipolarização = spread (caudas se afastam da mediana) + bipolaridade (cada
    metade se adensa) — operacionaliza o deslocamento centro->polos do modelo.

    s : array de vote shares (somam 1)
    y : array de posições ideológicas (0-1)

    Retorna (wolfson_raw, wolfson_norm):
      wolfson_raw  = 2*(2T - G)            -> recomendado p/ ideologia
      wolfson_norm = wolfson_raw * (mu/m)  -> Foster-Wolfson canônico (p/ renda;
                                             instável em ideologia, manter só p/ ref.)
    """
    s = np.asarray(s, dtype=float)
    y = np.asarray(y, dtype=float)
    o = np.argsort(y)
    y, s = y[o], s[o]

    if len(y) < 2 or np.allclose(y, y[0]):
        return 0.0, 0.0

    mu = float(np.sum(s * y))
    if mu <= 0:
        return np.nan, np.nan

    # Mediana ponderada
    cw = np.cumsum(s)
    m = y[np.searchsorted(cw, 0.5)]

    # Gini ponderado (diferença média absoluta)
    G = float(np.sum(s[:, None] * s[None, :] * np.abs(y[:, None] - y[None, :])) / (2 * mu))

    # L(0.5): fração da "massa de ideologia" detida pelos 50% inferiores da população
    cum_pop = np.cumsum(s)
    cum_id = np.cumsum(s * y)
    k = np.searchsorted(cum_pop, 0.5)
    pop_before = cum_pop[k - 1] if k > 0 else 0.0
    id_before = cum_id[k - 1] if k > 0 else 0.0
    L_half = (id_before + (0.5 - pop_before) * y[k]) / mu
    T = 0.5 - L_half

    w_raw = 2.0 * (2.0 * T - G)
    w_norm = w_raw * (mu / m) if m > 0 else np.nan
    return float(w_raw), float(w_norm)


# ============================================
# Cálculo das medidas de polarização
# ============================================

def calcular_medidas_polarizacao(df_votos_mun, ideology_dict):
    """
    Calcula múltiplas medidas de polarização
    """
    # Filtrar partidos com classificação
    df_votos_mun = df_votos_mun[
        df_votos_mun['sigla_partido'].isin(ideology_dict.keys())
    ].copy()
    
    if len(df_votos_mun) == 0:
        return {
            'esteban_ray': np.nan,
            'herfindahl': np.nan,
            'concentracao_bipartidaria': np.nan,
            'enp': np.nan,
            'dalton': np.nan,
            'dist_bipolar': np.nan,
            'reynal_querol': np.nan,
            'wolfson': np.nan,
            'wolfson_norm': np.nan
        }
    
    total_votos = df_votos_mun['votos'].sum()
    
    if total_votos == 0:
        return {
            'esteban_ray': np.nan,
            'herfindahl': np.nan,
            'concentracao_bipartidaria': np.nan,
            'enp': np.nan,
            'dalton': np.nan,
            'dist_bipolar': np.nan,
            'reynal_querol': np.nan,
            'wolfson': np.nan,
            'wolfson_norm': np.nan
        }
    
    df_votos_mun['vote_share'] = df_votos_mun['votos'] / total_votos
    df_votos_mun['ideology'] = df_votos_mun['sigla_partido'].map(ideology_dict)
    df_votos_mun = df_votos_mun.dropna(subset=['ideology'])
    
    # 1. Esteban-Ray
    er = calcular_esteban_ray(df_votos_mun, ideology_dict, alpha=1.0)
    
    # 2. Herfindahl
    herfindahl = (df_votos_mun['vote_share'] ** 2).sum()
    
    # 3. Concentração Bipartidária (esquerda + direita)
    esquerda = df_votos_mun[df_votos_mun['ideology'] < 0.33]['vote_share'].sum()
    direita = df_votos_mun[df_votos_mun['ideology'] > 0.67]['vote_share'].sum()
    concentracao_bip = esquerda + direita
    
    # 4. Effective Number of Parties
    enp = 1 / herfindahl if herfindahl > 0 else np.nan

    # ====== Índices adicionais (consistentes com o painel de jun/2026) ======
    s = df_votos_mun['vote_share'].values.astype(float)
    y = df_votos_mun['ideology'].values.astype(float)

    # 5. Índice de Dalton — desvio-padrão ponderado das posições (dispersão)
    mu = float(np.sum(s * y))
    dalton = float(np.sqrt(np.sum(s * (y - mu) ** 2)))

    # 6. Distância bipolar — média_direita − média_esquerda (divisor 0.5) ≈ 2·Δ*
    L = y < 0.5
    R = ~L
    if s[L].sum() > 0 and s[R].sum() > 0:
        dist_bipolar = float(np.sum(s[R] * y[R]) / s[R].sum()
                             - np.sum(s[L] * y[L]) / s[L].sum())
    else:
        dist_bipolar = np.nan

    # 7. Reynal-Querol — bipolarização position-free (não usa as posições)
    reynal_querol = float(1 - np.sum(((0.5 - s) / 0.5) ** 2 * s))

    # 8. Wolfson — bipolarização (spread + bipolaridade), mediana empírica
    wolfson, wolfson_norm = _wolfson(s, y)

    return {
        'esteban_ray': er,
        'herfindahl': herfindahl,
        'concentracao_bipartidaria': concentracao_bip,
        'enp': enp,
        'dalton': dalton,
        'dist_bipolar': dist_bipolar,
        'reynal_querol': reynal_querol,
        'wolfson': wolfson,
        'wolfson_norm': wolfson_norm
    }

# ============================================
# Função processar resultados TSE
# ============================================

def processar_resultados_tse(arquivo_csv, ano, cargo='PRESIDENTE'):
    """
    Processa resultados do TSE para calcular polarização
    
    Parameters:
    -----------
    arquivo_csv : str
        Caminho para arquivo de resultados TSE
    ano : int
        Ano da eleição (ex: 2006, 2010, 2014, 2018, 2022)
    cargo : str
        'PRESIDENTE' ou 'GOVERNADOR'
    """
    print(f"\n=== PROCESSANDO: {cargo} {ano} ===")
    
    # Carregar
    df = pd.read_csv(arquivo_csv, encoding='latin1', sep=';', dtype={'CD_MUNICIPIO': str})
    
    # Filtrar cargo
    if cargo == 'PRESIDENTE':
        df = df[df['CD_CARGO'] == 1]
    elif cargo == 'GOVERNADOR':
        df = df[df['CD_CARGO'] == 3]
    
    # Turno 1 apenas
    df = df[df['NR_TURNO'] == 1]
    
    # Agregar por município e partido
    df_agregado = df.groupby(['CD_MUNICIPIO', 'SG_PARTIDO'])['QT_VOTOS_NOMINAIS'].sum().reset_index()
    df_agregado.columns = ['codigo_tse', 'sigla_partido', 'votos']
    
    # Padronizar siglas
    df_agregado['sigla_partido'] = df_agregado['sigla_partido'].str.upper().str.strip()
    
    print(f"   Total de municípios: {df_agregado['codigo_tse'].nunique():,}")
    print(f"   Total de votos: {df_agregado['votos'].sum():,}")
    
    return df_agregado

# ============================================
# Função CALCULAR POLARIZAÇÃO PARA TODOS MUNICÍPIOS
# ============================================

def calcular_polarizacao_todos_municipios(df_resultados, ideology_dict, ano):
    """
    Calcula medidas de polarização para todos os municípios
    """
    print(f"\n=== CALCULANDO POLARIZAÇÃO: {ano} ===")
    
    resultados = []
    municipios = df_resultados['codigo_tse'].unique()
    
    total = len(municipios)
    for i, cod_tse in enumerate(municipios):
        if (i + 1) % 500 == 0:
            print(f"   Processados: {i+1:,} / {total:,} ({(i+1)/total*100:.1f}%)")
        
        df_mun = df_resultados[df_resultados['codigo_tse'] == cod_tse]
        
        medidas = calcular_medidas_polarizacao(df_mun, ideology_dict)
        
        resultados.append({
            'codigo_tse': cod_tse,
            'ano': ano,
            **medidas
        })
    
    df_polarizacao = pd.DataFrame(resultados)
    
    print(f"\n✅ Polarização calculada para {len(df_polarizacao):,} municípios")
    print("\n=== ESTATÍSTICAS DESCRITIVAS ===")
    print(df_polarizacao[['esteban_ray', 'dalton', 'wolfson', 'reynal_querol', 'dist_bipolar']].describe())
    
    return df_polarizacao

# ============================================
# Função processar_resultados_tse_chunks
# ============================================

def processar_resultados_tse_chunks(arquivo_csv, ano, cargo='PRESIDENTE', chunksize=500000):
    """
    Processa arquivo TSE grande em chunks para economizar memória
    """
    print(f"\n{'='*70}")
    print(f"PROCESSANDO TSE {ano} (EM CHUNKS)")
    print(f"{'='*70}")
    
    # Definir colunas dtype para economizar memória
    dtype_dict = {
        'CD_MUNICIPIO': str,
        'NR_TURNO': 'int8',
        'CD_CARGO': 'int8'
    }
    
    # Identificar colunas necessárias
    colunas_necessarias = [
        'CD_MUNICIPIO', 'SG_PARTIDO', 'QT_VOTOS_NOMINAIS',
        'NR_TURNO', 'CD_CARGO'
    ]
    
    print(f"\nProcessando arquivo em chunks de {chunksize:,} linhas...")
    
    # Lista para armazenar chunks processados
    chunks_processados = []
    total_linhas = 0
    
    # Processar em chunks
    try:
        for i, chunk in enumerate(pd.read_csv(
            arquivo_csv,
            encoding='latin1',
            sep=';',
            dtype=dtype_dict,
            usecols=colunas_necessarias,
            chunksize=chunksize,
            low_memory=False
        )):
            total_linhas += len(chunk)
            
            # Filtrar cargo (Presidente = 1)
            if cargo == 'PRESIDENTE':
                chunk = chunk[chunk['CD_CARGO'] == 1]
            
            # Filtrar turno 1
            chunk = chunk[chunk['NR_TURNO'] == 1]
            
            # Se chunk vazio após filtros, pular
            if len(chunk) == 0:
                continue
            
            # Agregar por município e partido
            chunk_agregado = chunk.groupby(
                ['CD_MUNICIPIO', 'SG_PARTIDO']
            )['QT_VOTOS_NOMINAIS'].sum().reset_index()
            
            chunks_processados.append(chunk_agregado)
            
            # Limpar memória
            del chunk
            gc.collect()
            
            if (i + 1) % 5 == 0:
                print(f"  Chunk {i+1}: {total_linhas:,} linhas lidas, "
                      f"{len(chunks_processados)} chunks processados")
        
        print(f"\n✅ Leitura completa: {total_linhas:,} linhas")
        print(f"  Chunks processados: {len(chunks_processados)}")
        
    except Exception as e:
        print(f"\n❌ Erro ao processar: {e}")
        return None
    
    # Combinar todos os chunks
    print("\nCombinando chunks...")
    df_final = pd.concat(chunks_processados, ignore_index=True)
    
    # Limpar memória
    del chunks_processados
    gc.collect()
    
    # Agregar novamente (pode haver duplicatas entre chunks)
    print("Agregando votos finais...")
    df_final = df_final.groupby(
        ['CD_MUNICIPIO', 'SG_PARTIDO']
    )['QT_VOTOS_NOMINAIS'].sum().reset_index()
    
    # Renomear colunas
    df_final.columns = ['codigo_tse', 'sigla_partido', 'votos']
    
    # Padronizar
    df_final['codigo_tse'] = df_final['codigo_tse'].astype(str).str.zfill(5)
    df_final['sigla_partido'] = df_final['sigla_partido'].str.upper().str.strip()
    
    # Remover partidos com votos zero
    df_final = df_final[df_final['votos'] > 0]
    
    print(f"\n✅ Processamento concluído:")
    print(f"   Municípios: {df_final['codigo_tse'].nunique():,}")
    print(f"   Partidos: {df_final['sigla_partido'].nunique()}")
    print(f"   Total de votos: {df_final['votos'].sum():,}")
    print(f"   Linhas no dataset final: {len(df_final):,}")
    
    return df_final

# ============================================
# Processar Eleição 2006
# ============================================

resultados_2006 = processar_resultados_tse_chunks(
    'votacao_candidato_munzona_2006_BRASIL.csv',
    2006,
    'PRESIDENTE',
    chunksize=500000
)

if resultados_2006 is not None:
    resultados_2006.to_csv('tse_2006_processado.csv', index=False, encoding='utf-8-sig')
    print("Salvo: tse_2006_processado.csv")
    
    # Calcular polarização
    polarizacao_2006 = calcular_polarizacao_todos_municipios(
        resultados_2006,
        ideology_dict_2006,
        2006
    )
    polarizacao_2006.to_csv('polarizacao_2006.csv', index=False, encoding='utf-8-sig')
    print("Polarização 2006 calculada")
    
    del resultados_2006
    gc.collect()

# ============================================
# Processar Eleição 2010
# ============================================

resultados_2010 = processar_resultados_tse_chunks(
    'votacao_candidato_munzona_2010_BRASIL.csv',
    2010,
    'PRESIDENTE',
    chunksize=500000
)

if resultados_2010 is not None:
    resultados_2010.to_csv('tse_2010_processado.csv', index=False, encoding='utf-8-sig')
    print("Salvo: tse_2010_processado.csv")
    
    # Calcular polarização
    polarizacao_2010 = calcular_polarizacao_todos_municipios(
        resultados_2010,
        ideology_dict_2010,
        2010
    )
    polarizacao_2010.to_csv('polarizacao_2010.csv', index=False, encoding='utf-8-sig')
    print("Polarização 2010 calculada")
    
    del resultados_2010
    gc.collect()

# ============================================
# Processar Eleição 2014
# ============================================

resultados_2014 = processar_resultados_tse_chunks(
    'votacao_candidato_munzona_2014_BRASIL.csv',
    2014,
    'PRESIDENTE',
    chunksize=500000
)

if resultados_2014 is not None:
    resultados_2014.to_csv('tse_2014_processado.csv', index=False, encoding='utf-8-sig')
    print("Salvo: tse_2014_processado.csv")
    
    # Calcular polarização
    polarizacao_2014 = calcular_polarizacao_todos_municipios(
        resultados_2014,
        ideology_dict_2014,
        2014
    )
    polarizacao_2014.to_csv('polarizacao_2014.csv', index=False, encoding='utf-8-sig')
    print("Polarização 2014 calculada")
    
    del resultados_2014
    gc.collect()

# ============================================
# Processar Eleição 2018
# ============================================

resultados_2018 = processar_resultados_tse_chunks(
    'votacao_candidato_munzona_2018_BRASIL.csv',
    2018,
    'PRESIDENTE',
    chunksize=500000
)

if resultados_2018 is not None:
    resultados_2018.to_csv('tse_2018_processado.csv', index=False, encoding='utf-8-sig')
    print("Salvo: tse_2018_processado.csv")
    
    # Calcular polarização
    polarizacao_2018 = calcular_polarizacao_todos_municipios(
        resultados_2018,
        ideology_dict_2018,
        2018
    )
    polarizacao_2018.to_csv('polarizacao_2018.csv', index=False, encoding='utf-8-sig')
    print("Polarização 2018 calculada")
    
    del resultados_2018
    gc.collect()

# ============================================
# Processar Eleição 2022
# ============================================

resultados_2022 = processar_resultados_tse_chunks(
    'votacao_candidato_munzona_2022_BRASIL.csv',
    2022,
    'PRESIDENTE',
    chunksize=500000
)

if resultados_2022 is not None:
    resultados_2022.to_csv('tse_2022_processado.csv', index=False, encoding='utf-8-sig')
    print("✅ Salvo: tse_2022_processado.csv")
    
    # Calcular polarização
    polarizacao_2022 = calcular_polarizacao_todos_municipios(
        resultados_2022,
        ideology_dict_2022,
        2022
    )
    polarizacao_2022.to_csv('polarizacao_2022.csv', index=False, encoding='utf-8-sig')
    print("✅ Polarização 2022 calculada")
       
    del resultados_2022
    gc.collect()

# ============================================
# Concatenar arquivos polarização
# ============================================

# Combinar
print("\nCombinando painéis...")
painel_polarizacao_2006_2022 = pd.concat([polarizacao_2006, polarizacao_2010, polarizacao_2014, polarizacao_2018, polarizacao_2022], ignore_index=True)
    
# Salvar
painel_polarizacao_2006_2022.to_csv('painel_polarizacao_municipal_2006_2022.csv', index=False, encoding='utf-8-sig')
    
# Checar
print(f"Arquivo: painel_polarizacao_municipal_2006_2022.csv")
print(f"Observações: {len(painel_polarizacao_2006_2022):,}")

# ============================================
# Plotagem da evolução das medidas de polarização
# ============================================

painel = pd.read_csv('painel_polarizacao_municipal_2006_2022.csv', encoding='utf-8-sig')

anos = sorted(painel['ano'].unique())

medidas = [
    ('esteban_ray',   'Índice de Esteban-Ray', 'Polarização ideológica\n(maior = mais polarizado)',     '#c0392b'),
    ('wolfson',       'Índice de Wolfson',     'Bipolarização centro→polos\n(maior = mais bipolar)',     '#8e44ad'),
    ('dalton',        'Índice de Dalton',      'Dispersão ideológica\n(maior = mais disperso)',          '#2980b9'),
    ('reynal_querol', 'Reynal-Querol',         'Bipolarização position-free\n(maior = mais bipolar)',    '#27ae60'),
]

stats = (
    painel
    .groupby('ano')[['esteban_ray', 'wolfson', 'dalton', 'reynal_querol']]
    .agg(['median', lambda q: q.quantile(0.25), lambda q: q.quantile(0.75)])
)
stats.columns = ['_'.join([col, lbl]) for col, lbl in stats.columns]
stats = stats.rename(columns=lambda c: c.replace('<lambda_0>', 'q25').replace('<lambda_1>', 'q75'))
stats = stats.reset_index()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes_flat = axes.flatten()

for ax, (col, titulo, ylabel, cor) in zip(axes_flat, medidas):
    med  = stats[f'{col}_median']
    q25  = stats[f'{col}_q25']
    q75  = stats[f'{col}_q75']

    ax.fill_between(anos, q25, q75, color=cor, alpha=0.15, label='IQR (25°–75°)')
    ax.plot(anos, med, color=cor, linewidth=2.5, marker='o', markersize=7, label='Mediana')

    for x, y in zip(anos, med):
        ax.annotate(f'{y:.3f}', xy=(x, y), xytext=(0, 10),
                    textcoords='offset points', ha='center', fontsize=9, color=cor)

    ax.set_xticks(anos)
    ax.set_xticklabels([str(a) for a in anos], fontsize=10)
    ax.set_title(titulo, fontsize=13, fontweight='bold', pad=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xlabel('Ano da eleição', fontsize=10)
    ax.legend(fontsize=9, loc='best')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines[['top', 'right']].set_visible(False)

fig.suptitle(
    'Evolução das Medidas de Polarização Eleitoral Municipal — Brasil (2006–2022)',
    fontsize=15, fontweight='bold', y=1.01
)
plt.tight_layout()
plt.savefig('evolucao_polarizacao_2006_2022.png', dpi=300, bbox_inches='tight')
print("\n✅ Gráfico salvo: evolucao_polarizacao_2006_2022.png")
plt.show()
