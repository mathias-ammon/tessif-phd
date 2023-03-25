import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_costs

# two sources, sink, two storages
# sink demands a consistent inflow of 10
# source1 highest flow_costs, no limited flow_rate (just for meeting sinks demand in case of no storage is simulated) and goes directrly in to sink
# source2 feeds both storages
# storage1 has higher flow_costs, storage2 has lower flow_costs
# expected behaviour: storage2 will feed sink all time

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 10},                                       # flow_costs higher than storage
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},              # force an inflow of exactly 10
        },
    },
    'storages': {
        'storageA': {
            'name': 'storage1',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            'flow_costs': {'electricity': 5},                                       # costs lower than storage 2 and source
        },
        'storageB': {
            'name': 'storage2',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            'flow_costs': {'electricity': 0},                                       # costs higher than storage1 but lower than source
        },
    },
    'busses': {
        'busA': {
            'name': 'bus1',
            'inputs': ('source2.electricity',),
            'outputs': ('storage1.electricity', 'storage2.electricity',),
            'component': 'bus',
        },
        'busB': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'storage1.electricity', 'storage2.electricity',),
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
}  # minimum working example storage - linear - flow_costs
