import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expansion_limits

# two sources, one sink
# sources are parametrized same with expansion_costs and limits as exception (costs source2 < source1, only source2 is limited)
# cummulated flow_rate of sources is lower than demand of sink
# expected behaiviour: source2 will be expanded to limit (due to lower costs) and source 1 fill up to meet demand of sink

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},        # flow_rate between 0 and 5
            'expandable': {'electricity': True},
            'expansion_costs': {'electricity': 5},
            'expansion_limits': {'electricity': nts.MinMax(min=5, max=float('+inf'))},
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},        # flow_rate between 0 and 5
            'expandable': {'electricity': True},
            'expansion_costs': {'electricity': 1},
            'expansion_limits': {'electricity': nts.MinMax(min=5, max=7)}
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=15, max=15)},      # force an inflow of exactly 10
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
}  # minimum working example source - expansion - expansion_limits
