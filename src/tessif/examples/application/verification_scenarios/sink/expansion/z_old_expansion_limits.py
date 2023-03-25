import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expansion_limits

# one source, two sinks
# sinks are parametrized same with expansion_costs and limits as exception (costs sink2 < sink1, only sink2 is limited)
# cummulated flow_rate of sinks is lower than outflow of source1
# expected behaiviour: sink2 will be expanded to limit (due to lower costs) and sink1 fill up to meet outlfow of source1

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=15, max=15)},          # force an outflow of exactly 10
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},            # flow_rate between 0 and 5
            'expandable': {'electricity': True},
            'expansion_costs': {'electricity': 5},
            'expansion_limits': {'electricity': nts.MinMax(min=5, max=float('+inf'))},
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},            # flow_rate between 0 and 5
            'expandable': {'electricity': True},
            'expansion_costs': {'electricity': 1},
            'expansion_limits': {'electricity': nts.MinMax(min=5, max=7)}
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
}  # minimum working example source - expansion - expansion_limits