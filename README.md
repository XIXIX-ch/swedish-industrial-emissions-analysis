# Swedish Industrial Air Emissions Analysis

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Data](https://img.shields.io/badge/Data-EEA%20E--PRTR-00594C)](https://www.eea.europa.eu/en/datahub/datahubitem-view/9405f714-8015-4b5b-a63c-280b82861b3d)

A reproducible Python analysis of facility-level industrial air releases
reported in Sweden under the European Pollutant Release and Transfer Register
(E-PRTR). The project covers 2018–2024 and combines trend, concentration,
sector, data-availability, and spatial analyses.

## Questions answered

- How did selected reported air releases change among consistently reporting
  facility–pollutant pairs?
- How available are annual values for six climate and air-pollution indicators?
- Which facilities account for the largest reported non-biogenic CO₂ releases?
- How concentrated are reported CO₂ releases across facilities and sectors?
- Where are the major reporting facilities located?

## Key findings

Among facility–pollutant pairs with a reported value in every year from 2018
through 2024:

| Pollutant | Facilities | 2018–2024 change |
|---|---:|---:|
| CO₂ excluding biomass | 73 | -10.7% |
| Nitrogen oxides (NOX) | 50 | -8.3% |
| Nitrous oxide (N₂O) | 20 | -19.9% |
| Particulate matter (PM10) | 11 | -32.7% |
| Ammonia (NH₃) | 33 | +3.0% |
| NMVOC | 27 | +9.6% |

For 2024, Swedish facilities reported approximately **14.15 million tonnes**
of CO₂ excluding biomass. The largest facility accounted for **11.4%**, the top
five for **49.1%**, and the top ten for **66.6%**. Energy, metals, and mineral
industries together accounted for **81.5%** of the reported total.

These are descriptive findings for reported E-PRTR releases, not a complete
inventory of all Swedish industrial emissions.

## Results

### Consistent-reporter trend

![Emission trend](outputs/figures/emission_trend_index_2018_2024.png)

### Annual value availability

![Reported value availability](outputs/figures/reporting_coverage_2018_2024.png)

### Largest reported CO₂ sources

![Top ten facilities](outputs/figures/top10_co2_facilities_2024.png)

### Sector contribution

![Sector contribution](outputs/figures/co2_sector_contribution_2024.png)

### Interactive map

[Open the interactive facility map](outputs/interactive/sweden_co2_facilities_2024.html)

## Methodology

1. Load the EEA facility and national air-release worksheets.
2. Filter facility records to Sweden and reshape 2018–2024 values to long form.
3. Validate the schema, unique facility–pollutant keys, non-negative releases,
   and the 2024 CO₂ total against the national worksheet.
4. Measure annual value availability for six selected pollutants.
5. Define a consistent panel as facility–pollutant pairs with values in all
   seven years; index each pollutant's summed releases to 2018 = 100.
6. Rank 2024 CO₂ sources and calculate top-1, top-5, and top-10 concentration.
7. Map Annex I activity codes to broad E-PRTR sectors and aggregate releases.
8. Validate Swedish coordinate bounds and export the interactive map.

All releases are read in kg/year and converted to tonnes or million tonnes only
for presentation.

## Repository structure

```text
.
├── 01_data_exploration.ipynb   # Narrative exploratory workflow
├── src/analyze.py              # Reproducible command-line pipeline
├── DATA.md                     # Source, provenance, and interpretation notes
├── requirements.txt            # Python dependencies
└── outputs/
    ├── figures/                # Publication-ready PNG charts
    ├── interactive/            # Plotly facility map
    └── tables/                 # Analysis-ready CSV outputs
```

## Run locally

Python 3.10 or later is recommended.

```bash
git clone https://github.com/XIXIX-ch/swedish-industrial-emissions-analysis.git
cd swedish-industrial-emissions-analysis
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Download the EEA workbook following [DATA.md](DATA.md), then run:

```bash
python src/analyze.py
```

Custom paths are supported:

```bash
python src/analyze.py --input /path/to/air_releases.xlsx --output-dir outputs
```

## Limitations

- E-PRTR is threshold-based. Blank cells can represent releases below reporting
  thresholds and should not automatically be classified as missing reports.
- The consistent panel reduces changes in sample composition but overrepresents
  persistent, generally larger reporters.
- The PM10 trend is based on only 11 facilities and is therefore exploratory.
- Sector assignment uses the leading digit of each facility's reported main
  Annex I activity and simplifies a more detailed activity classification.
- Results may differ when the EEA revises historical records or publishes a new
  workbook version.

## Data source

European Environment Agency, *Industrial Reporting under the Industrial
Emissions Directive and the European Pollutant Release and Transfer Register*.
See [DATA.md](DATA.md) for the workbook version and reproduction instructions.

## Author

Xi Chen
