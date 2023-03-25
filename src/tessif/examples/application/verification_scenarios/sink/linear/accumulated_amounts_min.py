import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# accumulated_amounts

# one source, two sinks
# source has a constant outflow of flow entities (flow rate)
# sink 1 is more expensive (flow_costs) and has minimum accumulated amounts
# sink 2 is cheaper than sink1 but has unlimited amount of flow entities available

# expected behaviour: source is fed by s1 until accumulated amount limit reached, then fed by s2

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},      # force an outflow of exactly 10
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'accumulated_amounts': {
                'electricity': nts.MinMax(min=50, max=float('+inf'))},      # minimum accumulated amounts
            'flow_costs': {'electricity': 10},                              # high flow costs
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'accumulated_amounts': {
                'electricity': nts.MinMax(min=0, max=float('+inf'))},       # unlimited accumulated amount
            'flow_costs': {'electricity': 0},                               # zero flow_costs (default)
        },
    },
    'storages': {},
    'busses': {
        'bus': {
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
}  # minimum working example sink - linear - accumulated amounts
