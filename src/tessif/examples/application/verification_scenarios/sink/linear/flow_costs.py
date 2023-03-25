import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_costs

# one source, two sinks
# source has a constant outflow of entities (flow rate), which is as high as the demand of each sink
# sink1 has higher flow_costs thank sink2
# sinks equal each other beside that
# expected behaviour: cheapest sink will be fed

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            # force an outflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
            'timeseries': {'electricity': nts.MinMax(min=10*[10], max=10*[10])},
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # costs higher than sink2
            'flow_costs': {'electricity': 10},
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            # costs lower than sink 1
            'flow_costs': {'electricity': 0},
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity',),
            'outputs': ('sink1.electricity', 'sink2.electricity',),
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
}  # minimum working example sink - linear - flow costs

# flow_costs_advanced

# one source, two sinks
# source has a constant outflow of entities (flow rate), which is as high as the demand of each sink
# sink 1 has low flow costs in the first half of the timeseries and higher costs in the second half
# sink 2 has constant flow costs which are between the two values of sink 1
# sinks equal each other beside that
# expected behaviour: cheapest sink will be fed; sink 1 first half, sink 2 second half

mapping_advanced = {
    'sources': {
        'source': {
            'name': 'source',
            'outputs': ('electricity',),
            # force an outflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
    },
    'transformers': {},
    'sinks': {
        'sink1': {
            'name': 'sink1',
            'inputs': ('electricity',),
            # flow_rate between 0 and 10 (same as source)
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
            # costs split in low and high during timeseries
            'flow_costs': {'electricity': [1, 1, 1, 1, 1, 3, 3, 3, 3, 3]},
        },
        'sink2': {
            'name': 'sink2',
            'inputs': ('electricity',),
            # flow_rate between 0 and 10 (same as source)
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},
            # costs between low and high costs from sink_1
            'flow_costs': {'electricity': 2},
        },
    },
    'storages': {},
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('source.electricity',),
            'outputs': ('sink1.electricity', 'sink2.electricity',),
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
}  # minimum working example sink - linear - flow costs
