import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_gradients

# three sources, one sink
# sources differ from each other in parametrization of flow_gradients and flow_costs
# flow gradients are chosen to be transient between s1 and s2 but not transient between s2 and s3
# due to the flow cost parameter, two changes are forced: 1) from s1 to s2 and 2) from s2 to s3
# expected behaviour:

# ------------------
# NEEDS MORE TESTING and version without flow costs list
# maybe work with additional storage, that feeds sink in case of non matching flow_gradients?
# what happens without storage?
# ------------------

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},                           # flow_costs > 0 (higher than source_2)
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))
            },
            'timeseries': {
                'electricity':
                    nts.MinMax(min=[10, 0, 0, 0, 0, 0, 0, 0, 0, 0],     # source_1 is forced to be active at the start
                               max=[10, 10, 10, 10, 10, 10, 10, 10, 10, 10])
            },
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 0},                           # flow_costs = 0 (default)
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=1, negative=1)        # flow_gradients = 1
            },
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
                    'emissions': float('+inf'),
                    'material': float('+inf')},
    },
}  # minimum working example source - linear - flow_gradients_positive

# flow_gradients --- ADVANCED ---

# three sources, one sink
# sources differ from each other in parametrization of flow_gradients and flow_costs
# flow gradients are chosen to be transient between s1 and s2 but not transient between s2 and s3
# due to the flow cost parameter, two changes are forced: 1) from s1 to s2 and 2) from s2 to s3
# expected behaviour:

# ------------------
# NEEDS MORE TESTING
# maybe work with additional storage, that feeds sink in case of non matching flow_gradients?
# what happens without storage?
# ------------------

mapping_advanced = {
    'sources': {
        'source1': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': [0, 0, 0, 1, 1, 1, 1, 1, 1, 1]},  # force s1 to be chosen in timestep 1-3
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=5, negative=5)},          # negative fg equals positive fg of source_2
        },
        'source2': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': [1, 1, 1, 0, 0, 0, 0, 1, 1, 1]},  # force s1 to be chosen in timestep 4-7
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=5, negative=10)},         # negative fg differs from positive fg of source_3
        },
        'source3': {
            'name': 'source3',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]},  # force s1 to be chosen in timestep 8-10
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=5, negative=5)},
        },
    },
    'transformers': {},
    'sinks': {
        'sink': {
            'name': 'sink',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
    },
    'storages': {},
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity', 'source3.electricity',),
            'outputs': ('sink.electricity',),
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
}  # minimum working example source - linear - flow gradients
