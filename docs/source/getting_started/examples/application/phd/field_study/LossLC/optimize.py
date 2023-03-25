import pandas as pd

import json
import importlib
import os
from pathlib import Path

from tessif.analyze import ComparativeResultier
from tessif.frused.paths import doc_dir
import tessif.examples.data.tsf.py_hard as tsf_examples
import tessif.simulate as optimize
from tessif.transform.es2mapping import compile_result_data_representation

# Change this to 8760 and "exp_results" for the full results.
# (Takes about 30min - 1h)
PERIODS = 24
FOLDER = "results"
FOLDER = "losslc_results"

PARENT = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "field_study",
    "LossLC",
)


# create dispatch problem aka LossLC combination
tessif_LossLC = tsf_examples.create_losslc_es(periods=PERIODS)

# define the softwares to be used
SOFTWARES = ['cllp', 'fine', 'omf', 'ppsa', ]
# use this in case you are just testing out the water
# SOFTWARES = ['cllp', ]

# dynamically access the tessif transform utilities based on requested
# softwares above. Store them in a dictionairy for
# ease of access.
transformers = {}
for software in SOFTWARES:
    transformers[software] = importlib.import_module(
        '.'.join(['tessif.transform.es2es', software]))

# Do the tessif -> software transformations and store them in a dictionairy for
# ease of access
transformed_LossLC_combinations = {}
for software in SOFTWARES:
    transformed_LossLC_combinations[software] = transformers[software].transform(
        tessif_LossLC)


# Perform the software specific optimizations
optimized_LossLC_combinations = {}
for software in SOFTWARES:
    optimizer = getattr(optimize, "_".join([software, "from_es"]))
    optimized_LossLC_combinations[software] = optimizer(
        transformed_LossLC_combinations[software])

# post process the allresultiers:
all_resultiers = {}
for software in SOFTWARES:
    post_processor = importlib.import_module(
        '.'.join(['tessif.transform.es2mapping', software]))
    all_resultiers[software] = post_processor.AllResultier(
        optimized_LossLC_combinations[software])

# post process the comparative results using the constructed all-resultiers:
comparatier = ComparativeResultier(all_resultiers)


data_storage_path = os.path.join(PARENT, FOLDER)

# store the all_loads results
for software in SOFTWARES:

    result_id = f"{software}_all_loads"
    storage_location = os.path.join(data_storage_path, result_id)
    result_df = comparatier.all_loads[software]
    result_df.to_csv(".".join([storage_location, "csv"]))

# store the all_socs results
result_id = f"all_socs"
storage_location = os.path.join(data_storage_path, result_id)
result_df = comparatier.all_socs

if not result_df.empty:
    result_df.to_csv(".".join([storage_location, "csv"]))

# store the rest of the all_* results:
for rtype in [
        "all_capacities",
        "all_original_capacities",
        "all_net_energy_flows",
        "all_costs_incurred",
        "all_emissions_caused",
]:
    result_id = rtype
    storage_location = os.path.join(data_storage_path, result_id)
    result_df = getattr(comparatier, rtype)
    result_df.to_csv(".".join([storage_location, "csv"]))

result_types = ['Load', 'Capacity', 'IntegratedGlobal']
post_processed_data = {}
for software in SOFTWARES:
    post_processor = importlib.import_module(
        '.'.join(['tessif.transform.es2mapping', software]))
    post_processed_data[software] = {}
    for result_type in result_types:
        post_processed_data[software][result_type] = getattr(
            post_processor, "".join([result_type, "Resultier"]))(
                optimized_LossLC_combinations[software])

wanted_results = {
    'Load': 'node_load',
    'Capacity': 'node_installed_capacity',
    'IntegratedGlobal': 'global_results',
}
nodes_of_interest = {
    'Load': [
        'High Voltage Grid',
        "Medium Voltage Grid",
        "Low Voltage Grid",
        'District Heating',
    ],
    'Capacity': [],
    'IntegratedGlobal': [],
}

for software in SOFTWARES:
    for rtype in result_types:
        if nodes_of_interest[rtype]:
            for node in nodes_of_interest[rtype]:
                result_id = f"{software}_{rtype}_{node}"
                storage_location = os.path.join(data_storage_path, result_id)
                res = getattr(post_processed_data[software][rtype], wanted_results[rtype])[
                    node]
                if rtype == 'Load':
                    res = res.sum()
                    res.name = result_id
                    res.to_json(
                        ".".join([storage_location, "json"]), orient="split")

        else:
            result_id = f"{software}_{rtype}"
            storage_location = os.path.join(data_storage_path, result_id)
            res = getattr(
                post_processed_data[software][rtype], wanted_results[rtype])
            res = pd.Series(res.values(), index=res.keys())
            res.name = result_id
            res.to_json(
                ".".join([storage_location, "json"]), orient="split")

# Use this in case you want to see the result representation of certain nodes
# rdrs = {}
# for software in SOFTWARES:
#     rdrs[software] = compile_result_data_representation(
#         optimized_es=optimized_LossLC_combinations[software],
#         software=software,
#         node="Heatline",
#     )
# # print(rdrs['fine'])
