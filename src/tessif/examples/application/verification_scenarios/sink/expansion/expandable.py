import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expandable

# one source, two sinks
# sinks are parametrized same with expandable contraint as exception (one true, one false)
# cummulated flow_rate of sinks is lower than outflow of source
# expected behaiviour: sink2 will be expanded to meet demand of sink

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # force an outflow of exactly 15
            'flow_rates': {'electricity': nts.MinMax(min=15, max=15)},
            # 'timeseries': {'electricity': nts.MinMax(min=10*[15], max=10*[15])},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # flow_rate between 0 and 5
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},
            'expandable': {'electricity': False},
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            # flow_rate between 0 and 5
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},
            'expandable': {'electricity': True},
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
}  # minimum working example source - expansion - expandable
