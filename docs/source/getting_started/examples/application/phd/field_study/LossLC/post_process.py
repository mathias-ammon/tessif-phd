import pandas as pd
from numpy import int_

import os
from collections import defaultdict
import numbers

from tessif.frused.paths import doc_dir

FOLDER = "results"

# locate the storage directory
cp = os.path.join(
    doc_dir, "source", "getting_started", "examples", "application",
    "phd", "model_scenario_combinations", "LossLC", FOLDER
)

softwares = ['cllp', 'fine', 'omf', 'ppsa', ]
# use this in case you are just testing out the water
# softwares = ['fine', ]
load_nodes = [
    'High Voltage Grid',
    "Medium Voltage Grid",
    "Low Voltage Grid",
    'District Heating',
]

# Result dicts for convenience access
globalesque_results = {}
load_results = {}
for software in softwares:
    load_results[software] = {}
    for node in load_nodes:
        load_result_file = f"{software}_Load_{node}"
        storage_path = os.path.join(cp, ".".join([load_result_file, "json"]))
        ser = pd.read_json(
            storage_path, orient="split", typ="series")
        ser.name = load_result_file
        load_results[software][node] = ser

    globalesque_results[software] = {}
    for rtype in ["Capacity", "IntegratedGlobal"]:
        result_file = f"{software}_{rtype}"
        storage_path = os.path.join(cp, ".".join([result_file, "json"]))
        ser = pd.read_json(
            storage_path, orient="split", typ="series")
        ser.name = result_file
        globalesque_results[software][rtype] = ser

# flatten capacity and igr results for better readability:
capacity_results = {}
integrated_global_results = {}
for software in softwares:
    capacity_results[software] = globalesque_results[software]["Capacity"]
    integrated_global_results[software] = globalesque_results[software]["IntegratedGlobal"]

# aggregate software results into one dataframe for ease of comparison
load_by_node = defaultdict(dict)
for software in softwares:
    for node in load_nodes:
        load_by_node[node][software] = load_results[software][node]

labels = ["Capacity", "IGR", "Load-High Voltage Grid",
          "Load-Medium Voltage Grid", "Load-Low Voltage Grid", "Load-District Heating"]
dimensions = ["MW or MWh", "€ or t_CO2", "MW", "MW", "MW", "MW"]
for pos, dct in enumerate([
    capacity_results,
    integrated_global_results,
    load_by_node["High Voltage Grid"],
    load_by_node["Medium Voltage Grid"],
    load_by_node["Low Voltage Grid"],
    load_by_node["District Heating"],
]):

    df = pd.concat(
        dct.values(),
        keys=dct.keys(),
        axis='columns')
    # give dataframe a name for higher recognition value
    df.index.name = labels[pos] + f" [{dimensions[pos]}]"
    # sort dataframe for index
    df = df.sort_index()

    # change None to "variable" since that is what it means
    df = df.fillna("variable")
    # cast values into integers, since they are deemed to provide enough
    # information
    df = df.applymap(
        lambda x: int_(x) if isinstance(x, numbers.Number) else x,
        # na_action="ignore",
    )

    # dynamically create the filename using the df.index name
    storage_path = os.path.join(cp, ".".join([labels[pos], "csv"]))

    # store the result dfs as csv for convenient access
    df.to_csv(storage_path)
