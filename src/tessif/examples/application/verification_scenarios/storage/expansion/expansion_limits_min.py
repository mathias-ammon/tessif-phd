import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expansion_limits_min

# source, sink, storage


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
                    min=[50, 0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                    max=[50, 0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                )
            },    # charging the storage
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            # flow_costs higher than storage
            'flow_costs': {'electricity': 100},
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
            'capacity': 1,
            'initial_soc': 0,
            'flow_rates': {'electricity': nts.MinMax(min=0, max=1)},
            "expandable": {"electricity": True, "capacity": True},
            "expansion_costs": {"electricity": 0, "capacity": 10},
            "expansion_limits": {
                "electricity": nts.MinMax(min=0, max=10),
                "capacity": nts.MinMax(min=3, max=10),
            }
            # storage 1 or 2 needs to be expanded to store source1's energy
            # at timestep 1
        },
        'storageB': {
            'name': 'storage2',
            'input': 'electricity',
            'output': 'electricity',
            'capacity': 1,
            'initial_soc': 0,
            'flow_rates': {'electricity': nts.MinMax(min=0, max=1)},
            'flow_costs': {'electricity': 2},
            "expandable": {"electricity": True, "capacity": True},
            "expansion_costs": {"electricity": 0, "capacity": 0.1},
            # storage 2 is cheaper to expand but storage 1 neeeds to be at
            # least at 3 units
        },
    },
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity', 'storage1.electricity', 'storage2.electricity'),
            'outputs': ('sink1.electricity', 'storage1.electricity', 'storage2.electricity'),
            'component': 'bus',
        },
    },
    'timeframe': {
        'primary': pd.date_range('01/01/2022', periods=10, freq='H'),
    },
    'global_constraints': {
        'primary': {'name': 'default',
                    'emissions': float("+inf"),
                    'material': float('+inf')},
    },
}  # minimum working example storage - expansion - expansion_limits_min.py
