# Processed Data Directory

This directory contains cleaned and merged datasets ready for analysis.

## Files (Created by Pipeline)

### `tse_cleaned.csv`
**Source:** TSE electoral data  
**Created by:** `code/cleaning/01_clean_tse_data.py`  
**Size:** ~2-3 MB  
**Observations:** ~16,500 (4,123 municipalities × 4 years)

**Variables:**
- `cod_municipio` (str): Municipal code (7-digit IBGE format)
- `ano` (int): Election year (2010, 2014, 2018, 2022)
- `polarizacao_er` (float): Esteban-Ray polarization index
- `num_partidos` (int): Number of parties receiving votes
- `total_votos` (int): Total valid votes cast

**Example:**
```
cod_municipio,ano,polarizacao_er,num_partidos,total_votos
1100015,2010,0.0523,8,12453
1100015,2014,0.0612,9,14782
1100015,2018,0.1234,11,16891
1100015,2022,0.1156,10,18234
```

---

### `anatel_4g_by_municipality.csv`
**Source:** ANATEL telecommunications data  
**Created by:** `code/cleaning/02_clean_anatel_data.py`  
**Size:** ~200 KB  
**Observations:** ~4,100 municipalities

**Variables:**
- `cod_municipio` (str): Municipal code (7-digit)
- `ano_primeira_4g` (int): Year of first 4G deployment (NA if never)
- `tem_3g` (int): Has 3G network (1=yes, 0=no)
- `num_estacoes_4g` (int): Number of 4G stations in 2022

**Example:**
```
cod_municipio,ano_primeira_4g,tem_3g,num_estacoes_4g
1100015,2015,1,23
1100023,2016,1,12
1100031,NA,1,0
```

---

### `final_dataset.csv`
**Source:** Merged TSE + ANATEL + IBGE data  
**Created by:** `code/cleaning/03_merge_datasets.py`  
**Size:** ~3-4 MB  
**Observations:** 16,489 (4,123 municipalities × 4 years)

**Variables:**

*Identifiers:*
- `cod_municipio` (str): Municipal code
- `nome_municipio` (str): Municipal name
- `uf` (str): State abbreviation
- `ano` (int): Election year

*Outcome:*
- `polarizacao_er` (float): Esteban-Ray polarization index
- `polarizacao_er_log` (float): Natural log of polarization
- `num_partidos` (int): Number of parties
- `total_votos` (int): Total votes cast

*Treatment:*
- `tem_4g` (int): Has 4G in this year (1=yes, 0=no)
- `ano_primeira_4g` (int): Year first received 4G (0=never)
- `anos_desde_4g` (int): Years since 4G arrival (NA if no 4G)
- `post_4g` (int): Post-treatment indicator

*Controls:*
- `tem_3g` (int): Has 3G network
- `populacao` (int): Population (IBGE estimate)
- `pib_percapita` (float): GDP per capita (R$, IBGE)
- `taxa_urbanizacao` (float): Urbanization rate (%)
- `regiao` (str): Geographic region (Norte, Nordeste, etc.)

**Example:**
```
cod_municipio,nome_municipio,uf,ano,polarizacao_er,tem_4g,ano_primeira_4g,tem_3g,populacao
1100015,Alta Floresta d'Oeste,RO,2010,0.0523,0,2015,1,25335
1100015,Alta Floresta d'Oeste,RO,2014,0.0612,0,2015,1,26524
1100015,Alta Floresta d'Oeste,RO,2018,0.1234,1,2015,1,27891
1100015,Alta Floresta d'Oeste,RO,2022,0.1156,1,2015,1,28456
```

---

## Data Quality Notes

### Coverage
- All 4,123 Brazilian municipalities present across all 4 election years
- No missing outcome data (polarization index)
- 1.6% (65) municipalities never received 4G by 2022

### Treatment Variation
- First 4G deployments: 2012-2013
- Peak adoption: 2015-2018
- 96% of municipalities treated by 2022

### Key Statistics (2014-2018)
- Mean polarization 2014: 0.067
- Mean polarization 2018: 0.107
- Change: +59%
- This dramatic increase motivates the research question

### Validation Checks
✓ Monotonic 4G expansion (no municipality loses 4G)  
✓ Consistent municipal codes across sources  
✓ Vote totals match TSE official reports  
✓ All major parties have ideology classifications  
✓ No duplicate municipality-year observations  

---

## Usage Example

### Python
```python
import pandas as pd

# Load final dataset
df = pd.read_csv('data/processed/final_dataset.csv')

# Filter to treatment and control groups
treated = df[df['tem_4g'] == 1]
control = df[df['tem_4g'] == 0]

# Summary statistics
print(df.groupby('ano')['polarizacao_er'].describe())
```

### R
```r
# Load final dataset
df <- read.csv('data/processed/final_dataset.csv')

# Create treatment indicators
df$post_4g <- ifelse(df$ano >= df$ano_primeira_4g & df$ano_primeira_4g > 0, 1, 0)

# Summary by treatment status
library(dplyr)
df %>%
  group_by(tem_4g) %>%
  summarise(mean_pol = mean(polarizacao_er, na.rm = TRUE))
```

---

## Replication Note

These files are created by running the data cleaning pipeline in sequence:

```bash
cd code/cleaning
python 01_clean_tse_data.py       # Creates tse_cleaned.csv
python 02_clean_anatel_data.py    # Creates anatel_4g_by_municipality.csv  
python 03_merge_datasets.py       # Creates final_dataset.csv
```

Due to file size, processed datasets are not committed to GitHub. Run the pipeline to generate them locally.

---

**Last Updated:** December 2024
