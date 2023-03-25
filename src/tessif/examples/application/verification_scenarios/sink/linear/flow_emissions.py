import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_emissions

# one source, two sinks
# sink 1 has constant emissions and low flow costs
# sink 2 has zero emissions and high flow costs
# source has a constant outflow of entities (flow rate), which is as high as the outflow rate from each source
# global constraint: emission limit set to a value that will be reached in the timeframe
# expected behaviour: sink_1 (cheap sink) will be fed from source until emission limit is reached, switch to sink_2 afterwards

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
            'timeseries': {'electricity': nts.MinMax(min=10*[10], max=10*[10])},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # flow_costs set to zero (lower than sink_2)
            'flow_costs': {'electricity': 0},
            # flow_emissions set > 0
            'flow_emissions': {'electricity': 1},
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            # flow_costs higher than source_1
            'flow_costs': {'electricity': 10},
            # flow_emissions set > 0
            'flow_emissions': {'electricity': 0},
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
                    # global emission constraint set to a limit
                    'emissions': 50,
                    'material': float('+inf')},
    },
}  # minimum working example sink - linear - flow emissions
