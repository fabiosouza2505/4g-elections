"""
Merge PIB Municipal + População → PIB per capita municipal

Fonte PIB:        pib_municipal_2006_2022.csv   (SIDRA 5938, var 37 – R$ mil)
Fonte população:  pop_municipal_2001_2025.csv   (SIDRA 6579, var 9324 – pessoas)
PIB per capita:   (PIB * 1000) / população

Lacunas na população (anos censitários sem estimativa na tab. 6579):
  - 2007 e 2010 → interpolação linear entre anos adjacentes
  - 2022        → extrapolação linear a partir de 2020–2021
"""

import pandas as pd

PIB_FILE    = "pib_municipal_2006_2022.csv"
POP_FILE    = "pop_municipal_2001_2025.csv"
OUTPUT_FILE = "pib_percapita_municipal.csv"

print("\n" + "=" * 80)
print("MERGE PIB + POPULAÇÃO MUNICIPAL")
print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
# Ambos os CSVs: separador ";", 2ª linha (índice 1) é rótulo descritivo.
# Colunas: D1C = código município (7 dígitos), D2C = ano, V = valor.

def ler_sidra(path: str, col_valor: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", skiprows=[1], dtype=str)
    df["cod_municipio"] = df["D1C"].str[:6]          # 6 dígitos IBGE
    df["ano"]           = pd.to_numeric(df["D2C"], errors="coerce")
    df[col_valor]       = pd.to_numeric(df["V"],   errors="coerce")
    return df[["cod_municipio", "ano", col_valor]].dropna()


print(f"Lendo PIB ...  {PIB_FILE}")
pib = ler_sidra(PIB_FILE, "pib_corrente_mil")
print(f"  {len(pib):,} obs. | anos {int(pib['ano'].min())}–{int(pib['ano'].max())}")

print(f"Lendo POP ...  {POP_FILE}")
pop = ler_sidra(POP_FILE, "populacao")
print(f"  {len(pop):,} obs. | anos {int(pop['ano'].min())}–{int(pop['ano'].max())}")


# ---------------------------------------------------------------------------
# Preencher anos censitários ausentes na população
# ---------------------------------------------------------------------------
# Anos-alvo: todos os anos do PIB
anos_pib = sorted(pib["ano"].dropna().unique().astype(int))

print(f"\nAnos no PIB  : {anos_pib}")
anos_pop = sorted(pop["ano"].dropna().unique().astype(int))
print(f"Anos na POP  : {anos_pop}")
anos_faltantes = sorted(set(anos_pib) - set(anos_pop))
print(f"Anos faltando na POP: {anos_faltantes}")

if anos_faltantes:
    # Pivota para wide, adiciona colunas ausentes e interpola/extrapola
    pop_wide = (
        pop
        .pivot_table(index="cod_municipio", columns="ano", values="populacao")
        .reindex(columns=sorted(set(anos_pib) | set(anos_pop)))
    )

    # interpolate(limit_direction='both') cobre lacunas internas (2007, 2010)
    # e extrapola bordas (2022) a partir da tendência linear dos extremos
    pop_wide = pop_wide.interpolate(method="linear", axis=1, limit_direction="both")

    pop = (
        pop_wide
        .reset_index()
        .melt(id_vars="cod_municipio", var_name="ano", value_name="populacao")
        .dropna(subset=["populacao"])
    )
    pop["ano"] = pop["ano"].astype(int)

    print(f"\nApós interpolação/extrapolação:")
    print(f"  {len(pop):,} obs. | anos {int(pop['ano'].min())}–{int(pop['ano'].max())}")


# ---------------------------------------------------------------------------
# Merge e cálculo do PIB per capita
# ---------------------------------------------------------------------------

dados = pib.merge(pop, on=["cod_municipio", "ano"], how="inner")
dados["pib_percapita"] = (dados["pib_corrente_mil"] * 1_000) / dados["populacao"]

# Marcar anos que tiveram população interpolada/extrapolada
dados["pop_interpolada"] = dados["ano"].isin(anos_faltantes).astype(int)


# ---------------------------------------------------------------------------
# Salvar
# ---------------------------------------------------------------------------

dados.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 80)
print("CONCLUÍDO")
print("=" * 80 + "\n")
print(f"Linhas finais     : {len(dados):,}")
print(f"Anos              : {int(dados['ano'].min())} a {int(dados['ano'].max())}")
print(f"Municípios        : {dados['cod_municipio'].nunique():,}")
print(f"Anos interpolados : {anos_faltantes}")
print(f"Arquivo           : {OUTPUT_FILE}\n")
print("=" * 80 + "\n")
