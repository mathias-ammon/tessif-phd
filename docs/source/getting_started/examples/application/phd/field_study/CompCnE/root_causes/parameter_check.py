# docs/source/getting_started/examples/application/phd/field_study/CompCnE/root_causes/parameter_check.py
"""Helper scipt to check if parameters were parsed as intended.
"""
import importlib
import os

import pandas as pd

from tessif import parse
from tessif.frused.paths import doc_dir
from tessif.frused.hooks.tsf import reparameterize_components

PERIODS = 8760
EXPANSION = True


FOLDER = "expansion_results"
FOLDER = "modified_expansion_results"

# define the softwares to be used
SOFTWARES = ["cllp", "fine", "omf", 'ppsa', ]
HOOK_PYPSA = True

if FOLDER == "modified_expansion_results":
    HOOK_PYPSA = True

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


file_location = os.path.join(PARENT, "root_causes")
if FOLDER == "expansion_results":

    # CHP component parameters:

    for transformer in tessif_CompCnE.transformers:
        if transformer.uid.name == "Hard Coal CHP":
            tessif_hc_chp = transformer

    chp_params = pd.Series(tessif_hc_chp.attributes)
    chp_params.name = "Parameter Values"
    chp_params.index.name = "Parameter"
    fle = os.path.join(file_location, "chp_tessif_params.csv")
    chp_params.to_csv(fle)

    cllp_es = transformed_CompCnE_combinations["cllp"]
    fine_es = transformed_CompCnE_combinations["fine"]
    omf_es = transformed_CompCnE_combinations["omf"]
    ppsa_es = transformed_CompCnE_combinations["ppsa"]

    # CHP and emissions
    parsed_link_carriers = ppsa_es.links["carrier"]
    fle = os.path.join(file_location, "chp_carriers_added.csv")
    parsed_link_carriers.to_csv(fle)

    parsed_carriers = ppsa_es.carriers
    fle = os.path.join(file_location, "chp_allcarrier_emisisons.csv")
    parsed_carriers.to_csv(fle)

    # print(ppsa_es.storage_units["cyclic_state_of_charge"])

if FOLDER == "modified_expansion_results":

    # Storage component parameters:

    for storage in tessif_CompCnE.storages:
        if storage.uid.name == "Battery":
            tessif_battery = storage

    storage_params = pd.Series(tessif_battery.attributes)
    storage_params.name = "Parameter Values"
    storage_params.index.name = "Parameter"
    fle = os.path.join(file_location, "storage_tessif_params.csv")
    storage_params.to_csv(fle)

    ppsa_es = transformed_CompCnE_combinations["ppsa"]

    # Storage and emissions
    parsed_storage_carriers = ppsa_es.storage_units["carrier"]
    fle = os.path.join(file_location, "storage_carriers_added.csv")
    parsed_storage_carriers.to_csv(fle)
    print(parsed_storage_carriers)

    parsed_carriers = ppsa_es.carriers
    fle = os.path.join(file_location, "storage_allcarrier_emisisons.csv")
    parsed_carriers.to_csv(fle)
    print(parsed_carriers)
