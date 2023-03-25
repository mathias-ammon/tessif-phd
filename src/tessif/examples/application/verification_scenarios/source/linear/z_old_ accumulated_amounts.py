import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# accumulated_amounts

# two sources, one sink
# source1 is cheaper but has limited amount of flow entities available (accumulated amounts)
# source2 is more expensive than s1 but has unlimited amount of flow entities
# sink has a constant demand of flow entities (flow rate), which is as high as the outflow rate from each source
# expected behaviour: sink is fed from s1 until empty, then fed from s2

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'accumulated_amounts': {
                'electricity': nts.MinMax(min=0, max=80)},              # limited accumulated amount of 80
            'flow_costs': {'electricity': 0},                           # cheap flow costs (default)
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'accumulated_amounts': {
                'electricity': nts.MinMax(min=0, max=float('+inf'))},   # unlimited accumulated amount
            'flow_costs': {'electricity': 1},                           # high flow_costs
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},  # force a flow rate of exactly 10
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
}  # minimum working example source - linear - accumulated amounts
