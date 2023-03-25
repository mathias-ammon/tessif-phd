import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_emissions

# two sources, one sink
# source 1 has constant emissions and low flow costs
# source 2 has zero emissions and high flow costs
# sink has a constant demand of flow entities (flow rate), which is as high as the outflow rate from each source
# global constraint: emission limit set to a value that will be reached in the timeframe
# expected behaviour: source_1 (cheap source) will feed the sink until emission limit is reached, source_2 will continue

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 0},                           # flow_costs set to zero (lower than source_2)
            'flow_emissions': {'electricity': 1},                       # flow_emissions set > 0 (specific value: 1 emission per flow entity)
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},                           # flow_costs higher than source_1
            'flow_emissions': {'electricity': 0},                       # flow_emissions set to zero (lower than source_1)
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
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
                    'emissions': 50,                                    # global emission constraint set to a limit
                    'material': float('+inf')},
    },
}  # minimum working example source - linear - flow emissions
