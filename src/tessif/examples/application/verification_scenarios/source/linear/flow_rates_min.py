import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_rates

# two sources, one sink
# sources differ in parametrization of flow_rate and flow_costs
# source_1 has a min flow rate with a lower value than the sinks demand
# source_2 has infinite flow rate (default parametrization) and lower flow costs than source_1
# expected behaviour:   source_1 will feed the sink with its min flow rate, remaining demand will be fed by source_2
#                       (-> the flow rate argument will force a flow from source_1)

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # min flow_rate
            'flow_rates': {'electricity': nts.MinMax(min=35, max=50)},
            # flow_costs > 0
            'flow_costs': {'electricity': 1},
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            # flow_rate unlimited (default)
            'flow_rates': {'electricity': nts.MinMax(min=0, max=float('+inf'))},
            # flow_costs = 0 (default)
            'flow_costs': {'electricity': 0},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # force a flow rate of exactly 50
            'flow_rates': {'electricity': nts.MinMax(min=50, max=50)},
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity',),
            'outputs': ('sink1.electricity',),
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
}  # minimum working example source - linear - flow_rates_min
