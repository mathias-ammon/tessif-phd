import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# final_soc

# source, sink, storage
# sink demands a consistent inflow of 10
# source high flow_costs, storage low flow_costs
# initial_soc of storage below overall demand of sink
# expected behaviour: storage will feed sink until empty, source follows to continue

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},  # costs > 0
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},  # force an inflow of exactly 10
        },
    },
    'storages': {
        'storageA': {
            'name': 'storage1',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            'final_soc': 20,
            'flow_costs': {'electricity': 0},  # costs = 0
        },
    },
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'storage1.electricity'),
            'outputs': ('sink1.electricity', 'storage1.electricity',),
            'component': 'bus',
        },
    },
    'timeframe': {
        'primary': pd.date_range('01/01/2022', periods=10, freq='H'),
    },
    'global_constraints': {
        'primary': {'name': 'default',
                    'emissions': float('+inf'),
                    'material': float('+inf')},
    },
}  # minimum working example storage - linear - initial_soc
