# docs/source/getting_started/examples/application/phd/field_study/CompCnE/root_causes/plausubility_check.py
"""Helper scipt to check if components behave as expected
"""

import importlib
import os

import pandas as pd

from tessif.frused.paths import (
    example_dir,
    doc_dir,
)
import tessif.parse
import tessif.transform.mapping2es.tsf as tsf
import tessif.simulate as optimize
import tessif.visualize.dcgrph as dcv

import tessif.frused.configurations as configurations
configurations.spellings_logging_level = "debug"

# define the softwares to be used
SOFTWARES = ['cllp', 'fine', 'omf', 'ppsa', ]
# use this in case you are just testing out the water
# SOFTWARES = ['cllp', 'omf', 'ppsa', ]

# RESULTIER = "StorageResultier"
# RESULT_TYPE = "node_soc"
# NODE = "Battery"

# storage
COMPONENT = "storage"
CONSTRAINT_TYPE = "phd"
CONSTRAINT = "cyclic_soc.py"
CONSTRAINT = "emissions.py"

# chp
COMPONENT = "chp"
CONSTRAINT_TYPE = "phd"
CONSTRAINT = "emissions.py"


location = os.path.join(
    example_dir,
    "application",
    "verification_scenarios",
    COMPONENT,
    CONSTRAINT_TYPE,
    CONSTRAINT,
)

module = tessif.parse.python_file(location)
# pprint.pprint(module.mapping)
es = tsf.transform(tessif.parse.python_mapping(module.mapping))

if COMPONENT == "chp":
    RESULTIER = "LoadResultier"
    RESULT_TYPE = "node_load"
    NODE = "Power Bus"

    node_colors = {
        "Gas Commodity": "#5A9BD4",  # blueish
        "Gas Pipeline": "#5A9BD4",  # blueish

        "Expensive Heat": "#CE7058",  # reddish
        "Heat Bus": "#CE7058",  # reddish
        "Heat Demand": "#CE7058",  # reddish

        "CHP": "#7AC36A",  # greenish

        "Expensive Power": "#FAA758",  # orangeish
        "Power Bus": "#FAA758",  # orangeish
        "Power Demand": "#FAA758",  # orangeish
        # "Central ": "#d4935a",  # brownish
    }

elif CONSTRAINT == "cyclic_soc.py":

    RESULTIER = "LoadResultier"
    RESULT_TYPE = "node_load"
    NODE = "Central Bus"

    node_colors = {
        "Over Producing": "#5A9BD4",  # blueish
        "Battery": "#CE7058",  # reddish
        "Unused Expensive": "#7AC36A",  # greenish
        "Demand": "#FAA758",  # orangeish
        "Central Bus": "#d4935a",  # brownish
    }

elif CONSTRAINT == "emissions.py":

    RESULTIER = "StorageResultier"
    RESULT_TYPE = "node_soc"
    NODE = "Battery"

    node_colors = {
        "Initial Charge": "#5A9BD4",  # blueish
        "Battery": "#CE7058",  # reddish
        "Expensive": "#7AC36A",  # gfreenish
        "Demand": "#FAA758",  # orangeish
        "Central Bus": "#d4935a",  # brownish
    }

app = dcv.draw_generic_graph(es, color_group=node_colors)
# app.run_server(debug=False)

# dynamically access the tessif transform utilities based on requested
# softwares above. Store them in a dictionairy for
# ease of access.
transformers = {}
for software in SOFTWARES:
    transformers[software] = importlib.import_module(
        '.'.join(['tessif.transform.es2es', software]))

# Do the tessif -> software transformations and store them in a dictionairy for
# ease of access
transformed_es = {}
for software in SOFTWARES:
    transformed_es[software] = transformers[software].transform(
        es)


# Perform the software specific optimizations
optimized_es = {}
for software in SOFTWARES:
    optimizer = getattr(optimize, "_".join([software, "from_es"]))
    optimized_es[software] = optimizer(
        transformed_es[software])

# Post process the load results
resultiers = {}
for software in SOFTWARES:
    post_processor = importlib.import_module(
        '.'.join(['tessif.transform.es2mapping', software]))
    resultiers[software] = getattr(
        post_processor, RESULTIER)(optimized_es[software])


for software in SOFTWARES:
    print(software)
    result = getattr(resultiers[software], RESULT_TYPE)[NODE]
    print(result)

root_causes_path = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "field_study",
    "CompCnE",
    "root_causes",
)

if COMPONENT == "chp":
    result_data = {
        software: getattr(resultiers[software], RESULT_TYPE)[NODE]["CHP"]
        for software in SOFTWARES
    }

    all_flows = pd.concat(
        objs=list(result_data.values()),
        keys=result_data.keys(),
        axis="columns",
    )
    all_flows.columns.name = "CHP"
    print(all_flows)
    fle = os.path.join(
        root_causes_path, "plausify_chp_emissions_chp_flows.csv")
    all_flows.to_csv(fle)

    from tessif.transform.es2mapping.ppsa import IntegratedGlobalResultier
    igr_res = IntegratedGlobalResultier(optimized_es["ppsa"]).global_results
    pypsa_igr = pd.Series(igr_res)
    pypsa_igr.name = "Result"
    pypsa_igr.index.name = "PyPSA IGR"

    fle = os.path.join(root_causes_path, "plausify_chp_emissions_igr.csv")
    pypsa_igr.to_csv(fle)


elif CONSTRAINT == "cyclic_soc.py":

    result_data = {
        software: getattr(resultiers[software], RESULT_TYPE)[NODE]
        for software in SOFTWARES
    }
    all_socs = pd.DataFrame.from_dict(result_data)
    fle = os.path.join(root_causes_path, "plausify_cyclic_soc.csv")
    all_socs.to_csv(fle)

elif CONSTRAINT == "emissions.py":
    result_data = {
        software: getattr(resultiers[software], RESULT_TYPE)[NODE]["Battery"]
        for software in SOFTWARES
    }

    all_flows = pd.concat(
        objs=list(result_data.values()),
        keys=result_data.keys(),
        axis="columns",
    )
    print(all_flows)
    fle = os.path.join(
        root_causes_path, "plausify_storage_emissions_battery_flows.csv")
    all_flows.to_csv(fle)

    from tessif.transform.es2mapping.ppsa import IntegratedGlobalResultier
    igr_res = IntegratedGlobalResultier(optimized_es["ppsa"]).global_results
    pypsa_igr = pd.Series(igr_res)
    pypsa_igr.name = "Result"
    pypsa_igr.index.name = "PyPSA IGR"

    fle = os.path.join(root_causes_path, "plausify_storage_emissions_igr.csv")
    pypsa_igr.to_csv(fle)
