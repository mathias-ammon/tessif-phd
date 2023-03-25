import os

from tessif.frused.paths import doc_dir

import pandas as pd
import plotly.express as px

PARENT = "LossLC"
FOLDERS = [
    "results",
]
FILE = "Capacity.csv"

NOT_NODES = [
    "Biogas",
    "Coal Supply Line",
    "District Heating",
    "Gas Station",
    "Gaspipeline",
    "High Voltage Grid",
    "Low Voltage Grid",
    "Medium Voltage Grid",
    "Low Voltage Transfer Grid",
    "High Voltage Transfer Grid",
]
PLOTLY = False
MATPLOTLIB = True

# locate the storage directory
parent_folder = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "model_scenario_combinations",
    PARENT,
)

# cp = os.path.join(parent_folder, FOLDER)

for folder in FOLDERS:
    capacities_path = os.path.join(parent_folder, folder, FILE)

    df = pd.read_csv(capacities_path, index_col=0)

    # only keep NODES data:
    keepers = [node for node in df.index if node not in NOT_NODES]
    df = df.loc[keepers]

    # rename df cols and rows for increased verbosity
    df.columns.name = "Softwares"
    df.index.name = "Nodes"

    print(df)
    # original df holds "variable" strings so data needs to be parsed to numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    # store the df as csv for reference
    write_path = os.path.join(parent_folder, folder, "Transfer_Capacities.csv")
    df.to_csv(write_path)

    if PLOTLY:
        figure = px.bar(
            df,
            barmode="group",
            text_auto=True,
            title="Installed Capacities in MWh",
            template="simple_white",
        )
        figure.show()

    if MATPLOTLIB:
        ax = df.plot(
            kind="bar",
            title="Installed Capacities",
            xlabel="Transfer Grid Nodes",
            ylabel="Installed Capacities in MWh",
            rot=45,
        )
        ax.grid(axis='y')
        figure = ax.figure
        figure.show()
