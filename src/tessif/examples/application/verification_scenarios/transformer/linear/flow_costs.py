import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_rates

# three sources, two transformers, two sinks
# source1 feed transformers with fuel
# transformers transforms fuel into heat and electricity (same conversion) with same flow_cost for fuel but different flow_cost for electricity
# transformer outflows heat goes into sink1 and electricity to sink2 with forced flow_rate of electricity
# source2 and source 3 feeds sinks directly with high flow_costs
# expected behaviour: transformer2 feeds sinks electricity demand as the cheapest energy flow

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('fuel', ),
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('heat', ),
            'flow_costs': {'heat': 100, },
        },
        'sourceC': {
            'name': 'source3',
            'outputs': ('electricity', ),
            'flow_costs': {'electricity': 100, },
        },
    },
    'transformers': {
        'transformerA': {
            'name': 'transformer1',
            'inputs': ['fuel', ],
            'outputs': ['heat', 'electricity', ],
            'conversions': {
                ('fuel', 'heat'): 0.5,
                ('fuel', 'electricity'): 0.5,
            },
            'flow_costs': {
                'fuel': 1,
                'heat': 0,
                'electricity': 1,
            }
        },
        'transformerB': {
            'name': 'transformer2',
            'inputs': ['fuel', ],
            'outputs': ['heat', 'electricity', ],
            'conversions': {
                ('fuel', 'heat'): 0.5,
                ('fuel', 'electricity'): 0.5,
            },
            'flow_costs': {
                'fuel': 1,
                'heat': 0,
                'electricity': 0,
            }
        },
    },
    'sinks': {
        'sinkA': {
            'name': 'sink1',
            'inputs': ('heat',),
        },
        'sinkB': {
            'name': 'sink2',
            'inputs': ('electricity',),
            'flow_rates': {
                'electricity': nts.MinMax(min=10, max=10),                          # force a flow rate of exactly 10
            },
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'bus1',
            'inputs': ('source1.fuel',),
            'outputs': ('transformer1.fuel', 'transformer2.fuel'),
        },
        'busB': {
            'name': 'centralbus',
            'inputs': ('transformer1.heat', 'transformer1.electricity', 'transformer2.heat', 'transformer2.electricity', 'source2.heat', 'source3.electricity',),
            'outputs': ('sink1.heat', 'sink2.electricity',),
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
}  # minimum working example transformer - linear - flow_rates
