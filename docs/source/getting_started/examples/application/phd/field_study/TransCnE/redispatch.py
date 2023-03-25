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

# prepare the redispatch calculations
redispatches = {}


def calc_redispatch(loads_from, loads_to, uid_XSsink, uid_DEFsource):
    """Calc redispatch between from bus and to bus."""

    # select all indices where surplus sink gets used
    congestion_occasions = loads_from[loads_from[uid_XSsink] > 0].index

    # access all lack bus loads, of prior selected indices
    pot_redispatch = loads_to.loc[congestion_occasions][uid_DEFsource]

    # redispatch = the amount of suprlus energy provided on timesteps where
    # excess energy was dumped
    redispatch = pot_redispatch[pot_redispatch.abs() > 0].abs()

    return redispatch


for software in SOFTWARES:
    redispatches["High2Medium"] = calc_redispatch(
        loads_from=load_results["High Voltage Grid"][software],
        loads_to=load_results["Medium Voltage Grid"][software],
        uid_XSsink="Excess Sink HV",
        uid_DEFsource="Deficit Source MV",
    )

    redispatches["Medium2High"] = calc_redispatch(
        loads_from=load_results["Medium Voltage Grid"][software],
        loads_to=load_results["High Voltage Grid"][software],
        uid_XSsink="Excess Sink MV",
        uid_DEFsource="Deficit Source HV",
    )

    redispatches["Low2Medium"] = calc_redispatch(
        loads_from=load_results["Low Voltage Grid"][software],
        loads_to=load_results["Medium Voltage Grid"][software],
        uid_XSsink="Excess Sink LV",
        uid_DEFsource="Deficit Source MV",
    )

    redispatches["Medium2Low"] = calc_redispatch(
        loads_from=load_results["Medium Voltage Grid"][software],
        loads_to=load_results["Low Voltage Grid"][software],
        uid_XSsink="Excess Sink MV",
        uid_DEFsource="Deficit Source LV",
    )

for direction, redispatch in redispatches.items():
    filename = f"Redispatch_{direction}.csv"
    location = os.path.join(parent_folder, FOLDER, filename)
    redispatch.name = f"Redispatch {direction}"
    redispatch.to_csv(location)
    print(direction)
    print(redispatch)
