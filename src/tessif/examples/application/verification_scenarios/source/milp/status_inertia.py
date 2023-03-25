import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# status_inertia

#

mapping = {
    'sources': {
        'source_1': {
            'name': 'source_1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': [1, 1, 1, 1, 1, 3, 3, 3, 3, 3]},  # costs split in low and high during timeseries
        },
        'source_2': {
            'name': 'source_2',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': 2},                               # costs between low and high costs from source_1
        },
    },
    'transformers': {},
    'sinks': {
        'sink': {
            'name': 'sink',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},      # force an inflow of exactly 10
        },
    },
    'storages': {},
    'busses': {
        'bus': {
            'name': 'central_bus',
            'inputs': ('source_1.electricity', 'source_2.electricity',),
            'outputs': ('sink.electricity',),
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
}  # minimum working example source - milp - status_inertia