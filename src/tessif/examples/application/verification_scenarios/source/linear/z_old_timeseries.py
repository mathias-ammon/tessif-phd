import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_rates

# two sources, one sink
# sources differ in parametrization of flow_costs and a given timeseries for source1
# source2 has infinite flow rate (default parametrization) but higher flow costs than source1
# expected behaviour:   source1 will feed the sink with max flow rate, remaining demand will be fed by source2
#                       (-> the timeseries argument will define the flow from source1)

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 0},                                       # flow_costs = 0
            'timeseries': {'electricity': nts.MinMax(min=[50, 40, 30, 20, 10, 0, 0, 0, 0, 0, ],
                                                     max=[50, 40, 30, 20, 10, 0, 0, 0, 0, 0, ])},  # forced flow_rate due to timeseries
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},                                       # flow_costs > 0
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
}  # minimum working example source - linear - timeseries
