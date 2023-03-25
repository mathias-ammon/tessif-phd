import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# accumulated_amounts

# one source, two sinks
# sink 1 is cheaper (flow_costs) but has limited amount of flow entities available (accumulated amounts)
# sink 2 is more expensive than s1 but has unlimited amount of flow entities
# source has a constant outflow of flow entities (flow rate), which is as high as the inflow (demand) of each sink
# expected behaviour: source is fed by sink1 until empty, then fed by sink2

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},  # force an outflow of exactly 10
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'accumulated_amounts': {
                'electricity': nts.MinMax(min=0, max=50)},              # limited accumulated amount
            'flow_costs': {'electricity': 0},                           # cheap flow costs (default)
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'accumulated_amounts': {
                'electricity': nts.MinMax(min=0, max=float('+inf'))},   # unlimited accumulated amount
            'flow_costs': {'electricity': 10},                          # high flow_costs
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
