import pprint
from collections import defaultdict
from pathlib import Path


from tessif.frused.paths import doc_dir

import pandas as pd
import plotly.express as px


PLOTLY = False
MATPLOTLIB = True

MSC_FOLDER = "TransCnE"


msc_path = (
    Path(doc_dir)
    / "source"
    / "getting_started"
    / "examples"
    / "application"
    / "phd"
    / "model_scenario_combinations"
    / MSC_FOLDER
)


igr_results = defaultdict(dict)
capacity_results = {}

for label, result in [
        ("No Congestion", "commitment_nocongestion_results"),
        ("Congestion", "commitment_congestion_results"),
        ("Expansion", "expansion_results"),
]:
    # Integrated Global Results
    igr_results_csv_path = msc_path / result / "IGR.csv"
    igr_results_df = pd.read_csv(igr_results_csv_path, index_col=0)

    igr_results["Total Costs"][label] = igr_results_df.loc["costs (sim)"]
    igr_results["Opex"][label] = igr_results_df.loc["opex (ppcd)"]
    igr_results["Capex"][label] = igr_results_df.loc["capex (ppcd)"]

    # Capacity Results
    capacity_results_csv_path = msc_path / result / "Transfer_Capacities.csv"
    capacity_results_df = pd.read_csv(capacity_results_csv_path, index_col=0)
    capacity_results[label] = capacity_results_df


# Plot Integrated Global Results
for label, dct in igr_results.items():

    df = pd.concat(
        dct.values(),
        keys=dct.keys(),
        axis='columns')
    df = df.transpose()
    df.index.name = "Nodes"
    df.columns.name = "Softwares"
    df.name = label

    if MATPLOTLIB:
        ax = df.plot(
            kind="bar",
            title=f"{label} Comparison",
            xlabel="Scenario",
            ylabel="Costs in €",
            rot=45,
        )
        ax.grid(axis='y')
        figure = ax.figure
        figure.show()

    if PLOTLY:
        figure = px.bar(
            df,
            barmode="group",
            text_auto=True,
            title=f"{label} Comparison in €",
            template="simple_white",
        )
        figure.show()

# Plot Capacity Results
for label, df in capacity_results.items():

    df.index.name = "Nodes"
    df.columns.name = "Softwares"
    df.name = label

    if MATPLOTLIB:
        ax = df.plot(
            kind="bar",
            title=f" {label} Transfer Grid Capacities",
            xlabel="Scenario",
            ylabel="Installed Capacity in MWh",
            rot=45,
        )
        ax.grid(axis='y')
        figure = ax.figure
        figure.show()

    if PLOTLY:
        figure = px.bar(
            df,
            barmode="group",
            text_auto=True,
            title="Installed Capacities in MWh",
            template="simple_white",
        )
        figure.show()
