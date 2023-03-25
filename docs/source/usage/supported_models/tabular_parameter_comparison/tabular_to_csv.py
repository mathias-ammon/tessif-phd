# docs/source/usage/supported_models/tabular_to_csv.py
"""Helper script to export ods/xlsx table to csv for documentation display.
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

# Pop unwanted spreadsheet
sp_data.pop("Identification")

# store each sheet as its component name csv
for component, table in sp_data.items():
    fle = os.path.join(cwd, component + ".csv")
    table.to_csv(fle)
