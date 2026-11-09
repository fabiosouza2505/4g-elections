import requests
import pandas as pd
import time

# ============================================================
# 1. DOWNLOAD TABELA 1554 — API SIDRA v3 (sintaxe correta)
# URL base gerada pelo próprio SIDRA
# ============================================================

# Estratégia: baixar por UF para evitar timeout
# N3[XX] = municípios da UF XX

ufs = [
    11, 12, 13, 14, 15, 16, 17,   # Norte
    21, 22, 23, 24, 25, 26, 27, 28, 29,  # Nordeste
    31, 32, 33, 35,  # Sudeste
    41, 42, 43,  # Sul
    50, 51, 52, 53  # Centro-Oeste
]

dfs = []
erros = []

for uf in ufs:
    # Sintaxe v3: N6[in N3[UF]] = municípios dentro da UF
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/1554"
        f"/periodos/2010/variaveis/140"
        f"?localidades=N6[in N3[{uf}]]"
        f"&classificacao=1568[all]"
    )
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        dados = r.json()
        
        # Estrutura v3: lista de variáveis → resultados → localidades → series
        registros = []
        for variavel in dados:
            for resultado in variavel['resultados']:
                categoria = resultado['classificacoes'][0]['categoria']
                # categoria é dict {cod: nome}
                for cod_cat, nome_cat in categoria.items():
                    for localidade in resultado['series']:
                        cod_mun = localidade['localidade']['id']
                        nome_mun = localidade['localidade']['nome']
                        valor = localidade['serie'].get('2010', None)
                        registros.append({
                            'CO_MUNICIPIO': cod_mun,
                            'NO_MUNICIPIO': nome_mun,
                            'cod_categoria': cod_cat,
                            'nom_categoria': nome_cat,
                            'n_pessoas': valor
                        })
        
        df_uf = pd.DataFrame(registros)
        dfs.append(df_uf)
        print(f"UF {uf}: {len(df_uf)} linhas | {df_uf['CO_MUNICIPIO'].nunique()} municípios")
    
    except Exception as e:
        print(f"UF {uf}: ERRO — {e}")
        erros.append(uf)
    
    time.sleep(0.5)

print(f"\nUFs com erro: {erros}")

# ============================================================
# 2. CONSOLIDAR E SALVAR RAW
# ============================================================

df_raw = pd.concat(dfs, ignore_index=True)
df_raw.to_csv("sidra_1554_raw.csv", index=False)

print(f"\nTotal bruto: {df_raw.shape}")
print(f"Municípios únicos: {df_raw['CO_MUNICIPIO'].nunique()}")
print(f"\nCategorias encontradas:")
print(df_raw[['cod_categoria', 'nom_categoria']].drop_duplicates().to_string())
print(f"\nAmostra:")
print(df_raw.head(8).to_string())

# ============================================================
# 3. CARREGAR E LIMPAR
# ============================================================

df = pd.read_csv("sidra_1554_raw.csv", dtype={'CO_MUNICIPIO': str})

# Garantir código IBGE com 7 dígitos
df['CO_MUNICIPIO'] = df['CO_MUNICIPIO'].str.zfill(7)

# Converter valores
df['n_pessoas'] = pd.to_numeric(df['n_pessoas'], errors='coerce')

# Limpar nome do município (a API retorna "Nome - UF")
df['NO_MUNICIPIO'] = df['NO_MUNICIPIO'].str.split(' - ').str[0].str.strip()

# ============================================================
# 4. PIVOTAR: longo → largo
# ============================================================

df_wide = df.pivot_table(
    index=['CO_MUNICIPIO', 'NO_MUNICIPIO'],
    columns='cod_categoria',
    values='n_pessoas',
    aggfunc='sum'
).reset_index()

# Renomear colunas para nomes legíveis
df_wide.columns.name = None
df_wide = df_wide.rename(columns={
    0:     'total',
    9493:  'sem_fund_incomp',
    9494:  'fund_med_incomp',
    9495:  'medio_sup_incomp',
    99713: 'superior_comp',
    11626: 'nao_determinado'
})

print(f"Shape após pivot: {df_wide.shape}")
print(df_wide.head(4).to_string())

# ============================================================
# 5. CONSTRUIR PROXIES DE EDUCAÇÃO
# ============================================================

# Denominador: exclui não-determinado para não enviesar proporções
df_wide['total_valido'] = (
    df_wide['total'] - df_wide['nao_determinado'].fillna(0)
)

# Proxy principal: prop com médio completo ou mais
# Mecanismo do paper: capacidade de acessar conteúdo diversificado
df_wide['prop_medio_mais'] = (
    (df_wide['medio_sup_incomp'] + df_wide['superior_comp'])
    / df_wide['total_valido']
)

# Proxy alternativa: prop sem instrução/fund incompleto
# Mecanismo: vulnerabilidade a echo chamber 1.0
df_wide['prop_baixa_instrucao'] = (
    df_wide['sem_fund_incomp'] / df_wide['total_valido']
)

# Diagnóstico
print("\n--- prop_medio_mais ---")
print(df_wide['prop_medio_mais'].describe())
print(f"Missings: {df_wide['prop_medio_mais'].isna().sum()}")

print("\n--- prop_baixa_instrucao ---")
print(df_wide['prop_baixa_instrucao'].describe())
print(f"Missings: {df_wide['prop_baixa_instrucao'].isna().sum()}")

# Verificar consistência: as proporções devem somar ~1
df_wide['check_soma'] = (
    df_wide['sem_fund_incomp'] +
    df_wide['fund_med_incomp'] +
    df_wide['medio_sup_incomp'] +
    df_wide['superior_comp']
) / df_wide['total_valido']

print(f"\nCheck consistência (deve ser ~1.0):")
print(df_wide['check_soma'].describe())

# ============================================================
# 6. SALVAR ARQUIVO FINAL
# ============================================================

cols_finais = [
    'CO_MUNICIPIO', 'NO_MUNICIPIO',
    'total', 'total_valido',
    'sem_fund_incomp', 'fund_med_incomp',
    'medio_sup_incomp', 'superior_comp',
    'prop_medio_mais', 'prop_baixa_instrucao'
]

df_wide[cols_finais].to_csv("controles_educacao_censo2010.csv", index=False)
print(f"\n✅ Salvo: controles_educacao_censo2010.csv")
print(f"   {len(df_wide)} municípios | {df_wide['prop_medio_mais'].notna().sum()} com proxy válida")