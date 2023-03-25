import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_rates

# two sources, one sink
# sources differ in parametrization of flow_rate and flow_costs
# source_1 has a max flow rate with a lower value than the sinks demand
# source_2 has infinite flow rate (default parametrization) but higher flow costs than source_1
# expected behaviour:   source_1 will feed the sink with max flow rate, remaining demand will be fed by source_2
#                       (-> the flow rate argument will cap the flow from source_1)

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=float('+inf'))},    # flow_rate unlimited (default)
            'flow_costs': {'electricity': 1},                                       # flow_costs > 0
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=35)},               # max flow_rate unlimited
            'flow_costs': {'electricity': 0},                                       # flow_costs = 0 (default)
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=50, max=50)},              # force a flow rate of exactly 50
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
}  # minimum working example source - linear - flow_rates_max
