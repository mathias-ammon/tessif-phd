# change spellings_logging_level to debug to declutter output
import pandas as pd
import tessif.examples.data.tsf.py_hard as tsf_examples
import os
from tessif.frused.paths import doc_dir, write_dir
import tessif.analyze
from tessif import parse

import tessif.frused.configurations as configurations
configurations.spellings_logging_level = 'debug'


SOFTWARES = ('cllp', 'fine', 'omf', 'ppsa', )
# SOFTWARES = ('ppsa',)


PERIODS = 24
GRID_CAPACITY = 60000  # no congestion
GRID_CAPACITY = 20000  # congestion
# GRID_CAPACITY = 1  # Expansion
EXPANSION = False

PARENT = "TransCnE"

FOLDER = "commitment_nocongestion_results"
# FOLDER = "commitment_congestion_results"
# FOLDER = "expansion_results"

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

# locate the storage directory
parent_location = os.path.join(
    doc_dir, "source", "getting_started", "examples", "application",
    "phd", "model_scenario_combinations", PARENT
)

result_path = os.path.join(parent_location, FOLDER)
creation_path = os.path.join(parent_location, "creation.py")

creation_module = parse.python_file(creation_path)
tessif_TransCnE = creation_module.create_transcne_es(
    periods=PERIODS, expansion=EXPANSION, gridcapacity=GRID_CAPACITY)

output_msg = tessif_TransCnE.to_cfg(
    directory=os.path.join(write_dir, 'tsf', "transCnE"),
)


# let the comparatier do the auto comparison:
memory_results = {}
for software in SOFTWARES:

    if software == "ppsa":
        transops = TRANS_OPS
    else:
        transops = None

    dct = tessif.analyze.trace_memory(
        path=os.path.join(write_dir, 'tsf', 'transCnE'),
        # parser=tessif.parse.hdf5,
        parser=tessif.parse.flat_config_folder,
        model=software,
        trans_ops=transops,
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

    if software == "ppsa":
        transops = TRANS_OPS
    else:
        transops = None

    dct = tessif.analyze.stop_time(
        path=os.path.join(write_dir, 'tsf', 'es_to_compare.hdf5'),
        parser=tessif.parse.hdf5,
        model=software,
        measurement='wall',
        trans_ops=TRANS_OPS
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
