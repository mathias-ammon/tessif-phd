import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# costs_for_beeing_active

#

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': [1, 1, 1, 1, 1, 3, 3, 3, 3, 3]},  # costs split in low and high during timeseries
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': 2},                               # costs between low and high costs from source1
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},      # force an inflow of exactly 10
        },
    },
    'storages': {},
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity',),
            'outputs': ('sink1.electricity',),
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
}  # minimum working example source - milp - costs_for_beeing_active