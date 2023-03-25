import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# gradient_costs

# one source, three sinks
# due to flow costs starting flow: source to sink_1
# due to change flow costs there will be a change in flow from source to sinks
# difference between sink_2 and sink_3 are gradient costs
# expected behaviour:source feed sink_1 until rise of flow costs, afterwards the sink with cheaper gradient costs will be fed

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},  			# force a flow rate of exactly 10
        },
    },
    'transformers': {},
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},  				# flow_rate between 0 and 10 (same as source)
            'flow_costs': {'electricity': [0, 0, 0, 0, 0, 10, 10, 10, 10, 10]},		# flow_costs force a change in terms fo the active sink
            'gradient_costs': {
                'electricity': nts.PositiveNegative(positive=0, negative=0), },  	# zero gradient costs (default)
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},  				# flow_rate between 0 and 10 (same as source)
            'flow_costs': {'electricity': [10, 10, 10, 10, 10, 0, 0, 0, 0, 0]},		# flow_costs force a change in terms fo the active sink
            'gradient_costs': {
                'electricity': nts.PositiveNegative(positive=2, negative=2)},  		# high gradient costs
        },
        'sinkC': {
            'name': 'sink3',
            'inputs': ('electricity',),
            'flow_rates': {'electricity': nts.MinMax(min=0, max=10)},  				# flow_rate between 0 and 10 (same as source)
            'flow_costs': {'electricity': [10, 10, 10, 10, 10, 0, 0, 0, 0, 0]},		# flow_costs force a change in terms fo the active sink
            'gradient_costs': {
                'electricity': nts.PositiveNegative(positive=1, negative=1)},  		# low gradient costs
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'centralbus',
            'inputs': ('source1.electricity',),
            'outputs': ('sink1.electricity', 'sink2.electricity', 'sink3.electricity',),
        },
    },
    'timeframe': {
        'primary': pd.date_range('01/01/2022', periods=10, freq='H'),
    },
    'global_constraints': {
        'primary': {
            'name': 'default',
            'emissions': float('+inf'),
            'material': float('+inf')},
    },
}  # minimum working example sink - linear - gradient_costs
