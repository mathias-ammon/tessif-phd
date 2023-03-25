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
from tessif.frused.hooks.tsf import reparameterize_components

# PERIODS = 3
PERIODS = 8760
# EXPANSION = False
EXPANSION = True


FOLDER = "commitment_results"
# FOLDER = "expansion_results"
FOLDER = "modified_expansion_results"

FOLDER = "trivia_results"
# FOLDER = "avs_results"
# FOLDER = "test_results"

# define the softwares to be used
SOFTWARES = ['cllp', 'fine', 'omf', 'ppsa', ]
# use this in case you are just testing out the water
SOFTWARES = ['ppsa', ]
SOFTWARES = ['omf', ]
HOOK_PYPSA = True

CYTOSCAPE_ADVANCED_GRAPH = True
MATPLOTLIB_ADVANCED_GRAPH = False
ADVANCED_GRAPH_ON = "omf"

PARENT = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "field_study",
    "CompCnE",
)


def reparam_ppsa(tessif_es):
    reparameterized_es = reparameterize_components(
        es=tessif_es,
        components={
            'Hard Coal CHP': {
                'flow_emissions': {'Hard_Coal': 0, 'electricity': 0, 'hot_water': 0},
            },
            'Hard Coal Supply': {
                'flow_emissions': {'Hard_Coal': 0.8 * 0.4 + 0.06 * 0.4},
            },
            'Biogas CHP': {
                'flow_emissions': {'biogas': 0, 'electricity': 0, 'hot_water': 0},
            },
            'Biogas Supply': {
                'flow_emissions': {'biogas': 0.25 * 0.4 + 0.01875 * 0.5},
            },

        },

    )
    return reparameterized_es


# create dispatch problem aka TransC or TransE combination
creation_module_path = os.path.join(PARENT, "creation.py")

creation_module = parse.python_file(creation_module_path)
tessif_CompCnE = creation_module.create_compcne_es(
    periods=PERIODS, expansion=EXPANSION,)


# dynamically access the tessif transform utilities based on requested
# softwares above. Store them in a dictionairy for
# ease of access.
transformers = {}
for software in SOFTWARES:
    transformers[software] = importlib.import_module(
        '.'.join(['tessif.transform.es2es', software]))

# Do the tessif -> software transformations and store them in a dictionairy for
# ease of access
transformed_CompCnE_combinations = {}
for software in SOFTWARES:
    # local copy of the tessif es:
    copied_es = tessif_CompCnE.duplicate(suffix='')
    if software == 'ppsa' and HOOK_PYPSA:
        copied_es = reparam_ppsa(copied_es)

    transformed_CompCnE_combinations[software] = transformers[
        software].transform(copied_es)


# Perform the software specific optimizations
optimized_CompCnE_combinations = {}
for software in SOFTWARES:
    optimizer = getattr(optimize, "_".join([software, "from_es"]))
    optimized_CompCnE_combinations[software] = optimizer(
        transformed_CompCnE_combinations[software])

# post process the allresultiers:
all_resultiers = {}
for software in SOFTWARES:
    post_processor = importlib.import_module(
        '.'.join(['tessif.transform.es2mapping', software]))
    all_resultiers[software] = post_processor.AllResultier(
        optimized_CompCnE_combinations[software])

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
                optimized_CompCnE_combinations[software])

wanted_results = {
    'Load': 'node_load',
    'Capacity': 'node_installed_capacity',
    'IntegratedGlobal': 'global_results',
}
nodes_of_interest = {
    'Load': ['Powerline', 'Heatline'],
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

        reference_capacity = all_resultiers[
            ADVANCED_GRAPH_ON].node_installed_capacity["El Demand"]
        reference_net_energy_flow = all_resultiers[
            ADVANCED_GRAPH_ON].edge_net_energy_flow[("Powerline", "El Demand")]
        reference_emissions = all_resultiers[
            ADVANCED_GRAPH_ON].edge_specific_emissions[("Solar Panel", "Powerline")]

        app = dcv.draw_advanced_graph(
            optimized_es=optimized_CompCnE_combinations[ADVANCED_GRAPH_ON],
            layout='cose',
            # layout_nodeDimensionsIncludeLabels=True,
            node_shape="circle",
            node_color={
                'Hard Coal Supply': '#666666',
                'Hard Coal Supply Line': '#666666',
                'Hard Coal PP': '#666666',
                'Hard Coal CHP': '#666666',
                'Solar Panel': '#FF7700',
                'Heat Storage': '#cc0033',
                'Heat Demand': 'Red',
                'Heat Plant': '#cc0033',
                'Heatline': 'Red',
                'Power To Heat': '#cc0033',
                'Biogas CHP': '#006600',
                'Biogas Line': '#006600',
                'Biogas Supply': '#006600',
                'Onshore Wind Turbine': '#99ccff',
                'Offshore Wind Turbine': '#00ccff',
                'Gas Station': '#336666',
                'Gas Line': '#336666',
                'Combined Cycle PP': '#336666',
                'El Demand': '#ffe34d',
                'Battery': '#ffe34d',
                'Powerline': '#ffcc00',
                'Lignite Supply': '#993300',
                'Lignite Supply Line': '#993300',
                'Lignite Power Plant': '#993300',
            },
            reference_node_width=reference_capacity,
            reference_edge_width=reference_net_energy_flow/13,
            reference_edge_blackness=reference_emissions,
            node_border_width=0.1,
            node_fill_border_width=1.5,
            # edge_minimum_grey=0.15,
            nodes_to_remove=[
                "Hard Coal Supply",
                "Hard Coal Supply Line",
                "Hard Coal PP",
                "Hard Coal CHP",

                "Lignite Supply",
                "Lignite Supply Line",
                "Lignite Power Plant",

                "Biogas Supply",
                "Biogas Line",

                "Gas Station",
                "Gas Line",

                "Heat Plant"
            ],
        )

    app.run_server()


if MATPLOTLIB_ADVANCED_GRAPH:
    if ADVANCED_GRAPH_ON in SOFTWARES:
        from tessif.transform.es2mapping import omf as tomf
        from tessif.transform import nxgrph as nxt
        import matplotlib.pyplot as plt
        import tessif.visualize.nxgrph as nxv

        es = optimized_CompCnE_combinations[software]
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
#         optimized_es=optimized_CompCnE_combinations[software],
#         software=software,
#         node="Heatline",
#     )
# # print(rdrs['fine'])
