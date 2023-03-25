import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_efficiencies

# two sources, sink, storage
# sink demands a consistent inflow of 10
# source1 high flow_costs but no limited flow_rate (default) flows directly into sink
# source2 with no flow costs but capped flow rate (10) feeds storage
# storage has no flow_costs and a efficiency of 0.8 (means an outflow of 8 entities causes a decrease of 10 in storage)
# expected behaviour: storage will feed sink with a flow_rate of 8 (10 go in, 8 go out due to efficiency) and source1 will deliver 2 to meet demand of sink

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # flow_costs higher than storage
            'flow_costs': {'electricity': 10},
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            # flow_costs higher than storage
            'flow_costs': {'electricity': 8},
            # flow_rate of max 10
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # force an inflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
    },
    'storages': {
        'storageA': {
            'name': 'storage1',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 100,
            # costs = 0
            'flow_costs': {'electricity': 0},
            # flow_efficiency <0 in outflow
            'flow_efficiencies': {'electricity': nts.InOut(inflow=1, outflow=0.8)},
        },
    },
    'busses': {
        'busA': {
            'name': 'bus1',
            'inputs': ('source2.electricity',),
            'outputs': ('storage1.electricity',),
            'component': 'bus',
        },
        'busB': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'storage1.electricity',),
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
}  # minimum working example storage - linear - flow_efficiencies
