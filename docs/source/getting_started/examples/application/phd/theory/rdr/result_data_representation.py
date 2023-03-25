import importlib
import matplotlib.pyplot as plt

from pathlib import Path

import tessif.simulate as optimize
from tessif.model.energy_system import AbstractEnergySystem as AES
from tessif import parse
from tessif.frused import configurations
from tessif.frused.paths import doc_dir
from tessif.transform.es2mapping import compile_result_data_representation
import tessif.visualize.nxgrph as nxv

# silence spellings mismatch warnings
configurations.spellings_logging_level = 'debug'

# construct the absolute path of the system model data
p = Path(doc_dir) / "source" / "getting_started" / "examples"
p = p / "application" / "phd" / "rdr" / "esm"
FOLDER = p.resolve()

# create the system model
es = AES.from_external(path=FOLDER, parser=parse.flat_config_folder)

# create the visual representation
drawing_data = nxv.draw_graph(
    es.to_nxgrph(),
    node_color={
        'CBES': '#666666',
        'CBE Bus': '#666666',
        'CHP': '#666666',

        'Heatline': '#b30000',
        'Heat Demand': '#b30000',

        'Power Demand': '#ffe34d',
        'Powerline': '#ffe34d',
    },
    node_size={
        'powerline': 5000,
        'district heating pipeline': 5000
    },
)
# plt.show()

software = "fine"
transformation_module = importlib.import_module(
    '.'.join(['tessif.transform.es2es', software]))

# 7. Transform the tessif system model into a fine system model:
software_es = transformation_module.transform(es)

# 8. Optimize the fine system model using fine's capabilities:
optimized_es = getattr(optimize, "_".join([software, "from_es"]))(software_es)

rdr = compile_result_data_representation(optimized_es, software, 'CHP')
print(rdr)
