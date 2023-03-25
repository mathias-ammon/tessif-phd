import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expansion_costs

# one source, two sinks
# sinks are parametrized same with expansion_costs as exception (costs sink2 < sink1)
# cummulated flow_rate of sinks is lower than outflow of source
# expected behaiviour: sink2 will be expanded due to lower expansion costs to meet outflow of source

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # force an inflow of exactly 15
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
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            # flow_rate between 0 and 5
            'flow_rates': {'electricity': nts.MinMax(min=5, max=5)},
            'expandable': {'electricity': True},
            'expansion_costs': {'electricity': 1},
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
}  # minimum working example source - expansion - expansion_costs
