# 4g-elections

# Digital Technology and Electoral Polarization in Brazil (2010-2022)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This repository contains the replication materials for the paper investigating the causal relationship between 4G mobile network expansion and electoral polarization in Brazil during the 2010-2022 period.

**Authors:** Fabio de Medeiros Souza and Priscila Honório Evangelista de Souza  
**Affiliation:** Universidade de Brasília (UnB)  
**Course:** Public Sector Economics (Prof. Maurício Bugarin)

## Abstract

This study examines how the expansion of 4G mobile networks affected political polarization in Brazilian municipalities. Using a staggered difference-in-differences approach with Callaway & Sant'Anna (2021) methodology, we analyze 4,123 municipalities across four electoral cycles (2010, 2014, 2018, 2022). We find that 4G access increased electoral polarization by approximately 2.3%, measured through the Esteban-Ray polarization index. The analysis controls for pre-existing 3G infrastructure to isolate the incremental effect of 4G technology, particularly its capacity for video streaming and multimedia consumption via platforms like WhatsApp.

## Repository Structure

```
├── data/
│   ├── raw/                    # Original datasets (not included - see Data Availability)
│   └── processed/              # Cleaned and merged datasets
├── code/
│   ├── cleaning/               # Data cleaning and merging scripts (Python)
│   ├── analysis/               # Econometric analysis (R)
│   └── figures/                # Figure generation scripts
├── docs/
│   ├── data_documentation.md   # Detailed data source documentation
│   └── methodology.md          # Extended methodology notes
├── output/
│   ├── tables/                 # Regression tables and summary statistics
│   └── figures/                # All figures used in the paper
├── README.md                   # This file
└── requirements.txt            # Python dependencies

```

## Data Availability

Due to file size constraints, raw data files are not included in this repository. All data sources are publicly available:

1. **Electoral Data (TSE)**: [Tribunal Superior Eleitoral](https://dadosabertos.tse.jus.br/)
2. **Telecommunications Data (ANATEL)**: [Agência Nacional de Telecomunicações](https://www.anatel.gov.br/dados/)
3. **Demographic Data (IBGE)**: [Instituto Brasileiro de Geografia e Estatística](https://www.ibge.gov.br/)
4. **Party Ideology Classifications**: Zucco & Power (Harvard Dataverse)

See `docs/data_documentation.md` for detailed instructions on downloading and preparing the raw data.

## Replication Instructions

### Prerequisites

**Python Requirements:**
- Python 3.8+
- pandas
- numpy
- See `requirements.txt` for complete list

**R Requirements:**
- R 4.0+
- did (Callaway & Sant'Anna estimator)
- fixest
- ggplot2
- See R script headers for complete package list

### Step-by-Step Replication

1. **Download raw data** following instructions in `docs/data_documentation.md`

2. **Data cleaning and merging** (Python):
```bash
cd code/cleaning
python 01_clean_tse_data.py
python 02_clean_anatel_data.py
python 03_merge_datasets.py
```

3. **Main analysis** (R):
```bash
cd code/analysis
Rscript 01_descriptive_statistics.R
Rscript 02_staggered_did.R
Rscript 03_robustness_checks.R
```

4. **Generate figures**:
```bash
cd code/figures
Rscript generate_all_figures.R
```

## Key Findings

- Electoral polarization increased dramatically from 2014 to 2018 (+59%)
- 4G network expansion contributed approximately 2.3% to polarization increases
- Effects are distinct from general internet access, representing the incremental impact of 4G over 3G
- Results robust to alternative specifications and control strategies

## Methodology Highlights

- **Identification Strategy**: Staggered difference-in-differences with Callaway & Sant'Anna (2021)
- **Treatment**: 4G network availability at municipal level
- **Outcome**: Esteban-Ray polarization index
- **Controls**: 3G infrastructure, municipal fixed effects, time fixed effects
- **Sample**: 16,489 municipality-election observations (4,123 municipalities × 4 elections)

## Citation

If you use this code or data in your research, please cite:

```bibtex
@unpublished{surname2024digital,
  author = {[Surname], Fabio and Souza, Priscila Hon{\'o}rio Evangelista},
  title = {Digital Technology and Electoral Polarization in Brazil: Evidence from 4G Network Expansion},
  year = {2024},
  note = {Working Paper, Universidade de Bras{\'i}lia}
}
```

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Contact

For questions or comments, please contact:
- Fabio de Medeiros Souza: [email]
- Priscila Honório Evangelista de Souza: [email]

## Acknowledgments

We thank Prof. Maurício Bugarin for guidance, our colleague at ANATEL for technical assistance with telecommunications data, and the broader academic community studying technology's effects on political behavior.

---

**Last Updated:** December 2025

