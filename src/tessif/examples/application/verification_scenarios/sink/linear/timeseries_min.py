import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# timeseries_min

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # force a flow rate of exactly 50
            'flow_rates': {'electricity': nts.MinMax(min=50, max=50)},
            'timeseries': {'electricity': nts.MinMax(min=10*[50], max=10*[50])},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_costs': {'electricity': 1},  # flow_costs > 0
            "flow_rates": {"electricity": nts.MinMax(0, 50)},
            'timeseries': {
                'electricity': nts.MinMax(
                    min=[50, 40, 30, 20, 10, 0, 0, 0, 0, 0, ],
                    max=10*[50]
                )
            },    # min flow_rate due to timeseries
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'flow_costs': {'electricity': 0},  # flow_costs = 0
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
}  # minimum working example sink - linear - timeseries_min
