import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_costs_matze

# two sources, one sink, two transformers

mapping = {
    'sources': {
        'sourceA': {
            'name': 'source1',
            'outputs': ('chemical_energy',),
        },
        'sourceB': {
            'name': 'source2',
            'outputs': ('chemical_energy',),
        },
    },
    'transformers': {
        'transformerA': {
            'name': 'transformer1',
            'inputs': ('chemical_energy',),
            'outputs': ('electricity',),
            'conversions': {
                ('chemical_energy', 'electricity'): 1,
            },
            'flow_costs': {
                'chemical_energy': 0,
                'electricity': 1,
            },  # more expansive
            'flow_rates': {
                'chemical_energy': nts.MinMax(min=0, max=float("+inf")),
                'electricity': nts.MinMax(min=5, max=10),
            },  # and minimum flow rate
        },
        'transformerB': {
            'name': 'transformer2',
            'inputs': ('chemical_energy',),
            'outputs': ('electricity',),
            'conversions': {
                ('chemical_energy', 'electricity'): 1,
            },
        },
    },
    'sinks': {
        'sink': {
            'name': 'sink',
            'inputs': ('electricity',),
            # force an inflow of exactly 10
            'flow_rates': {'electricity': nts.MinMax(min=10, max=10)},
        },
    },
    'storages': {},
    'busses': {
        'bus': {
            'name': 'centralbus',
            'inputs': ('transformer1.electricity', 'transformer2.electricity',),
            'outputs': ('sink.electricity',),
            'component': 'bus',
        },
        'supply_bus_1': {
            'name': 'supplybus1',
            'inputs': ('source1.chemical_energy', ),
            'outputs': ('transformer1.chemical_energy',),
            'component': 'bus',
        },
        'supply_bus_2': {
            'name': 'supplybus2',
            'inputs': ('source2.chemical_energy', ),
            'outputs': ('transformer2.chemical_energy',),
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
}  # minimum working example source - linear - flow rates min matze
