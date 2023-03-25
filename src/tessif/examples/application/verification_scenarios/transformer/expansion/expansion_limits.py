import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# expansion_limits

# two sources, one transformers, two sinks
# source1 feeds transformer with fuel
# transformer transform fuel into heat and electricity
# transformer outflow heat goes into sink1 and electricity to sink2 with forced flow_rate of electricity due to demand of sink2
# transormer cant meet sinks electricity demand, but is expandable to a limit below sinks demand
# source2 feeds sinks directly but with highest flow_costs
# expected behaviour: transormers feed sinks electricity demand until limited fuel flow_rate is reached (5 entities electricity per timestep due to conversion) and expands to limit, leaving demand will be met by source2

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('fuel',),
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('heat', 'electricity',),
            'flow_costs': {
                'heat': 100,
                'electricity': 100,
            },
        },
    },
    'transformers': {
        'transformerA': {
            'name' : 'transformer1',
            'inputs': ['fuel',],
            'outputs': ['heat', 'electricity',],
            'conversions': {
                ('fuel', 'heat'): 0.5,
                ('fuel', 'electricity'): 0.5,
            },
            'flow_rates': {
                'fuel': nts.MinMax(min=0, max=10),
                'heat': nts.MinMax(min=0, max=float('+inf')),
                'electricity': nts.MinMax(min=0, max=float('+inf')),
            },
            'expandable': {
                'fuel': True,
                'heat': False,
                'electricity': False,
            },
            'expansion_costs': {
                'fuel': 1,
                'heat': 0,
                'electricity': 0,
            },
            'expansion_limits': {
                'fuel': nts.MinMax(min=0, max=16),
                'heat': nts.MinMax(min=0, max=float('+inf')),
                'electricity': nts.MinMax(min=0, max=float('+inf')),
            },
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
                'electricity': nts.MinMax(min=10, max=10),                          # force a flow rate of exactly 15
            },
        },
    },
    'storages': {},
    'busses': {
        'busA': {
            'name': 'bus1',
            'inputs': ('source1.fuel',),
            'outputs': ('transformer1.fuel',),
        },
        'busB': {
            'name': 'centralbus',
            'inputs': ('transformer1.heat', 'transformer1.electricity', 'source2.heat', 'source2.electricity',),
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
}  # minimum working example transformer - linear - expansion_limits
