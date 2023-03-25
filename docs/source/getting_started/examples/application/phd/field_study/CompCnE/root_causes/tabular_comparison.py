# docs/source/getting_started/examples/application/phd/field_study/CompCnE/root_causes/tabular_comparison.py
"""Helper script to export ods/xlsx table to csv for documentation display.

Uses the tessif documented :ref:`SupportedModels_TabularComparison` to select
the components and software tools chosen by the :ref:`CRA_IRC` analysis.
"""
import os

import pandas as pd

from tessif.frused.paths import doc_dir

# manually access current location
cwd = os.path.join(
    doc_dir,
    "source",
    "usage",
    "supported_models",
    "tabular_parameter_comparison",
)

fle = os.path.join(cwd, "Tabular_Parameter_Comparison.ods")

# import the spreadsheet data
sp_data = pd.read_excel(
    fle,
    na_values="-",
    sheet_name=None,
    index_col=0,
)

# Filtering the data regarding the suggested investigations:
investigation_dicts = [
    {"chp_emissions": {"Transformer": ["Tessif", "PyPSA"]}},
    {"storage_cyclic": {"Storage": [
        "Tessif", "Calliope", "FINE", "Oemof", "PyPSA"]}},
    {"storage_emissions": {"Storage": ["Tessif", "PyPSA"]}},
]


selected = {}
for investigation in investigation_dicts:
    for investigation_tag in investigation:
        for component, tools in investigation[investigation_tag].items():
            table = sp_data[component]

            selected[investigation_tag] = table[tools]


parent = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "field_study",
    "CompCnE",
    "root_causes",
)

condensed = {}

fle = os.path.join(parent, "tabular_comparison_chp_emissions.csv")
condensed["chp_emissions"] = selected["chp_emissions"].iloc[:10]
condensed["chp_emissions"].to_csv(fle)

fle = os.path.join(parent, "tabular_comparison_storage_cyclic.csv")
condensed["storage_cyclic"] = selected["storage_cyclic"].iloc[:10]
condensed["storage_cyclic"].to_csv(fle)

fle = os.path.join(parent, "tabular_comparison_storage_emissions.csv")
condensed["storage_emissions"] = selected["storage_emissions"].iloc[:14]
condensed["storage_emissions"].to_csv(fle)

# # store each sheet as its component name csv
# for component, table in sp_data.items():
#     fle = os.path.join(cwd, component + ".csv")
#     table.to_csv(fle)
