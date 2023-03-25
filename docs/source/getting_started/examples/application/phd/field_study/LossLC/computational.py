# change spellings_logging_level to debug to declutter output
import tessif.analyze
import tessif.frused.configurations as configurations  # nopep8
configurations.spellings_logging_level = 'debug'


import tessif.examples.data.tsf.py_hard as tsf_examples  # nopep8

# Import path settings
from tessif.frused.paths import doc_dir  # nopep8
import os  # nopep8


PERIODS = 24
FOLDER = "results"
# EXPANSION = True
SOFTWARES = ('cllp', 'fine', 'omf', 'ppsa', )
# SOFTWARES = ('cllp',)
HOOK_PYPSA = False

# locate the storage directory
current_path = os.path.join(
    doc_dir, "source", "getting_started", "examples", "application",
    "phd", "model_scenario_combinations", "LossLC", FOLDER
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


hook = None
if HOOK_PYPSA:
    hook = reparam_ppsa

# Choose the underlying energy system
tsf_es = tsf_examples.create_component_es(periods=PERIODS)

# write it to disk, so the comparatier can read it out
import os  # nopep8
from tessif.frused.paths import write_dir  # nopep8

output_msg = tsf_es.to_hdf5(
    directory=os.path.join(write_dir, 'tsf'),
    filename='es_to_compare.hdf5',
)
# let the comparatier do the auto comparison:

import tessif.parse  # nopep8
import functools  # nopep8
from tessif.frused.hooks.tsf import reparameterize_components  # nopep8
import pandas as pd  # nopep8


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
    csv_path = os.path.join(current_path, "_".join(
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
    csv_path = os.path.join(current_path, "_".join(
        [software, "timings_results.csv"]))
    timings_df.to_csv(csv_path)

print("timing results obtianed")
