import pandas as pd
from numpy import int_

import os
from collections import defaultdict
import numbers

from tessif.frused.paths import doc_dir

FOLDER = "commitment_nocongestion_results"
# FOLDER = "commitment_congestion_results"
# FOLDER = "expansion_results"

# locate the storage directory
cp = os.path.join(
    doc_dir, "source", "getting_started", "examples", "application",
    "phd", "model_scenario_combinations", "TransCnE", FOLDER
)

softwares = ['cllp', 'fine', 'omf', 'ppsa', ]
# use this in case you are just testing out the water
# softwares = ['omf', ]
load_nodes = [
    'High Voltage Grid',
    "Medium Voltage Grid",
    "Low Voltage Grid",
    'District Heating',

    # "Low Medium Transfer",
    # "High Medium Transfer",
    # "Medium High Transfer",
    # "Medium Low Transfer",

    # "Excess Sink HV",
    # "Excess Sink MV",
    # "Excess Sink LV",

    # "Deficit Source HV",
    # "Deficit Source MV",
    # "Deficit Source LV",
]

# Result dicts for convenience access
globalesque_results = {}
load_results = {}
timeseries_results = {}
for software in softwares:
    load_results[software] = {}
    timeseries_results[software] = {}
    for node in load_nodes:
        load_result_file = f"{software}_Load_{node}"
        timeseries_load_result_file = f"{software}_timeseries_Load_{node}"

        storage_path = os.path.join(cp, ".".join([load_result_file, "json"]))
        ser = pd.read_json(
            storage_path, orient="split", typ="series")
        ser.name = load_result_file
        load_results[software][node] = ser

        timeseries_storage_path = os.path.join(cp, ".".join(
            [timeseries_load_result_file, "json"]))
        df = pd.read_json(
            timeseries_storage_path, orient="split", typ="frame")
        df.name = timeseries_load_result_file
        timeseries_results[software][node] = df

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
timeseries_by_node = defaultdict(dict)
for software in softwares:
    for node in load_nodes:
        load_by_node[node][software] = load_results[software][node]
        timeseries_by_node[node][software] = timeseries_results[software][node]


labels = [
    "Capacity",
    "IGR",
    "Load-High Voltage Grid",
    "Load-Medium Voltage Grid",
    "Load-Low Voltage Grid",
    "Load-District Heating",

    "Timeseries-High Voltage Grid",
    "Timeseries-Medium Voltage Grid",
    "Timeseries-Low Voltage Grid",
    "Timeseries-District Heating",

    "Load-Low Medium Transfer",
    "Load-High Medium Transfer",
    "Load-Medium High Transfer",
    "Load-Medium Low Transfer",

    "Timeseries-Low Medium Transfer",
    "Timeseries-High Medium Transfer",
    "Timeseries-Medium High Transfer",
    "Timeseries-Medium Low Transfer",

    "Timeseries-Excess Sink HV",
    "Timeseries-Excess Sink MV",
    "Timeseries-Excess Sink LV",

    "Timeseries-Deficit Source HV",
    "Timeseries-Deficit Source MV",
    "Timeseries-Deficit Source LV",
]
dimensions = [
    "MW or MWh",
    "€ or t_CO2",
    "MW",
    "MW",
    "MW",
    "MW",

    "MW",
    "MW",
    "MW",
    "MW",

    "MW",
    "MW",
    "MW",
    "MW",

    "MW",
    "MW",
    "MW",
    "MW",

    "MW",
    "MW",
    "MW",

    "MW",
    "MW",
    "MW",
]
for pos, dct in enumerate([
    capacity_results,
    integrated_global_results,
    load_by_node["High Voltage Grid"],
    load_by_node["Medium Voltage Grid"],
    load_by_node["Low Voltage Grid"],
    load_by_node["District Heating"],

    timeseries_by_node["High Voltage Grid"],
    timeseries_by_node["Medium Voltage Grid"],
    timeseries_by_node["Low Voltage Grid"],
    timeseries_by_node["District Heating"],

    # load_by_node["Low Medium Transfer"],
    # load_by_node["High Medium Transfer"],
    # load_by_node["Medium High Transfer"],
    # load_by_node["Medium Low Transfer"],

    # timeseries_by_node["High Voltage Grid"],
    # timeseries_by_node["Medium Voltage Grid"],
    # timeseries_by_node["Low Voltage Grid"],
    # timeseries_by_node["District Heating"],

    # timeseries_by_node["Low Medium Transfer"],
    # timeseries_by_node["High Medium Transfer"],
    # timeseries_by_node["Medium High Transfer"],
    # timeseries_by_node["Medium Low Transfer"],

    # timeseries_by_node["Excess Sink HV"],
    # timeseries_by_node["Excess Sink MV"],
    # timeseries_by_node["Excess Sink LV"],

    # timeseries_by_node["Deficit Source HV"],
    # timeseries_by_node["Deficit Source MV"],
    # timeseries_by_node["Deficit Source LV"],
]):

    df = pd.concat(
        dct.values(),
        keys=dct.keys(),
        axis='columns')

    # drop all zero  columns
    # df = df.loc[:, (df != 0).any(axis=0)]

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
