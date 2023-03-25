import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# idle_changes

# source, sink, storage
# sink demands a consistent inflow of 10
# source high flow_costs but no limited flow_rate (default)
# storage has low flow_costs, initial_soc of 50 and idle_changes of 2.5 per timestep
# expected behaviour: storage will feed sink with a flow_rate 10 for first four timesteps, because after 4 timesteps 10 entities will be lost due to idle changes

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # flow_costs higher than storage
            'flow_costs': {'electricity': 0},
            'flow_rates': {'electricity': nts.MinMax(min=0, max=50)},
            'timeseries': {
                'electricity': nts.MinMax(
                    min=[15, 15, 15, 15, 15, 15, 15, 0, 0, 0, ],
                    max=[15, 15, 15, 15, 15, 15, 15, 0, 0, 0, ],
                )
            },    # charging the storage
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            # flow_costs higher than storage
            'flow_costs': {'electricity': 2},
            'flow_rates': {'electricity': nts.MinMax(min=0, max=50)},
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
            'capacity': 220,
            'initial_soc': 0,
            # costs = 0
            'flow_rates': {'electricity': nts.MinMax(min=0, max=5)},
            # stored energy enough to meet demand during last 3 timesteps
            # outflow limit, however, causes the more expensive souce2
            # to provide 5 energy units for each of the remaining 3 timesteps.
        },
    },
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity', 'storage1.electricity'),
            'outputs': ('sink1.electricity', 'storage1.electricity',),
            'component': 'bus',
        },
    },
    'timeframe': {
        'primary': pd.date_range('01/01/2022', periods=10, freq='H'),
    },
    'global_constraints': {
        'primary': {'name': 'default',
                    'emissions': 22,
                    'material': float('+inf')},
    },
}  # minimum working example storage - linear - flow_rates_max.py
