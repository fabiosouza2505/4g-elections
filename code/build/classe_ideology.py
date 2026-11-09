import os
import pandas as pd
import numpy as np
import json
import gc
import matplotlib.pyplot as plt

script_dir = os.getcwd()  # executar a partir de data/
input_csv = os.path.join(script_dir, 'bls9_estimates_partiespresidents_long.csv')

# Carregar
ideology = pd.read_csv(input_csv)
print("=== DADOS CARREGADOS ===")

required_columns = {'party.or.pres', 'year', 'ideo'}
missing_columns = required_columns - set(ideology.columns)
if missing_columns:
    raise ValueError(f"Arquivo CSV faltando colunas obrigatórias: {missing_columns}")

ideology['party.or.pres'] = ideology['party.or.pres'].astype(str).str.upper().str.strip()
ideology['year'] = pd.to_numeric(ideology['year'], errors='coerce').astype('Int64')
ideology['ideo'] = pd.to_numeric(ideology['ideo'], errors='coerce')
ideology = ideology.dropna(subset=['party.or.pres', 'year', 'ideo']).copy()

print(f"Shape: {ideology.shape}")
print(ideology.head(141))

# Ver range
print("\n=== RANGE DOS SCORES ===")
print(f"Mínimo: {ideology['ideo'].min():.3f}")
print(f"Máximo: {ideology['ideo'].max():.3f}")
print(f"Média: {ideology['ideo'].mean():.3f}")

# Normalizar para 0-1
min_score = ideology['ideo'].min()
max_score = ideology['ideo'].max()
score_range = max_score - min_score
if score_range == 0:
    ideology['ideology_01'] = 0.5
else:
    ideology['ideology_01'] = (ideology['ideo'] - min_score) / score_range

# Criar dicionários

# 2005 → para eleição 2006 e 2008
ideology_dict_2006 = dict(zip(
    ideology[ideology['year'] == 2005]['party.or.pres'],
    ideology[ideology['year'] == 2005]['ideology_01']
))

# 2009 → para eleição 2010 e 2012
ideology_dict_2010 = dict(zip(
    ideology[ideology['year'] == 2009]['party.or.pres'],
    ideology[ideology['year'] == 2009]['ideology_01']
))

# 2013 → para eleição 2014
ideology_dict_2014 = dict(zip(
    ideology[ideology['year'] == 2013]['party.or.pres'],
    ideology[ideology['year'] == 2013]['ideology_01']
))

# 2017 → para eleição 2018
ideology_dict_2018 = dict(zip(
    ideology[ideology['year'] == 2017]['party.or.pres'],
    ideology[ideology['year'] == 2017]['ideology_01']
))

# 2021 → para eleição 2022
ideology_dict_2022 = dict(zip(
    ideology[ideology['year'] == 2021]['party.or.pres'],
    ideology[ideology['year'] == 2021]['ideology_01']
))

# Salvar dicionários
with open('ideology_2006.json', 'w', encoding='utf-8') as f:
    json.dump(ideology_dict_2006, f, indent=2, ensure_ascii=False)
with open('ideology_2010.json', 'w', encoding='utf-8') as f:
    json.dump(ideology_dict_2010, f, indent=2, ensure_ascii=False)
with open('ideology_2014.json', 'w', encoding='utf-8') as f:
    json.dump(ideology_dict_2014, f, indent=2, ensure_ascii=False)
with open('ideology_2018.json', 'w', encoding='utf-8') as f:
    json.dump(ideology_dict_2018, f, indent=2, ensure_ascii=False)
with open('ideology_2022.json', 'w', encoding='utf-8') as f:
    json.dump(ideology_dict_2022, f, indent=2, ensure_ascii=False)

# Estatísticas
print(f"\n=== RESUMO ===")
print(f"Partidos com classificação em 2006: {len(ideology_dict_2006)}")
print(f"Partidos com classificação em 2010: {len(ideology_dict_2010)}")
print(f"Partidos com classificação em 2014: {len(ideology_dict_2014)}")
print(f"Partidos com classificação em 2018: {len(ideology_dict_2018)}")
print(f"Partidos com classificação em 2022: {len(ideology_dict_2022)}")

# ============================================
# Plotagem das classificações ideológicas
# ============================================


fig, axes = plt.subplots(2, 3, figsize=(24, 12))
ax1, ax2, ax3 = axes[0, 0], axes[0, 1], axes[0, 2]
ax4, ax5 = axes[1, 0], axes[1, 1]
axes[1, 2].set_visible(False)

# 2006
parties_2006 = sorted(ideology_dict_2006.items(), key=lambda x: x[1])
parties_names = [p[0] for p in parties_2006]
parties_scores = [p[1] for p in parties_2006]

colors_2006 = plt.cm.RdBu(parties_scores)

ax1.barh(parties_names, parties_scores, color=colors_2006)
ax1.axvline(0.33, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax1.axvline(0.67, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax1.text(0.15, len(parties_names)-1, 'Esquerda', fontsize=10, alpha=0.5)
ax1.text(0.5, len(parties_names)-1, 'Centro', fontsize=10, alpha=0.5)
ax1.text(0.8, len(parties_names)-1, 'Direita', fontsize=10, alpha=0.5)
ax1.set_xlabel('Posição Ideológica (0=Esquerda, 1=Direita)', fontsize=11)
ax1.set_title('Classificação Ideológica - Eleição 2006\n(Zucco & Power 2005)',
              fontsize=13, fontweight='bold')
ax1.set_xlim(0, 1)

# 2010
parties_2010 = sorted(ideology_dict_2010.items(), key=lambda x: x[1])
parties_names = [p[0] for p in parties_2010]
parties_scores = [p[1] for p in parties_2010]

colors_2010 = plt.cm.RdBu(parties_scores)

ax2.barh(parties_names, parties_scores, color=colors_2010)
ax2.axvline(0.33, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax2.axvline(0.67, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax2.text(0.15, len(parties_names)-1, 'Esquerda', fontsize=10, alpha=0.5)
ax2.text(0.5, len(parties_names)-1, 'Centro', fontsize=10, alpha=0.5)
ax2.text(0.8, len(parties_names)-1, 'Direita', fontsize=10, alpha=0.5)
ax2.set_xlabel('Posição Ideológica (0=Esquerda, 1=Direita)', fontsize=11)
ax2.set_title('Classificação Ideológica - Eleição 2010\n(Zucco & Power 2009)',
              fontsize=13, fontweight='bold')
ax2.set_xlim(0, 1)

# 2014
parties_2014 = sorted(ideology_dict_2014.items(), key=lambda x: x[1])
parties_names = [p[0] for p in parties_2014]
parties_scores = [p[1] for p in parties_2014]

colors_2014 = plt.cm.RdBu(parties_scores)

ax3.barh(parties_names, parties_scores, color=colors_2014)
ax3.axvline(0.33, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax3.axvline(0.67, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax3.text(0.15, len(parties_names)-1, 'Esquerda', fontsize=10, alpha=0.5)
ax3.text(0.5, len(parties_names)-1, 'Centro', fontsize=10, alpha=0.5)
ax3.text(0.8, len(parties_names)-1, 'Direita', fontsize=10, alpha=0.5)
ax3.set_xlabel('Posição Ideológica (0=Esquerda, 1=Direita)', fontsize=11)
ax3.set_title('Classificação Ideológica - Eleição 2014\n(Zucco & Power 2013)',
              fontsize=13, fontweight='bold')
ax3.set_xlim(0, 1)

# 2018
parties_2018 = sorted(ideology_dict_2018.items(), key=lambda x: x[1])
parties_names = [p[0] for p in parties_2018]
parties_scores = [p[1] for p in parties_2018]

colors_2018 = plt.cm.RdBu(parties_scores)

ax4.barh(parties_names, parties_scores, color=colors_2018)
ax4.axvline(0.33, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax4.axvline(0.67, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax4.text(0.15, len(parties_names)-1, 'Esquerda', fontsize=10, alpha=0.5)
ax4.text(0.5, len(parties_names)-1, 'Centro', fontsize=10, alpha=0.5)
ax4.text(0.8, len(parties_names)-1, 'Direita', fontsize=10, alpha=0.5)
ax4.set_xlabel('Posição Ideológica (0=Esquerda, 1=Direita)', fontsize=11)
ax4.set_title('Classificação Ideológica - Eleição 2018\n(Zucco & Power 2017)',
              fontsize=13, fontweight='bold')
ax4.set_xlim(0, 1)

# 2022
parties_2022 = sorted(ideology_dict_2022.items(), key=lambda x: x[1])
parties_names = [p[0] for p in parties_2022]
parties_scores = [p[1] for p in parties_2022]

colors_2022 = plt.cm.RdBu(parties_scores)

ax5.barh(parties_names, parties_scores, color=colors_2022)
ax5.axvline(0.33, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax5.axvline(0.67, color='black', linestyle='--', alpha=0.3, linewidth=2)
ax5.text(0.15, len(parties_names)-1, 'Esquerda', fontsize=10, alpha=0.5)
ax5.text(0.5, len(parties_names)-1, 'Centro', fontsize=10, alpha=0.5)
ax5.text(0.8, len(parties_names)-1, 'Direita', fontsize=10, alpha=0.5)
ax5.set_xlabel('Posição Ideológica (0=Esquerda, 1=Direita)', fontsize=11)
ax5.set_title('Classificação Ideológica - Eleição 2022\n(Zucco & Power 2021)',
              fontsize=13, fontweight='bold')
ax5.set_xlim(0, 1)

plt.tight_layout()
plt.savefig('classificacao_ideologica_partidos_2006-2022.png', dpi=300, bbox_inches='tight')
print("\n✅ Gráfico salvo: classificacao_ideologica_partidos_2006-2022.png")
plt.show()

