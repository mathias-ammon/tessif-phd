import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expansion_limits_max

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # force an outflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=15, max=15)},
            'timeseries': {'electricity': nts.MinMax(min=10*[15], max=10*[15])},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # flow_rate between 0 and 5
            'flow_rates': {'electricity': nts.MinMax(min=5, max=5)},
            'expandable': {'electricity': True},
            'expansion_costs': {'electricity': 5},
            # 'expansion_limits': {'electricity': nts.MinMax(min=0, max=10)},
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            # flow_rate between 0 and 5
            'flow_rates': {'electricity': nts.MinMax(min=5, max=5)},
            'expandable': {'electricity': True},
            'expansion_costs': {'electricity': 1},
            'expansion_limits': {'electricity': nts.MinMax(min=0, max=7)}
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity',),
            'outputs': ('sink1.electricity', 'sink2.electricity',),
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
}  # minimum working example source - expansion - expansion_limits_max
