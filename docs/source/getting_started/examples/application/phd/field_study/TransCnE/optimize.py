import pandas as pd

import json
import importlib
import os
from pathlib import Path

from tessif.analyze import ComparativeResultier
from tessif import parse
from tessif.frused.paths import doc_dir
import tessif.examples.data.tsf.py_hard as tsf_examples
import tessif.simulate as optimize
from tessif.transform.es2mapping import compile_result_data_representation
import tessif.visualize.dcgrph as dcv

PERIODS = 24
# GRID_CAPACITY = 60000  # no congestion
# GRID_CAPACITY = 20000  # congestion
GRID_CAPACITY = 1  # Expansion
# EXPANSION = False
EXPANSION = True

FOLDER = "commitment_nocongestion_results"
# FOLDER = "commitment_congestion_results"
FOLDER = "expansion_results"

# define the softwares to be used
SOFTWARES = ['cllp', 'fine', 'omf', 'ppsa', ]
# use this in case you are just testing out the water
# SOFTWARES = ['omf', ]

CYTOSCAPE_ADVANCED_GRAPH = False
MATPLOTLIB_ADVANCED_GRAPH = False
ADVANCED_GRAPH_ON = "omf"


TRANS_OPS = {
    "ppsa": {
        "forced_links": (
            'Low Medium Transfer',
            'Medium Low Transfer',
            'High Medium Transfer',
            'Medium High Transfer',
        ),
        "excess_sinks": (
            "Excess Sink HV",
            "Excess Sink MV",
            "Excess Sink LV",
        ),
    }
}

PARENT = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "field_study",
    "TransCnE",
)

# create dispatch problem aka TransC or TransE combination
creation_module_path = os.path.join(PARENT, "creation.py")

creation_module = parse.python_file(creation_module_path)
tessif_TransCnE = creation_module.create_transcne_es(
    periods=PERIODS, expansion=EXPANSION, gridcapacity=GRID_CAPACITY)


# dynamically access the tessif transform utilities based on requested
# softwares above. Store them in a dictionairy for
# ease of access.
transformers = {}
for software in SOFTWARES:
    transformers[software] = importlib.import_module(
        '.'.join(['tessif.transform.es2es', software]))

# Do the tessif -> software transformations and store them in a dictionairy for
# ease of access
transformed_TransCnE_combinations = {}
for software in SOFTWARES:
    if software in TRANS_OPS:
        transops = TRANS_OPS[software]
    else:
        transops = {}

    transformed_TransCnE_combinations[software] = transformers[software].transform(
        tessif_TransCnE, **transops)


# Perform the software specific optimizations
optimized_TransCnE_combinations = {}
for software in SOFTWARES:
    optimizer = getattr(optimize, "_".join([software, "from_es"]))
    optimized_TransCnE_combinations[software] = optimizer(
        transformed_TransCnE_combinations[software])


# post process the allresultiers:
all_resultiers = {}
for software in SOFTWARES:
    post_processor = importlib.import_module(
        '.'.join(['tessif.transform.es2mapping', software]))
    all_resultiers[software] = post_processor.AllResultier(
        optimized_TransCnE_combinations[software])

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


result_types = ['Load', 'Capacity', 'IntegratedGlobal', ]
post_processed_data = {}
for software in SOFTWARES:
    post_processor = importlib.import_module(
        '.'.join(['tessif.transform.es2mapping', software]))
    post_processed_data[software] = {}
    for result_type in result_types:
        post_processed_data[software][result_type] = getattr(
            post_processor, "".join([result_type, "Resultier"]))(
                optimized_TransCnE_combinations[software])

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
                    # store timeseries results
                    res.name = f"{software}_timeseries_{rtype}_{node}"
                    timeseries_storage_location = storage_location.replace(
                        rtype, "timeseries_"+rtype)
                    res.to_json(
                        ".".join([timeseries_storage_location, "json"]),
                        orient="split",
                    )

                    # store regular loads as summed loads
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


# draw advanced graphs
advanced_graphs = {}
if CYTOSCAPE_ADVANCED_GRAPH:
    if ADVANCED_GRAPH_ON in SOFTWARES:
        app = dcv.draw_advanced_graph(
            optimized_es=optimized_TransCnE_combinations[ADVANCED_GRAPH_ON],
            # layout='style',
            # layout_nodeDimensionsIncludeLabels=True,
            node_shape="circle",
            node_color={
                'Coal Supply': '#666666',
                'Coal Supply Line': '#666666',
                'HKW': '#666666',
                'HKW2': '#666666',
                'Solar Thermal': '#b30000',
                'Heat Storage': '#cc0033',
                'District Heating': 'Red',
                'District Heating Demand': 'Red',
                'Power to Heat': '#b30000',
                'Biogas plant': '#006600',
                'Biogas': '#006600',
                'BHKW': '#006600',
                'Onshore Wind Power': '#99ccff',
                'Offshore Wind Power': '#00ccff',
                'Gas Station': '#336666',
                'Gaspipeline': '#336666',
                'GuD': '#336666',
                'Solar Panel': '#ffe34d',
                'Commercial Demand': '#ffe34d',
                'Household Demand': '#ffe34d',
                'Industrial Demand': '#ffe34d',
                'Car charging Station': '#669999',

                'Low Voltage Grid': '#ffcc00',
                'Medium Voltage Grid': '#ffcc00',
                'High Voltage Grid': '#ffcc00',

                'Low Medium Transfer': '#ff9900',
                'Medium Low Transfer': '#ff9900',

                'High Medium Transfer': '#ff9900',
                'Medium High Transfer': '#ff9900',

                "Excess Sink HV": "yellow",
                "Excess Sink MV": "yellow",
                "Excess Sink LV": "yellow",

                "Deficit Source HV": "yellow",
                "Deficit Source MV": "yellow",
                "Deficit Source LV": "yellow",
            }
        )

    app.run_server()


if MATPLOTLIB_ADVANCED_GRAPH:
    if ADVANCED_GRAPH_ON in SOFTWARES:
        from tessif.transform.es2mapping import omf as tomf
        from tessif.transform import nxgrph as nxt
        import matplotlib.pyplot as plt
        import tessif.visualize.nxgrph as nxv

        es = optimized_TransCnE_combinations[software]
        formatier = tomf.AllFormatier(es, cgrp='all')
        grph = nxt.Graph(tomf.FlowResultier(es))

        for key, value in formatier.edge_data()['edge_width'].items():
            formatier.edge_data()['edge_width'][key] = 4 * value

        nxv.draw_graphical_representation(
            formatier=formatier, colored_by='sector')

        figure = plt.gcf()
        figure.show()

# Use this in case you want to see the result representation of certain nodes
# rdrs = {}
# for software in SOFTWARES:
#     rdrs[software] = compile_result_data_representation(
#         optimized_es=optimized_TransCnE_combinations[software],
#         software=software,
#         node="Heatline",
#     )
# # print(rdrs['fine'])
