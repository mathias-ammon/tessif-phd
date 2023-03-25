import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_gradients_positive


mapping = {
    'sources': {
        'sources': {
            'sourceA': {
                'name': 'source1',
                'outputs': ('electricity',),
                'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
            },
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_costs': {'electricity': 10},                           # flow_costs > 0 (higher than source_2)
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))
            },
            'timeseries': {
                'electricity':
                    nts.MinMax(min=[10, 0, 0, 0, 0, 0, 0, 0, 0, 0],     # sink_1 is forced to be active at the start
                               max=[10, 10, 10, 10, 10, 10, 10, 10, 10, 10])
            },
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'flow_costs': {'electricity': 0},                           # flow_costs = 0 (default)
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=2, negative=2)        # flow_gradients = 2
            },
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity',),
            'outputs': ('sink1.electricity', 'sink2.electricity',),
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
}  # minimum working example source - linear - flow_gradients_positive
