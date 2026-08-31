# Data

This project uses the European Environment Agency (EEA) **Industrial
Reporting under the Industrial Emissions Directive and the European Pollutant
Release and Transfer Register** dataset.

- Dataset page: <https://www.eea.europa.eu/en/datahub/datahubitem-view/9405f714-8015-4b5b-a63c-280b82861b3d>
- Workbook used: `EEA_Industry_Dataset_EPRTR_Air_Releases.xlsx`
- Publication date recorded in the workbook: 2025-12-15
- Analysis scope: Sweden, 2018–2024
- Release unit: kg/year
- Main worksheet: `Air_Releases_Facilities`
- Reconciliation worksheet: `Air_Releases_National`

## Reproducing the analysis

1. Download the air-releases workbook from the EEA dataset page.
2. Place it in the repository root with the filename shown above.
3. Run `python src/analyze.py`.

The workbook is excluded from Git because it is third-party source data. The
repository contains analysis code and generated results, not a redistributed
copy of the source dataset. Consult the EEA dataset page for current terms and
metadata.

## Interpretation note

E-PRTR releases are threshold-based operator reports. A blank annual value is
not automatically a data-quality failure: it may mean that a release was below
the applicable reporting threshold or was otherwise not reportable. The project
therefore calls this metric *value availability*, not compliance or general
reporting completeness.
