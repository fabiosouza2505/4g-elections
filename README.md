# Political Polarization and Brazil’s 4G Rollout (2006–2022)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Replication materials for:

> **Designed for Coverage, Not Identification: Political Polarization and the Credibility of Causal Evidence from Brazil’s 4G Rollout**  
> Priscila Honório Evangelista and Fábio de Medeiros Souza — Universidade de Brasília (UnB)

**Status:** accepted for presentation at the 48th Brazilian Meeting of Econometrics (Encontro Brasileiro de Econometria, SBE) — session *Egg Timer Applied Microeconomics 3 – Politics, Crime, Cities and Climate*, Friday, December 18, 2026, 09:00–10:45. The final accepted version of the paper will be added to `paper/` when available.

## Summary

We study how the rollout of 4G mobile infrastructure affected the *bipolarization* of presidential voting in Brazilian municipalities. Party positions come from Zucco & Power; polarization is measured with the Esteban–Ray index and the Foster–Wolfson bipolarization index. The contribution has three parts:

1. **Measurement.** Measurement choices materially change conclusions. Including the PSL (Bolsonaro's party) in the 2018 ideology map raises the 2018 Esteban–Ray index from 0.056 to 0.107, which places the real jump in polarization between 2014 and 2018.
2. **Design.** We build a consolidated panel of five national elections (2006, 2010, 2014, 2018, 2022; 28,479 municipality-year observations). Because 4G arrives in 2013, there are two pre-treatment periods, so parallel trends can be tested in the Callaway & Sant'Anna (2021) estimator. Cohorts: 2014 (968 municipalities), 2018 (1,807), 2022 (1,783) and never-treated (1,270).
3. **Identification.** The 4G rollout is endogenous to the polarization trajectory. Early-cohort pre-trends are positive and significant, and the 2022 cohort's are negative. Correcting for observables does **not** remove the violation: not-yet vs. never-treated controls and outcome regression vs. doubly robust estimation (Sant'Anna & Zhao, 2020) leave the pre-trends essentially unchanged. We quantify the remaining robustness with Honest-DiD (Rambachan & Roth, 2023).

### Main estimates (Model 3b, CS dynamic aggregation, full sample)

| Outcome | Control group | Method | ATT | p-value |
|---|---|---|---|---|
| Esteban–Ray (PSL-corrected) | not-yet-treated | reg | +0.0013 | 0.013 |
| Esteban–Ray (PSL-corrected) | not-yet-treated | DR | +0.0024 | <0.001 |
| Esteban–Ray (PSL-corrected) | never-treated | reg | +0.0012 | 0.031 |
| Esteban–Ray (PSL-corrected) | never-treated | DR | +0.0026 | <0.001 |
| Foster–Wolfson | not-yet-treated | reg | +0.0240 | <0.001 |

**Honest-DiD (relative magnitudes).** The robust confidence interval for the average post-treatment effect excludes zero up to M̄ ≈ 0.1 for Esteban–Ray (fragile) and up to M̄ ≈ 0.6 for Wolfson (suggestive). Neither survives the conventional benchmark M̄ = 1. We read the results as **suggestive evidence of amplification** of bipolarization. Strong causal identification will need an exogenous supply-side instrument for the rollout.

Model 3b controls: `bl_densidade_2010_win + anos_3g + erbs_per_km2 + log_pib_pc + prop_medio_mais` (fixed broadband density in 2010, years of 3G, 4G stations per km², log GDP per capita, share of adults with secondary education or more).

## Repository structure

```
├── code/build/              Python pipeline: raw data → consolidated panel
├── data/
│   ├── raw/                 Small raw inputs (TSE–IBGE crosswalk, Zucco–Power estimates, IBGE GDP/population, SIDRA 1554)
│   ├── intermediate/        Processed TSE votes, municipal polarization by year, ANATEL, GDP per capita, education, ideology maps
│   └── processed/           painel_consolidado_2006_2022.csv (analysis panel)
├── estimation/
│   ├── esteban_ray_corr/    CS-DiD on the PSL-corrected Esteban–Ray index
│   │   ├── notyet_reg/      not-yet-treated, outcome regression (+ quartile/matrix heterogeneity)
│   │   ├── notyet_dr/       not-yet-treated, doubly robust
│   │   ├── never_reg/       never-treated, outcome regression
│   │   └── never_dr/        never-treated, doubly robust
│   ├── wolfson/notyet_reg/  CS-DiD on the Foster–Wolfson index (+ heterogeneity)
│   └── honest_did/          Rambachan–Roth sensitivity analysis
├── figures/                 Figures used in the paper
└── archive/v1_2010_2022/    Earlier version of the project (2010–2022 panel, 4 elections)
```

Each estimation folder holds the R Markdown file and its outputs (`resultados_staggered/`, `resultados_quartil/`): `resultados_<id>.csv` (aggregated ATTs), `att_gt_<id>.csv` (group-time ATTs), `tabela_estabilidade_att_educacao.csv` (stability across the specification families 1a–4d) and event-study plots.

## Replication

### 1. Build the panel (optional; the panel is already in `data/processed/`)

Large raw files are not included because of GitHub's size limits. Download them from:

- **TSE** – `votacao_candidato_munzona_<ano>_BRASIL.csv` for 2006–2022: <https://dadosabertos.tse.jus.br/>
- **ANATEL** – `Estacoes_SMP.csv` (mobile base stations) and `Densidade_Banda_Larga_Fixa.csv`: <https://informacoes.anatel.gov.br/paineis/>
- **Zucco & Power** – party ideology estimates (included in `data/raw/`): Harvard Dataverse

The scripts read and write files in the current working directory. Put all inputs in one folder and run from it, in this order:

```bash
python code/build/classe_ideology.py         # party ideology maps per election (ideology_<ano>.json)
python code/build/class_polarization.py      # TSE votes → municipal polarization indices
python code/build/class_anatel.py            # 3G/4G rollout, station intensity, broadband
python code/build/class_educ_data.py         # Census 2010 education controls (SIDRA 1554)
python code/build/class_renda.py             # GDP per capita
python code/build/build_painel_consolidado.py  # → painel_consolidado_2006_2022.csv
```

Python dependencies are listed in `requirements.txt`.

### 2. Estimation (R)

Open each `.Rmd` and knit it with the working directory set to its own folder (the RStudio default). Each one reads `data/processed/painel_consolidado_2006_2022.csv` by relative path.

R packages: `did`, `HonestDiD`, `fixest`, `tidyverse`, `cowplot`.

Recommended order: `esteban_ray_corr/notyet_reg` and `wolfson/notyet_reg` (main results), the three other `esteban_ray_corr` folders (2×2 control-group × method check), then `honest_did`.

## Citation

```bibtex
@unpublished{evangelista_souza_2026_4g,
  author = {Evangelista, Priscila Hon{\'o}rio and Souza, F{\'a}bio de Medeiros},
  title  = {Designed for Coverage, Not Identification: Political Polarization and the Credibility of Causal Evidence from {Brazil's} {4G} Rollout},
  year   = {2026},
  note   = {Paper presented at the 48th Brazilian Meeting of Econometrics (SBE). Universidade de Bras{\'i}lia}
}
```

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

We thank Prof. Maurício Bugarin (UnB) for guidance and a colleague at ANATEL for technical help with the telecommunications data.
