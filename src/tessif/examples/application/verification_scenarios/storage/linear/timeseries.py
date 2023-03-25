import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_rates

# source, sink, storage
# sink demands a consistent inflow of 10
# source high flow_costs and no limited flow_rate (default)
# storage has forced flow_rate given in a timeseries with enough initial_soc to meet the accumulated outflow
# expected behaviour: storage will feed sink within given timeseries, source will deliver the rest to meet demand of sink

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},                                   # flow_costs higher than storage
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
            'initial_soc': 100,
            'timeseries': {'electricity': nts.MinMax(min=[1, 2, 3, 4, 5, 4, 3, 2, 1, 0,],
                                                     max=[1, 2, 3, 4, 5, 4, 3, 2, 1, 0,])},  # forced flow_rate
        },
    },
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'storage1.electricity'),
            'outputs': ('sink1.electricity', 'storage1.electricity',),
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
}  # minimum working example storage - linear - timeseries
