import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_rates_min

# one source, two sinks
# sinks differ in parametrization of flow_rate and flow_costs
# sink1 has a unlimited flow rate
# sink2 has min flow rate with higher flow costs than sink1
# expected behaviour:   source1 will feed sink2 with min flow rate, remaining outflow will feed sink1
#                       (-> the flow rate argument will ensure the min flow from sink2)

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # force a flow rate of exactly 50
            'flow_rates': {'electricity': nts.MinMax(min=50, max=50)},
            'timeseries': {'electricity': nts.MinMax(min=10*[50], max=10*[50])},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # flow_rate unlimited
            'flow_rates': {'electricity': nts.MinMax(min=0, max=float('+inf'))},
            # flow_costs = 0
            'flow_costs': {'electricity': 0},
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            # flow_rate limited (min)
            # 'flow_rates': {'electricity': nts.MinMax(min=35, max=float('+inf'))},
            # flow_rate limited (min)
            'flow_rates': {'electricity': nts.MinMax(min=35, max=50)},
            # flow_costs > 0
            'flow_costs': {'electricity': 10},
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity',),
            'outputs': ('sink1.electricity', 'sink2.electricity',),
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
}  # minimum working example sink - linear - flow_rates_min
