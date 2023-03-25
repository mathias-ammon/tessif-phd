import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# timeseries_max

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # flow_costs = 0
            'flow_costs': {'electricity': 0},
            'flow_rates': {'electricity': nts.MinMax(min=0, max=50)},
            'timeseries': {'electricity': nts.MinMax(min=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                                                     max=[50, 40, 30, 20, 10, 0, 0, 0, 0, 0, ])},  # forced flow_rate due to timeseries
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            # flow_costs > 0
            'flow_costs': {'electricity': 1},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # force a flow rate of exactly 50
            'flow_rates': {'electricity': nts.MinMax(min=50, max=50)},
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity',),
            'outputs': ('sink1.electricity',),
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
}  # minimum working example source - linear - timeseries_max
