import os
from collections import defaultdict

import matplotlib.pyplot as plt
import pandas as pd

from tessif.frused.paths import doc_dir
from tessif.visualize import component_loads


PARENT = "TransCnE"
FOLDER = "commitment_nocongestion_results"
# FOLDER = "commitment_congestion_results"
# FOLDER = "expansion_results"
SOFTWARES = [
    'cllp',
    # 'fine',
    'omf',
    # 'ppsa',
]
NODES = [
    "Medium Voltage Grid",
    # "Low Medium Transfer",
    # "High Medium Transfer",
    # "Medium High Transfer",
    # "Medium Low Transfer",
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
for software in SOFTWARES:
    load_results[software] = {}
    for node in NODES:
        load_result_file = f"{software}_timeseries_Load_{node}"
        storage_path = os.path.join(cp, ".".join([load_result_file, "json"]))
        df = pd.read_json(
            storage_path, orient="split", typ="frame")
        df.name = load_result_file
        load_results[software][node] = df

        # store the df as csv for reference
        df.columns.name = "Softwares"
        write_path = os.path.join(cp, ".".join([load_result_file, "csv"]))
        df.to_csv(write_path)


# aggregate software results into one dataframe for ease of comparison
load_by_node = defaultdict(dict)
for software in SOFTWARES:
    for node in NODES:
        load_by_node[node][software] = load_results[software][node]

for software in SOFTWARES:
    for node in NODES:

        df = load_by_node[node][software]
        # drop all zero  columns
        df = df.loc[:, (df != 0).any(axis=0)]

        figure = component_loads.bar_lines(
            df,
            component_type='bus',
        )

        title = f"{node} Load Profile Results of Software: '{software}'"
        figure.axes[0].set_title(title)

        figure.show()
