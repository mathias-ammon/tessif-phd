import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# initial_status

#

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # 'flow_costs': {'electricity': 2},                           # higher flow_costs than source2
            'flow_rates': {'electricity': nts.MinMax(min=0, max=100)},
            'milp': {'electricity': True},
            'initial_status': True,
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            # 'flow_costs': {'electricity': 1},                           # flow_costs lower than source1
            'flow_rates': {'electricity': nts.MinMax(min=0, max=100)},
            'milp': {'electricity': True},
            'initial_status': False,
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # force an inflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
    },
    'storages': {},
    'busses': {
        'busA': {
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
}  # minimum working example source - milp - initial_status
