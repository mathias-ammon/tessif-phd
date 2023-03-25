import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

mapping = {
    'sources': {
        'so1': {
            'name': 'source-01',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
            'flow_costs': {'electricity': 1},
        },
        'so2': {
            'name': 'source-02',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
            'flow_costs': {'electricity': 1},
        },
    },
    'transformers': {
    },
    'sinks': {
        's1': {
            'name': 'sink-01',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=15)},
            'flow_costs': {'electricity': 1},
            'timeseries': {
                'electricity': nts.MinMax(
                    min=np.array([0, 15, 10]), max=np.array([0, 15, 10]))}
        },
        's2': {
            'name': 'sink-02',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=15)},
            'flow_costs': {'electricity': 1},
            'timeseries': {'electricity': nts.MinMax(
                min=np.array([15, 0, 10]), max=np.array([15, 0, 10]))}
        },
    },
    'storages': {
    },
    'busses': {
        'b1': {
            'name': 'bus-01',
            'inputs': ('source-01.electricity',),
            'outputs': ('sink-01.electricity',),
        },
        'b2': {
            'name': 'bus-02',
            'inputs': ('source-02.electricity',),
            'outputs': ('sink-02.electricity',),
        },
    },
    'connectors': {
        'c': {
            'name': 'connector',
            'interfaces': ('bus-01', 'bus-02'),
            'conversions': {
                ('bus-01', 'bus-02'): 0.9,
                ('bus-02', 'bus-01'): 0.8
            },
        },
    },
    'timeframe': {
        'primary': pd.date_range('7/13/1990', periods=3, freq='H'),
        'secondary': pd.date_range('10/03/2019', periods=3, freq='H'),
    },
    'global_constraints': {
        'primary': {'name': 'default',
                    'emissions': float('+inf'),
                    'resources': float('+inf')},
        'secondary': {'name': '80% reduction',
                      'emissions': 1000,
                      'resources': float('+inf')},
    },
}
