import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_costs

# two sources, one sink
# source2 has lower flow_costs than source1
# sources equal each other beside that
# sink has a constant demand of flow entities (flow rate), which is as high as the outflow rate from each source
# expected behaviour: cheapest source feeds the sink (source2)

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 2},                               # costs higher than source2
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},                               # costs lower than source1
        },
    },
    'transformers': {},
    'sinks': {
        'sink': {
            'name': 'sink',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},      # force an inflow of exactly 10
        },
    },
    'storages': {},
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity',),
            'outputs': ('sink.electricity',),
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
}  # minimum working example source - linear - flow costs


# two sources, one sink
# source 1 has low flow costs in the first half of the timeseries and higher costs in the second half
# source 2 has constant flow costs which are between the two values of source 1
# sources equal each other beside that
# sink has a constant demand of flow entities (flow rate), which is as high as the outflow rate from each source
# expected behaviour: cheapest source feeds the sink; source 1 first half, source 2 second half

mapping_advanced = {
    'sources': {
        'source1': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': [1, 1, 1, 1, 1, 3, 3, 3, 3, 3]},  # costs split in low and high during timeseries
        },
        'source2': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},       # flow_rate between 0 and 10 (same as sink)
            'flow_costs': {'electricity': 2},                               # costs between low and high costs from source_1
        },
    },
    'transformers': {},
    'sinks': {
        'sink': {
            'name': 'sink',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},      # force an inflow of exactly 10
        },
    },
    'storages': {},
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('source1.electricity', 'source2.electricity',),
            'outputs': ('sink.electricity',),
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
}  # minimum working example source - linear - flow costs