import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# gradient_costs_positive

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 1},  # flow_costs > 0 (higher than source_2)
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=float('+inf'), negative=float('+inf'))
            },
            'gradient_costs': {
                'electricity':
                    nts.PositiveNegative(positive=0, negative=0)
            },
            'timeseries': {
                'electricity':
                    nts.MinMax(min=[10, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                               max=[10, 10, 10, 10, 10, 10, 10, 10, 10, 10])
            },
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('electricity',),
            'flow_costs': {'electricity': 0},  # flow_costs = 0 (default)
            'flow_gradients': {
                'electricity':
                    nts.PositiveNegative(positive=1, negative=float('+inf'))
            },
            'gradient_costs': {
                'electricity':
                    nts.PositiveNegative(positive=2, negative=0)
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
}  # minimum working example source - linear - gradient_costs_positive

# gradient_costs_advanced

# three sources, one sink
# due to flow costs starting flow: source_1 to sink
# due to change flow costs there will be a change in flow from sources to sink
# difference between source_2 and sorce_3 are gradient costs
# expected behaviour: s1 will feed the sink until rise of flow costs, afterwards the source with cheaper gradient costs will feed the sink

mapping_advanced = {
    'sources': {
	    'source_1': {
		    'name': 'source_1',
			'outputs': ('electricity',),
			'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},               # flow_rate between 0 and 10 (same as sink)
			'flow_costs': {'electricity': [0, 0, 0, 0, 0, 10, 10, 10, 10, 10]},     # flow_costs force a change in terms fo the active source
			'gradient_costs': {
			    'electricity': nts.PositiveNegative(positive=0, negative=0)},       # zero gradient costs (default)
		},
		'source_2': {
			'name': 'source_2',
			'outputs': ('electricity',),
			'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},               # flow_rate between 0 and 10 (same as sink)
			'flow_costs': {'electricity': [10, 10, 10, 10, 10, 0, 0, 0, 0, 0]},     # flow_costs force a change in terms fo the active source
			'gradient_costs': {
			    'electricity': nts.PositiveNegative(positive=2, negative=2)},       # high gradient costs
		},
		'source_3': {
			'name': 'source_3',
			'outputs': ('electricity',),
			'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},               # flow_rate between 0 and 10 (same as sink)
			'flow_costs': {'electricity': [10, 10, 10, 10, 10, 0, 0, 0, 0, 0]},     # flow_costs force a change in terms fo the active source
			'gradient_costs': {
				'electricity': nts.PositiveNegative(positive=1, negative=1)},       # low gradient costs
	    },
    },
	'transformers': {},
	'sinks': {
		'sink': {
			'name': 'sink',
			'inputs': ('electricity',),
			'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},              # force a flow rate of exactly 10
		},
	},
	'storages': {},
	'busses': {
		'bus': {
			'name': 'central_bus',
			'inputs': ('source_1.electricity', 'source_2.electricity','source_3.electricity',),
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
}   # minimum working example source - linear - gradient_costs