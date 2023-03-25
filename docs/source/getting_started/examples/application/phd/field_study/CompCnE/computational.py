# change spellings_logging_level to debug to declutter output
import pandas as pd
import os
from tessif.frused.paths import doc_dir, write_dir
import tessif.analyze
from tessif import parse
from tessif.frused.hooks.tsf import reparameterize_components


import tessif.frused.configurations as configurations
configurations.spellings_logging_level = 'debug'

PARENT = "CompCnE"
SOFTWARES = ('cllp', 'fine', 'omf', 'ppsa', )
# SOFTWARES = ('cllp',)

PERIODS = 8760
EXPANSION = False

FOLDER = "commitment_results"
# FOLDER = "expansion_results"
# FOLDER = "modified_expansion_results"

# FOLDER = "trivia_results"

if FOLDER == "modified_expansion_results":
    HOOK_PYPSA = True
else:
    HOOK_PYPSA = False


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


hook = None
if HOOK_PYPSA:
    hook = reparam_ppsa

# locate the storage directory
parent_location = os.path.join(
    doc_dir, "source", "getting_started", "examples", "application",
    "phd", "field_study", PARENT
)

result_path = os.path.join(parent_location, FOLDER)
creation_path = os.path.join(parent_location, "creation.py")

creation_module = parse.python_file(creation_path)
tessif_CompCnE = creation_module.create_compcne_es(
    periods=PERIODS, expansion=EXPANSION)

output_msg = tessif_CompCnE.to_hdf5(
    directory=os.path.join(write_dir, 'tsf'),
    filename='es_to_compare.hdf5',
)


# let the comparatier do the auto comparison:
memory_results = {}
for software in SOFTWARES:

    dct = tessif.analyze.trace_memory(
        path=os.path.join(write_dir, 'tsf', 'es_to_compare.hdf5'),
        parser=tessif.parse.hdf5,
        model=software,
        hook=hook,
    )

    memory_df = pd.DataFrame(
        data=dct.values(), index=dct.keys(), columns=(software,))
    memory_df = memory_df.divide(1e6).round(0)
    memory_df.index.name = "Memory [MB]"
    memory_df.rename(index={'simulation': 'optimization'}, inplace=True)
    csv_path = os.path.join(result_path, "_".join(
        [software, "memory_results.csv"]))
    memory_df.to_csv(csv_path)

print("memory results obtianed")

timing_results = {}
for software in SOFTWARES:

    dct = tessif.analyze.stop_time(
        path=os.path.join(write_dir, 'tsf', 'es_to_compare.hdf5'),
        parser=tessif.parse.hdf5,
        model=software,
        measurement='wall',
        hook=hook,
    )

    timings_df = pd.DataFrame(
        data=dct.values(), index=dct.keys(), columns=(software,))
    timings_df = timings_df.round(1)
    timings_df.index.name = "Timings [s]"
    timings_df.rename(index={'simulation': 'optimization'}, inplace=True)
    csv_path = os.path.join(result_path, "_".join(
        [software, "timings_results.csv"]))
    timings_df.to_csv(csv_path)

print("timing results obtianed")
