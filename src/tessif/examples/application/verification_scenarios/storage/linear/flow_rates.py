import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_rates

# source, sink, storage
# sink demands a consistent inflow of 10
# source high flow_costs but no limited flow_rate (default)
# storage has low flow_costs and limited flow_rate of 5
# initial_soc of storage of 20
# expected behaviour: storage will feed sink with a flow_rate 5 (other 5 by source) unitl empty, aferwards just source

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},                                   # flow_costs higher than storage
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 0},                                   # flow_costs higher than storage
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},          # force an inflow of exactly 10
        },
    },
    'storages': {
        'storageA': {
            'name': 'storage1',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},            # flow_rate between 0 and 5 (same as sink)
            'flow_costs': {'electricity': 0},                                   # costs = 0
        },
    },
    'busses': {
        'busA': {
            'name': 'bus1',
            'inputs': ('source2.electricity', 'storage.electricity'),
            'outputs': ('storage1.electricity',),
            'component': 'bus',
        },
        'busB': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'storage1.electricity'),
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
}  # minimum working example storage - linear - flow_rates
