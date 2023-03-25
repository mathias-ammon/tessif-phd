import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expandable

# two sources, one sink
# sources are parametrized same with expandable contraint as exception (one true, one false)
# accumulated flow_rate of sources is lower than demand of sink
# expected behaviour: source2 will be expanded to meet demand of sink

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # flow_rate between 0 and 5
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},
            'expandable': {'electricity': False},
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            # flow_rate between 0 and 5
            'flow_rates': {'electricity': nts.MinMax(min=5, max=5)},
            'flow_costs': {'electricity': 1},
            'expandable': {'electricity': True},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # force an inflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=15, max=15)},
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
}  # minimum working example source - expansion - expandable
