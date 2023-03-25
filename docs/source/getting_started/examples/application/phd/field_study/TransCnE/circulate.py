import os
from collections import defaultdict

from tessif.frused.paths import doc_dir

import pandas as pd

PARENT = "TransCnE"
FOLDER = "commitment_nocongestion_results"
# FOLDER = "commitment_congestion_results"
# FOLDER = "expansion_results"
SOFTWARES = [
    # 'cllp',
    # 'fine',
    'omf',
    # 'ppsa',
]
NODES = [
    "High Voltage Grid",
    "Medium Voltage Grid",
    "Low Voltage Grid",
]

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

cp = os.path.join(parent_folder, FOLDER)


load_results = {}

for node in NODES:
    summed_loads_file = f"Timeseries-{node}.csv"
    summed_loads_path = os.path.join(parent_folder, FOLDER, summed_loads_file)

    df = pd.read_csv(summed_loads_path, index_col=0,  header=[0, 1])
    df.columns.name = "softwares"
    load_results[node] = df


def calc_circulated_energy(
        tansfer_grid_connected_bus_loads,
        transfer_grid_transformer_uids
):
    """Calc redispatch between from bus and to bus."""

    loads1 = tansfer_grid_connected_bus_loads
    grid1, grid2 = transfer_grid_transformer_uids

    # select all indices where grid 1 transfers energy from or to bus
    pot_circulate_occasions = loads1[
        loads1[grid1] != 0.0].index

    # abbrevate for brevity
    cos = pot_circulate_occasions

    # energy gets circulated when grid 1 transfers energy from or to the bus,
    # while grid 2 also does:
    circulate_occasions = loads1.loc[cos][loads1.loc[cos][grid2] != 0].index

    # abbrevate again for brevity
    cos = circulate_occasions

    # calculate the absolute difference of the identified energy flows
    amount_circulated = loads1.loc[
        cos][grid1].abs() - loads1.loc[cos][grid2].abs()

    # since we do not know which direction the energy circulates, we are
    # content for now with just knowing the amount
    amount_circulated = amount_circulated.abs()

    return amount_circulated


# prepare the circulation calculations
circulations = {}
for software in SOFTWARES:
    circulations["Medium and High"] = calc_circulated_energy(
        tansfer_grid_connected_bus_loads=load_results["Medium Voltage Grid"][software],
        transfer_grid_transformer_uids=(
            "Medium High Transfer", "High Medium Transfer")
    )

    circulations["Medium and Low"] = calc_circulated_energy(
        tansfer_grid_connected_bus_loads=load_results["Medium Voltage Grid"][software],
        transfer_grid_transformer_uids=(
            "Medium Low Transfer", "Low Medium Transfer")
    )


for direction, circulation in circulations.items():
    filename = f"Circulation {direction}.csv"
    location = os.path.join(parent_folder, FOLDER, filename)
    circulation.name = f"Circulation {direction}"
    circulation.to_csv(location)
    print(direction)
    print(circulation)
