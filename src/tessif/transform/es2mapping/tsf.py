"""
Extract energy system data out of tessif energy system objects and transform
them into `mappings
<https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`_.
"""

import pandas as pd

from tessif.frused import namedtuples


def extract_parameters(energy_system):
    """
    Extract the parameters that describe the :class:`tessif energy system
    <tessif.model.energy_system>` into an energy system `mapping
    <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`_.

    Parameters
    ----------
    energy_system: ~tessif.model.energy_system.AbstractEnergySystem
        A :class:`tessif energy system <tessif.model.energy_system>` Object.

    Return
    ------
    energy_system_dictionairy: dict
        Dictionairy containing the energy system data.

    Examples
    --------
    Using the hardcoded :mod:`example
    <tessif.examples.data.tsf.py_hard.create_fpwe>` (thoroughly explained
    :ref:`here <Models_Tessif_Fpwe>`):

    >>> import tessif.examples.data.tsf.py_hard as tsf_examples
    >>> from tessif.transform.es2mapping.tsf import extract_parameters
    >>> es = tsf_examples.create_fpwe()
    >>> es_dict = extract_parameters(es)
    >>> print(type(es_dict))
    <class 'dict'>

    Show the dictionary's contents:

    >>> for key in es_dict.keys():
    ...     for key2 in es_dict[key].keys():
    ...         for k, v in es_dict[key][key2].items():
    ...             print('{} = {}'.format(
    ...                 k, sorted(v) if isinstance(v, list) else v))
    ... # lists are sorted for doctesting consistency
    ...         print(50*'-')
    ...         print()
    inputs = ['Gas Station.fuel']
    interfaces = ['Gas Station.fuel', 'Generator.fuel']
    outputs = ['Generator.fuel']
    timeseries = None
    name = Pipeline
    latitude = 42
    longitude = 42
    region = Here
    sector = Power
    carrier = gas
    component = None
    node_type = bus
    --------------------------------------------------
    <BLANKLINE>
    inputs = ['Battery.electricity', 'Generator.electricity', 'Solar Panel.electricity']
    interfaces = ['Battery.electricity', 'Demand.electricity', 'Generator.electricity', 'Solar Panel.electricity']
    outputs = ['Battery.electricity', 'Demand.electricity']
    timeseries = None
    name = Powerline
    latitude = 42
    longitude = 42
    region = Here
    sector = Power
    carrier = electricity
    component = None
    node_type = bus
    --------------------------------------------------
    <BLANKLINE>
    accumulated_amounts = {'electricity': [0, inf]}
    costs_for_being_active = 0
    expandable = {'electricity': False}
    expansion_costs = {'electricity': 0}
    expansion_limits = {'electricity': [0, inf]}
    flow_costs = {'electricity': 0}
    flow_emissions = {'electricity': 0}
    flow_gradients = {'electricity': [12, 12]}
    flow_rates = {'electricity': [11, 11]}
    gradient_costs = {'electricity': [0, 0]}
    initial_status = True
    inputs = ['electricity']
    interfaces = ['electricity']
    milp = {'electricity': False}
    number_of_status_changes = [8, inf]
    status_changing_costs = [0, 0]
    status_inertia = [1, 2]
    timeseries = None
    name = Demand
    latitude = 42
    longitude = 42
    region = Here
    sector = Power
    carrier = electricity
    component = None
    node_type = demand
    --------------------------------------------------
    <BLANKLINE>
    accumulated_amounts = {'fuel': [0, inf]}
    costs_for_being_active = 0
    expandable = {'fuel': False}
    expansion_costs = {'fuel': 5}
    expansion_limits = {'fuel': [0, inf]}
    flow_costs = {'fuel': 10}
    flow_emissions = {'fuel': 3}
    flow_gradients = {'fuel': [100, 100]}
    flow_rates = {'fuel': [0, 100]}
    gradient_costs = {'fuel': [0, 0]}
    initial_status = True
    interfaces = ['fuel']
    milp = {'fuel': False}
    number_of_status_changes = [10, inf]
    outputs = ['fuel']
    status_changing_costs = [0, 0]
    status_inertia = [1, 1]
    timeseries = None
    name = Gas Station
    latitude = 42
    longitude = 42
    region = Here
    sector = Power
    carrier = Gas
    component = None
    node_type = source
    --------------------------------------------------
    <BLANKLINE>
    accumulated_amounts = {'electricity': [0, 1000]}
    costs_for_being_active = 0
    expandable = {'electricity': False}
    expansion_costs = {'electricity': 5}
    expansion_limits = {'electricity': [0, inf]}
    flow_costs = {'electricity': 0}
    flow_emissions = {'electricity': 0}
    flow_gradients = {'electricity': [42, 42]}
    flow_rates = {'electricity': [20, 20]}
    gradient_costs = {'electricity': [0, 0]}
    initial_status = True
    interfaces = ['electricity']
    milp = {'electricity': False}
    number_of_status_changes = [10, inf]
    outputs = ['electricity']
    status_changing_costs = [0, 0]
    status_inertia = [1, 1]
    timeseries = {'electricity': [array([12,  3,  7]), array([12,  3,  7])]}
    name = Solar Panel
    latitude = 42
    longitude = 42
    region = Here
    sector = Power
    carrier = electricity
    component = None
    node_type = Renewable
    --------------------------------------------------
    <BLANKLINE>
    conversions = {('fuel', 'electricity'): 0.42}
    costs_for_being_active = 0
    expandable = {'electricity': False, 'fuel': False}
    expansion_costs = {'electricity': 0, 'fuel': 0}
    expansion_limits = {'electricity': [0, inf], 'fuel': [0, inf]}
    flow_costs = {'electricity': 10, 'fuel': 0}
    flow_emissions = {'electricity': 10, 'fuel': 0}
    flow_gradients = {'electricity': [15, 15], 'fuel': [50, 50]}
    flow_rates = {'electricity': [0, 15], 'fuel': [0, 50]}
    gradient_costs = {'electricity': [0, 0], 'fuel': [0, 0]}
    initial_status = True
    inputs = ['fuel']
    interfaces = ['electricity', 'fuel']
    milp = {'electricity': False, 'fuel': False}
    number_of_status_changes = [9, inf]
    outputs = ['electricity']
    status_changing_costs = [0, 0]
    status_inertia = [0, 2]
    timeseries = None
    name = Generator
    latitude = 42
    longitude = 42
    region = Here
    sector = Power
    carrier = electricity
    component = None
    node_type = transformer
    --------------------------------------------------
    <BLANKLINE>
    capacity = 10
    costs_for_being_active = 0
    expandable = {'capacity': False, 'electricity': False}
    expansion_costs = {'capacity': 2, 'electricity': 0}
    expansion_limits = {'capacity': [0, inf], 'electricity': [0, inf]}
    final_soc = None
    fixed_expansion_ratios = {'electricity': True}
    flow_costs = {'electricity': 0}
    flow_efficiencies = {'electricity': [1, 1]}
    flow_emissions = {'electricity': 0}
    flow_gradients = {'electricity': [inf, inf]}
    flow_rates = {'electricity': [0, 30]}
    gradient_costs = {'electricity': [0, 0]}
    idle_changes = [0, 1]
    initial_soc = 10
    initial_status = True
    input = electricity
    interfaces = ['electricity']
    milp = {'electricity': False}
    number_of_status_changes = [42, inf]
    output = electricity
    status_changing_costs = [0, 0]
    status_inertia = [0, 2]
    timeseries = None
    name = Battery
    latitude = 42
    longitude = 42
    region = Here
    sector = Power
    carrier = electricity
    component = None
    node_type = storage
    --------------------------------------------------
    <BLANKLINE>
    start = 1990-07-13T00:00:00.000000000
    periods = 3
    freq = H
    --------------------------------------------------
    <BLANKLINE>
    name = default
    emissions = inf
    resources = inf
    --------------------------------------------------
    <BLANKLINE>
    """
    # store the 'energy_system' object's attributes in a python dictionary
    es_dict = energy_system.__dict__

    # pop the _es_attributes parameter, since it is reistantiated during
    # initialization and causes trobules below
    es_dict.pop("_es_attributes")

    # strip the leading '_' from the dictionary's keys
    for key in list(es_dict.keys()):
        if key.startswith('_'):
            new_key = key.lstrip('_')
            es_dict[new_key] = es_dict.pop(key)

    del es_dict['uid']

    for key, value in es_dict.items():
        if isinstance(value, tuple):

            # replace the tuples containing the component objects with a dict
            # that has the component's name as key and it's parameters as value
            es_dict[key] = {
                str(es_dict[key][i].uid):
                    es_dict[key][i].parameters for i in range(len(value))}

            for k, v in es_dict[key].items():

                # add the parameters stored in 'uid' to the others
                es_dict[key][k].update(es_dict[key][k].pop('uid')._asdict())

                for paramkey, paramval in es_dict[key][k].items():

                    # convert frozensets and namedtuples to lists
                    types_to_convert = (
                        frozenset,
                        namedtuples.MinMax,
                        namedtuples.PositiveNegative,
                        namedtuples.OnOff,
                        namedtuples.InOut)
                    if isinstance(paramval, types_to_convert):
                        es_dict[key][k][paramkey] = list(
                            es_dict[key][k][paramkey])
                    if isinstance(paramval, dict):
                        for k2, v2 in paramval.items():
                            if isinstance(v2, types_to_convert):
                                es_dict[key][k][paramkey][k2] = list(
                                    es_dict[key][k][paramkey][k2])

        # instead of the full timeseries DatetimeIndex, only the first
        # datetime, the number of periods and the freqency are stored.
        if isinstance(value, pd.core.indexes.datetimes.DatetimeIndex):
            timeframe = {
                'start': str(value[0].to_datetime64()),
                'periods': len(value),
                'freq': value.freqstr}
            es_dict['timeframe'] = {'primary': timeframe}

    es_dict['global_constraints'] = {'primary': es_dict['global_constraints']}

    return es_dict
