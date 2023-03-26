# tessif/examples/data/tsf/py_hard.py
"""
:mod:`~tessif.examples.data.tsf.py_hard` is a :mod:`tessif` module for giving
examples on how to create a :class:`tessif energy system
<tessif.model.energy_system.AbstractEnergySystem>`.

It collects minimum working examples, meaningful working
examples and full-fledged use case wrappers for common scenarios.
"""
# 1. Import the needed packages:
from datetime import datetime
import os
import random

import numpy as np
from oemof.tools import economics
import pandas as pd

import tessif.frused.namedtuples as nts
from tessif.frused.paths import example_dir
from tessif.model import components, energy_system


def create_mwe(directory=None, filename=None):
    """
    Create a minimal (parameterized) working example using :mod:`tessif's
    model <tessif.model>`.

    Creates a simple energy system simulation to potentially
    store it on disc inside :paramref:`~create_mwe.directory` as
    :paramref:`~create_mwe.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_mwe.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``mwe.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    See also
    --------
    :ref:`Models_Tessif_mwe` for a step by step explanation.

    Examples
    --------
    Use :func:`create_mwe` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_mwe()

    >>> for node in es.nodes:
    ...     print(node.uid.name)
    Pipeline
    Powerline
    Gas Station
    Demand
    Generator
    Battery

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Gas Station': '#006666',
    ...         'Pipeline': '#006666',
    ...         'Generator': '#006666',
    ...         'Powerline': '#ffcc00',
    ...         'Battery': '#ff6600',
    ...         'Demand': '#009900',
    ...     },
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/mwe.png
        :align: center
        :alt: Image showing the mwe energy system graph
    """
    # 2. Create a simulation time frame of 2 one hour time steps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3. Creating the individual energy system components:
    fuel_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
    )

    power_generator = components.Transformer(
        name='Generator',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.42},
        # Minimum number of arguments required
        flow_costs={'electricity': 2, 'fuel': 0},
    )

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    storage = components.Storage(
        name='Battery',
        input='electricity',
        output='electricity',
        capacity=20,
        initial_soc=10,
        # Minimum number of arguments required
        # flow_rates={'electricity': nts.MinMax(min=0, max=11)},
        flow_costs={'electricity': 0.1}
    )

    fuel_supply_line = components.Bus(
        name='Pipeline',
        inputs=('Gas Station.fuel',),
        outputs=('Generator.fuel',),
        # Minimum number of arguments required
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=('Generator.electricity', 'Battery.electricity'),
        outputs=('Demand.electricity', 'Battery.electricity'),
        # Minimum number of arguments required
    )

    # 4. Creating the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Minimum_Working_Example',
        busses=(fuel_supply_line, electricity_line),
        sinks=(demand,),
        sources=(fuel_supply,),
        transformers=(power_generator,),
        storages=(storage,),
        timeframe=timeframe,
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'mwe.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def create_fpwe(directory=None, filename=None):
    """
    Create a fully parameterized working example using :mod:`tessif's model
    <tessif.model>`.

    Creates a simple energy system simulation to potentially
    store it on disc inside :paramref:`~create_fpwe.directory` as
    :paramref:`~create_fpwe.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_fpwe.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``fpwe.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_Fpwe` - For a step by step explanation on creating this
    energy system.

    :ref:`examples_auto_comparison_fpwe` - For simulating and
    comparing the fpwe using different supported models.

    Examples
    --------
    Use :func:`create_fpwe` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_fpwe()

    >>> for node in es.nodes:
    ...     print(node.uid.name)
    Pipeline
    Powerline
    Gas Station
    Solar Panel
    Demand
    Generator
    Battery

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Solar Panel': '#ff9900',
    ...         'Gas Station': '#006666',
    ...         'Pipeline': '#006666',
    ...         'Generator': '#006666',
    ...         'Powerline': '#ffcc00',
    ...         'Battery': '#ff6600',
    ...         'Demand': '#009900',
    ...     },
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/fpwe.png
        :align: center
        :alt: Image showing the fpwe energy system graph
    """

    # 2. Create a simulation time frame of 3 one hour time steps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=3, freq='H')

    # 3. Initiate the global constraints
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
        'resources': float('+inf')}

    # 3. Creating the individual energy system components:
    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=1000)},
        flow_rates={'electricity': nts.MinMax(min=20, max=20)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=42, negative=42)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([12, 3, 7]), max=np.array([12, 3, 7]))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 5},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    fuel_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        accumulated_amounts={
            'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'fuel': nts.MinMax(min=0, max=100)},  # float('+inf'))},
        flow_costs={'fuel': 10},
        flow_emissions={'fuel': 3},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=100, negative=100)},
        gradient_costs={'fuel': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False},
        expansion_costs={'fuel': 5},
        expansion_limits={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        milp={'fuel': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    power_generator = components.Transformer(
        name='Generator',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.42},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=50),
            'electricity': nts.MinMax(min=0, max=15)},
        flow_costs={'fuel': 0, 'electricity': 10},
        flow_emissions={'fuel': 0, 'electricity': 10},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=50, negative=50),
            'electricity': nts.PositiveNegative(positive=15, negative=15)},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'electricity': False},
        expansion_costs={'fuel': 0, 'electricity': 0},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False, 'fuel': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=2),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=9),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=11, max=11)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=12, negative=12)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=2, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=8),
        costs_for_being_active=0
        # Total number of arguments to specify sink object
    )

    storage = components.Storage(
        name='Battery',
        input='electricity',
        output='electricity',
        capacity=10,
        initial_soc=10,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=1),
        flow_rates={'electricity': nts.MinMax(min=0, max=30)},
        flow_efficiencies={
            'electricity': nts.InOut(inflow=1, outflow=1)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': False, 'electricity': False},
        expansion_costs={'capacity': 2, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=2),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=42),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    fuel_supply_line = components.Bus(
        name='Pipeline',
        inputs=('Gas Station.fuel',),
        outputs=('Generator.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=('Generator.electricity', 'Battery.electricity',
                'Solar Panel.electricity',),
        outputs=('Demand.electricity', 'Battery.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # 4. Creating the actual energy system:

    explicit_es = energy_system.AbstractEnergySystem(
        uid='Fully_Parameterized_Working_Example',
        busses=(fuel_supply_line, electricity_line),
        sinks=(demand,),
        sources=(fuel_supply, solar_panel),
        transformers=(power_generator,),
        storages=(storage,),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'fpwe.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def emission_objective(directory=None, filename=None):
    """
    Create a minimal working example using :mod:`tessif's
    model <tessif.model>` optimizing it for costs and keeping
    the total emissions below an emission objective.

    Creates a simple energy system simulation to potentially
    store it on disc inside :paramref:`~emission_objective.directory` as
    :paramref:`~emission_objective.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~emission_objective.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be
        ``emission_objective.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`examples_auto_comparison_emissions` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Secondary_Objectives` - For a detailed description on how to
    constrain values like co2 emissions.

    Examples
    --------

    Use :func:`emission_objective` to quickly access a tessif energy system
    to use for doctesting or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.emission_objective()
    >>> print(es.global_constraints['emissions'])
    60

    Transform the energy system to i.e. oemof, to see if the constraint holds:

    >>> import tessif.transform.es2es.omf as tessif_to_oemof
    >>> oemof_es = tessif_to_oemof.transform(es)
    >>> print(oemof_es.global_constraints['emissions'])
    60

    Optmize the energy system to see the constraint's consequences:

    >>> import tessif.simulate as simulate
    >>> optimized_oemof_es = simulate.omf_from_es(oemof_es, solver='cbc')

    >>> import tessif.transform.es2mapping.omf as oemof_results
    >>> resultier = oemof_results.LoadResultier(optimized_oemof_es)

    >>> # Generator costs/emissions are 2/1 unit respectively
    >>> # Wind Power costs/emissions are 4/0 units respectively
    >>> print(resultier.node_load['Powerline'])
    Powerline            Gas Plant  Generator  Wind Power  Demand
    1990-07-13 00:00:00       -5.0  -0.000000   -5.000000    10.0
    1990-07-13 01:00:00       -5.0  -0.000000   -5.000000    10.0
    1990-07-13 02:00:00       -5.0  -0.000000   -5.000000    10.0
    1990-07-13 03:00:00       -5.0  -0.507246   -4.492754    10.0

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Wind Power': '#00ccff',
    ...         'Gas Source': '#336666',
    ...         'Gas Grid': '#336666',
    ...         'Gas Plant': '#336666',
    ...         'Gas Station': '#666666',
    ...         'Pipeline': '#666666',
    ...         'Generator': '#666666',
    ...         'Powerline': 'yellow',
    ...         'Demand': 'yellow',
    ...     },
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    IGNORE:
    >>> title = plt.gca().set_title('emission_objective example')
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: ../images/emission_objective_example.png
        :align: center
        :alt: Image showing the emission objective example energy system graph
    """

    # 2. Create a simulation time frame of four one-hour timesteps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3. Creating the individual energy system components:

    # first supply chain
    fuel_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        flow_emissions={'fuel': 1.5},
        flow_costs={'fuel': 2},
    )

    fuel_supply_line = components.Bus(
        name='Pipeline',
        inputs=('Gas Station.fuel',),
        outputs=('Generator.fuel',),
        # Minimum number of arguments required
    )

    # conventional power supply is cheaper, but has emissions allocated to it
    power_generator = components.Transformer(
        name='Generator',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.42},
        # Minimum number of arguments required
        flow_costs={'electricity': 2, 'fuel': 0},
        flow_emissions={'electricity': 3, 'fuel': 0},
    )

    # second supply chain
    gas_supply = components.Source(
        name='Gas Source',
        outputs=('gas',),
        # Minimum number of arguments required
        flow_emissions={'gas': 0.5},
        flow_costs={'gas': 1},
    )

    gas_grid = components.Bus(
        name='Gas Grid',
        inputs=('Gas Source.gas',),
        outputs=('Gas Plant.gas',),
        # Minimum number of arguments required
    )

    # conventional power supply is cheaper, but has emissions allocated to it
    gas_plant = components.Transformer(
        name='Gas Plant',
        inputs=('gas',),
        outputs=('electricity',),
        conversions={('gas', 'electricity'): 0.6},
        # Minimum number of arguments required
        flow_rates={'electricity': (0, 5), 'gas': (0, float('+inf'))},
        flow_costs={'electricity': 1, 'gas': 0},
        flow_emissions={'electricity': 2, 'gas': 0},
    )

    # wind power is more expensive but has no emissions allocated to it
    wind_power = components.Source(
        name='Wind Power',
        outputs=('electricity',),
        flow_costs={'electricity': 10},
    )

    # Demand needing 10 energy units per time step
    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=('Generator.electricity', 'Wind Power.electricity',
                'Gas Plant.electricity'),
        outputs=('Demand.electricity',),
        # Minimum number of arguments required
    )

    global_constraints = {
        'emissions': 60}

    # 4. Creating the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Emission_Objective_Example',
        busses=(fuel_supply_line, electricity_line, gas_grid),
        sinks=(demand,),
        sources=(fuel_supply, wind_power, gas_supply),
        transformers=(power_generator, gas_plant),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'emission_objective.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def create_connected_es(directory=None, filename=None):
    """
    Create a minimal working example using :mod:`tessif's
    model <tessif.model>` connecting to seperate energy systems using a
    :class:`tessif.model.components.Connector` object. Effectively creating
    a `transs hipment problem
    <https://en.wikipedia.org/wiki/Transshipment_problem>`_.

    Creates a simple energy system simulation to potentially
    store it on disc inside :paramref:`~create_connected_es.directory` as
    :paramref:`~create_connected_es.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_connected_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``connected_es.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Transshipment` - For simulating and
    comparing this energy system using different supported models.

    :meth:`tessif.model.energy_system.AbstractEnergySystem.connect` - For the
    built-in mehtod of tessif's energy systems.

    :ref:`Examples_Application_Computational` - For a comprehensive example
    on how to connect energy systems and how this can be used to measure
    computational scalability.

    Examples
    --------
    Use :func:`create_connected_es` to quickly access a tessif energy system
    to use for doctesting or trying out this framework's utilities:

    >>> import tessif.examples.data.tsf.py_hard as coded_examples
    >>> es = coded_examples.create_connected_es()
    >>> for connector in es.connectors:
    ...     print(connector.conversions)
    {('bus-01', 'bus-02'): 0.9, ('bus-02', 'bus-01'): 0.8}

    Transform the energy system to i.e. oemof, to see if conversion factors
    remain:

    >>> import tessif.transform.es2es.omf as tessif_to_oemof
    >>> oemof_es = tessif_to_oemof.transform(es)
    >>> for node in oemof_es.nodes:
    ...     if node.label.name == 'connector':
    ...        for bus_tuple, factor in node.conversion_factors.items():
    ...            print('({}, {}): {}'.format(
    ...                bus_tuple[0], bus_tuple[1], factor[0]))
    (bus-01, bus-02): 0.9
    (bus-02, bus-01): 0.8

    Optmize the energy system to see the transhipment problem:

    >>> import tessif.simulate as simulate
    >>> optimized_oemof_es = simulate.omf_from_es(oemof_es, solver='cbc')

    >>> import tessif.transform.es2mapping.omf as oemof_results
    >>> resultier = oemof_results.LoadResultier(optimized_oemof_es)

    >>> print(resultier.node_load['connector'])
    connector              bus-01  bus-02  bus-01  bus-02
    1990-07-13 00:00:00 -5.555556   -0.00     0.0     5.0
    1990-07-13 01:00:00 -0.000000   -6.25     5.0     0.0
    1990-07-13 02:00:00 -0.000000   -0.00     0.0     0.0

    >>> print(resultier.node_load['bus-01'])
    bus-01               connector  source-01  connector  sink-01
    1990-07-13 00:00:00       -0.0  -5.555556   5.555556      0.0
    1990-07-13 01:00:00       -5.0 -10.000000   0.000000     15.0
    1990-07-13 02:00:00       -0.0 -10.000000   0.000000     10.0

    >>> print(resultier.node_load['bus-02'])
    bus-02               connector  source-02  connector  sink-02
    1990-07-13 00:00:00       -5.0     -10.00       0.00     15.0
    1990-07-13 01:00:00       -0.0      -6.25       6.25      0.0
    1990-07-13 02:00:00       -0.0     -10.00       0.00     10.0

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'connector': '#9999ff',
    ...                 'bus-01': '#cc0033',
    ...                 'bus-02': '#00ccff'},
    ...     node_size={'connector': 5000},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    IGNORE:
    >>> title = plt.gca().set_title('connected_es example')
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: ../images/connected_es_example.png
        :align: center
        :alt: alternate text
    """

    timeframe = pd.date_range('7/13/1990', periods=3, freq='H')

    s1 = components.Sink(
        name='sink-01',
        inputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=15)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([0, 15, 10]), max=np.array([0, 15, 10]))})

    so1 = components.Source(
        name='source-01',
        outputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        flow_costs={'electricity': 1},
        flow_emissions={'electricity': 0.8})

    mb1 = components.Bus(
        name='bus-01',
        inputs=('source-01.electricity',),
        outputs=('sink-01.electricity',),
    )

    s2 = components.Sink(
        name='sink-02',
        inputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=15)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([15, 0, 10]), max=np.array([15, 0, 10]))})

    so2 = components.Source(
        name='source-02',
        outputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        flow_costs={'electricity': 1},
        flow_emissions={'electricity': 1.2})

    mb2 = components.Bus(
        name='bus-02',
        inputs=('source-02.electricity',),
        outputs=('sink-02.electricity',),
    )

    c = components.Connector(
        name='connector',
        interfaces=('bus-01', 'bus-02'),
        conversions={('bus-01', 'bus-02'): 0.9,
                     ('bus-02', 'bus-01'): 0.8})

    connected_es = energy_system.AbstractEnergySystem(
        uid='Connected-Energy-Systems-Example',
        busses=(mb1, mb2),
        sinks=(s1, s2,),
        sources=(so1, so2),
        connectors=(c,),
        timeframe=timeframe
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'connected_es.tsf'

    connected_es.dump(directory=directory, filename=filename)

    return connected_es


def create_storage_example(directory=None, filename=None):
    """
    Create a small energy system utilizing a storage.

    Creates a simple energy system simulation to potentially
    store it on disc inside :paramref:`~create_storage_example.directory` as
    :paramref:`~create_storage_example.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_storage_example.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``storage_example.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Warning
    -------
    In this example the installed capacity is set to 0, but expandable
    (A common use case). Most, if not any, of the
    :ref:`supported models <SupportedModels>` however, use capacity specific
    values for idle losses and initial as well as final soc constraints.

    Given the initial capacity is 0, this problem is solved by setting the
    initial soc as well as the idle losses to 0, if necessary.

    To avoid this caveat, set the inital capacity to a small value and adjust
    initial soc and idle changes accordingly. This might involve some trial and
    error.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Storage` - For simulating and
    comparing this energy system using different supported models.

    Examples
    --------
    Use :func:`create_storage_example` to quickly access a tessif energy
    system to use for doctesting or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as coded_examples
    >>> tsf_es = coded_examples.create_storage_example()

    >>> for node in tsf_es.nodes:
    ...     print(node.uid.name)
    Powerline
    Generator
    Demand
    Storage

    Transform the tessif energy system into oemof and pypsa:

    >>> # Import the model transformation utilities:
    >>> from tessif.transform.es2es import (
    ...     ppsa as tsf2pypsa,
    ...     omf as tsf2omf,
    ... )

    >>> # Do the transformation:
    >>> oemof_es = tsf2omf.transform(tsf_es)
    >>> pypsa_es = tsf2pypsa.transform(tsf_es)

    Do some examplary checks on the flow conversions:

    >>> # oemof:
    >>> for node in oemof_es.nodes:
    ...     if node.label.name == 'Storage':
    ...         print(node.inflow_conversion_factor[0])
    ...         print(node.outflow_conversion_factor[0])
    0.9
    0.9

    >>> # pypsa:
    >>> print(pypsa_es.storage_units['efficiency_store']['Storage'])
    0.9
    >>> print(pypsa_es.storage_units['efficiency_dispatch']['Storage'])
    0.9

    Simulate the transformed energy system:

    >>> # Import the simulation utility:
    >>> import tessif.simulate

    >>> # Optimize the energy systems:
    >>> optimized_oemof_es = tessif.simulate.omf_from_es(oemof_es)
    >>> optimized_pypsa_es = tessif.simulate.ppsa_from_es(pypsa_es)

    Do some post processing:

    >>> # Import the post-processing utilities:
    >>> from tessif.transform.es2mapping import (
    ...     ppsa as post_process_pypsa,
    ...     omf as post_process_oemof,
    ... )

    >>> # Conduct the post-processing:
    >>> oemof_load_results = post_process_oemof.LoadResultier(
    ...     optimized_oemof_es)
    >>> pypsa_load_results = post_process_pypsa.LoadResultier(
    ...     optimized_pypsa_es)

    To see the load results:

    >>> # oemof:
    >>> oemof_loads = post_process_oemof.LoadResultier(optimized_oemof_es)
    >>> print(oemof_loads.node_load['Powerline'])
    Powerline            Generator  Storage  Demand  Storage
    1990-07-13 00:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 01:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 02:00:00      -19.0     -0.0     7.0     12.0
    1990-07-13 03:00:00       -0.0    -10.0    10.0      0.0
    1990-07-13 04:00:00       -0.0    -10.0    10.0      0.0


    >>> # pypsa:
    >>> pypsa_loads = post_process_pypsa.LoadResultier(optimized_pypsa_es)
    >>> print(pypsa_loads.node_load['Powerline'])
    Powerline            Generator  Storage  Demand  Storage
    1990-07-13 00:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 01:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 02:00:00      -19.0     -0.0     7.0     12.0
    1990-07-13 03:00:00       -0.0    -10.0    10.0      0.0
    1990-07-13 04:00:00       -0.0    -10.0    10.0      0.0

    And to check the state of charge results:

    >>> # oemof:
    >>> oemof_socs = post_process_oemof.StorageResultier(optimized_oemof_es)
    >>> print(oemof_socs.node_soc['Storage'])
    1990-07-13 00:00:00     8.100000
    1990-07-13 01:00:00    16.200000
    1990-07-13 02:00:00    27.000000
    1990-07-13 03:00:00    15.888889
    1990-07-13 04:00:00     4.777778
    Freq: H, Name: Storage, dtype: float64

    >>> # pypsa:
    >>> pypsa_socs = post_process_pypsa.StorageResultier(optimized_pypsa_es)
    >>> print(pypsa_socs.node_soc['Storage'])
    1990-07-13 00:00:00     8.100000
    1990-07-13 01:00:00    16.200000
    1990-07-13 02:00:00    27.000000
    1990-07-13 03:00:00    15.888889
    1990-07-13 04:00:00     4.777778
    Freq: H, Name: Storage, dtype: float64


    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = tsf_es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Powerline': '#009900',
    ...                 'Storage': '#cc0033',
    ...                 'Demand': '#00ccff',
    ...                 'Generator': '#ffD700',},
    ...     node_size={'Storage': 5000},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    IGNORE:
    >>> title = plt.gca().set_title('storage example es')
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: ../images/storage_es_example.png
        :align: center
        :alt: Image showing the create_storage_example energy system graph.
    """

    timeframe = pd.date_range('7/13/1990', periods=5, freq='H')

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        carrier='electricity',
        node_type='sink',
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        timeseries={
            'electricity': nts.MinMax(
                min=np.array([10, 10, 7, 10, 10]),
                max=np.array([10, 10, 7, 10, 10])
            )
        }
    )

    generator = components.Source(
        name='Generator',
        outputs=('electricity',),
        carrier='electricity',
        node_type='source',
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        flow_costs={'electricity': 2},
        timeseries={
            'electricity': nts.MinMax(
                min=np.array([19, 19, 19, 0, 0]),
                max=np.array([19, 19, 19, 0, 0])
            )
        }
    )

    powerline = components.Bus(
        name='Powerline',
        inputs=('Generator.electricity', 'Storage.electricity'),
        outputs=('Demand.electricity', 'Storage.electricity',),
        carrier='electricity',
        node_type='bus',
    )

    storage = components.Storage(
        name='Storage',
        input='electricity',
        output='electricity',
        capacity=0,
        initial_soc=0,
        carrier='electricity',
        node_type='storage',
        flow_efficiencies={
             'electricity': nts.InOut(inflow=0.9, outflow=0.9)},
        flow_costs={'electricity': 1},
        flow_emissions={'electricity': 0.5},
        expandable={'capacity': True, 'electricity': False},
        expansion_costs={'capacity': 0, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
    )

    storage_es = energy_system.AbstractEnergySystem(
        uid='Storage-Energysystem-Example',
        busses=(powerline,),
        sinks=(demand,),
        sources=(generator,),
        storages=(storage,),
        timeframe=timeframe
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'storage_es.tsf'

    storage_es.dump(directory=directory, filename=filename)

    return storage_es


def create_storage_fixed_ratio_expansion_example(
        directory=None, filename=None):
    """
    Create a small energy system utilizing an expandable storage with a fixed
    capacity to outflow ratio.

    Creates a simple energy system simulation to potentially store it on disc
    inside
    :paramref:`~create_storage_fixed_ratio_expansion_example.directory` as
    :paramref:`~create_storage_fixed_ratio_expansion_example.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_storage_fixed_ratio_expansion_example.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be
        ``storage_fixed_ratio_example.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Warning
    -------
    In this example the installed capacity is set to 1, but expandable.
    The flow rate to 0.1. By enabling both expandables (capacity and flow rate)
    as well as fixing their ratios the installed capacity result will be
    much higher than needed. Or in other words, the flow rate will determine
    the amount of installed capacity.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Storage` - For simulating and
    comparing this energy system using different supported models.

    Examples
    --------
    Use :func:`create_storage_fixed_ratio_expansion_example` to quickly
    access a tessif energy system to use for doctesting, or trying out this
    framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as coded_examples
    >>> tsf_es = coded_examples.create_storage_fixed_ratio_expansion_example()

    >>> for node in tsf_es.nodes:
    ...     print(node.uid.name)
    Powerline
    Generator
    Demand
    Storage

    Transform the tessif energy system into oemof and pypsa:

    >>> # Import the model transformation utilities:
    >>> from tessif.transform.es2es import (
    ...     ppsa as tsf2pypsa,
    ...     omf as tsf2omf,
    ... )

    >>> # Do the transformation:
    >>> oemof_es = tsf2omf.transform(tsf_es)
    >>> pypsa_es = tsf2pypsa.transform(tsf_es)

    Do some examplary checks on the flow conversions:

    >>> # oemof:
    >>> for node in oemof_es.nodes:
    ...     if node.label.name == 'Storage':
    ...         print(node.inflow_conversion_factor[0])
    ...         print(node.outflow_conversion_factor[0])
    0.95
    0.89

    >>> # pypsa:
    >>> print(pypsa_es.storage_units['efficiency_store']['Storage'])
    0.95
    >>> print(pypsa_es.storage_units['efficiency_dispatch']['Storage'])
    0.89

    Simulate the transformed energy system:

    >>> # Import the simulation utility:
    >>> import tessif.simulate

    >>> # Optimize the energy systems:
    >>> optimized_oemof_es = tessif.simulate.omf_from_es(oemof_es)
    >>> optimized_pypsa_es = tessif.simulate.ppsa_from_es(pypsa_es)

    Do some post processing:

    >>> # Import the post-processing utilities:
    >>> from tessif.transform.es2mapping import (
    ...     ppsa as post_process_pypsa,
    ...     omf as post_process_oemof,
    ... )

    >>> # Conduct the post-processing:
    >>> oemof_load_results = post_process_oemof.LoadResultier(
    ...     optimized_oemof_es)
    >>> pypsa_load_results = post_process_pypsa.LoadResultier(
    ...     optimized_pypsa_es)

    Check if the load results are the same as in the example above:

    >>> # oemof:
    >>> oemof_loads = post_process_oemof.LoadResultier(optimized_oemof_es)
    >>> print(oemof_loads.node_load['Powerline'])
    Powerline            Generator  Storage  Demand  Storage
    1990-07-13 00:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 01:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 02:00:00      -19.0     -0.0     7.0     12.0
    1990-07-13 03:00:00       -0.0    -10.0    10.0      0.0
    1990-07-13 04:00:00       -0.0    -10.0    10.0      0.0

    >>> # pypsa:
    >>> pypsa_loads = post_process_pypsa.LoadResultier(optimized_pypsa_es)
    >>> print(pypsa_loads.node_load['Powerline'])
    Powerline            Generator  Storage  Demand  Storage
    1990-07-13 00:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 01:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 02:00:00      -19.0     -0.0     7.0     12.0
    1990-07-13 03:00:00       -0.0    -10.0    10.0      0.0
    1990-07-13 04:00:00       -0.0    -10.0    10.0      0.0

    Check the installed capacity:

    >>> # oemof:
    >>> oemof_capacities = post_process_oemof.CapacityResultier(
    ...     optimized_oemof_es)
    >>> print(oemof_capacities.node_installed_capacity['Storage'])
    120.0

    >>> # pypsa:
    >>> pypsa_capacities = post_process_pypsa.CapacityResultier(
    ...     optimized_pypsa_es)
    >>> print(pypsa_capacities.node_installed_capacity['Storage'])
    120.0

    The integrated global results or high priority resutls:

    >>> # oemof:
    >>> oemof_hps = post_process_oemof.IntegratedGlobalResultier(
    ...     optimized_oemof_es)
    >>> for key, result in oemof_hps.global_results.items():
    ...     if 'emissions' not in key:
    ...          print(f'{key}: {result}')
    costs (sim): 258.0
    opex (ppcd): 20.0
    capex (ppcd): 238.0

    >>> # pypsa:
    >>> pypsa_hps = post_process_pypsa.IntegratedGlobalResultier(
    ...     optimized_pypsa_es)
    >>> for key, result in pypsa_hps.global_results.items():
    ...     if 'emissions' not in key:
    ...          print(f'{key}: {result}')
    costs (sim): 258.0
    opex (ppcd): 20.0
    capex (ppcd): 238.0

    And to check the state of charge results:

    >>> # oemof:
    >>> oemof_socs = post_process_oemof.StorageResultier(optimized_oemof_es)
    >>> print(oemof_socs.node_soc['Storage'])
    1990-07-13 00:00:00     8.550000
    1990-07-13 01:00:00    17.100000
    1990-07-13 02:00:00    28.500000
    1990-07-13 03:00:00    17.264045
    1990-07-13 04:00:00     6.028090
    Freq: H, Name: Storage, dtype: float64

    >>> # pypsa:
    >>> pypsa_socs = post_process_pypsa.StorageResultier(optimized_pypsa_es)
    >>> print(pypsa_socs.node_soc['Storage'])
    1990-07-13 00:00:00     8.550000
    1990-07-13 01:00:00    17.100000
    1990-07-13 02:00:00    28.500000
    1990-07-13 03:00:00    17.264045
    1990-07-13 04:00:00     6.028090
    Freq: H, Name: Storage, dtype: float64

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = tsf_es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Powerline': '#009900',
    ...                 'Storage': '#cc0033',
    ...                 'Demand': '#00ccff',
    ...                 'Generator': '#ffD700',},
    ...     node_size={'Storage': 5000},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/storage_es_example.png
        :align: center
        :alt: Image showing the create_storage_example energy system graph.

    Reparameterize the storage component usinng one of tessif's
    :attr:`hooks <tessif.frused.hooks.tsf.reparameterize_components>`, to
    unbind capacity and flow rate expansion:

    >>> from tessif.frused.hooks.tsf import reparameterize_components
    >>> reparameterized_es = reparameterize_components(
    ...     es=tsf_es,
    ...     components={
    ...         'Storage': {
    ...             'fixed_expansion_ratios': {'electricity': False},
    ...         },
    ...     },
    ... )

    Redo the transformations and simulations:

    >>> # Transformation:
    >>> oemof_es = tsf2omf.transform(reparameterized_es)
    >>> pypsa_es = tsf2pypsa.transform(reparameterized_es)

    >>> # Optimization/Simulation:
    >>> optimized_oemof_es = tessif.simulate.omf_from_es(oemof_es)
    >>> optimized_pypsa_es = tessif.simulate.ppsa_from_es(pypsa_es)

    Recheck installed capacities socs and loads:

    Installed capacity:

    >>> # oemof:
    >>> oemof_capacities = post_process_oemof.CapacityResultier(
    ...     optimized_oemof_es)
    >>> print(oemof_capacities.node_installed_capacity['Storage'])
    28.5

    >>> # pypsa:
    >>> pypsa_capacities = post_process_pypsa.CapacityResultier(
    ...     optimized_pypsa_es)
    >>> print(pypsa_capacities.node_installed_capacity['Storage'])
    120.0

    Note
    ----
    Note how oemof is able to unbind these values, whereas pypsa is not.


    Integrated global results or high priority resutls:

    >>> # oemof:
    >>> oemof_hps = post_process_oemof.IntegratedGlobalResultier(
    ...     optimized_oemof_es)
    >>> for key, result in oemof_hps.global_results.items():
    ...     if 'emissions' not in key:
    ...          print(f'{key}: {result}')
    costs (sim): 75.0
    opex (ppcd): 20.0
    capex (ppcd): 55.0

    >>> # pypsa:
    >>> pypsa_hps = post_process_pypsa.IntegratedGlobalResultier(
    ...     optimized_pypsa_es)
    >>> for key, result in pypsa_hps.global_results.items():
    ...     if 'emissions' not in key:
    ...          print(f'{key}: {result}')
    costs (sim): 258.0
    opex (ppcd): 20.0
    capex (ppcd): 238.0

    Note
    ----
    Note how PyPSA still calculates higher capex for the storage expansion,
    since cpacity and power ratio are fixed.

    State of charge results:

    >>> # oemof:
    >>> oemof_socs = post_process_oemof.StorageResultier(optimized_oemof_es)
    >>> print(oemof_socs.node_soc['Storage'])
    1990-07-13 00:00:00     8.550000
    1990-07-13 01:00:00    17.100000
    1990-07-13 02:00:00    28.500000
    1990-07-13 03:00:00    17.264045
    1990-07-13 04:00:00     6.028090
    Freq: H, Name: Storage, dtype: float64

    >>> # pypsa:
    >>> pypsa_socs = post_process_pypsa.StorageResultier(optimized_pypsa_es)
    >>> print(pypsa_socs.node_soc['Storage'])
    1990-07-13 00:00:00     8.550000
    1990-07-13 01:00:00    17.100000
    1990-07-13 02:00:00    28.500000
    1990-07-13 03:00:00    17.264045
    1990-07-13 04:00:00     6.028090
    Freq: H, Name: Storage, dtype: float64

    Loads:

    >>> # oemof:
    >>> oemof_loads = post_process_oemof.LoadResultier(optimized_oemof_es)
    >>> print(oemof_loads.node_load['Powerline'])
    Powerline            Generator  Storage  Demand  Storage
    1990-07-13 00:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 01:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 02:00:00      -19.0     -0.0     7.0     12.0
    1990-07-13 03:00:00       -0.0    -10.0    10.0      0.0
    1990-07-13 04:00:00       -0.0    -10.0    10.0      0.0

    >>> # pypsa:
    >>> pypsa_loads = post_process_pypsa.LoadResultier(optimized_pypsa_es)
    >>> print(pypsa_loads.node_load['Powerline'])
    Powerline            Generator  Storage  Demand  Storage
    1990-07-13 00:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 01:00:00      -19.0     -0.0    10.0      9.0
    1990-07-13 02:00:00      -19.0     -0.0     7.0     12.0
    1990-07-13 03:00:00       -0.0    -10.0    10.0      0.0
    1990-07-13 04:00:00       -0.0    -10.0    10.0      0.0
    """

    timeframe = pd.date_range('7/13/1990', periods=5, freq='H')

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        carrier='electricity',
        node_type='sink',
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        timeseries={
            'electricity': nts.MinMax(
                min=np.array([10, 10, 7, 10, 10]),
                max=np.array([10, 10, 7, 10, 10])
            )
        }
    )

    generator = components.Source(
        name='Generator',
        outputs=('electricity',),
        carrier='electricity',
        node_type='source',
        flow_rates={'electricity': nts.MinMax(min=0, max=10)},
        flow_costs={'electricity': 0},
        timeseries={
            'electricity': nts.MinMax(
                min=np.array([19, 19, 19, 0, 0]),
                max=np.array([19, 19, 19, 0, 0])
            )
        }
    )

    powerline = components.Bus(
        name='Powerline',
        inputs=('Generator.electricity', 'Storage.electricity'),
        outputs=('Demand.electricity', 'Storage.electricity',),
        carrier='electricity',
        node_type='bus',
    )

    storage = components.Storage(
        name='Storage',
        input='electricity',
        output='electricity',
        capacity=1,
        initial_soc=0,
        carrier='electricity',
        node_type='storage',
        flow_rates={'electricity': nts.MinMax(min=0, max=0.1)},
        flow_efficiencies={
             'electricity': nts.InOut(inflow=0.95, outflow=0.89)},
        flow_costs={'electricity': 1},
        flow_emissions={'electricity': 0.5},
        expandable={'capacity': True, 'electricity': True},
        fixed_expansion_ratios={'electricity': True},
        expansion_costs={'capacity': 2, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=1, max=float('+inf')),
            'electricity': nts.MinMax(min=0.1, max=float('+inf'))},
    )

    # energy dissipation parameterization
    # storage = components.Storage(
    #     name='Storage',
    #     input='electricity',
    #     output='electricity',
    #     capacity=1,
    #     initial_soc=0,
    #     carrier='electricity',
    #     node_type='storage',
    #     flow_rates={'electricity': nts.MinMax(min=0, max=0.9)},
    #     flow_efficiencies={
    #          'electricity': nts.InOut(inflow=0.8, outflow=0.9)},
    #     flow_costs={'electricity': 3},
    #     flow_emissions={'electricity': 0.5},
    #     expandable={'capacity': True, 'electricity': True},
    #     fixed_expansion_ratios={'electricity': True},
    #     expansion_costs={'capacity': 5, 'electricity': 0},
    #     expansion_limits={
    #         'capacity': nts.MinMax(min=1, max=float('+inf')),
    #         'electricity': nts.MinMax(min=0.9, max=float('+inf'))},
    # )

    storage_es = energy_system.AbstractEnergySystem(
        uid='Storage-Energysystem-Example',
        busses=(powerline,),
        sinks=(demand,),
        sources=(generator,),
        storages=(storage,),
        timeframe=timeframe
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'storage_fixed_ratio_example.tsf'

    storage_es.dump(directory=directory, filename=filename)

    return storage_es


def create_expansion_plan_example(directory=None, filename=None):
    """
    Create a small energy system utilizing two emisison free and
    expandable sources, as well as an emitting one.

    Creates a simple energy system simulation to potentially
    store it on disc inside
    :paramref:`~create_expansion_plan_example.directory` as
    :paramref:`~create_expansion_plan_example.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_expansion_plan_example.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``expp.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Expansion` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Examples_Application_Components`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization among models.

    Examples
    --------
    Use :func:`create_expansion_plan_example` to quickly access a tessif
    energy system to use for doctesting, or trying out this framework's
    utilities.

    (For a step by step explanation see :ref:`Models_Tessif_mwe`):

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_expansion_plan_example()

    >>> for node in es.nodes:
    ...     print(str(node.uid))
    Powerline
    Emitting Source
    Capped Renewable
    Uncapped Renewable
    Demand

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Powerline': '#009900',
    ...                 'Emitting Source': '#cc0033',
    ...                 'Demand': '#00ccff',
    ...                 'Capped Renewable': '#ffD700',
    ...                 'Uncapped Renewable': '#ffD700',},
    ...     node_size={'Powerline': 5000},
    ...     layout='dot')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/expansion_plan_example.png
        :align: center
        :alt: Image showing the expansion plan example energy system graph.
    """

    # 2. Create a simulation time frame of 2 one hour time steps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3. Creating the individual energy system components:

    # emitting source having no costs and no flow constraints but emissions
    emitting_source = components.Source(
        name='Emitting Source',
        outputs=('electricity',),
        # Minimum number of arguments required
        flow_emissions={
            'electricity': 1
        },

    )

    # capped source having no costs, no emission, no flow constraints
    # but existing and max installed capacity (for expansion) as well
    # as expansion costs
    capped_renewable = components.Source(
        name='Capped Renewable',
        outputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=1, max=2)},
        flow_costs={'electricity': 2, },
        expandable={'electricity': True},
        expansion_costs={'electricity': 1},
        expansion_limits={'electricity': nts.MinMax(min=1, max=4)},
    )

    # uncapped source having no costs and no emissions
    # but an externally set timeseries as well as expansion costs
    uncapped_min, uncapped_max = [1, 2, 3, 1], [1, 2, 3, 1]

    uncapped_renewable = components.Source(
        name='Uncapped Renewable',
        outputs=('electricity',),
        # Minimum number of arguments required
        # flow_rates={'electricity': nts.MinMax(min=0, max=1)},
        flow_costs={'electricity': 2, },
        expandable={'electricity': True},
        expansion_costs={'electricity': 2},
        timeseries={
            'electricity': nts.MinMax(
                min=uncapped_min,
                max=uncapped_max
            )
        },
        expansion_limits={
            'electricity': nts.MinMax(
                min=max(uncapped_max),
                max=float('+inf'),
            )
        },
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=(
            'Emitting Source.electricity',
            'Capped Renewable.electricity',
            'Uncapped Renewable.electricity'),
        outputs=('Demand.electricity',),
        # Minimum number of arguments required
    )

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    global_constraints = {'emissions': 20}

    # 4. Creating the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Expansion Plan Example',
        busses=(electricity_line,),
        sinks=(demand,),
        sources=(
            emitting_source,
            capped_renewable,
            uncapped_renewable,
        ),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'expp.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def create_zero_costs_es(directory=None, filename=None):
    """
    Create a small energy system having to costs alocated to commitment
    and expansion, but a low emission consttaint.

    Interesting about this example is the fact that there are many possible
    solutions, so solver ambiguity might be observed using this es. This
    energy system also serves as a method of validation for the post-processing
    capabilities, to handle 0 costs in case of scaling results to maximum
    occuring costs.

    Creates a simple energy system simulation to potentially
    store it on disc inside
    :paramref:`~create_zero_costs_es.directory` as
    :paramref:`~create_zero_costs_es.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_zero_costs_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``expp.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    Examples
    --------
    Use :func:`create_zero_costs_es` to quickly access a tessif
    energy system to use for doctesting, or trying out this framework's
    utilities.

    (For a step by step explanation see :ref:`Models_Tessif_mwe`):

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_zero_costs_es()

    >>> for node in es.nodes:
    ...     print(str(node.uid))
    Powerline
    Emitting Source
    Capped Renewable
    Uncapped Renewable
    Demand

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Powerline': '#009900',
    ...                 'Emitting Source': '#cc0033',
    ...                 'Demand': '#00ccff',
    ...                 'Capped Renewable': '#ffD700',
    ...                 'Uncapped Renewable': '#ffD700',},
    ...     node_size={'Powerline': 5000},
    ...     layout='dot')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/zero_costs_example.png
        :align: center
        :alt: Image showing the zero costs example energy system graph.
    """

    # 2. Create a simulation time frame of 2 one hour time steps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3. Creating the individual energy system components:
    # emitting source having no costs and no flow constraints but emissions
    emitting_source = components.Source(
        name='Emitting Source',
        outputs=('electricity',),
        # Minimum number of arguments required
        flow_emissions={
            'electricity': 1
        },

    )

    # capped source having no costs, no emission, no flow constraints
    # but existing and max installed capacity (for expansion) as well
    # as expansion costs
    capped_renewable = components.Source(
        name='Capped Renewable',
        outputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=0, max=2)},
        expandable={'electricity': True},
        expansion_limits={'electricity': nts.MinMax(min=2, max=4)},
    )

    # uncapped source having no costs and no emissions
    # and an externally set timeseries as well as expansion costs
    uncapped_min, uncapped_max = [1, 2, 3, 1], [1, 2, 3, 1]

    uncapped_renewable = components.Source(
        name='Uncapped Renewable',
        outputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=0, max=1)},
        expandable={'electricity': True},
        timeseries={
            'electricity': nts.MinMax(
                min=uncapped_min,
                max=uncapped_max
            )
        },
        expansion_limits={
            'electricity': nts.MinMax(
                min=max(uncapped_max),
                max=float('+inf'),
            )
        },
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=(
            'Emitting Source.electricity',
            'Capped Renewable.electricity',
            'Uncapped Renewable.electricity'),
        outputs=('Demand.electricity',),
        # Minimum number of arguments required
    )

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    global_constraints = {'emissions': 8}

    # 4. Creating the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Zero Costs Example',
        busses=(electricity_line,),
        sinks=(demand,),
        sources=(
            emitting_source,
            capped_renewable,
            uncapped_renewable,
        ),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # 5. Store the energy system:

    if not filename:
        filename = 'zero_costs.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def _create_minimal_es_unit(n, timeframe=None, seed=None):
    """
    Create a minimal self simular energy system unit.

    Is used by create_self_similar_energy_system().

    The self similar energy system unit consists of:

        - 3 :class:`~tessif.model.components.Source` objects:

            - One having a randomized output, emulating renewable sources.
              With an installed power between 10 and 200 units.
            - One `slack source <https://en.wikipedia.org/wiki/Slack_bus>`_
              providing energy to balance the system if needed.
              (This could be interpreted as an import node, for meeting load
              demands)
            - One commodity source feeding the transformer

        - 2 :class:`~tessif.model.components.Sink` objects:

            - One having a fixed input with a net demand between 50 and 100
              units.
            - One `slack sink <https://en.wikipedia.org/wiki/Slack_bus>`_
              taking energy in to balance the system if needed.
              (This could be interpreted as an export node, for handling excess
              loads.)

        - 2 :class:`~tessif.model.components.Bus` objects:

            - One central bus connecting the storage and transformer, as well
              as the sinks and sources and up to 2 additional self similar
              energy system units.

            - An auxiliary bus connecting the transformer and the central bus

        - 1 :class:`~tessif.model.components.Transformer` object:

            - Fully parameterized transformer emulating a coal power plant
              with an installed capacity between 50 and 100 units.

        - 1 :class:`~tessif.model.components.Storage` object:

            - no constraints to in and outflow. Efficiency,
              losses, expansion investment etc. oriented at grid level
              batteries (e.g. tesla)

    Parameters
    ----------
    n: int
        Number of the es unit. This ist needed to be able to give each
        component in the complete self similar es a unique name.

    timeframe: pandas.DatetimeIndex
        Datetime index representing the evaluated timeframe. Explicitly
        stating:

            - initial datatime
              (0th element of the :class:`pandas.DatetimeIndex`)
            - number of time steps (length of :class:`pandas.DatetimeIndex`)
            - temporal resolution (:attr:`pandas.DatetimeIndex.freq`)

        For example::

            idx = pd.DatetimeIndex(
                data=pd.date_range(
                    '2016-01-01 00:00:00', periods=11, freq='H'))
    """
    if timeframe is None:
        timeframe = pd.date_range(
            datetime.now(),
            periods=1, freq='H')

    # See tessif.examples.data.tsf.py_hard as well as
    # tessif.model.components for examples and information
    # (both in the code and using the doc)

    # 1) randomize demand and production
    if seed:
        random.seed(seed)
    demand = random.randint(1, 100)
    renewable_output = random.randint(1, 50)

    demand_sink = components.Sink(
        name='Sink ' + str(n),
        inputs=('electricity',),
        flow_rates={'electricity': nts.MinMax(min=demand, max=demand)},)

    # excess_sink enables the energy system to be always solvable even if
    # the randomized components wouldn't provide a solvable energy system.
    excess_sink = components.Sink(
        name='Excess Sink ' + str(n),
        inputs=('electricity',),
        flow_costs={'electricity': 100})

    # 2) Create the sources
    excess_source = components.Source(
        name='Excess Source ' + str(n),
        outputs=('electricity',),
        flow_costs={'electricity': 100})

    # 2.1) renewable source
    renewable_source = components.Source(
        name='Renewable Source ' + str(n),
        outputs=('electricity',),
        flow_costs={'electricity': 5},
        node_type='Renewable',
        carrier='Electricity',
        flow_rates={'electricity': nts.MinMax(
            min=renewable_output, max=renewable_output)},
        flow_emissions={'electricity': 0},
    )

    # 2.2) non-renewable source
    non_renewable_source = components.Source(
        name='Non Renewable Source ' + str(n),
        outputs=('fuel',),
        flow_costs={'fuel': 10},
    )

    # 3) Create the transformer
    power_generator = components.Transformer(
        name='Power Generator ' + str(n),
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.42},
    )

    # 4) Create the connector. (Use connectors list to prevent error in case no
    # connector is created.)
    connectors = list()

    if n == 0:
        pass
    else:
        connector = components.Connector(
            name='Connector ' + str(n),
            interfaces=('Central Bus ' + str(n-1),
                        'Central Bus ' + str(n)),
            inputs=['Central Bus ' + str(n-1),
                    'Central Bus ' + str(n)],
            outputs=('Central Bus ' + str(n-1),
                     'Central Bus ' + str(n)),
        )
        connectors.append(connector)

    # 5) Create the storage
    storage = components.Storage(
        name='Storage ' + str(n),
        input='electricity',
        output='electricity',
        capacity=1,
        initial_soc=1
    )

    # 6) Create the bus
    central_bus = components.Bus(
        name='Central Bus ' + str(n),
        inputs=(
            'Excess Source ' + str(n) + '.electricity',
            'Storage ' + str(n) + '.electricity',
            'Renewable Source ' + str(n) + '.electricity',
            'Power Generator ' + str(n) + '.electricity',
        ),
        outputs=(
            'Excess Sink ' + str(n) + '.electricity',
            'Sink ' + str(n) + '.electricity',
            'Storage ' + str(n) + '.electricity',
        )
    )

    # There needs to be another bus which connects the transformer and the
    # non-renewable source.
    fuel_line = components.Bus(
        name='Fuel Line ' + str(n),
        inputs=(
            'Non Renewable Source ' + str(n) + '.fuel',
        ),
        outputs=(
            'Power Generator ' + str(n) + '.fuel',
        )
    )

    minimal_es = energy_system.AbstractEnergySystem(
        uid='Energy System ' + str(n),
        busses=(central_bus, fuel_line),
        sinks=(demand_sink, excess_sink),
        sources=(excess_source, non_renewable_source, renewable_source),
        connectors=connectors,
        transformers=(power_generator,),
        storages=(storage,),
        timeframe=timeframe,
    )

    return minimal_es


def _create_component_es_unit(n, timeframe, expansion_problem=False):
    """
    Create a self similar energy system unit based on the component es model.

    Is used by create_self_similar_energy_system().

    For more info on the original example look at create_component_es().

    Parameters
    ----------
    n: int
        Number of the es unit. This ist needed to be able to give each
        component in the complete self similar es a unique name.

    timeframe: pandas.DatetimeIndex
        Datetime index representing the evaluated timeframe. Explicitly
        stating:

            - initial datatime
              (0th element of the :class:`pandas.DatetimeIndex`)
            - number of time steps (length of :class:`pandas.DatetimeIndex`)
            - temporal resolution (:attr:`pandas.DatetimeIndex.freq`)

        For example::

            idx = pd.DatetimeIndex(
                data=pd.date_range(
                    '2016-01-01 00:00:00', periods=11, freq='H'))

    expansion_problem : bool, default=False
        Boolean which states whether a commitment problem (False)
        or expansion problem (True) is to be solved

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`Examples_Application_Components`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.
    """
    # Initiate the global constraints depending on the scenario
    if expansion_problem is False:
        global_constraints = {
            'name': 'Commitment_Scenario',
            'emissions': float('+inf'),
        }
    else:
        global_constraints = {
            'name': 'Expansion_Scenario',
            'emissions': 250000,
        }

    periods = len(timeframe)

    # Variables for timeseries of fluctuate wind, solar and demand
    csv_data = pd.read_csv(os.path.join(
        example_dir, 'data', 'tsf', 'load_profiles',
        'component_scenario_profiles.csv'), index_col=0, sep=';')

    # solar:
    pv = csv_data['pv'].values.flatten()[0:periods]
    # scale relative values with the installed pv power
    pv = pv * 1100

    # wind onshore:
    wind_onshore = csv_data['wind_on'].values.flatten()[0:periods]
    # scale relative values with installed onshore power
    wind_onshore = wind_onshore * 1100

    # wind offshore:
    wind_offshore = csv_data['wind_off'].values.flatten()[0:periods]
    # scale relative values with installed offshore power
    wind_offshore = wind_offshore * 150

    # electricity demand:
    el_demand = csv_data['el_demand'].values.flatten()[0:periods]
    max_el = np.max(el_demand)

    # heat demand:
    th_demand = csv_data['th_demand'].values.flatten()[0:periods]
    max_th = np.max(th_demand)

    # Creating the individual energy system components:

    # ---------------- Sources (incl wind and solar) -----------------------

    hard_coal_supply = components.Source(
        name='Hard Coal Supply ' + str(n),
        outputs=('Hard_Coal',),
        sector='Power',
        carrier='Hard_Coal',
        node_type='source',
        accumulated_amounts={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'Hard_Coal': 0},
        flow_emissions={'Hard_Coal': 0},
        flow_gradients={'Hard_Coal': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'Hard_Coal': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False},
        expansion_costs={'Hard_Coal': 0},
        expansion_limits={'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
    )

    lignite_supply = components.Source(
        name='Lignite Supply ' + str(n),
        outputs=('lignite',),
        sector='Power',
        carrier='Lignite',
        node_type='source',
        accumulated_amounts={
            'lignite': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'lignite': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'lignite': 0},
        flow_emissions={'lignite': 0},
        flow_gradients={'lignite': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'lignite': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'lignite': False},
        expansion_costs={'lignite': 0},
        expansion_limits={'lignite': nts.MinMax(min=0, max=float('+inf'))},
    )

    fuel_supply = components.Source(
        name='Gas Station ' + str(n),
        outputs=('fuel',),
        sector='Power',
        carrier='Gas',
        node_type='source',
        accumulated_amounts={
            'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        flow_gradients={'fuel': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'fuel': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False},
        expansion_costs={'fuel': 0},
        expansion_limits={'fuel': nts.MinMax(min=0, max=float('+inf'))},
    )

    biogas_supply = components.Source(
        name='Biogas Supply ' + str(n),
        outputs=('biogas',),
        sector='Power',
        carrier='Biogas',
        node_type='source',
        accumulated_amounts={
            'biogas': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'biogas': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'biogas': 0},
        flow_emissions={'biogas': 0},
        flow_gradients={'biogas': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'biogas': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'biogas': False},
        expansion_costs={'biogas': 0},
        expansion_limits={'biogas': nts.MinMax(min=0, max=float('+inf'))},
    )

    solar_panel = components.Source(
        name='Solar Panel ' + str(n),
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=1100)},
        flow_costs={'electricity': 80},
        flow_emissions={'electricity': 0.05},
        flow_gradients={'electricity': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(pv))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 1000000},
        expansion_limits={'electricity': nts.MinMax(
            min=1100, max=float('+inf'))},
    )

    onshore_wind_turbine = components.Source(
        name='Onshore Wind Turbine ' + str(n),
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=1100)},
        flow_costs={'electricity': 60},
        flow_emissions={'electricity': 0.02},
        flow_gradients={'electricity': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(wind_onshore))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 1750000},
        expansion_limits={'electricity': nts.MinMax(
            min=1100, max=float('+inf'))},
    )

    offshore_wind_turbine = components.Source(
        name='Offshore Wind Turbine ' + str(n),
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=150)},
        flow_costs={'electricity': 105},
        flow_emissions={'electricity': 0.02},
        flow_gradients={'electricity': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(wind_offshore))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 3900000},
        expansion_limits={'electricity': nts.MinMax(
            min=150, max=float('+inf'))},
    )

    # ---------------- Transformer -----------------------

    hard_coal_chp = components.Transformer(
        name='Hard Coal CHP ' + str(n),
        inputs=('Hard_Coal',),
        outputs=('electricity', 'hot_water',),
        conversions={('Hard_Coal', 'electricity'): 0.4,
                     ('Hard_Coal', 'hot_water'): 0.4},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=300),
            'hot_water': nts.MinMax(min=0, max=300)},
        flow_costs={'Hard_Coal': 0, 'electricity': 80, 'hot_water': 6},
        flow_emissions={'Hard_Coal': 0, 'electricity': 0.8, 'hot_water': 0.06},
        flow_gradients={
            'Hard_Coal': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'Hard_Coal': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False,
                    'electricity': expansion_problem,
                    'hot_water': expansion_problem},
        expansion_costs={'Hard_Coal': 0,
                         'electricity': 1750000, 'hot_water': 131250},
        expansion_limits={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=300, max=float('+inf')),
            'hot_water': nts.MinMax(min=300, max=float('+inf'))},
    )

    hard_coal_power_plant = components.Transformer(
        name='Hard Coal PP ' + str(n),
        inputs=('Hard_Coal',),
        outputs=('electricity',),
        conversions={('Hard_Coal', 'electricity'): 0.43},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=500), },
        flow_costs={'Hard_Coal': 0, 'electricity': 80},
        flow_emissions={'Hard_Coal': 0, 'electricity': 0.8},
        flow_gradients={
            'Hard_Coal': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'Hard_Coal': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False, 'electricity': expansion_problem},
        expansion_costs={'Hard_Coal': 0, 'electricity': 1650000},
        expansion_limits={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=500, max=float('+inf'))},
    )

    combined_cycle_power_plant = components.Transformer(
        name='Combined Cycle PP ' + str(n),
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.6},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=600)},
        flow_costs={'fuel': 0, 'electricity': 90},
        flow_emissions={'fuel': 0, 'electricity': 0.35},
        flow_gradients={
            'fuel': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'electricity': expansion_problem},
        expansion_costs={'fuel': 0, 'electricity': 950000},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=600, max=float('+inf'))},
    )

    lignite_power_plant = components.Transformer(
        name='Lignite Power Plant ' + str(n),
        inputs=('lignite',),
        outputs=('electricity',),
        conversions={('lignite', 'electricity'): 0.4},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'lignite': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=500)},
        flow_costs={'lignite': 0, 'electricity': 65},
        flow_emissions={'lignite': 0, 'electricity': 1},
        flow_gradients={
            'lignite': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'lignite': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'lignite': False, 'electricity': expansion_problem},
        expansion_costs={'lignite': 0, 'electricity': 1900000},
        expansion_limits={
            'lignite': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=500, max=float('+inf'))},
    )

    biogas_chp = components.Transformer(
        name='Biogas CHP ' + str(n),
        inputs=('biogas',),
        outputs=('electricity', 'hot_water',),
        conversions={('biogas', 'electricity'): 0.4,
                     ('biogas', 'hot_water'): 0.5},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'biogas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=200),
            'hot_water': nts.MinMax(min=0, max=250)},
        flow_costs={'biogas': 0, 'electricity': 150, 'hot_water': 11.25},
        flow_emissions={'biogas': 0,
                        'electricity': 0.25, 'hot_water': 0.01875},
        flow_gradients={
            'biogas': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'biogas': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'biogas': False,
                    'electricity': expansion_problem,
                    'hot_water': expansion_problem},
        expansion_costs={'biogas': 0,
                         'electricity': 3500000, 'hot_water': 262500},
        expansion_limits={
            'biogas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=200, max=float('+inf')),
            'hot_water': nts.MinMax(min=250, max=float('+inf'))},
    )

    heat_plant = components.Transformer(
        name='Heat Plant ' + str(n),
        inputs=('fuel',),
        outputs=('hot_water',),
        conversions={('fuel', 'hot_water'): 0.9},
        sector='Heat',
        carrier='hot_water',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=450)},
        flow_costs={'fuel': 0, 'hot_water': 35},
        flow_emissions={'fuel': 0, 'hot_water': 0.23},
        flow_gradients={
            'fuel': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'hot_water': expansion_problem},
        expansion_costs={'fuel': 0, 'hot_water': 390000},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=450, max=float('+inf'))},
    )

    power_to_heat = components.Transformer(
        name='Power To Heat ' + str(n),
        inputs=('electricity',),
        outputs=('hot_water',),
        conversions={('electricity', 'hot_water'): 0.99},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=100)},
        flow_costs={'electricity': 0, 'hot_water': 20},
        flow_emissions={'electricity': 0, 'hot_water': 0.0007},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'electricity': False, 'hot_water': expansion_problem},
        expansion_costs={'electricity': 0, 'hot_water': 100000},
        expansion_limits={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=100, max=float('+inf'))},
    )

    # ---------------- Storages -----------------------

    storage = components.Storage(
        name='Battery ' + str(n),
        input='electricity',
        output='electricity',
        capacity=100,
        initial_soc=0,
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.5),
        flow_rates={'electricity': nts.MinMax(min=0, max=33)},
        flow_efficiencies={
            'electricity': nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={'electricity': 400},
        flow_emissions={'electricity': 0.06},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': expansion_problem,
                    'electricity': expansion_problem},
        fixed_expansion_ratios={'electricity': expansion_problem},
        expansion_costs={'capacity': 1630000, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=100, max=float('+inf')),
            'electricity': nts.MinMax(min=33, max=float('+inf'))},
    )

    heat_storage = components.Storage(
        name='Heat Storage ' + str(n),
        input='hot_water',
        output='hot_water',
        capacity=50,
        initial_soc=0,
        sector='Heat',
        carrier='hot_water',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.25),
        flow_rates={'hot_water': nts.MinMax(min=0, max=10)},
        flow_efficiencies={
            'hot_water': nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={'hot_water': 20},
        flow_emissions={'hot_water': 0},
        flow_gradients={
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'hot_water': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': expansion_problem,
                    'hot_water': expansion_problem},
        fixed_expansion_ratios={'hot_water': expansion_problem},
        expansion_costs={'capacity': 4500, 'hot_water': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=50, max=float('+inf')),
            'hot_water': nts.MinMax(min=10, max=float('+inf'))},
    )

    # ---------------- Sinks -----------------------

    el_demand = components.Sink(
        name='El Demand ' + str(n),
        inputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=max_el)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(el_demand),
            max=np.array(el_demand))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
    )

    heat_demand = components.Sink(
        name='Heat Demand ' + str(n),
        inputs=('hot_water',),
        sector='Heat',
        carrier='hot_water',
        node_type='demand',
        accumulated_amounts={
            'hot_water': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'hot_water': nts.MinMax(min=0, max=max_th)},
        flow_costs={'hot_water': 0},
        flow_emissions={'hot_water': 0},
        flow_gradients={
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'hot_water': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'hot_water': nts.MinMax(
            min=np.array(th_demand),
            max=np.array(th_demand))},
        expandable={'hot_water': False},
        expansion_costs={'hot_water': 0},
        expansion_limits={'hot_water': nts.MinMax(
            min=0, max=float('+inf'))},
    )

    # ---------------- Busses -----------------------

    fuel_supply_line = components.Bus(
        name='Gas Line ' + str(n),
        inputs=('Gas Station ' + str(n) + '.fuel',),
        outputs=('Combined Cycle PP ' + str(n) + '.fuel',
                 'Heat Plant ' + str(n) + '.fuel'),
        sector='Coupled',
        carrier='Gas',
        node_type='bus',
    )

    biogas_supply_line = components.Bus(
        name='Biogas Line ' + str(n),
        inputs=('Biogas Supply ' + str(n) + '.biogas',),
        outputs=('Biogas CHP ' + str(n) + '.biogas',),
        sector='Coupled',
        carrier='Biogas',
        node_type='bus',
    )

    hard_coal_supply_line = components.Bus(
        name='Hard Coal Supply Line ' + str(n),
        inputs=('Hard Coal Supply ' + str(n) + '.Hard_Coal',),
        outputs=('Hard Coal PP ' + str(n) + '.Hard_Coal',
                 'Hard Coal CHP ' + str(n) + '.Hard_Coal',),
        sector='Coupled',
        carrier='Hard_Coal',
        node_type='bus',
    )

    lignite_supply_line = components.Bus(
        name='Lignite Supply Line ' + str(n),
        inputs=('Lignite Supply ' + str(n) + '.lignite',),
        outputs=('Lignite Power Plant ' + str(n) + '.lignite',),
        sector='Power',
        carrier='Lignite',
        node_type='bus',
    )

    electricity_line = components.Bus(
        name='Powerline ' + str(n),
        inputs=('Combined Cycle PP ' + str(n) + '.electricity',
                'Battery ' + str(n) + '.electricity',
                'Lignite Power Plant ' + str(n) + '.electricity',
                'Hard Coal PP ' + str(n) + '.electricity',
                'Hard Coal CHP ' + str(n) + '.electricity',
                'Solar Panel ' + str(n) + '.electricity',
                'Offshore Wind Turbine ' + str(n) + '.electricity',
                'Biogas CHP ' + str(n) + '.electricity',
                'Onshore Wind Turbine ' + str(n) + '.electricity',
                ),
        outputs=('El Demand ' + str(n) + '.electricity',
                 'Battery ' + str(n) + '.electricity',
                 'Power To Heat ' + str(n) + '.electricity'),
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    heat_line = components.Bus(
        name='Heatline ' + str(n),
        inputs=('Heat Plant ' + str(n) + '.hot_water',
                'Hard Coal CHP ' + str(n) + '.hot_water',
                'Biogas CHP ' + str(n) + '.hot_water',
                'Power To Heat ' + str(n) + '.hot_water',
                'Heat Storage ' + str(n) + '.hot_water'),
        outputs=('Heat Demand ' + str(n) + '.hot_water',
                 'Heat Storage ' + str(n) + '.hot_water'),
        sector='Heat',
        carrier='hot_water',
        node_type='bus',
    )

    # ---------------- Connectors -----------------------

    # Use connectors list to prevent error in case no connector is created.
    connectors = list()
    if n == 0:
        pass
    else:
        electricity_connector = components.Connector(
            name='Electricity Connector ' + str(n-1),
            interfaces=('Powerline ' + str(n-1),
                        'Powerline ' + str(n)),
            inputs=('Powerline ' + str(n-1),
                    'Powerline ' + str(n)),
            outputs=('Powerline ' + str(n-1),
                     'Powerline ' + str(n)),
        )
        connectors.append(electricity_connector)

        heat_connector = components.Connector(
            name='Heat Connector ' + str(n - 1),
            interfaces=('Heatline ' + str(n - 1),
                        'Heatline ' + str(n)),
            inputs=('Heatline ' + str(n - 1),
                    'Heatline ' + str(n)),
            outputs=('Heatline ' + str(n - 1),
                     'Heatline ' + str(n)),
        )
        connectors.append(heat_connector)

    # Create the actual energy system:

    explicit_es = energy_system.AbstractEnergySystem(
        uid='Component Based Energy System ' + str(n),
        busses=(fuel_supply_line, electricity_line, hard_coal_supply_line,
                lignite_supply_line, biogas_supply_line, heat_line,),
        sinks=(el_demand, heat_demand),
        sources=(fuel_supply, solar_panel, onshore_wind_turbine,
                 hard_coal_supply, lignite_supply, offshore_wind_turbine,
                 biogas_supply,),
        connectors=connectors,
        transformers=(combined_cycle_power_plant, hard_coal_power_plant,
                      lignite_power_plant, biogas_chp, heat_plant,
                      power_to_heat, hard_coal_chp),
        storages=(storage, heat_storage),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return explicit_es


def _create_grid_es_unit(n, timeframe, transformer_efficiency=0.93,
                         gridcapacity=60000, expansion=True):
    """Create a self similar energy system unit of a generic grid style es.

    Is used by create_self_similar_energy_system().

    For more info on the original example look at create_transcne_es().

    Parameters
    ----------
    n: int
        Number of the es unit. This ist needed to be able to give each
        component in the complete self similar es a unique name.

    timeframe: pandas.DatetimeIndex
        Datetime index representing the evaluated timeframe. Explicitly
        stating:

            - initial datatime
              (0th element of the :class:`pandas.DatetimeIndex`)
            - number of time steps (length of :class:`pandas.DatetimeIndex`)
            - temporal resolution (:attr:`pandas.DatetimeIndex.freq`)

        For example::

            idx = pd.DatetimeIndex(
                data=pd.date_range(
                    '2016-01-01 00:00:00', periods=11, freq='H'))

    transformer_efficiency : int, default=0.99
        Efficiency of the grid transformers (must be a value between 0 and 1)

    gridcapacity : int, default=60000
        Transmission capacity of the transformers of the grid structure
        (at 0 the parts of the grid are not connected)

    expansion: bool, default=False
        If ``True`` :paramref:`gridcapacity` is subject to expansion.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.
    """
    periods = len(timeframe)

    # Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
    }

    # -------------Low Voltage and heat ------------------

    solar_panel = components.Source(
        name='Solar Panel ' + str(n),
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='Renewable',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0,
                                                          max=max_pv+0.001)},  # TODO: Remove "+0.001" when zero division bug in es2es.cllp is fixed.
        flow_costs={'low-voltage-electricity': 60.85},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=pv, max=pv)},
    )

    gas_supply = components.Source(
        name='Gas Station ' + str(n),
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    biogas_supply = components.Source(
        name='Biogas Plant ' + str(n),
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW ' + str(n),
        inputs=('fuel',),
        outputs=('low-voltage-electricity', 'heat'),
        conversions={
            ('fuel', 'low-voltage-electricity'): 0.33,
            ('fuel', 'heat'): 0.52,
        },
        # Minimum number of arguments required',
        sector='Coupled',
        carrier='low-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'low-voltage-electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697),
        },
        flow_costs={'fuel': 0, 'low-voltage-electricity': 124.4, 'heat': 31.1},
        flow_emissions={
            'fuel': 0,
            'low-voltage-electricity': 0.1573,
            'heat': 0.0732,
        },
    )

    household_demand = components.Sink(
        name='Household Demand ' + str(n),
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand ' + str(n),
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand ' + str(n),
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline ' + str(n),
        inputs=('Gas Station ' + str(n) + '.fuel',),
        outputs=('GuD ' + str(n) + '.fuel',),
        # Minimum number of arguments required
        sector='Power',
        carrier='gas',
        node_type='bus',
    )

    biogas_supply_line = components.Bus(
        name='Biogas ' + str(n),
        inputs=('Biogas Plant ' + str(n) + '.fuel',),
        outputs=('BHKW ' + str(n) + '.fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='gas',
        node_type='bus',
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Grid ' + str(n),
        inputs=(
            'BHKW ' + str(n) + '.low-voltage-electricity',
            'Deficit Source LV ' + str(n) + '.low-voltage-electricity',
            'Solar Panel ' + str(n) + '.low-voltage-electricity',
            'Medium Low Transfer ' + str(n) + '.low-voltage-electricity',
        ),
        outputs=(
            'Household Demand ' + str(n) + '.low-voltage-electricity',
            'Commercial Demand ' + str(n) + '.low-voltage-electricity',
            'Low Medium Transfer ' + str(n) + '.low-voltage-electricity',
            'Excess Sink LV ' + str(n) + '.low-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    heat_line = components.Bus(
        name='District Heating ' + str(n),
        inputs=(
            'BHKW ' + str(n) + '.heat',
            'Solar Thermal ' + str(n) + '.heat',
            'Power to Heat ' + str(n) + '.heat',
            'HKW ' + str(n) + '.heat',
        ),
        outputs=('District Heating Demand ' + str(n) + '.heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='hot water',
        node_type='bus',
    )

    # ----- -------Medium Voltage and Heat ------------------

    onshore_wind_power = components.Source(
        name='Onshore Wind Power ' + str(n),
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='power',
        carrier='medium-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'medium-voltage-electricity': 61.1},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal ' + str(n),
        outputs=('heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        # TODO: Remove "+0.001" when zero division bug in es2es.cllp is fixed.
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t+0.001)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand ' + str(n),
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station ' + str(n),
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat ' + str(n),
        inputs=('medium-voltage-electricity',),
        outputs=('heat',),
        conversions={('medium-voltage-electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'medium-voltage-electricity': 0, 'heat': 0},
        flow_emissions={'medium-voltage-electricity': 0, 'heat': 0},
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Grid ' + str(n),
        inputs=(
            'Onshore Wind Power ' + str(n) + '.medium-voltage-electricity',
            'High Medium Transfer ' + str(n) + '.medium-voltage-electricity',
            'Low Medium Transfer ' + str(n) + '.medium-voltage-electricity',
            'Deficit Source MV ' + str(n) + '.medium-voltage-electricity',
        ),
        outputs=(
            'Car charging Station ' + str(n) + '.medium-voltage-electricity',
            'Industrial Demand ' + str(n) + '.medium-voltage-electricity',
            'Power to Heat ' + str(n) + '.medium-voltage-electricity',
            'Medium High Transfer ' + str(n) + '.medium-voltage-electricity',
            'Medium Low Transfer ' + str(n) + '.medium-voltage-electricity',
            'Excess Sink MV ' + str(n) + '.medium-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    # ----------------- High Voltage -------------------------

    offshore_wind_power = components.Source(
        name='Offshore Wind Power ' + str(n),
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='high-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'high-voltage-electricity': 106.4},
        flow_emissions={'high-voltage-electricity': 0},
        timeseries={
            'high-voltage-electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply ' + str(n),
        outputs=('fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
    )

    hkw_generator = components.Transformer(
        name='HKW ' + str(n),
        inputs=('fuel',),
        outputs=('high-voltage-electricity', 'heat'),
        conversions={
            ('fuel', 'high-voltage-electricity'): 0.24,
            ('fuel', 'heat'): 0.6,
        },
        # Minimum number of arguments required
        sector='Coupled',
        carrier='high-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96),
        },
        flow_costs={
            'fuel': 0,
            'high-voltage-electricity': 80.65,
            'heat': 20.1625,
        },
        flow_emissions={
            'fuel': 0,
            'high-voltage-electricity': 0.5136,
            'heat': 0.293,
        },
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2 ' + str(n),
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.43},
        # Minimum number of arguments required
        sector='Coupled',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=43913),
        },
        flow_costs={'fuel': 0, 'high-voltage-electricity': 80.65},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.5136},
    )

    gud_generator = components.Transformer(
        name='GuD ' + str(n),
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.59},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='generator',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'high-voltage-electricity': nts.MinMax(min=0, max=26742),
        },
        flow_costs={'fuel': 0, 'high-voltage-electricity': 88.7},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.3366},
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line ' + str(n),
        inputs=('Coal Supply ' + str(n) + '.fuel',),
        outputs=('HKW ' + str(n) + '.fuel', 'HKW2 ' + str(n) + '.fuel'),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
    )

    high_electricity_line = components.Bus(
        name='High Voltage Grid ' + str(n),
        inputs=(
            'Offshore Wind Power ' + str(n) + '.high-voltage-electricity',
            'HKW2 ' + str(n) + '.high-voltage-electricity',
            'GuD ' + str(n) + '.high-voltage-electricity',
            'HKW ' + str(n) + '.high-voltage-electricity',
            'Medium High Transfer ' + str(n) + '.high-voltage-electricity',
            'Deficit Source HV ' + str(n) + '.high-voltage-electricity',
        ),
        outputs=(
            'Pumped Storage ' + str(n) + '.high-voltage-electricity',
            'High Medium Transfer ' + str(n) + '.high-voltage-electricity',
            'Excess Sink HV ' + str(n) + '.high-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    # Grid Structure and Transformer

    low_medium_transformator = components.Transformer(
        name='Low Medium Transfer ' + str(n),
        inputs=('low-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={('low-voltage-electricity',
                      'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        flow_emissions={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 0},
        expandable={
            'low-voltage-electricity': False,
            'medium-voltage-electricity': expansion,
        },
        expansion_costs={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        expansion_limits={
            'low-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    medium_low_transformator = components.Transformer(
        name='Medium Low Transfer ' + str(n),
        inputs=('medium-voltage-electricity',),
        outputs=('low-voltage-electricity',),
        conversions={('medium-voltage-electricity',
                      'low-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'low-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),

        },
        flow_costs={
            'medium-voltage-electricity': 0,
            'low-voltage-electricity': 10,
        },
        flow_emissions={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 0,
        },
        expandable={
            'medium-voltage-electricity': False,
            'low-voltage-electricity': expansion,
        },
        expansion_costs={
            'medium-voltage-electricity': 0,
            'low-voltage-electricity': 10,
        },
        expansion_limits={
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'low-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    medium_high_transformator = components.Transformer(
        name='Medium High Transfer ' + str(n),
        inputs=('medium-voltage-electricity',),
        outputs=('high-voltage-electricity',),
        conversions={
            ('medium-voltage-electricity',
             'high-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'high-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 10,
        },
        flow_emissions={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 0,
        },
        expandable={
            'medium-voltage-electricity': False,
            'high-voltage-electricity': expansion,
        },
        expansion_costs={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 10,
        },
        expansion_limits={
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'high-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    high_medium_transformator = components.Transformer(
        name='High Medium Transfer ' + str(n),
        inputs=('high-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={
            ('high-voltage-electricity',
             'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        flow_emissions={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 0,
        },
        expandable={
            'high-voltage-electricity': False,
            'medium-voltage-electricity': expansion,
        },
        expansion_costs={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        expansion_limits={
            'high-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    # ---------- Deficit Sources ---------------

    power_source_lv = components.Source(
        name='Deficit Source LV ' + str(n),
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
    )

    power_source_mv = components.Source(
        name='Deficit Source MV ' + str(n),
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
        },
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
    )

    power_source_hv = components.Source(
        name='Deficit Source HV ' + str(n),
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
    )

    power_sink_lv = components.Sink(
        name='Excess Sink LV ' + str(n),
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
    )

    # ------------------- Excess Sinks --------------------------
    power_sink_mv = components.Sink(
        name='Excess Sink MV ' + str(n),
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
        },
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
    )

    power_sink_hv = components.Sink(
        name='Excess Sink HV ' + str(n),
        inputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
    )

    # ---------------- Connectors -----------------------

    # Use connectors list to prevent error in case no connector is created.
    connectors = list()
    if n == 0:
        pass
    else:
        lv_connector = components.Connector(
            name='LV Connector ' + str(n-1),
            interfaces=('Low Voltage Grid ' + str(n-1),
                        'Low Voltage Grid ' + str(n)),
            inputs=('Low Voltage Grid ' + str(n-1),
                    'Low Voltage Grid ' + str(n)),
            outputs=('Low Voltage Grid ' + str(n-1),
                     'Low Voltage Grid ' + str(n)),
        )
        connectors.append(lv_connector)

        mv_connector = components.Connector(
            name='MV Connector ' + str(n-1),
            interfaces=('Medium Voltage Grid ' + str(n-1),
                        'Medium Voltage Grid ' + str(n)),
            inputs=('Medium Voltage Grid ' + str(n-1),
                    'Medium Voltage Grid ' + str(n)),
            outputs=('Medium Voltage Grid ' + str(n-1),
                     'Medium Voltage Grid ' + str(n)),
        )
        connectors.append(mv_connector)

        hv_connector = components.Connector(
            name='HV Connector ' + str(n-1),
            interfaces=('High Voltage Grid ' + str(n-1),
                        'High Voltage Grid ' + str(n)),
            inputs=('High Voltage Grid ' + str(n-1),
                    'High Voltage Grid ' + str(n)),
            outputs=('High Voltage Grid ' + str(n-1),
                     'High Voltage Grid ' + str(n)),
        )
        connectors.append(hv_connector)

        heat_connector = components.Connector(
            name='Heat Connector ' + str(n - 1),
            interfaces=('District Heating ' + str(n - 1),
                        'District Heating ' + str(n)),
            inputs=('District Heating ' + str(n - 1),
                    'District Heating ' + str(n)),
            outputs=('District Heating ' + str(n - 1),
                     'District Heating ' + str(n)),
        )
        connectors.append(heat_connector)

    # Create the actual energy system:
    if expansion:
        uid = "TransE"
    else:
        uid = "TransC"

    es = energy_system.AbstractEnergySystem(
        uid=uid,
        busses=(
            gas_supply_line,
            low_electricity_line,
            heat_line,
            medium_electricity_line,
            high_electricity_line,
            coal_supply_line,
            biogas_supply_line,
        ),
        sinks=(
            household_demand,
            commercial_demand,
            heat_demand,
            industrial_demand,
            car_charging_station_demand,
            power_sink_lv,
            power_sink_mv,
            power_sink_hv,
        ),
        sources=(
            solar_panel,
            offshore_wind_power,
            onshore_wind_power,
            gas_supply,
            coal_supply,
            solar_thermal,
            biogas_supply,
            power_source_lv,
            power_source_mv,
            power_source_hv,
        ),
        connectors=connectors,
        transformers=(
            bhkw_generator,
            power_to_heat,
            gud_generator,
            hkw_generator,
            high_medium_transformator,
            low_medium_transformator,
            medium_low_transformator,
            medium_high_transformator,
            hkw_generator_2,
        ),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return es


def _create_hhes_unit(n, timeframe):
    """
    Create a self similar energy system unit based on a model of Hamburgs es.

    Is used by create_self_similar_energy_system().

    For more info on the original example look at create_hhes().


    Parameters
    ----------
    n: int
        Number of the es unit. This ist needed to be able to give each
        component in the complete self similar es a unique name.

    timeframe: pandas.DatetimeIndex
        Datetime index representing the evaluated timeframe. Explicitly
        stating:

            - initial datatime
              (0th element of the :class:`pandas.DatetimeIndex`)
            - number of time steps (length of :class:`pandas.DatetimeIndex`)
            - temporal resolution (:attr:`pandas.DatetimeIndex.freq`)

        For example::

            idx = pd.DatetimeIndex(
                data=pd.date_range(
                    '2016-01-01 00:00:00', periods=11, freq='H'))

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_HH` - For simulating and
    comparing this energy system using different supported models.
    """
    periods = len(timeframe)

    # Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv_HH = pd.read_csv(os.path.join(d, 'solar_HH_2019.csv'), index_col=0,
                        sep=';')
    pv_HH = pv_HH.values.flatten()[0:periods]
    max_pv = np.max(pv_HH)

    # wind onshore:
    wo_HH = pd.read_csv(os.path.join(d, 'wind_HH_2019.csv'), index_col=0,
                        sep=';')
    wo_HH = wo_HH.values.flatten()[0:periods]
    max_wo = np.max(wo_HH)

    # electricity demand:
    de_HH = pd.read_csv(os.path.join(d, 'el_demand_HH_2019.csv'), index_col=0,
                        sep=';')
    de_HH = de_HH['Last (MW)'].values.flatten()[0:periods]
    de_HH = np.array(de_HH)
    max_de = np.max(de_HH)

    # heat demand:
    th_HH = pd.read_csv(os.path.join(d, 'th_demand_HH_2019.csv'), index_col=0,
                        sep=';')
    th_HH = th_HH['actual_total_load'].values.flatten()[0:periods]
    th_HH = np.array(th_HH)
    max_th = np.max(th_HH)

    # Create the individual energy system components:
    in_stat = False
    cfba = 0

    # Global Constraints:
    global_constraints = {
        'name': '2019',
        'emissions': float('+inf'),
        # 'resources': float('+inf'),
    }

    # Fossil Sources:
    gass = components.Source(
        name='gas supply ' + str(n),
        outputs=('gas',),
        region='HH',
        node_type='gas_supply',
        component='source',
        sector='coupled',
        carrier='gas',
        flow_emissions={'gas': 0.2},
    )

    coals = components.Source(
        name='coal supply ' + str(n),
        outputs=('coal',),
        region='HH',
        node_type='coal_supply',
        component='source',
        sector='coupled',
        carrier='coal',
        flow_emissions={'coal': 0.34},
    )

    oils = components.Source(
        name='oil supply ' + str(n),
        outputs=('oil',),
        region='HH',
        node_type='oil_supply',
        component='source',
        sector='power',
        carrier='oil',
    )

    waste = components.Source(
        name='waste ' + str(n),
        outputs=('waste',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='coupled',
        carrier='waste',
        flow_emissions={'waste': 0.0426},
    )

    # HKW ADM:
    chp1 = components.Transformer(
        name='chp1 ' + str(n),
        inputs=('gas',),
        outputs=('electricity',
                 'hot_water'),
        conversions={
            ('gas', 'electricity'): 0.3773,
            ('gas', 'hot_water'): 0.3,
        },  # conventional_power_plants_DE.xls
        latitude=53.51,
        longitude=9.94985,
        region='HH',
        node_type='HKW ADM',
        component='transformer',
        sector='coupled',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf')),  # 6.75
            'hot_water': nts.MinMax(min=0, max=float('+inf'))
        },
        flow_costs={'gas': 0,
                    'electricity': 90,
                    'hot_water': 21.6},

        # emissions are attributed to gas supply
        # so pypsa can handle them better
        flow_emissions={'gas': 0,  # 0.2,
                        'electricity': 0,  # 0.2/0.3773,
                        'hot_water': 0},  # 0.2/0.3},

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 1),
        status_changing_costs=nts.OnOff(24, 0),
        costs_for_being_active=cfba,
    )

    # HKW Moorburg
    pp1 = components.Transformer(
        name='pp1 ' + str(n),
        inputs=('coal',),
        outputs=('electricity',),
        conversions={('coal', 'electricity'): 0.4625},
        latitude=53.489,
        longitude=9.949,
        region='HH',
        node_type='HKW Moorburg Block A',
        component='transformer',
        sector='power',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=784),  # 296
        },
        flow_costs={
            'coal': 0,
            'electricity': 82
        },

        flow_emissions={
            'coal': 0,  # 0.34,
            'electricity': 0.34/0.4625
        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    pp2 = components.Transformer(
        name='pp2 ' + str(n),
        inputs=('coal',),
        outputs=('electricity',),
        conversions={('coal', 'electricity'): 0.4625},
        latitude=53.489,
        longitude=9.949,
        region='HH',
        node_type='HKW Moorburg Block B',
        component='transformer',
        sector='power',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=784)  # 296
        },
        flow_costs={'coal': 0,
                    'electricity': 82},

        flow_emissions={
            'coal': 0,  # 0.34,
            'electricity': 0.34/0.4625
        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    # HKW Tiefstack:
    chp2 = components.Transformer(
        name='chp2 ' + str(n),
        inputs=('gas',),
        outputs=('electricity',
                 'hot_water',),
        conversions={
            ('gas', 'electricity'): 0.585,
            ('gas', 'hot_water'): 0.40,
        },
        latitude=53.53,
        longitude=10.07,
        region='HH',
        node_type='HKW Tiefstack GuD',
        component='transformer',
        sector='coupled',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=123),  # 51
            'hot_water': nts.MinMax(min=0, max=180),
        },
        flow_costs={'gas': 0,
                    'electricity': 90,
                    'hot_water': 18.9,
                    },
        # emissions are attributed to gas supply
        # so pypsa can handle them better
        flow_emissions={'gas': 0,  # 0.2,
                        'electricity': 0,  # 0.2/0.585,
                        'hot_water': 0,  # 0.2/0.4,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 5),
        status_changing_costs=nts.OnOff(40, 0),
        costs_for_being_active=cfba,
    )

    chp3 = components.Transformer(
        name='chp3 ' + str(n),
        inputs=('coal',),
        outputs=('electricity',
                 'hot_water',),
        conversions={('coal', 'electricity'): 0.4075,
                     ('coal', 'hot_water'): 0.40,
                     },
        latitude=53.53,
        longitude=10.06,
        region='HH',
        node_type='HKW Tiefstack Block 2',
        component='transformer',
        sector='coupled',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=188),  # 68
            'hot_water': nts.MinMax(min=0, max=293),
        },
        flow_costs={'coal': 0,
                    'electricity': 82,
                    'hot_water': 19.68,
                    },
        # emissions are attributed to coal supply
        # so pypsa can handle them better
        flow_emissions={'coal': 0,  # 0.34,
                        'electricity': 0,  # 0.34/0.4075,
                        'hot_water': 0,  # 0.34/0.4,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    # Wedel GT:
    pp3 = components.Transformer(
        name='pp3 ' + str(n),
        inputs=('oil',),
        outputs=('electricity',),
        conversions={
            ('oil', 'electricity'): 0.3072
        },
        latitude=53.5662,
        longitude=9.72864,
        region='SH',
        node_type='Wedel GT A',
        component='transformer',
        sector='power',
        carrier='oil',

        flow_rates={
            'oil': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=50.5)  # 20.2
        },
        flow_costs={'oil': 0,
                    'electricity': 90
                    },
        flow_emissions={'oil': 0,  # 0.28,
                        'electricity': 0.28/0.3072,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(45, 0),
        costs_for_being_active=cfba,
    )

    pp4 = components.Transformer(
        name='pp4 ' + str(n),
        inputs=('oil',),
        outputs=('electricity',),
        conversions={
            ('oil', 'electricity'): 0.3072
        },
        latitude=53.5662,
        longitude=9.72864,
        region='SH',
        node_type='Wedel GT B',
        component='transformer',
        sector='power',
        carrier='oil',

        flow_rates={
            'oil': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=50.5)  # 20.2
        },
        flow_costs={'oil': 0,
                    'electricity': 90
                    },
        flow_emissions={'oil': 0,  # 0.28,
                        'electricity': 0.28/0.3072,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(45, 0),
        costs_for_being_active=cfba,
    )

    # HKW Wedel:
    chp4 = components.Transformer(
        name='chp4 ' + str(n),
        inputs=('coal',),
        outputs=('electricity',
                 'hot_water',),
        conversions={('coal', 'electricity'): 0.4075,
                     ('coal', 'hot_water'): 0.40,
                     },
        latitude=53.5667,
        longitude=9.72864,
        region='SH',
        node_type='HKW Wedel Block 1',
        component='transformer',
        sector='coupled',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=130),  # 57
            'hot_water': nts.MinMax(min=0, max=130),
        },
        flow_costs={'coal': 0,
                    'electricity': 82,
                    'hot_water': 19.68,
                    },
        # emissions are attributed to coal supply
        # so pypsa can handle them better
        flow_emissions={'coal': 0,  # 0.34,
                        'electricity': 0,  # 0.34/0.4075,
                        'hot_water': 0,  # 0.34/0.40,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    chp5 = components.Transformer(
        name='chp5 ' + str(n),
        inputs=('coal',),
        outputs=('electricity',
                 'hot_water'),
        conversions={('coal', 'electricity'): 0.4075,
                     ('coal', 'hot_water'): 0.40,
                     },
        latitude=53.5667,
        longitude=9.72864,
        region='SH',
        node_type='HKW Wedel Block 2',
        component='transformer',
        sector='coupled',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=118),  # 44
            'hot_water': nts.MinMax(min=0, max=88),
        },
        flow_costs={'coal': 0,
                    'electricity': 82,
                    'hot_water': 19.68,
                    },
        # emissions are attributed to coal supply
        # so pypsa can handle them better
        flow_emissions={'coal': 0,  # 0.34,
                        'electricity': 0,  # 0.34/0.4075,
                        'hot_water': 0,  # 0.34/0.40,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    # MVR Waste Combustion Rugenberger Damm:
    chp6 = components.Transformer(
        name='chp6 ' + str(n),
        inputs=('waste',),
        outputs=('electricity',
                 'hot_water',),
        conversions={('waste', 'electricity'): 0.06,
                     ('waste', 'hot_water'): 0.15,
                     },
        latitude=53.52111,
        longitude=9.93339,
        region='HH',
        node_type='MVR Müllverwertung Rugenberger Damm',
        component='transformer',
        sector='coupled',
        carrier='waste',

        flow_rates={
            'waste': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=24),  # 9.6
            'hot_water': nts.MinMax(min=0, max=70),
        },
        flow_costs={'waste': 0,
                    'electricity': 82,
                    'hot_water': 20,
                    },

        # emissions are attributed to waste supply
        # so pypsa can handle them better
        flow_emissions={'waste': 0,  # 0.0426,
                        'electricity': 0,  # 0.0426/0.06,
                        'hot_water': 0,  # 0.0426/0.15,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(40, 0),
        costs_for_being_active=cfba,
    )

    # Heizwerk Hafencity:
    hp1 = components.Transformer(
        name='hp1 ' + str(n),
        inputs=('gas',),
        outputs=('hot_water',),
        conversions={('gas', 'hot_water'): 0.96666, },
        latitude=53.54106052,
        longitude=9.99590096,
        region='HH',
        node_type='Heizwerk Hafencity',
        component='transformer',
        sector='heat',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=348),  # max=348
        },
        flow_costs={'gas': 0,
                    'hot_water': 20,
                    },
        flow_emissions={'gas': 0.0,  # 0.2
                        'hot_water': 0.2/0.96666,
                        },

        expandable={'gas': False,
                    'hot_water': True},
        expansion_costs={'gas': 0,
                         'hot_water': 0, },
        expansion_limits={'gas': nts.MinMax(min=0, max=float('+inf')),
                          'hot_water': nts.MinMax(min=348, max=float('+inf'))},
    )

    # Biomass Combined Heat and Power
    bm_chp = components.Transformer(
        name='biomass chp ' + str(n),
        latitude=53.54106052,
        longitude=9.99590096,
        region='HH',
        node_type='Heizwerk Hafencity',
        component='transformer',
        sector='heat',
        carrier='gas',
        inputs=('biomass',),
        outputs=('electricity', 'hot_water',),
        conversions={
            ('biomass', 'electricity'): 48.4/126,
            ('biomass', 'hot_water'): 1,
        },
        flow_rates={
            'biomass': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=48.4),
            'hot_water': nts.MinMax(min=0, max=126),
        },
        flow_costs={
            'biomass': 0,
            'electricity': 61,  # 61
            'hot_water': 20,  # 61
        },
        flow_emissions={
            'biomass': 0,
            # emissions reallocated to source
            'electricity': 0,  # 0.001,
            'hot_water': 0,  # 0.001,
        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(40, 0),
    )

    # Renewables:
    pv1 = components.Source(
        name='pv1 ' + str(n),
        outputs=('electricity',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='power',
        carrier='solar',

        # TODO: Remove "+0.001" when zero division bug in es2es.cllp is fixed.
        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv+0.001)},
        flow_costs={'electricity': 74},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv_HH, max=pv_HH)},

        expandable={'electricity': True},
        expansion_costs={'electricity': economics.annuity(capex=1000000, n=20,
                                                          wacc=0.05)},
        expansion_limits={'electricity': nts.MinMax(
            min=max_pv+0.001, max=float('+inf'))},  # TODO: Remove "+0.001" when zero division bug in es2es.cllp is fixed.
    )

    won1 = components.Source(
        name='won1 ' + str(n),
        outputs=('electricity',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='power',
        carrier='wind',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_wo)},
        flow_costs={'electricity': 61},
        flow_emissions={'electricity': 0.007},  # 0.007
        timeseries={'electricity': nts.MinMax(min=wo_HH, max=wo_HH)},

        expandable={'electricity': True},
        expansion_costs={'electricity': economics.annuity(capex=1750000, n=20,
                                                          wacc=0.05)},
        expansion_limits={'electricity': nts.MinMax(
            min=max_wo, max=float('+inf'))},
    )

    bm_supply = components.Source(
        name='biomass supply ' + str(n),
        outputs=('biomass',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='coupled',
        carrier='biomass',
        # reallocating the biomass chp emissions to the source
        flow_emissions={'biomass': 0.001/1+0.001/(48.8/126)},
    )

    # Storages:
    est = components.Storage(
        name='est ' + str(n),
        input='electricity',
        output='electricity',
        capacity=1,
        initial_soc=1,

        region='HH',
        sector='power',
        carrier='electricity',
        component='storage',

        flow_rates={'electricity': nts.MinMax(0, float('+inf'))},
        flow_costs={'electricity': 20},
        flow_emissions={'electricity': 0},

        expendable={'capacity': True, 'electricity': False},
        expansion_costs={'capacity': economics.annuity(capex=1000000, n=10,
                                                       wacc=0.05)}
    )

    # P2H Karoline:
    p2h = components.Transformer(
        name='p2h ' + str(n),
        inputs=('electricity',),
        outputs=('hot_water',),
        conversions={('electricity', 'hot_water'): 0.99, },
        latitude=53.55912,
        longitude=9.97148,
        region='HH',
        node_type='power2heat',
        component='transformer',
        sector='heat',
        carrier='hot_water',

        flow_rates={'electricity': nts.MinMax(min=0, max=float('+inf')),
                    'hot_water': nts.MinMax(min=0, max=45)},  # 45
        flow_costs={'electricity': 0,
                    'hot_water': 0},
        flow_emissions={'electricity': 0,
                        'hot_water': 0},  # 0.007
        expandable={'electricity': False,
                    'hot_water': True},
        expansion_costs={'hot_water': economics.annuity(capex=200000, n=30,
                                                        wacc=0.05)},
        expansion_limits={'hot_water': nts.MinMax(min=45, max=200)},

    )

    # Imported Electricity/ Heat:
    imel = components.Source(
        name='imported el ' + str(n),
        outputs=('electricity',),
        region='HH',
        node_type='import',
        component='source',
        sector='power',
        carrier='electricity',

        flow_costs={'electricity': 999},
        flow_emissions={'electricity': 0.401},

        expendable={'electricity': True},
        expansion_costs={'electricity': 999999999},
    )

    imth = components.Source(
        name='imported heat ' + str(n),
        outputs=('hot_water',),
        region='HH',
        node_type='import',
        component='source',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),

        flow_costs={'hot_water': 999},
        flow_emissions={'hot_water': 0.1},

        expendable={'hot_water': True},
        expansion_costs={'hot_water': 999999999},
    )

    # Sinks:
    demand_el = components.Sink(
        name='demand el ' + str(n),
        inputs=('electricity',),
        region='HH',
        node_type='demand',
        component='sink',
        sector='power',
        carrier='electricity',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_de)},
        timeseries={'electricity': nts.MinMax(min=de_HH, max=de_HH)},
    )

    demand_th = components.Sink(
        name='demand th ' + str(n),
        inputs=('hot_water',),
        region='HH',
        node_type='demand',
        component='sink',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),

        flow_rates={'hot_water': nts.MinMax(min=0, max=max_th)},
        timeseries={'hot_water': nts.MinMax(min=th_HH, max=th_HH)},
    )

    excess_el = components.Sink(
        name='excess el ' + str(n),
        inputs=('electricity',),
        region='HH',
        node_type='excess',
        component='sink',
        sector='power',
        carrier='electricity',
    )

    excess_th = components.Sink(
        name='excess th ' + str(n),
        inputs=('hot_water',),
        region='HH',
        node_type='excess',
        component='sink',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),
    )

    # Busses:
    bm_logistics = components.Bus(
        name='biomass logistics ' + str(n),
        region='HH',
        node_type='logistics',
        component='bus',
        sector='coupled',
        carrier='biomass',

        inputs=('biomass supply ' + str(n) + '.biomass',),
        outputs=('biomass chp ' + str(n) + '.biomass',),
    )

    gas_pipeline = components.Bus(
        name='gas pipeline ' + str(n),
        region='HH',
        node_type='gas_pipeline',
        component='bus',
        sector='coupled',
        carrier='gas',

        inputs=('gas supply ' + str(n) + '.gas',),
        outputs=('chp1 ' + str(n) + '.gas',
                 'chp2 ' + str(n) + '.gas',

                 'hp1 ' + str(n) + '.gas'),
    )

    coal_supply_line = components.Bus(
        name='coal supply line ' + str(n),
        region='HH',
        node_type='gas_pipeline',
        component='bus',
        sector='coupled',
        carrier='coal',

        inputs=('coal supply ' + str(n) + '.coal',),
        outputs=('pp1 ' + str(n) + '.coal',
                 'pp2 ' + str(n) + '.coal',
                 'chp3 ' + str(n) + '.coal',
                 'chp4 ' + str(n) + '.coal',
                 'chp5 ' + str(n) + '.coal',),
    )

    oil_supply_line = components.Bus(
        name='oil supply line ' + str(n),
        region='HH',
        node_type='oil_delivery',
        component='bus',
        sector='power',
        carrier='oil',

        inputs=('oil supply ' + str(n) + '.oil',),
        outputs=('pp3 ' + str(n) + '.oil',
                 'pp4 ' + str(n) + '.oil',),
    )

    waste_supply = components.Bus(
        name='waste supply ' + str(n),
        region='HH',
        node_type='waste_supply',
        component='bus',
        sector='coupled',
        carrier='waste',

        inputs=('waste ' + str(n) + '.waste',),
        outputs=('chp6 ' + str(n) + '.waste',),
    )

    powerline = components.Bus(
        name='Powerline ' + str(n),
        region='HH',
        node_type='powerline',
        component='bus',
        sector='power',
        carrier='electricity',

        inputs=('chp1 ' + str(n) + '.electricity',
                'chp2 ' + str(n) + '.electricity',
                'chp3 ' + str(n) + '.electricity',
                'chp4 ' + str(n) + '.electricity',
                'chp5 ' + str(n) + '.electricity',
                'chp6 ' + str(n) + '.electricity',

                'pp1 ' + str(n) + '.electricity',
                'pp2 ' + str(n) + '.electricity',
                'pp3 ' + str(n) + '.electricity',
                'pp4 ' + str(n) + '.electricity',

                'pv1 ' + str(n) + '.electricity',
                'won1 ' + str(n) + '.electricity',
                'biomass chp ' + str(n) + '.electricity',
                # 'bm1 ' + str(n) + '.electricity',

                'imported el ' + str(n) + '.electricity',

                'est ' + str(n) + '.electricity'),
        outputs=('demand el ' + str(n) + '.electricity',
                 'excess el ' + str(n) + '.electricity',

                 'est ' + str(n) + '.electricity',

                 'p2h ' + str(n) + '.electricity',),
    )

    district_heating = components.Bus(
        name='District Heating Pipeline ' + str(n),
        region='HH',
        node_type='district_heating_pipeline',
        component='bus',
        sector='heat',
        carrier='hot_water',

        inputs=('chp1 ' + str(n) + '.hot_water',
                'chp2 ' + str(n) + '.hot_water',
                'chp3 ' + str(n) + '.hot_water',
                'chp4 ' + str(n) + '.hot_water',
                'chp6 ' + str(n) + '.hot_water',
                'chp5 ' + str(n) + '.hot_water',

                # 'bm1 ' + str(n) + '.hot_water',
                'biomass chp ' + str(n) + '.hot_water',

                'imported heat ' + str(n) + '.hot_water',

                'p2h ' + str(n) + '.hot_water',

                'hp1 ' + str(n) + '.hot_water',),
        outputs=('demand th ' + str(n) + '.hot_water',
                 'excess th ' + str(n) + '.hot_water',),)

    # ---------------- Connectors -----------------------

    # Use connectors list to prevent error in case no connector is created.
    connectors = list()
    if n == 0:
        pass
    else:
        electricity_connector = components.Connector(
            name='Electricity Connector ' + str(n-1),
            interfaces=('Powerline ' + str(n-1),
                        'Powerline ' + str(n)),
            inputs=('Powerline ' + str(n-1),
                    'Powerline ' + str(n)),
            outputs=('Powerline ' + str(n-1),
                     'Powerline ' + str(n)),
        )
        connectors.append(electricity_connector)

        heat_connector = components.Connector(
            name='Heat Connector ' + str(n - 1),
            interfaces=('District Heating Pipeline ' + str(n - 1),
                        'District Heating Pipeline ' + str(n)),
            inputs=('District Heating Pipeline ' + str(n - 1),
                    'District Heating Pipeline ' + str(n)),
            outputs=('District Heating Pipeline ' + str(n - 1),
                     'District Heating Pipeline ' + str(n)),
        )
        connectors.append(heat_connector)

    # Create the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Energy System Hamburg',
        busses=(coal_supply_line, gas_pipeline, oil_supply_line, waste_supply,
                powerline, district_heating, bm_logistics),
        sinks=(demand_el, demand_th, excess_el, excess_th,),
        sources=(gass, coals, oils, waste, pv1,
                 won1, bm_supply, imel, imth,),
        connectors=connectors,
        transformers=(chp1, chp2, chp3, chp4, chp5, chp6, pp1, pp2, pp3, pp4,
                      hp1, p2h, bm_chp),
        storages=(est,),
        timeframe=timeframe,
        global_constraints=global_constraints,
        # milp=True,
    )

    return explicit_es


def create_self_similar_energy_system(N=1, timeframe=None, unit='minimal',
                                      **kwargs):
    """
    Create a `self-similar <https://en.wikipedia.org/wiki/Self-similarity>`_
    energy system.

    This energy system is obtained by repeating its unit N times. The singular
    units are connected to each other through their central bus. Meaning the
    central bus of energy system N is connected to the central bus of energy
    system N-1 via a :class:`~tessif.model.components.Connector` object.

    Parameters
    ----------
    N: int
        Number of units the self similar energy system consists of.

    timeframe: pandas.DatetimeIndex
        Datetime index representing the evaluated timeframe. Explicitly
        stating:

            - initial datatime
              (0th element of the :class:`pandas.DatetimeIndex`)
            - number of time steps (length of :class:`pandas.DatetimeIndex`)
            - temporal resolution (:attr:`pandas.DatetimeIndex.freq`)

        For example::

            idx = pd.DatetimeIndex(
                data=pd.date_range(
                    '2016-01-01 00:00:00', periods=11, freq='H'))

    unit: str
        Specify which of tessif's hardcoded examples should be used as unit of
        the self similar energy system.

        Currently available are:

            - 'minimal':
                Uses _create_minimal_es_unit() which is the smallest unit
                available.
            - 'component':
                Uses _create_component_es_unit() which is based on
                create_component_es().
            - 'grid':
                Uses _create_grid_es_unit() which is based on
                create_transcne_es().
            - 'hamburg':
                Uses _create_hhes_unit() which is based on create_hhes_unit().

    kwargs:
        Are passed to the _create_[...]_unit() function.

    Examples
    --------
    Create a self similar energy system out of N=2 minimum self similar energy
    system units:

    >>> from tessif.frused.paths import example_dir
    >>> import os
    >>> storage_path = os.path.join(example_dir, 'data', 'tsf',)

    >>> import tessif.examples.data.tsf.py_hard as coded_examples
    >>> sses = coded_examples.create_self_similar_energy_system(N=2)

    # Create an image using AbstractEnergySystem.to_nxgrph() and
    # tessif.visualize.nxgrph
    """
    if timeframe is None:
        timeframe = pd.date_range(
            datetime.now().date(),
            periods=2, freq='H')

    # Create the energy system using tessif
    fractals = list()
    for n in range(N):
        # the n-th energy system starting to count at 0 is added to the list of
        # es units.
        if unit == 'minimal':
            fractals.append(_create_minimal_es_unit(n=n, timeframe=timeframe,
                                                    **kwargs))
        elif unit == 'component':
            fractals.append(_create_component_es_unit(n=n, timeframe=timeframe,
                                                      **kwargs))
        elif unit == 'grid':
            fractals.append(_create_grid_es_unit(n=n, timeframe=timeframe,
                                                 **kwargs))
        elif unit == 'hamburg':
            fractals.append(_create_hhes_unit(n=n, timeframe=timeframe,
                                              **kwargs))

    self_similar_es = energy_system.AbstractEnergySystem(
        uid=''.join(['Self_Similar_Energy_System_(N=', str(N), ')']),
        busses=[bus for fractal in fractals for bus in fractal.busses],
        sinks=[sink for fractal in fractals for sink in fractal.sinks],
        sources=[source for fractal in fractals for source in fractal.sources],
        connectors=[connector for fractal in fractals
                    for connector in fractal.connectors],
        transformers=[transformer for fractal in fractals
                      for transformer in fractal.transformers],
        storages=[storage for fractal in fractals
                  for storage in fractal.storages],
        timeframe=timeframe)

    return self_similar_es


def create_chp(directory=None, filename=None):
    """
    Create a minimal working example using :mod:`tessif's
    model <tessif.model>` optimizing it for costs to demonstrate
    a chp application.

    Creates a simple energy system simulation to potentially
    store it on disc inside :paramref:`~create_chp.directory` as
    :paramref:`~create_chp.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_chp.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``chp.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_CHP` - For simulating and
    comparing this energy system using different supported models.

    Examples
    --------

    Use :func:`create_chp` to quickly access a tessif energy system
    to use for doctesting or trying out this framework's utilities.

    (For a step by step explanation see :ref:`Models_Tessif_mwe`):

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_chp()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gas Grid
    Powerline
    Heat Grid
    Gas Source
    Backup Power
    Backup Heat
    Power Demand
    Heat Demand
    CHP
    """

    # 2. Create a simulation time frame of four one-hour timesteps as a
    # :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    global_constraints = {'emissions': float('+inf')}

    # 3. Creating the individual energy system components:
    gas_supply = components.Source(
        name='Gas Source',
        outputs=('gas',),
        # Minimum number of arguments required
    )

    gas_grid = components.Bus(
        name='Gas Grid',
        inputs=('Gas Source.gas', ),
        outputs=('CHP.gas',),
        # Minimum number of arguments required
    )

    # conventional power supply is cheaper, but has emissions allocated to it
    chp = components.Transformer(
        name='CHP',
        inputs=('gas',),
        outputs=('electricity', 'heat'),
        conversions={
            ('gas', 'electricity'): 0.3,
            ('gas', 'heat'): 0.2,
        },
        # Minimum number of arguments required
        # flow_rates={
        #     'electricity': (0, 9),
        #     'heat': (0, 6),
        #     'gas': (0, float('+inf'))
        # },
        flow_costs={'electricity': 3, 'heat': 2, 'gas': 0},
        flow_emissions={'electricity': 2, 'heat': 3, 'gas': 0},
    )

    # back up power, expensive
    backup_power = components.Source(
        name='Backup Power',
        outputs=('electricity',),
        flow_costs={'electricity': 10},
    )

    # Power demand needing 10 energy units per time step
    power_demand = components.Sink(
        name='Power Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    power_line = components.Bus(
        name='Powerline',
        inputs=('Backup Power.electricity', 'CHP.electricity'),
        outputs=('Power Demand.electricity',),
        # Minimum number of arguments required
    )

    # Back up heat source, expensive
    backup_heat = components.Source(
        name='Backup Heat',
        outputs=('heat',),
        flow_costs={'heat': 10},
    )

    # Heat demand needing 10 energy units per time step
    heat_demand = components.Sink(
        name='Heat Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        flow_rates={'heat': nts.MinMax(min=10, max=10)},
    )

    heat_grid = components.Bus(
        name='Heat Grid',
        inputs=('CHP.heat', 'Backup Heat.heat'),
        outputs=('Heat Demand.heat',),
        # Minimum number of arguments required
    )

    # 4. Creating the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='CHP_Example',
        busses=(gas_grid, power_line, heat_grid),
        sinks=(power_demand, heat_demand),
        sources=(gas_supply, backup_power, backup_heat),
        transformers=(chp,),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # 5. Store the energy system:
    if not filename:
        filename = 'chp.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def create_variable_chp(directory=None, filename=None):
    """Same as create_chp() but with two chps that use additional functionality
    from tessif's :class:`tessif.model.components.CHP` class.

    Creates a simple energy system simulation to potentially
    store it on disc inside :paramref:`~create_chp.directory` as
    :paramref:`~create_chp.filename`.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_chp.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``chp.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_CHP` - For simulating and
    comparing this energy system using different supported models.

    Examples
    --------

    Use :func:`create_chp` to quickly access a tessif energy system
    to use for doctesting or trying out this framework's utilities.

    (For a step by step explanation see :ref:`Models_Tessif_mwe`):

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_variable_chp()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gas Grid
    Powerline
    Heat Grid
    CHP1
    CHP2
    Gas Source
    Backup Power
    Backup Heat
    Power Demand
    Heat Demand
    """
    # 2. Create a simulation time frame of four one-hour timesteps as a
    # :class:`pandas.DatetimeIndex`:
    periods = 4
    timeframe = pd.date_range('7/13/1990', periods=periods, freq='H')

    global_constraints = {'emissions': float('+inf')}

    # 3. Create the individual energy system components:
    gas_supply = components.Source(
        name='Gas Source',
        outputs=('gas',),
        # Minimum number of arguments required
    )

    gas_grid = components.Bus(
        name='Gas Grid',
        inputs=('Gas Source.gas',),
        outputs=('CHP1.gas', 'CHP2.gas'),
        # Minimum number of arguments required
    )

    # conventional power supply is cheaper, but has emissions allocated to it
    chp1 = components.CHP(
        name='CHP1',
        inputs=('gas',),
        outputs=('electricity', 'heat'),
        # Minimum number of arguments required
        conversions={
            ('gas', 'electricity'): 0.3,
            ('gas', 'heat'): 0.2,
        },
        conversion_factor_full_condensation={('gas', 'electricity'): 0.5},
        flow_rates={
            'electricity': (0, 9),
            'heat': (0, 6),
            'gas': (0, float('+inf'))
        },
        flow_costs={'electricity': 3, 'heat': 2, 'gas': 0},
        flow_emissions={'electricity': 2, 'heat': 3, 'gas': 0},
    )

    chp2 = components.CHP(
        name='CHP2',
        inputs=('gas',),
        outputs=('electricity', 'heat'),
        # Minimum number of arguments required
        enthalpy_loss=nts.MinMax(
            [1.0 for p in range(0, periods)],
            [0.18 for p in range(0, periods)]),
        power_wo_dist_heat=nts.MinMax(
            [8 for p in range(0, periods)],
            [20 for p in range(0, periods)]),
        el_efficiency_wo_dist_heat=nts.MinMax(
            [0.43 for p in range(0, periods)],
            [0.53 for p in range(0, periods)]),
        min_condenser_load=[3 for p in range(0, periods)],
        power_loss_index=[0.19 for p in range(0, periods)],
        back_pressure=False,
        flow_costs={'electricity': 3, 'heat': 2, 'gas': 0},
        flow_emissions={'electricity': 2, 'heat': 3, 'gas': 0},
    )

    # back up power, expensive
    backup_power = components.Source(
        name='Backup Power',
        outputs=('electricity',),
        flow_costs={'electricity': 10},
    )

    # Power demand needing 20 energy units per time step
    power_demand = components.Sink(
        name='Power Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        flow_rates={'electricity': nts.MinMax(min=20, max=20)},
    )

    power_line = components.Bus(
        name='Powerline',
        inputs=('Backup Power.electricity', 'CHP1.electricity',
                'CHP2.electricity'),
        outputs=('Power Demand.electricity',),
        # Minimum number of arguments required
        sector='Power'
    )

    # Back up heat source, expensive
    backup_heat = components.Source(
        name='Backup Heat',
        outputs=('heat',),
        flow_costs={'heat': 10},
    )

    # Heat demand needing 10 energy units per time step
    heat_demand = components.Sink(
        name='Heat Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        flow_rates={'heat': nts.MinMax(min=10, max=10)},
    )

    heat_grid = components.Bus(
        name='Heat Grid',
        inputs=('CHP1.heat', 'CHP2.heat', 'Backup Heat.heat'),
        outputs=('Heat Demand.heat',),
        # Minimum number of arguments required
        sector='Heat'
    )

    # 4. Create the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='CHP_Example',
        busses=(gas_grid, power_line, heat_grid),
        chps=(chp1, chp2, ),
        sinks=(power_demand, heat_demand),
        sources=(gas_supply, backup_power, backup_heat),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # 5. Store the energy system:
    if not filename:
        filename = 'chp.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def create_time_varying_efficiency_transformer():
    """Create a small es having a transformer with varying efficiency.

    Returns
    -------
    :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif minimum working example energy system.

    Example
    -------
    Visualize the energy system for better understanding what the output means:

    >>> import tessif.visualize.dcgrph as dcv  # nopep8

    >>> app = dcv.draw_generic_graph(
    ...     energy_system=create_time_varying_efficiency_transformer(),
    ...     color_group={
    ...         'Transformer': '#006666',
    ...         'Commodity': '#006666',
    ...         'Com Bus': '#006666',
    ...         'Powerline': '#ffcc00',
    ...         'Import': '#ff6600',
    ...         'Demand': '#009900',
    ...      },
    ...  )

    >>>  # Serve interactive drawing to http://127.0.0.1:8050/
    >>>  # app.run_server(debug=False)

    .. image:: ../images/time_varying_efficiency_transformer.png
        :align: center
        :alt: Image showing the mwe energy system graph
    """

    opt_timespan = pd.date_range('7/13/1990', periods=3, freq='H')

    demand = components.Sink(
        name='Demand',
        inputs=('electricity',),
        carrier='electricity',
        node_type='sink',
        flow_rates={'electricity': nts.MinMax(min=10, max=10)},
    )

    commodity = components.Source(
        name='Commodity',
        outputs=('energy',),
        carrier='energy',
        node_type='source',
    )

    import_source = components.Source(
        name='Import',
        outputs=('electricity',),
        carrier='electricity',
        node_type='source',
        flow_costs={"electricity": 1000}
    )

    transformer = components.Transformer(
        name='Transformer',
        inputs=('energy',),
        outputs=('electricity',),
        conversions={('energy', 'electricity'): [3/5, 4/5, 2/5]},
        # conversions={('energy', 'electricity'): 1},
        #
        # flow_rates={
        #     "energy": nts.MinMax(0, float("+inf")),
        #     "electricity": nts.MinMax(0, 10)
        # },
        flow_costs={"energy": 0, "electricity": 100},
        flow_emissions={"energy": 0, "electricity": 1000},
    )

    commodity_bus = components.Bus(
        name='Com Bus',
        inputs=('Commodity.energy',),
        outputs=('Transformer.energy',),
        carrier='energy',
        node_type='bus',
    )

    powerline = components.Bus(
        name='Powerline',
        inputs=('Transformer.electricity', "Import.electricity"),
        outputs=('Demand.electricity',),
        carrier='electricity',
        node_type='bus',
    )

    transformer_eff_es = energy_system.AbstractEnergySystem(
        uid='Transformer-Timeseries-Example',
        busses=(commodity_bus, powerline,),
        sinks=(demand,),
        sources=(commodity, import_source),
        transformers=(transformer,),
        timeframe=opt_timespan,
    )

    return transformer_eff_es


def create_hhes(periods=24, directory=None, filename=None):
    """
    Create a model of Hamburg's energy system using :mod:`tessif's
    model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_hhes.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``hhes.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_HH` - For simulating and
    comparing this energy system using different supported models.

    Examples
    --------
    Use :func:`create_hhes` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_hhes()

    >>> for node in es.nodes:
    ...     print(node.uid)
    coal supply line
    gas pipeline
    oil supply line
    waste supply
    powerline
    district heating pipeline
    biomass logistics
    gas supply
    coal supply
    oil supply
    waste
    pv1
    won1
    biomass supply
    imported el
    imported heat
    demand el
    demand th
    excess el
    excess th
    chp1
    chp2
    chp3
    chp4
    chp5
    chp6
    pp1
    pp2
    pp3
    pp4
    hp1
    p2h
    biomass chp
    est

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'coal supply': '#404040',
    ...         'coal supply line': '#404040',
    ...         'pp1': '#404040',
    ...         'pp2': '#404040',
    ...         'chp3': '#404040',
    ...         'chp4': '#404040',
    ...         'chp5': '#404040',
    ...         'hp1': '#b30000',
    ...         'imported heat': '#b30000',
    ...         'district heating pipeline': 'Red',
    ...         'demand th': 'Red',
    ...         'excess th': 'Red',
    ...         'p2h': '#b30000',
    ...         'bm1': '#006600',
    ...         'won1': '#99ccff',
    ...         'gas supply': '#336666',
    ...         'gas pipeline': '#336666',
    ...         'chp1': '#336666',
    ...         'chp2': '#336666',
    ...         'waste': '#009900',
    ...         'waste supply': '#009900',
    ...         'chp6': '#009900',
    ...         'oil supply': '#666666',
    ...         'oil supply line': '#666666',
    ...         'pp3': '#666666',
    ...         'pp4': '#666666',
    ...         'pv1': '#ffd900',
    ...         'imported el': '#ffd900',
    ...         'demand el': '#ffe34d',
    ...         'excess el': '#ffe34d',
    ...         'est': '#ffe34d',
    ...         'powerline': '#ffcc00',
    ...     },
    ...     node_size={
    ...         'powerline': 5000,
    ...         'district heating pipeline': 5000
    ...     },
    ...     layout='dot',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/hh_es_example.png
        :align: center
        :alt: Image showing the create_hhes energy system graph.

    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('2019-01-01', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv_HH = pd.read_csv(os.path.join(d, 'solar_HH_2019.csv'), index_col=0,
                        sep=';')
    pv_HH = pv_HH.values.flatten()[0:periods]
    max_pv = np.max(pv_HH)

    # wind onshore:
    wo_HH = pd.read_csv(os.path.join(d, 'wind_HH_2019.csv'), index_col=0,
                        sep=';')
    wo_HH = wo_HH.values.flatten()[0:periods]
    max_wo = np.max(wo_HH)

    # electricity demand:
    de_HH = pd.read_csv(os.path.join(d, 'el_demand_HH_2019.csv'), index_col=0,
                        sep=';')
    de_HH = de_HH['Last (MW)'].values.flatten()[0:periods]
    de_HH = np.array(de_HH)
    max_de = np.max(de_HH)

    # heat demand:
    th_HH = pd.read_csv(os.path.join(d, 'th_demand_HH_2019.csv'), index_col=0,
                        sep=';')
    th_HH = th_HH['actual_total_load'].values.flatten()[0:periods]
    th_HH = np.array(th_HH)
    max_th = np.max(th_HH)

    # 4. Create the individual energy system components:
    in_stat = False
    cfba = 0

    # Global Constraints:

    global_constraints = {
        'name': '2019',
        'emissions': float('+inf'),
        # 'resources': float('+inf'),
    }

    # Fossil Sources:

    gass = components.Source(
        name='gas supply',
        outputs=('gas',),
        region='HH',
        node_type='gas_supply',
        component='source',
        sector='coupled',
        carrier='gas',
        flow_emissions={'gas': 0.2},
    )

    coals = components.Source(
        name='coal supply',
        outputs=('coal',),
        region='HH',
        node_type='coal_supply',
        component='source',
        sector='coupled',
        carrier='coal',
        flow_emissions={'coal': 0.34},
    )

    oils = components.Source(
        name='oil supply',
        outputs=('oil',),
        region='HH',
        node_type='oil_supply',
        component='source',
        sector='power',
        carrier='oil',
    )

    waste = components.Source(
        name='waste',
        outputs=('waste',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='coupled',
        carrier='waste',
        flow_emissions={'waste': 0.0426},
    )

    # HKW ADM:

    chp1 = components.Transformer(
        name='chp1',
        inputs=('gas',),
        outputs=('electricity',
                 'hot_water'),
        conversions={
            ('gas', 'electricity'): 0.3773,
            ('gas', 'hot_water'): 0.3,
        },  # conventional_power_plants_DE.xls
        latitude=53.51,
        longitude=9.94985,
        region='HH',
        node_type='HKW ADM',
        component='transformer',
        sector='coupled',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf')),  # 6.75
            'hot_water': nts.MinMax(min=0, max=float('+inf'))
        },
        flow_costs={'gas': 0,
                    'electricity': 90,
                    'hot_water': 21.6},

        # emissions are attributed to gas supply
        # so pypsa can handle them better
        flow_emissions={'gas': 0,  # 0.2,
                        'electricity': 0,  # 0.2/0.3773,
                        'hot_water': 0},  # 0.2/0.3},

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 1),
        status_changing_costs=nts.OnOff(24, 0),
        costs_for_being_active=cfba,
    )

    # HKW Moorburg:

    pp1 = components.Transformer(
        name='pp1',
        inputs=('coal',),
        outputs=('electricity',),
        conversions={('coal', 'electricity'): 0.4625},
        latitude=53.489,
        longitude=9.949,
        region='HH',
        node_type='HKW Moorburg Block A',
        component='transformer',
        sector='power',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=784),  # 296
        },
        flow_costs={
            'coal': 0,
            'electricity': 82
        },

        flow_emissions={
            'coal': 0,  # 0.34,
            'electricity': 0.34/0.4625
        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    pp2 = components.Transformer(
        name='pp2',
        inputs=('coal',),
        outputs=('electricity',),
        conversions={('coal', 'electricity'): 0.4625},
        latitude=53.489,
        longitude=9.949,
        region='HH',
        node_type='HKW Moorburg Block B',
        component='transformer',
        sector='power',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=784)  # 296
        },
        flow_costs={'coal': 0,
                    'electricity': 82},

        flow_emissions={
            'coal': 0,  # 0.34,
            'electricity': 0.34/0.4625
        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    # HKW Tiefstack:

    chp2 = components.Transformer(
        name='chp2',
        inputs=('gas',),
        outputs=('electricity',
                 'hot_water',),
        conversions={
            ('gas', 'electricity'): 0.585,
            ('gas', 'hot_water'): 0.40,
        },
        latitude=53.53,
        longitude=10.07,
        region='HH',
        node_type='HKW Tiefstack GuD',
        component='transformer',
        sector='coupled',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=123),  # 51
            'hot_water': nts.MinMax(min=0, max=180),
        },
        flow_costs={'gas': 0,
                    'electricity': 90,
                    'hot_water': 18.9,
                    },
        # emissions are attributed to gas supply
        # so pypsa can handle them better
        flow_emissions={'gas': 0,  # 0.2,
                        'electricity': 0,  # 0.2/0.585,
                        'hot_water': 0,  # 0.2/0.4,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 5),
        status_changing_costs=nts.OnOff(40, 0),
        costs_for_being_active=cfba,
    )

    chp3 = components.Transformer(
        name='chp3',
        inputs=('coal',),
        outputs=('electricity',
                 'hot_water',),
        conversions={('coal', 'electricity'): 0.4075,
                     ('coal', 'hot_water'): 0.40,
                     },
        latitude=53.53,
        longitude=10.06,
        region='HH',
        node_type='HKW Tiefstack Block 2',
        component='transformer',
        sector='coupled',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=188),  # 68
            'hot_water': nts.MinMax(min=0, max=293),
        },
        flow_costs={'coal': 0,
                    'electricity': 82,
                    'hot_water': 19.68,
                    },
        # emissions are attributed to coal supply
        # so pypsa can handle them better
        flow_emissions={'coal': 0,  # 0.34,
                        'electricity': 0,  # 0.34/0.4075,
                        'hot_water': 0,  # 0.34/0.4,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    # Wedel GT:

    pp3 = components.Transformer(
        name='pp3',
        inputs=('oil',),
        outputs=('electricity',),
        conversions={
            ('oil', 'electricity'): 0.3072
        },
        latitude=53.5662,
        longitude=9.72864,
        region='SH',
        node_type='Wedel GT A',
        component='transformer',
        sector='power',
        carrier='oil',

        flow_rates={
            'oil': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=50.5)  # 20.2
        },
        flow_costs={'oil': 0,
                    'electricity': 90
                    },
        flow_emissions={'oil': 0,  # 0.28,
                        'electricity': 0.28/0.3072,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(45, 0),
        costs_for_being_active=cfba,
    )

    pp4 = components.Transformer(
        name='pp4',
        inputs=('oil',),
        outputs=('electricity',),
        conversions={
            ('oil', 'electricity'): 0.3072
        },
        latitude=53.5662,
        longitude=9.72864,
        region='SH',
        node_type='Wedel GT B',
        component='transformer',
        sector='power',
        carrier='oil',

        flow_rates={
            'oil': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=50.5)  # 20.2
        },
        flow_costs={'oil': 0,
                    'electricity': 90
                    },
        flow_emissions={'oil': 0,  # 0.28,
                        'electricity': 0.28/0.3072,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(45, 0),
        costs_for_being_active=cfba,
    )

    # HKW Wedel:

    chp4 = components.Transformer(
        name='chp4',
        inputs=('coal',),
        outputs=('electricity',
                 'hot_water',),
        conversions={('coal', 'electricity'): 0.4075,
                     ('coal', 'hot_water'): 0.40,
                     },
        latitude=53.5667,
        longitude=9.72864,
        region='SH',
        node_type='HKW Wedel Block 1',
        component='transformer',
        sector='coupled',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=130),  # 57
            'hot_water': nts.MinMax(min=0, max=130),
        },
        flow_costs={'coal': 0,
                    'electricity': 82,
                    'hot_water': 19.68,
                    },
        # emissions are attributed to coal supply
        # so pypsa can handle them better
        flow_emissions={'coal': 0,  # 0.34,
                        'electricity': 0,  # 0.34/0.4075,
                        'hot_water': 0,  # 0.34/0.40,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    chp5 = components.Transformer(
        name='chp5',
        inputs=('coal',),
        outputs=('electricity',
                 'hot_water'),
        conversions={('coal', 'electricity'): 0.4075,
                     ('coal', 'hot_water'): 0.40,
                     },
        latitude=53.5667,
        longitude=9.72864,
        region='SH',
        node_type='HKW Wedel Block 2',
        component='transformer',
        sector='coupled',
        carrier='coal',

        flow_rates={
            'coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=118),  # 44
            'hot_water': nts.MinMax(min=0, max=88),
        },
        flow_costs={'coal': 0,
                    'electricity': 82,
                    'hot_water': 19.68,
                    },
        # emissions are attributed to coal supply
        # so pypsa can handle them better
        flow_emissions={'coal': 0,  # 0.34,
                        'electricity': 0,  # 0.34/0.4075,
                        'hot_water': 0,  # 0.34/0.40,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 7),
        status_changing_costs=nts.OnOff(49, 0),
        costs_for_being_active=cfba,
    )

    # MVR Waste Combustion Rugenberger Damm:

    chp6 = components.Transformer(
        name='chp6',
        inputs=('waste',),
        outputs=('electricity',
                 'hot_water',),
        conversions={('waste', 'electricity'): 0.06,
                     ('waste', 'hot_water'): 0.15,
                     },
        latitude=53.52111,
        longitude=9.93339,
        region='HH',
        node_type='MVR Müllverwertung Rugenberger Damm',
        component='transformer',
        sector='coupled',
        carrier='waste',

        flow_rates={
            'waste': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=24),  # 9.6
            'hot_water': nts.MinMax(min=0, max=70),
        },
        flow_costs={'waste': 0,
                    'electricity': 82,
                    'hot_water': 20,
                    },

        # emissions are attributed to waste supply
        # so pypsa can handle them better
        flow_emissions={'waste': 0,  # 0.0426,
                        'electricity': 0,  # 0.0426/0.06,
                        'hot_water': 0,  # 0.0426/0.15,
                        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(40, 0),
        costs_for_being_active=cfba,
    )

    # Heizwerk Hafencity:
    hp1 = components.Transformer(
        name='hp1',
        inputs=('gas',),
        outputs=('hot_water',),
        conversions={('gas', 'hot_water'): 0.96666, },
        latitude=53.54106052,
        longitude=9.99590096,
        region='HH',
        node_type='Heizwerk Hafencity',
        component='transformer',
        sector='heat',
        carrier='gas',

        flow_rates={
            'gas': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=348),  # max=348
        },
        flow_costs={'gas': 0,
                    'hot_water': 20,
                    },
        flow_emissions={'gas': 0.0,  # 0.2
                        'hot_water': 0.2/0.96666,
                        },

        expandable={'gas': False,
                    'hot_water': True},
        expansion_costs={'gas': 0,
                         'hot_water': 0, },
        expansion_limits={'gas': nts.MinMax(min=0, max=float('+inf')),
                          'hot_water': nts.MinMax(min=348, max=float('+inf'))},
    )

    # Biomass Combined Heat and Power
    bm_chp = components.Transformer(
        name='biomass chp',
        latitude=53.54106052,
        longitude=9.99590096,
        region='HH',
        node_type='Heizwerk Hafencity',
        component='transformer',
        sector='heat',
        carrier='gas',
        inputs=('biomass',),
        outputs=('electricity', 'hot_water',),
        conversions={
            ('biomass', 'electricity'): 48.4/126,
            ('biomass', 'hot_water'): 1,
        },
        flow_rates={
            'biomass': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=48.4),
            'hot_water': nts.MinMax(min=0, max=126),
        },
        flow_costs={
            'biomass': 0,
            'electricity': 61,  # 61
            'hot_water': 20,  # 61
        },
        flow_emissions={
            'biomass': 0,
            # emissions reallocated to source
            'electricity': 0,  # 0.001,
            'hot_water': 0,  # 0.001,
        },

        initial_status=in_stat,
        status_inertia=nts.OnOff(0, 9),
        status_changing_costs=nts.OnOff(40, 0),
    )

    # Renewables:

    pv1 = components.Source(
        name='pv1',
        outputs=('electricity',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='power',
        carrier='solar',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'electricity': 74},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv_HH, max=pv_HH)},

        expandable={'electricity': True},
        expansion_costs={'electricity': economics.annuity(capex=1000000, n=20,
                                                          wacc=0.05)},
        expansion_limits={'electricity': nts.MinMax(
            min=max_pv, max=float('+inf'))},
    )

    won1 = components.Source(
        name='won1',
        outputs=('electricity',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='power',
        carrier='wind',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_wo)},
        flow_costs={'electricity': 61},
        flow_emissions={'electricity': 0.007},  # 0.007
        timeseries={'electricity': nts.MinMax(min=wo_HH, max=wo_HH)},

        expandable={'electricity': True},
        expansion_costs={'electricity': economics.annuity(capex=1750000, n=20,
                                                          wacc=0.05)},
        expansion_limits={'electricity': nts.MinMax(
            min=max_wo, max=float('+inf'))},
    )

    bm_supply = components.Source(
        name='biomass supply',
        outputs=('biomass',),
        region='HH',
        node_type='renewable',
        component='source',
        sector='coupled',
        carrier='biomass',
        # reallocating the biomass chp emissions to the source
        flow_emissions={'biomass': 0.001/1+0.001/(48.8/126)},
    )

    # Storages:

    est = components.Storage(
        name='est',
        input='electricity',
        output='electricity',
        capacity=1,
        initial_soc=1,

        region='HH',
        sector='power',
        carrier='electricity',
        component='storage',

        flow_rates={'electricity': nts.MinMax(0, float('+inf'))},
        flow_costs={'electricity': 20},
        flow_emissions={'electricity': 0},

        expendable={'capacity': True, 'electricity': False},
        expansion_costs={'capacity': economics.annuity(capex=1000000, n=10,
                                                       wacc=0.05)}
    )

    # P2H Karoline:

    p2h = components.Transformer(
        name='p2h',
        inputs=('electricity',),
        outputs=('hot_water',),
        conversions={('electricity', 'hot_water'): 0.99, },
        latitude=53.55912,
        longitude=9.97148,
        region='HH',
        node_type='power2heat',
        component='transformer',
        sector='heat',
        carrier='hot_water',

        flow_rates={'electricity': nts.MinMax(min=0, max=float('+inf')),
                    'hot_water': nts.MinMax(min=0, max=45)},  # 45
        flow_costs={'electricity': 0,
                    'hot_water': 0},
        flow_emissions={'electricity': 0,
                        'hot_water': 0},  # 0.007
        expandable={'electricity': False,
                    'hot_water': True},
        expansion_costs={'hot_water': economics.annuity(capex=200000, n=30,
                                                        wacc=0.05)},
        expansion_limits={'hot_water': nts.MinMax(min=45, max=200)},

    )

    # Imported Electricity/ Heat:

    imel = components.Source(
        name='imported el',
        outputs=('electricity',),
        region='HH',
        node_type='import',
        component='source',
        sector='power',
        carrier='electricity',

        flow_costs={'electricity': 999},
        flow_emissions={'electricity': 0.401},

        expendable={'electricity': True},
        expansion_costs={'electricity': 999999999},
    )

    imth = components.Source(
        name='imported heat',
        outputs=('hot_water',),
        region='HH',
        node_type='import',
        component='source',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),

        flow_costs={'hot_water': 999},
        flow_emissions={'hot_water': 0.1},

        expendable={'hot_water': True},
        expansion_costs={'hot_water': 999999999},
    )

    # Sinks:

    demand_el = components.Sink(
        name='demand el',
        inputs=('electricity',),
        region='HH',
        node_type='demand',
        component='sink',
        sector='power',
        carrier='electricity',

        flow_rates={'electricity': nts.MinMax(min=0, max=max_de)},
        timeseries={'electricity': nts.MinMax(min=de_HH, max=de_HH)},
    )

    demand_th = components.Sink(
        name='demand th',
        inputs=('hot_water',),
        region='HH',
        node_type='demand',
        component='sink',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),

        flow_rates={'hot_water': nts.MinMax(min=0, max=max_th)},
        timeseries={'hot_water': nts.MinMax(min=th_HH, max=th_HH)},
    )

    excess_el = components.Sink(
        name='excess el',
        inputs=('electricity',),
        region='HH',
        node_type='excess',
        component='sink',
        sector='power',
        carrier='electricity',
    )

    excess_th = components.Sink(
        name='excess th',
        inputs=('hot_water',),
        region='HH',
        node_type='excess',
        component='sink',
        sector='heat',
        carrier='hot_water',  # ('hot_water', 'steam'),
    )

    # Busses:

    bm_logistics = components.Bus(
        name='biomass logistics',
        region='HH',
        node_type='logistics',
        component='bus',
        sector='coupled',
        carrier='biomass',

        inputs=('biomass supply.biomass',),
        outputs=('biomass chp.biomass',),
    )

    gas_pipeline = components.Bus(
        name='gas pipeline',
        region='HH',
        node_type='gas_pipeline',
        component='bus',
        sector='coupled',
        carrier='gas',

        inputs=('gas supply.gas',),
        outputs=('chp1.gas',
                 'chp2.gas',

                 'hp1.gas'),
    )

    coal_supply_line = components.Bus(
        name='coal supply line',
        region='HH',
        node_type='gas_pipeline',
        component='bus',
        sector='coupled',
        carrier='coal',

        inputs=('coal supply.coal',),
        outputs=('pp1.coal',
                 'pp2.coal',
                 'chp3.coal',
                 'chp4.coal',
                 'chp5.coal',),
    )

    oil_supply_line = components.Bus(
        name='oil supply line',
        region='HH',
        node_type='oil_delivery',
        component='bus',
        sector='power',
        carrier='oil',

        inputs=('oil supply.oil',),
        outputs=('pp3.oil',
                 'pp4.oil',),
    )

    waste_supply = components.Bus(
        name='waste supply',
        region='HH',
        node_type='waste_supply',
        component='bus',
        sector='coupled',
        carrier='waste',

        inputs=('waste.waste',),
        outputs=('chp6.waste',),
    )

    powerline = components.Bus(
        name='powerline',
        region='HH',
        node_type='powerline',
        component='bus',
        sector='power',
        carrier='electricity',

        inputs=('chp1.electricity',
                'chp2.electricity',
                'chp3.electricity',
                'chp4.electricity',
                'chp5.electricity',
                'chp6.electricity',

                'pp1.electricity',
                'pp2.electricity',
                'pp3.electricity',
                'pp4.electricity',

                'pv1.electricity',
                'won1.electricity',
                'biomass chp.electricity',
                # 'bm1.electricity',

                'imported el.electricity',

                'est.electricity'),
        outputs=('demand el.electricity',
                 'excess el.electricity',

                 'est.electricity',

                 'p2h.electricity',),
    )

    district_heating = components.Bus(
        name='district heating pipeline',
        region='HH',
        node_type='district_heating_pipeline',
        component='bus',
        sector='heat',
        carrier='hot_water',

        inputs=('chp1.hot_water',
                'chp2.hot_water',
                'chp3.hot_water',
                'chp4.hot_water',
                'chp6.hot_water',
                'chp5.hot_water',

                # 'bm1.hot_water',
                'biomass chp.hot_water',

                'imported heat.hot_water',

                'p2h.hot_water',

                'hp1.hot_water',),
        outputs=('demand th.hot_water',
                 'excess th.hot_water',),)

    # 4. Create the actual energy system:
    explicit_es = energy_system.AbstractEnergySystem(
        uid='Energy System Hamburg',
        busses=(coal_supply_line, gas_pipeline, oil_supply_line, waste_supply,
                powerline, district_heating, bm_logistics),
        sinks=(demand_el, demand_th, excess_el, excess_th,),
        sources=(gass, coals, oils, waste, pv1,
                 won1, bm_supply, imel, imth,),
        transformers=(chp1, chp2, chp3, chp4, chp5, chp6, pp1, pp2, pp3, pp4,
                      hp1, p2h, bm_chp),
        storages=(est,),
        timeframe=timeframe,
        global_constraints=global_constraints,
        # milp=True,
    )

    # 5. Store the energy system:
    if not filename:
        filename = 'hhes.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def create_grid_es(periods=3, directory=None, filename=None):
    """
    Create a model of a generic grid style energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=3
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_grid_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``grid_es.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Grid` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Examples_Application_Grid`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.

    Examples
    --------
    Use :func:`create_grid_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_grid_es()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gaspipeline
    Low Voltage Powerline
    District Heating
    Medium Voltage Powerline
    High Voltage Powerline
    Coal Supply Line
    Biogas
    Solar Panel
    Gas Station
    Onshore Wind Power
    Offshore Wind Power
    Coal Supply
    Solar Thermal
    Biogas plant
    Household Demand
    Commercial Demand
    District Heating Demand
    Industrial Demand
    Car charging Station
    BHKW
    Power to Heat
    GuD
    HKW
    Battery
    Heat Storage
    Pumped Storage
    Low Voltage Transformator
    High Voltage Transformator

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Coal Supply': '#666666',
    ...         'Coal Supply Line': '#666666',
    ...         'HKW': '#b30000',
    ...         'Solar Thermal': '#b30000',
    ...         'Heat Storage': '#cc0033',
    ...         'District Heating': 'Red',
    ...         'District Heating Demand': 'Red',
    ...         'Power to Heat': '#b30000',
    ...         'Biogas plant': '#006600',
    ...         'Biogas': '#006600',
    ...         'BHKW': '#006600',
    ...         'Onshore Wind Power': '#99ccff',
    ...         'Offshore Wind Power': '#00ccff',
    ...         'Gas Station': '#336666',
    ...         'Gaspipeline': '#336666',
    ...         'GuD': '#336666',
    ...         'Solar Panel': '#ffe34d',
    ...         'Commercial Demand': '#ffe34d',
    ...         'Household Demand': '#ffe34d',
    ...         'Industrial Demand': '#ffe34d',
    ...         'Battery': '#ffe34d',
    ...         'Car charging Station': '#669999',
    ...         'Low Voltage Powerline': '#ffcc00',
    ...         'Medium Voltage Powerline': '#ffcc00',
    ...         'High Voltage Powerline': '#ffcc00',
    ...         'High Voltage Transformator': 'yellow',
    ...         'Low Voltage Transformator': 'yellow',
    ...         'Pumped Storage': '#0000cc',
    ...     },
    ...     title='Generic Grid Example Energy System Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/grid_es_example.png
        :align: center
        :alt: Image showing the create_grid_es energy system graph.
    """
    timeframe = pd.date_range('7/13/1990', periods=periods, freq='H')

    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
        'resources': float('+inf')}

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=1000)},
        flow_rates={'electricity': nts.MinMax(min=0, max=25)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=42, negative=42)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([12, 22, 7]), max=np.array([12, 22, 7]))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 5},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        accumulated_amounts={
            'fuel': nts.MinMax(min=0, max=float('+inf'))},
        # max=100)},   float('+inf'))},
        flow_rates={'fuel': nts.MinMax(min=0, max=1000)},
        flow_costs={'fuel': 10},
        flow_emissions={'fuel': 3},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=1000, negative=1000)},
        gradient_costs={'fuel': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False},
        expansion_costs={'fuel': 5},
        expansion_limits={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        milp={'fuel': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        accumulated_amounts={
            'fuel': nts.MinMax(min=0, max=float('+inf'))},
        # max=100)},   float('+inf'))},
        flow_rates={'fuel': nts.MinMax(min=0, max=1000)},
        flow_costs={'fuel': 0},  # flow_costs={'fuel': 8},
        flow_emissions={'fuel': 0},  # flow_emissions={'fuel': 3},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=1000, negative=1000)},
        gradient_costs={'fuel': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False},
        expansion_costs={'fuel': 5},
        expansion_limits={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        milp={'fuel': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.35, ('fuel', 'heat'): 0.55},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=100),
            'electricity': nts.MinMax(min=0, max=30),
            'heat': nts.MinMax(min=0, max=100)},
        flow_costs={'fuel': 0, 'electricity': 10, 'heat': 5},
        flow_emissions={'fuel': 0, 'electricity': 10, 'heat': 5},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=100, negative=100),
            'electricity': nts.PositiveNegative(positive=30, negative=30),
            'heat': nts.PositiveNegative(positive=100, negative=100)},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'heat': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'electricity': False, 'heat': False},
        expansion_costs={'fuel': 0, 'electricity': 0, 'heat': 0},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False, 'fuel': False, 'heat': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=9),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=190, max=190)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=200, negative=200)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=2, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=8),
        costs_for_being_active=0
        # Total number of arguments to specify sink object
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=200)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=200, negative=200)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([80, 20, 130]), max=np.array([80, 20, 130]))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=2, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=8),
        costs_for_being_active=0
        # Total number of arguments to specify sink object
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        accumulated_amounts={
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'heat': nts.MinMax(min=300, max=500)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        flow_gradients={
            'heat': nts.PositiveNegative(positive=500, negative=500)},
        gradient_costs={'heat': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'heat': nts.MinMax(
            min=np.array([340, 300, 380]), max=np.array([340, 300, 380]))},
        expandable={'heat': False},
        expansion_costs={'heat': 0},
        expansion_limits={'heat': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'heat': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=2, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=8),
        costs_for_being_active=0
        # Total number of arguments to specify sink object
    )

    battery_storage = components.Storage(
        name='Battery',
        input='electricity',
        output='electricity',
        capacity=20,
        initial_soc=10,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=1),
        flow_rates={'electricity': nts.MinMax(min=0, max=30)},
        flow_efficiencies={
            'electricity': nts.InOut(inflow=1, outflow=1)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': False, 'electricity': False},
        expansion_costs={'capacity': 2, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=2),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=42),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Powerline',
        inputs=('BHKW.electricity', 'Battery.electricity',
                'Solar Panel.electricity',),
        outputs=('Household Demand.electricity',
                 'Commercial Demand.electricity', 'Battery.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=('BHKW.heat', 'Solar Thermal.heat',
                'Heat Storage.heat', 'Power to Heat.heat', 'HKW.heat'),
        outputs=('District Heating Demand.heat', 'Heat Storage.heat'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Medium Voltage and heat

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=2000)},
        flow_rates={'electricity': nts.MinMax(min=0, max=100)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=100, negative=100)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([60, 80, 34]), max=np.array([60, 80, 34]))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 8},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        accumulated_amounts={
            'heat': nts.MinMax(min=0, max=1000)},
        flow_rates={'heat': nts.MinMax(min=0, max=50)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        flow_gradients={
            'heat': nts.PositiveNegative(positive=42, negative=42)},
        gradient_costs={'heat': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'heat': nts.MinMax(
            min=np.array([24, 44, 14]), max=np.array([24, 44, 14]))},
        expandable={'heat': False},
        expansion_costs={'heat': 4},
        expansion_limits={'heat': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'heat': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=400)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=400, negative=400)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([160, 160, 120]), max=np.array([160, 160, 120]))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=2, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=8),
        costs_for_being_active=0
        # Total number of arguments to specify sink object
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=1000)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=1000, negative=1000)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([0, 0, 100]), max=np.array([0, 0, 100]))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=2, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=8),
        costs_for_being_active=0
        # Total number of arguments to specify sink object
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('electricity',),
        outputs=('heat',),
        conversions={('electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='coupled',
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=100),
            'heat': nts.MinMax(min=0, max=100)},
        flow_costs={'electricity': 0, 'heat': 1},
        flow_emissions={'electricity': 0, 'heat': 1},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=100, negative=100),
            'heat': nts.PositiveNegative(positive=100, negative=100)},
        gradient_costs={
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'heat': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'electricity': False, 'heat': False},
        expansion_costs={'electricity': 0, 'heat': 0},
        expansion_limits={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False, 'fuel': False, 'heat': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=0),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=9),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    heat_storage = components.Storage(
        name='Heat Storage',
        input='heat',
        output='heat',
        capacity=50,
        initial_soc=10,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='Hot Water',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.15),
        flow_rates={'heat': nts.MinMax(min=0, max=50)},
        flow_efficiencies={
            'heat': nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        flow_gradients={
            'heat': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'heat': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': False, 'heat': False},
        expansion_costs={'capacity': 2, 'heat': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        milp={'heat': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=2),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=42),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Powerline',
        inputs=('Onshore Wind Power.electricity',),
        outputs=('Car charging Station.electricity',
                 'Industrial Demand.electricity',
                 'Power to Heat.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_medium_transformator = components.Connector(
        name='Low Voltage Transformator',
        interfaces=(
            str(medium_electricity_line.uid),
            str(low_electricity_line.uid)
        ),
        conversions={
            (
                str(medium_electricity_line.uid),
                str(low_electricity_line.uid)
            ): 1,
            (
                str(low_electricity_line.uid),
                str(medium_electricity_line.uid),
            ): 1,
        },
        timeseries=None,
        node_type='connector',
        sector='power',
    )

    # High Voltage

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=4000)},
        flow_rates={'electricity': nts.MinMax(min=0, max=200)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(positive=200, negative=200)},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array([120, 140, 70]), max=np.array([120, 140, 70]))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 9},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        accumulated_amounts={
            'fuel': nts.MinMax(min=0, max=float('+inf'))},
        # max=100)},   float('+inf'))},
        flow_rates={'fuel': nts.MinMax(min=0, max=500)},
        flow_costs={'fuel': 8},
        flow_emissions={'fuel': 5},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=500, negative=500)},
        gradient_costs={'fuel': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False},
        expansion_costs={'fuel': 5},
        expansion_limits={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        milp={'fuel': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=1, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=10),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.35, ('fuel', 'heat'): 0.53},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=500),
            'electricity': nts.MinMax(min=0, max=500),
            'heat': nts.MinMax(min=0, max=500)},
        flow_costs={'fuel': 0, 'electricity': 5, 'heat': 5},
        flow_emissions={'fuel': 0, 'electricity': 5, 'heat': 5},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=500, negative=500),
            'electricity': nts.PositiveNegative(positive=500, negative=500),
            'heat': nts.PositiveNegative(positive=500, negative=500)},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'heat': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'electricity': False, 'heat': False},
        expansion_costs={'fuel': 0, 'electricity': 0, 'heat': 0},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False, 'fuel': False, 'heat': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=1),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=9),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.6},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=500),
            'electricity': nts.MinMax(min=0, max=500)},
        flow_costs={'fuel': 0, 'electricity': 5},
        flow_emissions={'fuel': 0, 'electricity': 5},
        flow_gradients={
            'fuel': nts.PositiveNegative(positive=500, negative=500),
            'electricity': nts.PositiveNegative(positive=500, negative=500)},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'electricity': False},
        expansion_costs={'fuel': 0, 'electricity': 0},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False, 'fuel': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=2),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=9),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    pumped_storage = components.Storage(
        name='Pumped Storage',
        input='electricity',
        output='electricity',
        capacity=400,
        initial_soc=50,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0),
        flow_rates={'electricity': nts.MinMax(min=0, max=100)},
        flow_efficiencies={
            'electricity': nts.InOut(inflow=0.9, outflow=0.9)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': False, 'electricity': False},
        expansion_costs={'capacity': 2, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        milp={'electricity': False},
        initial_status=True,
        status_inertia=nts.OnOff(on=0, off=2),
        status_changing_costs=nts.OnOff(on=0, off=0),
        number_of_status_changes=nts.OnOff(on=float('+inf'), off=42),
        costs_for_being_active=0
        # Total number of arguments to specify source object
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_electricity_line = components.Bus(
        name='High Voltage Powerline',
        inputs=('Offshore Wind Power.electricity',
                'Pumped Storage.electricity',
                'GuD.electricity',
                'HKW.electricity'),
        outputs=('Pumped Storage.electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_medium_transformator = components.Connector(
        name='High Voltage Transformator',
        interfaces=(
            str(medium_electricity_line.uid),
            str(high_electricity_line.uid)
        ),
        conversions={
            (
                str(medium_electricity_line.uid),
                str(high_electricity_line.uid)
            ): 1,
            (
                str(high_electricity_line.uid),
                str(medium_electricity_line.uid),
            ): 1,
        },
        timeseries=None,
        node_type='connector',
        sector='coupled',
    )

    # Building the Energysystem

    es = energy_system.AbstractEnergySystem(
        uid='my_energy_system',
        busses=(
            gas_supply_line,
            low_electricity_line,
            heat_line,
            medium_electricity_line, high_electricity_line,
            coal_supply_line,
            biogas_supply_line),
        sinks=(
            household_demand, commercial_demand, heat_demand,
            industrial_demand, car_charging_station_demand,),
        sources=(
            solar_panel, gas_supply, onshore_wind_power, offshore_wind_power,
            coal_supply, solar_thermal, biogas_supply),
        transformers=(bhkw_generator, power_to_heat,
                      gud_generator, hkw_generator),
        storages=(battery_storage, heat_storage, pumped_storage),
        connectors=(low_medium_transformator, high_medium_transformator),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # Store the energy system:
    if not filename:
        filename = 'grid_es.tsf'

    es.dump(directory=directory, filename=filename)

    return es


def create_component_es(expansion_problem=False, periods=3, directory=None,
                        filename=None):
    """
    Create a model of a generic component based energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    expansion_problem : bool, default=False
        Boolean which states whether a commitment problem (False)
        or expansion problem (True) is to be solved

    periods : int, default=3
        Number of time steps of the evaluated timeframe
        (one time step is one hour)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_component_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``component_es.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`Examples_Application_Components`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.

    Examples
    --------
    Use :func:`create_component_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_component_es()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gas Line
    Powerline
    Hard Coal Supply Line
    Lignite Supply Line
    Biogas Line
    Heatline
    Gas Station
    Solar Panel
    Onshore Wind Turbine
    Hard Coal Supply
    Lignite Supply
    Offshore Wind Turbine
    Biogas Supply
    El Demand
    Heat Demand
    Combined Cycle PP
    Hard Coal PP
    Lignite Power Plant
    Biogas CHP
    Heat Plant
    Power To Heat
    Hard Coal CHP
    Battery
    Heat Storage


    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...        'Hard Coal Supply': '#666666',
    ...        'Hard Coal Supply Line': '#666666',
    ...        'Hard Coal PP': '#666666',
    ...        'Hard Coal CHP': '#666666',
    ...        'Solar Panel': '#FF7700',
    ...        'Heat Storage': '#cc0033',
    ...        'Heat Demand': 'Red',
    ...        'Heat Plant': '#cc0033',
    ...        'Heatline': 'Red',
    ...        'Power To Heat': '#cc0033',
    ...        'Biogas CHP': '#006600',
    ...        'Biogas Line': '#006600',
    ...        'Biogas Supply': '#006600',
    ...        'Onshore Wind Turbine': '#99ccff',
    ...        'Offshore Wind Turbine': '#00ccff',
    ...        'Gas Station': '#336666',
    ...        'Gas Line': '#336666',
    ...        'Combined Cycle PP': '#336666',
    ...        'El Demand': '#ffe34d',
    ...        'Battery': '#ffe34d',
    ...        'Powerline': '#ffcc00',
    ...        'Lignite Supply': '#993300',
    ...        'Lignite Supply Line': '#993300',
    ...        'Lignite Power Plant': '#993300',
    ...      },
    ...     node_size={
    ...        'Powerline': 5000,
    ...        'Heatline': 5000
    ...    },
    ...      title='Component Based Example Energy System Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/component_es_example.png
        :align: center
        :alt: Image showing the create_component_es energy system graph.
    """
    # Create a simulation time frame
    timeframe = pd.date_range('1/1/2019', periods=periods, freq='H')

    # Initiate the global constraints depending on the scenario
    if expansion_problem is False:
        global_constraints = {
            'name': 'Commitment_Scenario',
            'emissions': float('+inf'),
        }
    else:
        global_constraints = {
            'name': 'Expansion_Scenario',
            'emissions': 250000,
        }

    # Variables for timeseries of fluctuate wind, solar and demand

    csv_data = pd.read_csv(os.path.join(
        example_dir, 'data', 'tsf', 'load_profiles',
        'component_scenario_profiles.csv'), index_col=0, sep=';')

    # solar:
    pv = csv_data['pv'].values.flatten()[0:periods]
    # scale relative values with the installed pv power
    pv = pv * 1100

    # wind onshore:
    wind_onshore = csv_data['wind_on'].values.flatten()[0:periods]
    # scale relative values with installed onshore power
    wind_onshore = wind_onshore * 1100

    # wind offshore:
    wind_offshore = csv_data['wind_off'].values.flatten()[0:periods]
    # scale relative values with installed offshore power
    wind_offshore = wind_offshore * 150

    # electricity demand:
    el_demand = csv_data['el_demand'].values.flatten()[0:periods]
    max_el = np.max(el_demand)

    # heat demand:
    th_demand = csv_data['th_demand'].values.flatten()[0:periods]
    max_th = np.max(th_demand)

    # Creating the individual energy system components:

    # ---------------- Sources (incl wind and solar) -----------------------

    hard_coal_supply = components.Source(
        name='Hard Coal Supply',
        outputs=('Hard_Coal',),
        sector='Power',
        carrier='Hard_Coal',
        node_type='source',
        accumulated_amounts={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'Hard_Coal': 0},
        flow_emissions={'Hard_Coal': 0},
        flow_gradients={'Hard_Coal': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'Hard_Coal': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False},
        expansion_costs={'Hard_Coal': 0},
        expansion_limits={'Hard_Coal': nts.MinMax(min=0, max=float('+inf'))},
    )

    lignite_supply = components.Source(
        name='Lignite Supply',
        outputs=('lignite',),
        sector='Power',
        carrier='Lignite',
        node_type='source',
        accumulated_amounts={
            'lignite': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'lignite': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'lignite': 0},
        flow_emissions={'lignite': 0},
        flow_gradients={'lignite': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'lignite': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'lignite': False},
        expansion_costs={'lignite': 0},
        expansion_limits={'lignite': nts.MinMax(min=0, max=float('+inf'))},
    )

    fuel_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        sector='Power',
        carrier='Gas',
        node_type='source',
        accumulated_amounts={
            'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        flow_gradients={'fuel': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'fuel': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False},
        expansion_costs={'fuel': 0},
        expansion_limits={'fuel': nts.MinMax(min=0, max=float('+inf'))},
    )

    biogas_supply = components.Source(
        name='Biogas Supply',
        outputs=('biogas',),
        sector='Power',
        carrier='Biogas',
        node_type='source',
        accumulated_amounts={
            'biogas': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'biogas': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'biogas': 0},
        flow_emissions={'biogas': 0},
        flow_gradients={'biogas': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'biogas': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'biogas': False},
        expansion_costs={'biogas': 0},
        expansion_limits={'biogas': nts.MinMax(min=0, max=float('+inf'))},
    )

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=1100)},
        flow_costs={'electricity': 80},
        flow_emissions={'electricity': 0.05},
        flow_gradients={'electricity': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(pv))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 1000000},
        expansion_limits={'electricity': nts.MinMax(
            min=1100, max=float('+inf'))},
    )

    onshore_wind_turbine = components.Source(
        name='Onshore Wind Turbine',
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=1100)},
        flow_costs={'electricity': 60},
        flow_emissions={'electricity': 0.02},
        flow_gradients={'electricity': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(wind_onshore))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 1750000},
        expansion_limits={'electricity': nts.MinMax(
            min=1100, max=float('+inf'))},
    )

    offshore_wind_turbine = components.Source(
        name='Offshore Wind Turbine',
        outputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=150)},
        flow_costs={'electricity': 105},
        flow_emissions={'electricity': 0.02},
        flow_gradients={'electricity': nts.PositiveNegative(
            positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(periods * [0]),
            max=np.array(wind_offshore))},
        expandable={'electricity': expansion_problem},
        expansion_costs={'electricity': 3900000},
        expansion_limits={'electricity': nts.MinMax(
            min=150, max=float('+inf'))},
    )

    # ---------------- Transformer -----------------------

    hard_coal_chp = components.Transformer(
        name='Hard Coal CHP',
        inputs=('Hard_Coal',),
        outputs=('electricity', 'hot_water',),
        conversions={('Hard_Coal', 'electricity'): 0.4,
                     ('Hard_Coal', 'hot_water'): 0.4},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=300),
            'hot_water': nts.MinMax(min=0, max=300)},
        flow_costs={'Hard_Coal': 0, 'electricity': 80, 'hot_water': 6},
        flow_emissions={'Hard_Coal': 0, 'electricity': 0.8, 'hot_water': 0.06},
        flow_gradients={
            'Hard_Coal': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'Hard_Coal': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False,
                    'electricity': expansion_problem,
                    'hot_water': expansion_problem},
        expansion_costs={'Hard_Coal': 0,
                         'electricity': 1750000, 'hot_water': 131250},
        expansion_limits={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=300, max=float('+inf')),
            'hot_water': nts.MinMax(min=300, max=float('+inf'))},
    )

    hard_coal_power_plant = components.Transformer(
        name='Hard Coal PP',
        inputs=('Hard_Coal',),
        outputs=('electricity',),
        conversions={('Hard_Coal', 'electricity'): 0.43},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=500), },
        flow_costs={'Hard_Coal': 0, 'electricity': 80},
        flow_emissions={'Hard_Coal': 0, 'electricity': 0.8},
        flow_gradients={
            'Hard_Coal': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'Hard_Coal': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'Hard_Coal': False, 'electricity': expansion_problem},
        expansion_costs={'Hard_Coal': 0, 'electricity': 1650000},
        expansion_limits={
            'Hard_Coal': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=500, max=float('+inf'))},
    )

    combined_cycle_power_plant = components.Transformer(
        name='Combined Cycle PP',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.6},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=600)},
        flow_costs={'fuel': 0, 'electricity': 90},
        flow_emissions={'fuel': 0, 'electricity': 0.35},
        flow_gradients={
            'fuel': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'electricity': expansion_problem},
        expansion_costs={'fuel': 0, 'electricity': 950000},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=600, max=float('+inf'))},
    )

    lignite_power_plant = components.Transformer(
        name='Lignite Power Plant',
        inputs=('lignite',),
        outputs=('electricity',),
        conversions={('lignite', 'electricity'): 0.4},
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'lignite': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=500)},
        flow_costs={'lignite': 0, 'electricity': 65},
        flow_emissions={'lignite': 0, 'electricity': 1},
        flow_gradients={
            'lignite': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'lignite': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'lignite': False, 'electricity': expansion_problem},
        expansion_costs={'lignite': 0, 'electricity': 1900000},
        expansion_limits={
            'lignite': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=500, max=float('+inf'))},
    )

    biogas_chp = components.Transformer(
        name='Biogas CHP',
        inputs=('biogas',),
        outputs=('electricity', 'hot_water',),
        conversions={('biogas', 'electricity'): 0.4,
                     ('biogas', 'hot_water'): 0.5},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'biogas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=0, max=200),
            'hot_water': nts.MinMax(min=0, max=250)},
        flow_costs={'biogas': 0, 'electricity': 150, 'hot_water': 11.25},
        flow_emissions={'biogas': 0,
                        'electricity': 0.25, 'hot_water': 0.01875},
        flow_gradients={
            'biogas': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'biogas': nts.PositiveNegative(positive=0, negative=0),
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'biogas': False,
                    'electricity': expansion_problem,
                    'hot_water': expansion_problem},
        expansion_costs={'biogas': 0,
                         'electricity': 3500000, 'hot_water': 262500},
        expansion_limits={
            'biogas': nts.MinMax(min=0, max=float('+inf')),
            'electricity': nts.MinMax(min=200, max=float('+inf')),
            'hot_water': nts.MinMax(min=250, max=float('+inf'))},
    )

    heat_plant = components.Transformer(
        name='Heat Plant',
        inputs=('fuel',),
        outputs=('hot_water',),
        conversions={('fuel', 'hot_water'): 0.9},
        sector='Heat',
        carrier='hot_water',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=450)},
        flow_costs={'fuel': 0, 'hot_water': 35},
        flow_emissions={'fuel': 0, 'hot_water': 0.23},
        flow_gradients={
            'fuel': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'fuel': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'fuel': False, 'hot_water': expansion_problem},
        expansion_costs={'fuel': 0, 'hot_water': 390000},
        expansion_limits={
            'fuel': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=450, max=float('+inf'))},
    )

    power_to_heat = components.Transformer(
        name='Power To Heat',
        inputs=('electricity',),
        outputs=('hot_water',),
        conversions={('electricity', 'hot_water'): 0.99},
        sector='Coupled',
        carrier='coupled',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=0, max=100)},
        flow_costs={'electricity': 0, 'hot_water': 20},
        flow_emissions={'electricity': 0, 'hot_water': 0.0007},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf')),
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={
            'electricity': nts.PositiveNegative(positive=0, negative=0),
            'hot_water': nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={'electricity': False, 'hot_water': expansion_problem},
        expansion_costs={'electricity': 0, 'hot_water': 100000},
        expansion_limits={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'hot_water': nts.MinMax(min=100, max=float('+inf'))},
    )

    # ---------------- Storages -----------------------

    storage = components.Storage(
        name='Battery',
        input='electricity',
        output='electricity',
        capacity=100,
        initial_soc=0,
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.5),
        flow_rates={'electricity': nts.MinMax(min=0, max=33)},
        flow_efficiencies={
            'electricity': nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={'electricity': 400},
        flow_emissions={'electricity': 0.06},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': expansion_problem,
                    'electricity': expansion_problem},
        fixed_expansion_ratios={'electricity': expansion_problem},
        expansion_costs={'capacity': 1630000, 'electricity': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=100, max=float('+inf')),
            'electricity': nts.MinMax(min=33, max=float('+inf'))},
    )

    heat_storage = components.Storage(
        name='Heat Storage',
        input='hot_water',
        output='hot_water',
        capacity=50,
        initial_soc=0,
        sector='Heat',
        carrier='hot_water',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0.25),
        flow_rates={'hot_water': nts.MinMax(min=0, max=10)},
        flow_efficiencies={
            'hot_water': nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={'hot_water': 20},
        flow_emissions={'hot_water': 0},
        flow_gradients={
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'hot_water': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={'capacity': expansion_problem,
                    'hot_water': expansion_problem},
        fixed_expansion_ratios={'hot_water': expansion_problem},
        expansion_costs={'capacity': 4500, 'hot_water': 0},
        expansion_limits={
            'capacity': nts.MinMax(min=50, max=float('+inf')),
            'hot_water': nts.MinMax(min=10, max=float('+inf'))},
    )

    # ---------------- Sinks -----------------------

    el_demand = components.Sink(
        name='El Demand',
        inputs=('electricity',),
        sector='Power',
        carrier='electricity',
        node_type='demand',
        accumulated_amounts={
            'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'electricity': nts.MinMax(min=0, max=max_el)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        flow_gradients={
            'electricity': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'electricity': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'electricity': nts.MinMax(
            min=np.array(el_demand),
            max=np.array(el_demand))},
        expandable={'electricity': False},
        expansion_costs={'electricity': 0},
        expansion_limits={'electricity': nts.MinMax(
            min=0, max=float('+inf'))},
    )

    heat_demand = components.Sink(
        name='Heat Demand',
        inputs=('hot_water',),
        sector='Heat',
        carrier='hot_water',
        node_type='demand',
        accumulated_amounts={
            'hot_water': nts.MinMax(min=0, max=float('+inf'))},
        flow_rates={'hot_water': nts.MinMax(min=0, max=max_th)},
        flow_costs={'hot_water': 0},
        flow_emissions={'hot_water': 0},
        flow_gradients={
            'hot_water': nts.PositiveNegative(
                positive=float('+inf'), negative=float('+inf'))},
        gradient_costs={'hot_water': nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={'hot_water': nts.MinMax(
            min=np.array(th_demand),
            max=np.array(th_demand))},
        expandable={'hot_water': False},
        expansion_costs={'hot_water': 0},
        expansion_limits={'hot_water': nts.MinMax(
            min=0, max=float('+inf'))},
    )

    # ---------------- Busses -----------------------

    fuel_supply_line = components.Bus(
        name='Gas Line',
        inputs=('Gas Station.fuel',),
        outputs=('Combined Cycle PP.fuel', 'Heat Plant.fuel'),
        sector='Coupled',
        carrier='Gas',
        node_type='bus',
    )

    biogas_supply_line = components.Bus(
        name='Biogas Line',
        inputs=('Biogas Supply.biogas',),
        outputs=('Biogas CHP.biogas',),
        sector='Coupled',
        carrier='Biogas',
        node_type='bus',
    )

    hard_coal_supply_line = components.Bus(
        name='Hard Coal Supply Line',
        inputs=('Hard Coal Supply.Hard_Coal',),
        outputs=('Hard Coal PP.Hard_Coal', 'Hard Coal CHP.Hard_Coal',),
        sector='Coupled',
        carrier='Hard_Coal',
        node_type='bus',
    )

    lignite_supply_line = components.Bus(
        name='Lignite Supply Line',
        inputs=('Lignite Supply.lignite',),
        outputs=('Lignite Power Plant.lignite',),
        sector='Power',
        carrier='Lignite',
        node_type='bus',
    )

    electricity_line = components.Bus(
        name='Powerline',
        inputs=('Combined Cycle PP.electricity', 'Battery.electricity',
                'Lignite Power Plant.electricity', 'Hard Coal PP.electricity',
                'Hard Coal CHP.electricity', 'Solar Panel.electricity',
                'Offshore Wind Turbine.electricity', 'Biogas CHP.electricity',
                'Onshore Wind Turbine.electricity',
                ),
        outputs=('El Demand.electricity', 'Battery.electricity',
                 'Power To Heat.electricity'),
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    heat_line = components.Bus(
        name='Heatline',
        inputs=('Heat Plant.hot_water', 'Hard Coal CHP.hot_water',
                'Biogas CHP.hot_water', 'Power To Heat.hot_water',
                'Heat Storage.hot_water'),
        outputs=('Heat Demand.hot_water', 'Heat Storage.hot_water'),
        sector='Heat',
        carrier='hot_water',
        node_type='bus',
    )

    # Create the actual energy system:

    explicit_es = energy_system.AbstractEnergySystem(
        uid='Component_es',
        busses=(fuel_supply_line, electricity_line, hard_coal_supply_line,
                lignite_supply_line, biogas_supply_line, heat_line,),
        sinks=(el_demand, heat_demand),
        sources=(fuel_supply, solar_panel, onshore_wind_turbine,
                 hard_coal_supply, lignite_supply, offshore_wind_turbine,
                 biogas_supply,),
        transformers=(combined_cycle_power_plant, hard_coal_power_plant,
                      lignite_power_plant, biogas_chp, heat_plant,
                      power_to_heat, hard_coal_chp),
        storages=(storage, heat_storage),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # Store the energy system:
    if not filename:
        filename = 'component_es.tsf'

    explicit_es.dump(directory=directory, filename=filename)

    return explicit_es


def create_grid_kp_es(periods=24, directory=None, filename=None):
    """
    Create a model of a generic grid style energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_grid_kp_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``grid_es_KP.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Grid` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Examples_Application_Grid`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.

    Examples
    --------
    Use :func:`create_grid_kp_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_grid_kp_es()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gaspipeline
    Low Voltage Powerline
    District Heating
    Medium Voltage Powerline
    High Voltage Powerline
    Coal Supply Line
    Biogas
    Solar Panel
    Gas Station
    Onshore Wind Power
    Offshore Wind Power
    Coal Supply
    Solar Thermal
    Biogas plant
    Household Demand
    Commercial Demand
    District Heating Demand
    Industrial Demand
    Car charging Station
    BHKW
    Power to Heat
    GuD
    HKW
    HKW2
    Low Voltage Transformator
    High Voltage Transformator

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Coal Supply': '#666666',
    ...         'Coal Supply Line': '#666666',
    ...         'HKW': '#666666',
    ...         'HKW2': '#666666',
    ...         'Solar Thermal': '#b30000',
    ...         'Heat Storage': '#cc0033',
    ...         'District Heating': 'Red',
    ...         'District Heating Demand': 'Red',
    ...         'Power to Heat': '#b30000',
    ...         'Biogas plant': '#006600',
    ...         'Biogas': '#006600',
    ...         'BHKW': '#006600',
    ...         'Onshore Wind Power': '#99ccff',
    ...         'Offshore Wind Power': '#00ccff',
    ...         'Gas Station': '#336666',
    ...         'Gaspipeline': '#336666',
    ...         'GuD': '#336666',
    ...         'Solar Panel': '#ffe34d',
    ...         'Commercial Demand': '#ffe34d',
    ...         'Household Demand': '#ffe34d',
    ...         'Industrial Demand': '#ffe34d',
    ...         'Car charging Station': '#669999',
    ...         'Low Voltage Powerline': '#ffcc00',
    ...         'Medium Voltage Powerline': '#ffcc00',
    ...         'High Voltage Powerline': '#ffcc00',
    ...         'High Voltage Transformator': 'yellow',
    ...         'Low Voltage Transformator': 'yellow',
    ...     },
    ...     title='Energy System Grid "Kupferplatte" Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/grid_es_KP_example.png
        :align: center
        :alt: Image showing the create_grid_KP_es energy system graph.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
        'resources': float('+inf')
    }

    # Low Voltage and heat

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'electricity': 60.85},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv, max=pv)},

    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.33, ('fuel', 'heat'): 0.52},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697)},
        flow_costs={'fuel': 0, 'electricity': 124.4, 'heat': 31.1},
        flow_emissions={'fuel': 0, 'electricity': 0.1573, 'heat': 0.0732},
        timeseries=None,
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Powerline',
        inputs=('BHKW.electricity', 'Battery.electricity',
                'Solar Panel.electricity',),
        outputs=('Household Demand.electricity',
                 'Commercial Demand.electricity', 'Battery.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=('BHKW.heat', 'Solar Thermal.heat',
                'Heat Storage.heat', 'Power to Heat.heat', 'HKW.heat'),
        outputs=('District Heating Demand.heat', 'Heat Storage.heat'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Medium Voltage and heat

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'electricity': 61.1},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('electricity',),
        outputs=('heat',),
        conversions={('electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=50000),
            'heat': nts.MinMax(min=0, max=50000)},
        flow_costs={'electricity': 0, 'heat': 0},
        flow_emissions={'electricity': 0, 'heat': 0},
        timeseries=None,
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Powerline',
        inputs=('Onshore Wind Power.electricity',),
        outputs=('Car charging Station.electricity',
                 'Industrial Demand.electricity', 'Power to Heat.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_medium_transformator = components.Connector(
        name='Low Voltage Transformator',
        interfaces=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        conversions={('Medium Voltage Powerline', 'Low Voltage Powerline'): 1,
                     ('Low Voltage Powerline', 'Medium Voltage Powerline'): 1},
        inputs=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        outputs=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        timeseries=None,
        node_type='connector',
    )

    # High Voltage

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'electricity': 106.4},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.24, ('fuel', 'heat'): 0.6},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96)},
        flow_costs={'fuel': 0, 'electricity': 80.65, 'heat': 20.1625},
        flow_emissions={'fuel': 0, 'electricity': 0.5136, 'heat': 0.293},
        timeseries=None,
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.43},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=43913)},
        flow_costs={'fuel': 0, 'electricity': 80.65},
        flow_emissions={'fuel': 0, 'electricity': 0.5136},
        timeseries=None,
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.59},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'electricity': nts.MinMax(min=0, max=26742)},
        flow_costs={'fuel': 0, 'electricity': 88.7},
        flow_emissions={'fuel': 0, 'electricity': 0.3366},
        timeseries=None,
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_electricity_line = components.Bus(
        name='High Voltage Powerline',
        inputs=('Offshore Wind Power.electricity', 'GuD.electricity',
                'HKW.electricity', 'HKW2.electricity'),
        outputs=('Power Sink.electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_medium_transformator = components.Connector(
        name='High Voltage Transformator',
        interfaces=('Medium Voltage Powerline', 'High Voltage Powerline'),
        conversions={('Medium Voltage Powerline', 'High Voltage Powerline'): 1,
                     ('High Voltage Powerline', 'Medium Voltage Powerline'): 1
                     },
        inputs=('Medium Voltage Powerline', 'High Voltage Powerline'),
        outputs=('Medium Voltage Powerline', 'High Voltage Powerline'),
        timeseries=None,
        node_type='connector',
    )

    # 4. Create the actual energy system:
    es = energy_system.AbstractEnergySystem(
        uid='Energy System Grid "Kupferplatte"',
        busses=(gas_supply_line, low_electricity_line, heat_line,
                medium_electricity_line, high_electricity_line,
                coal_supply_line, biogas_supply_line),
        sinks=(household_demand, commercial_demand, heat_demand,
               industrial_demand, car_charging_station_demand,),
        sources=(solar_panel, gas_supply, onshore_wind_power,
                 offshore_wind_power, coal_supply, solar_thermal,
                 biogas_supply,),
        transformers=(bhkw_generator, power_to_heat,
                      gud_generator, hkw_generator, hkw_generator_2),
        connectors=(low_medium_transformator, high_medium_transformator),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # Store the energy system:
    if not filename:
        filename = 'grid_es_KP.tsf'

    es.dump(directory=directory, filename=filename)

    return es


def create_grid_cs_es(periods=24, transformer_efficiency=0.99, directory=None,
                      filename=None):
    """
    Create a model of a generic grid style energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    transformer_efficiency : int, default=0.99
        Efficiency of the grid transformers (must be a value between 0 and 1)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_grid_cs_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``grid_es_CS.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Grid` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Examples_Application_Grid`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.

    Examples
    --------
    Use :func:`create_grid_cs_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_grid_cs_es()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gaspipeline
    Low Voltage Powerline
    District Heating
    Medium Voltage Powerline
    High Voltage Powerline
    Coal Supply Line
    Biogas
    Solar Panel
    Gas Station
    Onshore Wind Power
    Offshore Wind Power
    Coal Supply
    Solar Thermal
    Biogas plant
    Household Demand
    Commercial Demand
    District Heating Demand
    Industrial Demand
    Car charging Station
    BHKW
    Power to Heat
    GuD
    HKW
    HKW2
    Pumped Storage
    Low Voltage Transformator
    High Voltage Transformator

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Coal Supply': '#666666',
    ...         'Coal Supply Line': '#666666',
    ...         'HKW': '#666666',
    ...         'HKW2': '#666666',
    ...         'Solar Thermal': '#b30000',
    ...         'Heat Storage': '#cc0033',
    ...         'District Heating': 'Red',
    ...         'District Heating Demand': 'Red',
    ...         'Power to Heat': '#b30000',
    ...         'Biogas plant': '#006600',
    ...         'Biogas': '#006600',
    ...         'BHKW': '#006600',
    ...         'Onshore Wind Power': '#99ccff',
    ...         'Offshore Wind Power': '#00ccff',
    ...         'Gas Station': '#336666',
    ...         'Gaspipeline': '#336666',
    ...         'GuD': '#336666',
    ...         'Solar Panel': '#ffe34d',
    ...         'Commercial Demand': '#ffe34d',
    ...         'Household Demand': '#ffe34d',
    ...         'Industrial Demand': '#ffe34d',
    ...         'Car charging Station': '#669999',
    ...         'Low Voltage Powerline': '#ffcc00',
    ...         'Medium Voltage Powerline': '#ffcc00',
    ...         'High Voltage Powerline': '#ffcc00',
    ...         'High Voltage Transformator': 'yellow',
    ...         'Low Voltage Transformator': 'yellow',
    ...         'Pumped Storage': '#0000cc',
    ...     },
    ...     title='Energy System Grid Connectors and Storage Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/grid_es_CS_example.png
        :align: center
        :alt: Image showing the create_grid_CS_es energy system graph.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
        'resources': float('+inf')
    }

    # Low Voltage and heat

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'electricity': 60.85},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv, max=pv)},
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.33, ('fuel', 'heat'): 0.52},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697)},
        flow_costs={'fuel': 0, 'electricity': 124.4, 'heat': 31.1},
        flow_emissions={'fuel': 0, 'electricity': 0.1573, 'heat': 0.0732},
        timeseries=None,
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Powerline',
        inputs=('BHKW.electricity', 'Solar Panel.electricity',),
        outputs=('Household Demand.electricity',
                 'Commercial Demand.electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=('BHKW.heat', 'Solar Thermal.heat',
                'Power to Heat.heat', 'HKW.heat'),
        outputs=('District Heating Demand.heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Medium Voltage and heat

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'electricity': 61.1},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('electricity',),
        outputs=('heat',),
        conversions={('electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'electricity': 0, 'heat': 0},
        flow_emissions={'electricity': 0, 'heat': 0},
        timeseries=None,
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Powerline',
        inputs=('Onshore Wind Power.electricity',),
        outputs=('Car charging Station.electricity',
                 'Industrial Demand.electricity', 'Power to Heat.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_medium_transformator = components.Connector(
        name='Low Voltage Transformator',
        interfaces=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        conversions={('Medium Voltage Powerline',
                      'Low Voltage Powerline'): transformer_efficiency,
                     ('Low Voltage Powerline',
                      'Medium Voltage Powerline'): transformer_efficiency},
        inputs=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        outputs=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        timeseries=None,
        node_type='connector',
    )

    # High Voltage

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'electricity': 106.4},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.24, ('fuel', 'heat'): 0.6},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96)},
        flow_costs={'fuel': 0, 'electricity': 80.65, 'heat': 20.1625},
        flow_emissions={'fuel': 0, 'electricity': 0.5136, 'heat': 0.293},
        timeseries=None,
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.43},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=43913)},
        flow_costs={'fuel': 0, 'electricity': 80.65},
        flow_emissions={'fuel': 0, 'electricity': 0.5136},
        timeseries=None,
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.59},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'electricity': nts.MinMax(min=0, max=26742)},
        flow_costs={'fuel': 0, 'electricity': 88.7},
        flow_emissions={'fuel': 0, 'electricity': 0.3366},
        timeseries=None,
    )

    pumped_storage = components.Storage(
        name='Pumped Storage',
        input='electricity',
        output='electricity',
        capacity=40000,
        initial_soc=50,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0),
        flow_rates={'electricity': nts.MinMax(min=0, max=8600)},
        flow_efficiencies={
            'electricity': nts.InOut(inflow=0.86, outflow=0.86)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries=None,
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_electricity_line = components.Bus(
        name='High Voltage Powerline',
        inputs=('Offshore Wind Power.electricity',
                'Pumped Storage.electricity', 'GuD.electricity',
                'HKW.electricity', 'HKW2.electricity'),
        outputs=('Pumped Storage.electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_medium_transformator = components.Connector(
        name='High Voltage Transformator',
        interfaces=('Medium Voltage Powerline', 'High Voltage Powerline'),
        conversions={('Medium Voltage Powerline',
                      'High Voltage Powerline'): transformer_efficiency,
                     ('High Voltage Powerline',
                      'Medium Voltage Powerline'): transformer_efficiency},
        inputs=('Medium Voltage Powerline', 'High Voltage Powerline'),
        outputs=('Medium Voltage Powerline', 'High Voltage Powerline'),
        timeseries=None,
        node_type='connector',
    )

    # 4. Create the actual energy system:
    es = energy_system.AbstractEnergySystem(
        uid='Energy System Grid Connectors and Storage',
        busses=(gas_supply_line, low_electricity_line, heat_line,
                medium_electricity_line, high_electricity_line,
                coal_supply_line, biogas_supply_line),
        sinks=(household_demand, commercial_demand, heat_demand,
               industrial_demand, car_charging_station_demand,),
        sources=(solar_panel, gas_supply, onshore_wind_power,
                 offshore_wind_power, coal_supply, solar_thermal,
                 biogas_supply),
        transformers=(bhkw_generator, power_to_heat,
                      gud_generator, hkw_generator, hkw_generator_2),
        storages=(pumped_storage,),
        connectors=(low_medium_transformator, high_medium_transformator),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # Store the energy system:
    if not filename:
        filename = 'grid_es_CS.tsf'

    es.dump(directory=directory, filename=filename)

    return es


def create_grid_cp_es(periods=24, transformer_efficiency=0.99, directory=None,
                      filename=None):
    """
    Create a model of a generic grid style energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    transformer_efficiency : int, default=0.99
        Efficiency of the grid transformers (must be a value between 0 and 1)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_grid_cp_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``grid_es_CP.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Grid` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Examples_Application_Grid`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.

    Examples
    --------
    Use :func:`create_grid_cp_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_grid_cp_es()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gaspipeline
    Low Voltage Powerline
    District Heating
    Medium Voltage Powerline
    High Voltage Powerline
    Coal Supply Line
    Biogas
    Solar Panel
    Gas Station
    Onshore Wind Power
    Offshore Wind Power
    Coal Supply
    Solar Thermal
    Biogas plant
    Power Source
    Household Demand
    Commercial Demand
    District Heating Demand
    Industrial Demand
    Car charging Station
    Power Sink
    BHKW
    Power to Heat
    GuD
    HKW
    HKW2
    Low Voltage Transformator
    High Voltage Transformator

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Coal Supply': '#666666',
    ...         'Coal Supply Line': '#666666',
    ...         'HKW': '#666666',
    ...         'HKW2': '#666666',
    ...         'Solar Thermal': '#b30000',
    ...         'Heat Storage': '#cc0033',
    ...         'District Heating': 'Red',
    ...         'District Heating Demand': 'Red',
    ...         'Power to Heat': '#b30000',
    ...         'Biogas plant': '#006600',
    ...         'Biogas': '#006600',
    ...         'BHKW': '#006600',
    ...         'Onshore Wind Power': '#99ccff',
    ...         'Offshore Wind Power': '#00ccff',
    ...         'Gas Station': '#336666',
    ...         'Gaspipeline': '#336666',
    ...         'GuD': '#336666',
    ...         'Solar Panel': '#ffe34d',
    ...         'Commercial Demand': '#ffe34d',
    ...         'Household Demand': '#ffe34d',
    ...         'Industrial Demand': '#ffe34d',
    ...         'Car charging Station': '#669999',
    ...         'Low Voltage Powerline': '#ffcc00',
    ...         'Medium Voltage Powerline': '#ffcc00',
    ...         'High Voltage Powerline': '#ffcc00',
    ...         'High Voltage Transformator': 'yellow',
    ...         'Low Voltage Transformator': 'yellow',
    ...     },
    ...     title='Energy System Grid Connectors and Powersource/-sink Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/grid_es_CP_example.png
        :align: center
        :alt: Image showing the create_grid_CP_es energy system graph.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
        'resources': float('+inf')
    }

    # Low Voltage and heat

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'electricity': 60.85},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv, max=pv)},
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.33, ('fuel', 'heat'): 0.52},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697)},
        flow_costs={'fuel': 0, 'electricity': 124.4, 'heat': 31.1},
        flow_emissions={'fuel': 0, 'electricity': 0.1573, 'heat': 0.0732},
        timeseries=None,
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Powerline',
        inputs=('BHKW.electricity', 'Battery.electricity',
                'Solar Panel.electricity',),
        outputs=('Household Demand.electricity',
                 'Commercial Demand.electricity', 'Battery.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=('BHKW.heat', 'Solar Thermal.heat',
                'Heat Storage.heat', 'Power to Heat.heat', 'HKW.heat'),
        outputs=('District Heating Demand.heat', 'Heat Storage.heat'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Medium Voltage and heat

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'electricity': 61.1},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('electricity',),
        outputs=('heat',),
        conversions={('electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'electricity': 0, 'heat': 0},
        flow_emissions={'electricity': 0, 'heat': 0},
        timeseries=None,
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Powerline',
        inputs=('Onshore Wind Power.electricity',),
        outputs=('Car charging Station.electricity',
                 'Industrial Demand.electricity', 'Power to Heat.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_medium_transformator = components.Connector(
        name='Low Voltage Transformator',
        interfaces=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        conversions={('Medium Voltage Powerline',
                      'Low Voltage Powerline'): transformer_efficiency,
                     ('Low Voltage Powerline',
                      'Medium Voltage Powerline'): transformer_efficiency},
        inputs=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        outputs=('Medium Voltage Powerline', 'Low Voltage Powerline'),
        timeseries=None,
        node_type='connector',
    )

    # High Voltage

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'electricity': 106.4},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.24, ('fuel', 'heat'): 0.6},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96)},
        flow_costs={'fuel': 0, 'electricity': 80.65, 'heat': 20.1625},
        flow_emissions={'fuel': 0, 'electricity': 0.5136, 'heat': 0.293},
        timeseries=None,
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.43},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=43913)},
        flow_costs={'fuel': 0, 'electricity': 80.65},
        flow_emissions={'fuel': 0, 'electricity': 0.5136},
        timeseries=None,
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.59},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'electricity': nts.MinMax(min=0, max=26742)},
        flow_costs={'fuel': 0, 'electricity': 88.7},
        flow_emissions={'fuel': 0, 'electricity': 0.3366},
        timeseries=None,
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_electricity_line = components.Bus(
        name='High Voltage Powerline',
        inputs=('Offshore Wind Power.electricity',
                'Pumped Storage.electricity', 'GuD.electricity',
                'HKW.electricity', 'Power Source.electricity',
                'HKW2.electricity'),
        outputs=('Pumped Storage.electricity', 'Power Sink.electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_medium_transformator = components.Connector(
        name='High Voltage Transformator',
        interfaces=('Medium Voltage Powerline', 'High Voltage Powerline'),
        conversions={('Medium Voltage Powerline',
                      'High Voltage Powerline'): transformer_efficiency,
                     ('High Voltage Powerline',
                      'Medium Voltage Powerline'): transformer_efficiency},
        inputs=('Medium Voltage Powerline', 'High Voltage Powerline'),
        outputs=('Medium Voltage Powerline', 'High Voltage Powerline'),
        timeseries=None,
        node_type='connector',
    )

    power_source = components.Source(
        name='Power Source',
        outputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Electricity',
        node_type='source',
        flow_rates={'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'electricity': 300},
        flow_emissions={'electricity': 0.6},
        timeseries=None,
    )

    power_sink = components.Sink(
        name='Power Sink',
        inputs=('electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={'electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'electricity': 300},
        flow_emissions={'electricity': 0.6},
        timeseries=None,
    )

    # 4. Create the actual energy system:
    es = energy_system.AbstractEnergySystem(
        uid='Energy System Grid Connectors and Powersource/-sink',
        busses=(gas_supply_line, low_electricity_line, heat_line,
                medium_electricity_line, high_electricity_line,
                coal_supply_line, biogas_supply_line),
        sinks=(household_demand, commercial_demand, heat_demand,
               industrial_demand, car_charging_station_demand, power_sink,),
        sources=(solar_panel, gas_supply, onshore_wind_power,
                 offshore_wind_power, coal_supply, solar_thermal,
                 biogas_supply, power_source,),
        transformers=(bhkw_generator, power_to_heat,
                      gud_generator, hkw_generator, hkw_generator_2),
        connectors=(low_medium_transformator, high_medium_transformator),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # Store the energy system:
    if not filename:
        filename = 'grid_es_CP.tsf'

    es.dump(directory=directory, filename=filename)

    return es


def create_grid_ts_es(periods=24, transformer_efficiency=0.99,
                      gridcapacity=60000, directory=None, filename=None):
    """
    Create a model of a generic grid style energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    transformer_efficiency : int, default=0.99
        Efficiency of the grid transformers (must be a value between 0 and 1)

    gridcapacity : int, default=60000
        Transmission capacity of the transformers of the gridstructure
        (at 0 the parts of the grid are not connected)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_grid_ts_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``grid_es_TS.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Grid` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Examples_Application_Grid`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.

    Examples
    --------
    Use :func:`create_grid_ts_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_grid_ts_es()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gaspipeline
    Low Voltage Powerline
    District Heating
    Medium Voltage Powerline
    High Voltage Powerline
    Coal Supply Line
    Biogas
    Solar Panel
    Gas Station
    Onshore Wind Power
    Offshore Wind Power
    Coal Supply
    Solar Thermal
    Biogas plant
    Household Demand
    Commercial Demand
    District Heating Demand
    Industrial Demand
    Car charging Station
    BHKW
    Power to Heat
    GuD
    HKW
    High Medium Transformator
    Low Medium Transformator
    Medium Low Transformator
    Medium High Transformator
    HKW2
    Pumped Storage LV
    Pumped Storage MV
    Pumped Storage HV

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Coal Supply': '#666666',
    ...         'Coal Supply Line': '#666666',
    ...         'HKW': '#666666',
    ...         'HKW2': '#666666',
    ...         'Solar Thermal': '#b30000',
    ...         'Heat Storage': '#cc0033',
    ...         'District Heating': 'Red',
    ...         'District Heating Demand': 'Red',
    ...         'Power to Heat': '#b30000',
    ...         'Biogas plant': '#006600',
    ...         'Biogas': '#006600',
    ...         'BHKW': '#006600',
    ...         'Onshore Wind Power': '#99ccff',
    ...         'Offshore Wind Power': '#00ccff',
    ...         'Gas Station': '#336666',
    ...         'Gaspipeline': '#336666',
    ...         'GuD': '#336666',
    ...         'Solar Panel': '#ffe34d',
    ...         'Commercial Demand': '#ffe34d',
    ...         'Household Demand': '#ffe34d',
    ...         'Industrial Demand': '#ffe34d',
    ...         'Car charging Station': '#669999',
    ...         'Low Voltage Powerline': '#ffcc00',
    ...         'Medium Voltage Powerline': '#ffcc00',
    ...         'High Voltage Powerline': '#ffcc00',
    ...         'High Voltage Transformator': 'yellow',
    ...         'Low Voltage Transformator': 'yellow',
    ...         'Pumped Storage LV': '#0000cc',
    ...         'Pumped Storage MV': '#0000cc',
    ...         'Pumped Storage HV': '#0000cc',
    ...     },
    ...     title='Energy System Grid Transformer and Storages Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/grid_es_TS_example.png
        :align: center
        :alt: Image showing the create_grid_TS_es energy system graph.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
        'resources': float('+inf')
    }

    # Low Voltage and heat

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'low-voltage-electricity': 60.85},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=pv, max=pv)},
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('low-voltage-electricity', 'heat'),
        conversions={('fuel', 'low-voltage-electricity'): 0.33,
                     ('fuel', 'heat'): 0.52},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'low-voltage-electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697)},
        flow_costs={'fuel': 0, 'low-voltage-electricity': 124.4, 'heat': 31.1},
        flow_emissions={'fuel': 0,
                        'low-voltage-electricity': 0.1573, 'heat': 0.0732},
        timeseries=None,
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Powerline',
        inputs=('BHKW.low-voltage-electricity',
                'Solar Panel.low-voltage-electricity',
                'Medium Low Transformator.low-voltage-electricity',
                'Pumped Storage LV.low-voltage-electricity'),
        outputs=('Household Demand.low-voltage-electricity',
                 'Commercial Demand.low-voltage-electricity',
                 'Low Medium Transformator.low-voltage-electricity',
                 'Pumped Storage LV.low-voltage-electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=('BHKW.heat', 'Solar Thermal.heat',
                'Power to Heat.heat', 'HKW.heat'),
        outputs=('District Heating Demand.heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Medium Voltage and heat

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='power',
        carrier='electricity',
        node_type='Renewable',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'medium-voltage-electricity': 61.1},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('medium-voltage-electricity',),
        outputs=('heat',),
        conversions={('medium-voltage-electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'medium-voltage-electricity': 0, 'heat': 0},
        flow_emissions={'medium-voltage-electricity': 0, 'heat': 0},
        timeseries=None,
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Powerline',
        inputs=('Onshore Wind Power.medium-voltage-electricity',
                'High Medium Transformator.medium-voltage-electricity',
                'Low Medium Transformator.medium-voltage-electricity',
                'Pumped Storage MV.medium-voltage-electricity'),
        outputs=('Car charging Station.medium-voltage-electricity',
                 'Industrial Demand.medium-voltage-electricity',
                 'Power to Heat.medium-voltage-electricity',
                 'Medium High Transformator.medium-voltage-electricity',
                 'Medium Low Transformator.medium-voltage-electricity',
                 'Pumped Storage MV.medium-voltage-electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # High Voltage

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='Renewable',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'high-voltage-electricity': 106.4},
        flow_emissions={'high-voltage-electricity': 0},
        timeseries={
            'high-voltage-electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('high-voltage-electricity', 'heat'),
        conversions={('fuel', 'high-voltage-electricity'): 0.24,
                     ('fuel', 'heat'): 0.6},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96)},
        flow_costs={'fuel': 0,
                    'high-voltage-electricity': 80.65, 'heat': 20.1625},
        flow_emissions={'fuel': 0,
                        'high-voltage-electricity': 0.5136, 'heat': 0.293},
        timeseries=None,
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.43},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=43913)},
        flow_costs={'fuel': 0, 'high-voltage-electricity': 80.65},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.5136},
        timeseries=None,
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.59},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'high-voltage-electricity': nts.MinMax(min=0, max=26742)},
        flow_costs={'fuel': 0, 'high-voltage-electricity': 88.7},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.3366},
        timeseries=None,
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_electricity_line = components.Bus(
        name='High Voltage Powerline',
        inputs=('Offshore Wind Power.high-voltage-electricity',
                'HKW2.high-voltage-electricity',
                'GuD.high-voltage-electricity', 'HKW.high-voltage-electricity',
                'Medium High Transformator.high-voltage-electricity',
                'Pumped Storage HV.high-voltage-electricity'),
        outputs=('High Medium Transformator.high-voltage-electricity',
                 'Pumped Storage HV.high-voltage-electricity'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Grid structure and Transformer

    low_medium_transformator = components.Transformer(
        name='Low Medium Transformator',
        inputs=('low-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={('low-voltage-electricity',
                      'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=gridcapacity),
            'medium-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity)},
        flow_costs={'low-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    medium_low_transformator = components.Transformer(
        name='Medium Low Transformator',
        inputs=('medium-voltage-electricity',),
        outputs=('low-voltage-electricity',),
        conversions={('medium-voltage-electricity',
                      'low-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity),
            'medium-voltage-electricity': nts.MinMax(min=0, max=gridcapacity)},
        flow_costs={'low-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    medium_high_transformator = components.Transformer(
        name='Medium High Transformator',
        inputs=('medium-voltage-electricity',),
        outputs=('high-voltage-electricity',),
        conversions={('medium-voltage-electricity',
                      'high-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity),
            'medium-voltage-electricity': nts.MinMax(min=0, max=gridcapacity)},
        flow_costs={'high-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'high-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    high_medium_transformator = components.Transformer(
        name='High Medium Transformator',
        inputs=('high-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={('high-voltage-electricity',
                      'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=gridcapacity),
            'medium-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity)},
        flow_costs={'high-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'high-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    # Storages

    pumped_storage_lv = components.Storage(
        name='Pumped Storage LV',
        input='low-voltage-electricity',
        output='low-voltage-electricity',
        capacity=40000,
        initial_soc=50,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0),
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=8600)},
        flow_efficiencies={
            'low-voltage-electricity': nts.InOut(inflow=0.86, outflow=0.86)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries=None,
    )

    pumped_storage_mv = components.Storage(
        name='Pumped Storage MV',
        input='medium-voltage-electricity',
        output='medium-voltage-electricity',
        capacity=40000,
        initial_soc=50,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0),
        flow_rates={'medium-voltage-electricity': nts.MinMax(min=0, max=8600)},
        flow_efficiencies={'medium-voltage-electricity': nts.InOut(
            inflow=0.86, outflow=0.86)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries=None,
    )

    pumped_storage_hv = components.Storage(
        name='Pumped Storage HV',
        input='high-voltage-electricity',
        output='high-voltage-electricity',
        capacity=40000,
        initial_soc=50,
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='storage',
        idle_changes=nts.PositiveNegative(positive=0, negative=0),
        flow_rates={'high-voltage-electricity': nts.MinMax(min=0, max=8600)},
        flow_efficiencies={
            'high-voltage-electricity': nts.InOut(inflow=0.86, outflow=0.86)},
        flow_costs={'high-voltage-electricity': 0},
        flow_emissions={'high-voltage-electricity': 0},
        timeseries=None,
    )

    # 4. Create the actual energy system:
    es = energy_system.AbstractEnergySystem(
        uid='Energy System Grid Transformers and Storages',
        busses=(gas_supply_line, low_electricity_line, heat_line,
                medium_electricity_line, high_electricity_line,
                coal_supply_line, biogas_supply_line,),
        sinks=(household_demand, commercial_demand, heat_demand,
               industrial_demand, car_charging_station_demand,),
        sources=(solar_panel, gas_supply, onshore_wind_power,
                 offshore_wind_power, coal_supply, solar_thermal,
                 biogas_supply,),
        transformers=(bhkw_generator, power_to_heat, gud_generator,
                      hkw_generator, high_medium_transformator,
                      low_medium_transformator, medium_low_transformator,
                      medium_high_transformator, hkw_generator_2,),
        storages=(pumped_storage_lv, pumped_storage_mv, pumped_storage_hv,),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # Store the energy system:
    if not filename:
        filename = 'grid_es_TS.tsf'

    es.dump(directory=directory, filename=filename)

    return es


def create_grid_tp_es(periods=24, transformer_efficiency=0.99,
                      gridcapacity=60000, directory=None, filename=None):
    """
    Create a model of a generic grid style energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    transformer_efficiency : int, default=0.99
        Efficiency of the grid transformers (must be a value between 0 and 1)

    gridcapacity : int, default=60000
        Transmission capacity of the transformers of the gridstructure
        (at 0 the parts of the grid are not connected)

    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~tessif.model.energy_system.AbstractEnergySystem.dump`
        .

        Will be :func:`joined <os.path.join>` with
        :paramref:`~create_grid_tp_es.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/tsf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``grid_es_TP.tsf``.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    References
    ----------
    :ref:`Models_Tessif_mwe` - For a step by step explanation on how to create
    a Tessif energy system.

    :ref:`AutoCompare_Grid` - For simulating and
    comparing this energy system using different supported models.

    :ref:`Examples_Application_Grid`,  - For a comprehensive example
    on a reference energy system to analyze and compare commitment
    optimization respecting among models.

    Examples
    --------
    Use :func:`create_grid_tp_es` to quickly access a tessif energy system
    to use for doctesting, or trying out this framework's utilities.

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.create_grid_tp_es()

    >>> for node in es.nodes:
    ...     print(node.uid)
    Gaspipeline
    Low Voltage Powerline
    District Heating
    Medium Voltage Powerline
    High Voltage Powerline
    Coal Supply Line
    Biogas
    Solar Panel
    Offshore Wind Power
    Onshore Wind Power
    Gas Station
    Coal Supply
    Solar Thermal
    Biogas plant
    Power Source LV
    Power Source MV
    Power Source HV
    Household Demand
    Commercial Demand
    District Heating Demand
    Industrial Demand
    Car charging Station
    Power Sink LV
    Power Sink MV
    Power Sink HV
    BHKW
    Power to Heat
    GuD
    HKW
    High Medium Transformator
    Low Medium Transformator
    Medium Low Transformator
    Medium High Transformator
    HKW2

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={
    ...         'Coal Supply': '#666666',
    ...         'Coal Supply Line': '#666666',
    ...         'HKW': '#666666',
    ...         'HKW2': '#666666',
    ...         'Solar Thermal': '#b30000',
    ...         'Heat Storage': '#cc0033',
    ...         'District Heating': 'Red',
    ...         'District Heating Demand': 'Red',
    ...         'Power to Heat': '#b30000',
    ...         'Biogas plant': '#006600',
    ...         'Biogas': '#006600',
    ...         'BHKW': '#006600',
    ...         'Onshore Wind Power': '#99ccff',
    ...         'Offshore Wind Power': '#00ccff',
    ...         'Gas Station': '#336666',
    ...         'Gaspipeline': '#336666',
    ...         'GuD': '#336666',
    ...         'Solar Panel': '#ffe34d',
    ...         'Commercial Demand': '#ffe34d',
    ...         'Household Demand': '#ffe34d',
    ...         'Industrial Demand': '#ffe34d',
    ...         'Car charging Station': '#669999',
    ...         'Low Voltage Powerline': '#ffcc00',
    ...         'Medium Voltage Powerline': '#ffcc00',
    ...         'High Voltage Powerline': '#ffcc00',
    ...         'High Voltage Transformator': 'yellow',
    ...         'Low Voltage Transformator': 'yellow',
    ...     },
    ...     title='Energy System Grid Transformer and Powersources/-sinks Graph',
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: ../images/grid_es_TP_example.png
        :align: center
        :alt: Image showing the create_grid_TP_es energy system graph.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
        'resources': float('+inf')
    }

    # Low Voltage and heat

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='Renewable',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'low-voltage-electricity': 60.85},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=pv, max=pv)},
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('low-voltage-electricity', 'heat'),
        conversions={('fuel', 'low-voltage-electricity'): 0.33,
                     ('fuel', 'heat'): 0.52},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='low-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'low-voltage-electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697)},
        flow_costs={'fuel': 0, 'low-voltage-electricity': 124.4, 'heat': 31.1},
        flow_emissions={'fuel': 0,
                        'low-voltage-electricity': 0.1573, 'heat': 0.0732},
        timeseries=None,
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='gas',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Powerline',
        inputs=('BHKW.low-voltage-electricity',
                'Power Source LV.low-voltage-electricity',
                'Solar Panel.low-voltage-electricity',
                'Medium Low Transformator.low-voltage-electricity'),
        outputs=('Household Demand.low-voltage-electricity',
                 'Commercial Demand.low-voltage-electricity',
                 'Low Medium Transformator.low-voltage-electricity',
                 'Power Sink LV.low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=('BHKW.heat', 'Solar Thermal.heat',
                'Power to Heat.heat', 'HKW.heat'),
        outputs=('District Heating Demand.heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Medium Voltage and heat

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='power',
        carrier='medium-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'medium-voltage-electricity': 61.1},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('medium-voltage-electricity',),
        outputs=('heat',),
        conversions={('medium-voltage-electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'medium-voltage-electricity': 0, 'heat': 0},
        flow_emissions={'medium-voltage-electricity': 0, 'heat': 0},
        timeseries=None,
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Powerline',
        inputs=('Onshore Wind Power.medium-voltage-electricity',
                'High Medium Transformator.medium-voltage-electricity',
                'Low Medium Transformator.medium-voltage-electricity',
                'Power Source MV.medium-voltage-electricity',),
        outputs=('Car charging Station.medium-voltage-electricity',
                 'Industrial Demand.medium-voltage-electricity',
                 'Power to Heat.medium-voltage-electricity',
                 'Medium High Transformator.medium-voltage-electricity',
                 'Medium Low Transformator.medium-voltage-electricity',
                 'Power Sink MV.medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # High Voltage

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='high-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'high-voltage-electricity': 106.4},
        flow_emissions={'high-voltage-electricity': 0},
        timeseries={
            'high-voltage-electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('high-voltage-electricity', 'heat'),
        conversions={('fuel', 'high-voltage-electricity'): 0.24,
                     ('fuel', 'heat'): 0.6},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='high-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96)},
        flow_costs={'fuel': 0,
                    'high-voltage-electricity': 80.65, 'heat': 20.1625},
        flow_emissions={'fuel': 0,
                        'high-voltage-electricity': 0.5136, 'heat': 0.293},
        timeseries=None,
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.43},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=43913)},
        flow_costs={'fuel': 0, 'high-voltage-electricity': 80.65},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.5136},
        timeseries=None,
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.59},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='generator',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'high-voltage-electricity': nts.MinMax(min=0, max=26742)},
        flow_costs={'fuel': 0, 'high-voltage-electricity': 88.7},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.3366},
        timeseries=None,
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    high_electricity_line = components.Bus(
        name='High Voltage Powerline',
        inputs=('Offshore Wind Power.high-voltage-electricity',
                'HKW2.high-voltage-electricity',
                'GuD.high-voltage-electricity', 'HKW.high-voltage-electricity',
                'Medium High Transformator.high-voltage-electricity',
                'Power Source HV.high-voltage-electricity',),
        outputs=('Pumped Storage.high-voltage-electricity',
                 'High Medium Transformator.high-voltage-electricity',
                 'Power Sink HV.high-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='bus',
        # Total number of arguments to specify bus object
    )

    # Grid structure and Transformer

    low_medium_transformator = components.Transformer(
        name='Low Medium Transformator',
        inputs=('low-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={('low-voltage-electricity',
                      'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=gridcapacity),
            'medium-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity)},
        flow_costs={'low-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    medium_low_transformator = components.Transformer(
        name='Medium Low Transformator',
        inputs=('medium-voltage-electricity',),
        outputs=('low-voltage-electricity',),
        conversions={('medium-voltage-electricity',
                      'low-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity),
            'medium-voltage-electricity': nts.MinMax(min=0, max=gridcapacity)},
        flow_costs={'low-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    medium_high_transformator = components.Transformer(
        name='Medium High Transformator',
        inputs=('medium-voltage-electricity',),
        outputs=('high-voltage-electricity',),
        conversions={('medium-voltage-electricity',
                      'high-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity),
            'medium-voltage-electricity': nts.MinMax(min=0, max=gridcapacity)},
        flow_costs={'high-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'high-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    high_medium_transformator = components.Transformer(
        name='High Medium Transformator',
        inputs=('high-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={('high-voltage-electricity',
                      'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=gridcapacity),
            'medium-voltage-electricity': nts.MinMax(
                min=0, max=transformer_efficiency * gridcapacity)},
        flow_costs={'high-voltage-electricity': 0,
                    'medium-voltage-electricity': 0},
        flow_emissions={'high-voltage-electricity': 0,
                        'medium-voltage-electricity': 0},
        timeseries=None,
    )

    # Surplus Grid

    power_source_lv = components.Source(
        name='Power Source LV',
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
        timeseries=None,
    )

    power_source_mv = components.Source(
        name='Power Source MV',
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={'medium-voltage-electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
        timeseries=None,
    )

    power_source_hv = components.Source(
        name='Power Source HV',
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
        timeseries=None,
    )

    power_sink_lv = components.Sink(
        name='Power Sink LV',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
        timeseries=None,
    )

    power_sink_mv = components.Sink(
        name='Power Sink MV',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={'medium-voltage-electricity': nts.MinMax(
            min=0, max=float('+inf'))},
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
        timeseries=None,
    )

    power_sink_hv = components.Sink(
        name='Power Sink HV',
        inputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
        timeseries=None,
    )

    # 4. Create the actual energy system:
    es = energy_system.AbstractEnergySystem(
        uid='Energy System Grid Transformers and Powersources/-sinks',
        busses=(gas_supply_line, low_electricity_line, heat_line,
                medium_electricity_line, high_electricity_line,
                coal_supply_line, biogas_supply_line,),
        sinks=(household_demand, commercial_demand, heat_demand,
               industrial_demand, car_charging_station_demand,
               power_sink_lv, power_sink_mv, power_sink_hv,),
        sources=(solar_panel, offshore_wind_power, onshore_wind_power,
                 gas_supply, coal_supply, solar_thermal, biogas_supply,
                 power_source_lv, power_source_mv, power_source_hv,),
        transformers=(bhkw_generator, power_to_heat, gud_generator,
                      hkw_generator, high_medium_transformator,
                      low_medium_transformator, medium_low_transformator,
                      medium_high_transformator, hkw_generator_2),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    # Store the energy system:
    if not filename:
        filename = 'grid_es_TP.tsf'

    es.dump(directory=directory, filename=filename)

    return es


def create_transcne_es(
        periods=24,
        transformer_efficiency=0.93,
        gridcapacity=60000,
        expansion=False
):
    """Create the TransCnE system model scenarios combinations.

    As found in :ref:`TransCnE`

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    transformer_efficiency : int, default=0.99
        Efficiency of the grid transformers (must be a value between 0 and 1)

    gridcapacity : int, default=60000
        Transmission capacity of the transformers of the grid structure
        (at 0 the parts of the grid are not connected)

    expansion: bool, default=False
        If ``True`` :paramref:`gridcapacity` is subject to expansion.

    Note
    ----
    Changes compared to `Hanke Project Thesis
    <https://tore.tuhh.de/handle/11420/11759>`_:

        1. Rename ``"Power Source [Voltage]"`` to
           ``"Deficit Source [Voltage]"``
        2. Rename ``"Power Sinks [Voltage]"`` to ``"Excess Sinks [Voltage]"``
        3. Rename ``"[High/Mid/Low] Voltage Powerline"`` to ``"[High/Mid/Low]
           Voltage Grid"``
        4. Rename ``"[Voltage to Voltage] Transformator"`` to
           ``"[Voltage to Voltage] Transfer"``
        5. Change :paramref:`gridcapacity` to reference the maximum outflow.
        6. :paramref:`expansion` capabilities are added to allow :paramref:`gridcapacity`
           to be expanded
        7. Default :paramref:`transformer_efficiency` is decreased to ``0.93`` to
           discourage energy circulation between to grid busses to dissipate
           surplus amounts.
        8. Outflow costs of 10 cost units per power unit are added to all
           ``Transfer`` components, to further discourage energy circulation
           between to grid busses to dissipate surplus amounts and to encourage
           local production and consumption.

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
    }

    # -------------Low Voltage and heat ------------------

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='Renewable',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'low-voltage-electricity': 60.85},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=pv, max=pv)},
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
        timeseries=None,
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('low-voltage-electricity', 'heat'),
        conversions={
            ('fuel', 'low-voltage-electricity'): 0.33,
            ('fuel', 'heat'): 0.52,
        },
        # Minimum number of arguments required',
        sector='Coupled',
        carrier='low-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'low-voltage-electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697),
        },
        flow_costs={'fuel': 0, 'low-voltage-electricity': 124.4, 'heat': 31.1},
        flow_emissions={
            'fuel': 0,
            'low-voltage-electricity': 0.1573,
            'heat': 0.0732,
        },
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='low-voltage-electricity',
        node_type='demand',
        flow_rates={'low-voltage-electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'low-voltage-electricity': 0},
        flow_emissions={'low-voltage-electricity': 0},
        timeseries={'low-voltage-electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        sector='Power',
        carrier='gas',
        node_type='bus',
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='gas',
        node_type='bus',
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Grid',
        inputs=(
            'BHKW.low-voltage-electricity',
            'Deficit Source LV.low-voltage-electricity',
            'Solar Panel.low-voltage-electricity',
            'Medium Low Transfer.low-voltage-electricity',
        ),
        outputs=(
            'Household Demand.low-voltage-electricity',
            'Commercial Demand.low-voltage-electricity',
            'Low Medium Transfer.low-voltage-electricity',
            'Excess Sink LV.low-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=(
            'BHKW.heat',
            'Solar Thermal.heat',
            'Power to Heat.heat',
            'HKW.heat',
        ),
        outputs=('District Heating Demand.heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
    )

    # ----- -------Medium Voltage and Heat ------------------

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='power',
        carrier='medium-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'medium-voltage-electricity': 61.1},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='medium-voltage-electricity',
        node_type='demand',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'medium-voltage-electricity': 0},
        flow_emissions={'medium-voltage-electricity': 0},
        timeseries={
            'medium-voltage-electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('medium-voltage-electricity',),
        outputs=('heat',),
        conversions={('medium-voltage-electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
            'heat': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'medium-voltage-electricity': 0, 'heat': 0},
        flow_emissions={'medium-voltage-electricity': 0, 'heat': 0},
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Grid',
        inputs=(
            'Onshore Wind Power.medium-voltage-electricity',
            'High Medium Transfer.medium-voltage-electricity',
            'Low Medium Transfer.medium-voltage-electricity',
            'Deficit Source MV.medium-voltage-electricity',
        ),
        outputs=(
            'Car charging Station.medium-voltage-electricity',
            'Industrial Demand.medium-voltage-electricity',
            'Power to Heat.medium-voltage-electricity',
            'Medium High Transfer.medium-voltage-electricity',
            'Medium Low Transfer.medium-voltage-electricity',
            'Excess Sink MV.medium-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    # ----------------- High Voltage -------------------------

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='high-voltage-electricity',
        node_type='Renewable',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'high-voltage-electricity': 106.4},
        flow_emissions={'high-voltage-electricity': 0},
        timeseries={
            'high-voltage-electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('high-voltage-electricity', 'heat'),
        conversions={
            ('fuel', 'high-voltage-electricity'): 0.24,
            ('fuel', 'heat'): 0.6,
        },
        # Minimum number of arguments required
        sector='Coupled',
        carrier='high-voltage-electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96),
        },
        flow_costs={
            'fuel': 0,
            'high-voltage-electricity': 80.65,
            'heat': 20.1625,
        },
        flow_emissions={
            'fuel': 0,
            'high-voltage-electricity': 0.5136,
            'heat': 0.293,
        },
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.43},
        # Minimum number of arguments required
        sector='Coupled',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'high-voltage-electricity': nts.MinMax(min=0, max=43913),
        },
        flow_costs={'fuel': 0, 'high-voltage-electricity': 80.65},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.5136},
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('high-voltage-electricity',),
        conversions={('fuel', 'high-voltage-electricity'): 0.59},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='generator',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'high-voltage-electricity': nts.MinMax(min=0, max=26742),
        },
        flow_costs={'fuel': 0, 'high-voltage-electricity': 88.7},
        flow_emissions={'fuel': 0, 'high-voltage-electricity': 0.3366},
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
    )

    high_electricity_line = components.Bus(
        name='High Voltage Grid',
        inputs=(
            'Offshore Wind Power.high-voltage-electricity',
            'HKW2.high-voltage-electricity',
            'GuD.high-voltage-electricity', 'HKW.high-voltage-electricity',
            'Medium High Transfer.high-voltage-electricity',
            'Deficit Source HV.high-voltage-electricity',
        ),
        outputs=(
            'Pumped Storage.high-voltage-electricity',
            'High Medium Transfer.high-voltage-electricity',
            'Excess Sink HV.high-voltage-electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    # Gridstructure and Transformer

    low_medium_transformator = components.Transformer(
        name='Low Medium Transfer',
        inputs=('low-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={('low-voltage-electricity',
                      'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        flow_emissions={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 0},
        expandable={
            'low-voltage-electricity': False,
            'medium-voltage-electricity': expansion,
        },
        expansion_costs={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        expansion_limits={
            'low-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    medium_low_transformator = components.Transformer(
        name='Medium Low Transfer',
        inputs=('medium-voltage-electricity',),
        outputs=('low-voltage-electricity',),
        conversions={('medium-voltage-electricity',
                      'low-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        latitude=42,
        longitude=42,
        region='Here',
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'low-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),

        },
        flow_costs={
            'medium-voltage-electricity': 0,
            'low-voltage-electricity': 10,
        },
        flow_emissions={
            'low-voltage-electricity': 0,
            'medium-voltage-electricity': 0,
        },
        expandable={
            'medium-voltage-electricity': False,
            'low-voltage-electricity': expansion,
        },
        expansion_costs={
            'medium-voltage-electricity': 0,
            'low-voltage-electricity': 10,
        },
        expansion_limits={
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'low-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    medium_high_transformator = components.Transformer(
        name='Medium High Transfer',
        inputs=('medium-voltage-electricity',),
        outputs=('high-voltage-electricity',),
        conversions={
            ('medium-voltage-electricity',
             'high-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'high-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 10,
        },
        flow_emissions={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 0,
        },
        expandable={
            'medium-voltage-electricity': False,
            'high-voltage-electricity': expansion,
        },
        expansion_costs={
            'medium-voltage-electricity': 0,
            'high-voltage-electricity': 10,
        },
        expansion_limits={
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'high-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    high_medium_transformator = components.Transformer(
        name='High Medium Transfer',
        inputs=('high-voltage-electricity',),
        outputs=('medium-voltage-electricity',),
        conversions={
            ('high-voltage-electricity',
             'medium-voltage-electricity'): transformer_efficiency},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(
                min=0,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=0,
                max=gridcapacity,
            ),
        },
        flow_costs={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        flow_emissions={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 0,
        },
        expandable={
            'high-voltage-electricity': False,
            'medium-voltage-electricity': expansion,
        },
        expansion_costs={
            'high-voltage-electricity': 0,
            'medium-voltage-electricity': 10,
        },
        expansion_limits={
            'high-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
            'medium-voltage-electricity': nts.MinMax(
                min=gridcapacity,
                max=float("+inf"),
            ),
        },
    )

    # ---------- Deficit Sources ---------------

    power_source_lv = components.Source(
        name='Deficit Source LV',
        outputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
    )

    power_source_mv = components.Source(
        name='Deficit Source MV',
        outputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
        },
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
    )

    power_source_hv = components.Source(
        name='Deficit Source HV',
        outputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='source',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
    )

    power_sink_lv = components.Sink(
        name='Excess Sink LV',
        inputs=('low-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'low-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'low-voltage-electricity': 300},
        flow_emissions={'low-voltage-electricity': 0.6},
    )

    # ------------------- Excess Sinks --------------------------
    power_sink_mv = components.Sink(
        name='Excess Sink MV',
        inputs=('medium-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'medium-voltage-electricity': nts.MinMax(min=0, max=float('+inf')),
        },
        flow_costs={'medium-voltage-electricity': 300},
        flow_emissions={'medium-voltage-electricity': 0.6},
    )

    power_sink_hv = components.Sink(
        name='Excess Sink HV',
        inputs=('high-voltage-electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='sink',
        flow_rates={
            'high-voltage-electricity': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'high-voltage-electricity': 300},
        flow_emissions={'high-voltage-electricity': 0.6},
    )

    # 4. Create the actual energy system:
    if expansion:
        uid = "TransE"
    else:
        uid = "TransC"

    es = energy_system.AbstractEnergySystem(
        uid=uid,
        busses=(
            gas_supply_line,
            low_electricity_line,
            heat_line,
            medium_electricity_line,
            high_electricity_line,
            coal_supply_line,
            biogas_supply_line,
        ),
        sinks=(
            household_demand,
            commercial_demand,
            heat_demand,
            industrial_demand,
            car_charging_station_demand,
            power_sink_lv,
            power_sink_mv,
            power_sink_hv,
        ),
        sources=(
            solar_panel,
            offshore_wind_power,
            onshore_wind_power,
            gas_supply,
            coal_supply,
            solar_thermal,
            biogas_supply,
            power_source_lv,
            power_source_mv,
            power_source_hv,
        ),
        transformers=(
            bhkw_generator,
            power_to_heat,
            gud_generator,
            hkw_generator,
            high_medium_transformator,
            low_medium_transformator,
            medium_low_transformator,
            medium_high_transformator,
            hkw_generator_2,
        ),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return es


def create_simple_transformer_grid_es(expansion=False):
    """Create a simplified grid energy system  for testing.

    Emulates common grid (congestion) behaviours, during its 6 timesteps:

        1. Everything provided by HV-Source
        2. Too much provided by HV-Source; H2M grid congests
           and MV-BS and MV-XS need to compensate
        3. Too little provided, so MV-BS needs to provide
        4. Everything provided by MV-Source
        5. Too much provided by MV-Source, M2H grid congests
           and HV-BS and HV-XS need to compensate
        6. Too little provided, so MV-BS needs to provide

    Parameters
    ----------
    expansion: bool
        Boolean indicating whether to use the "expansion"
        model-scenario-combination. If ``True``, the High -> Medium Voltage
        connection can be expanded at the cost of X per capacity, whereas the
        Medium -> High voltage connection can be expanded at the cost of 100
        per capacity unit.

        Leading to the first beeing expanded, so no redispatch has to be done
        from high to medium. The latter however will be not expanded, since
        redispatching from medium to high is more cost-efficient in this case.

        The above behaviours subsequently change to:

        1. Everything provided by HV-Source
        2. Too much provided by HV-Source; It's enough to
           also satisfy the MV-Demand, since the high to medium connection
           gets expanded. The HV-XS takes the excess indicating the amount
           of surpluss that would get capped in a real world application.
        3. Too little provided, so MV-BS needs to provide
        4. Everything provided by MV-Source
        5. Too much provided by MV-Source, M2H grid congests
           and HV-BS and MV-XS need to compensate
        6. Too little provided, so MV-BS needs to provide

    Returns
    -------
    tessif.model.energy_system.AbstractEnergySystem
        Tessif energy system model (scenario comibnation) emulating common
        grid analysis topics.

    Example
    -------
    1. Create the Model-Scenario-Combination (msc):

    >>> msc = create_simple_transformer_grid_es()

    2. Optimize using oemof and see the results::

        import tessif.transform.es2es.omf as tsf2omf  # nopep8
        import tessif.simulate as optimize  # nopep8
        import tessif.transform.es2mapping.omf as post_process_omf  # nopep8

        omf_es = tsf2omf.transform(msc)
        opt_omf_es = optimize.omf_from_es(omf_es)
        all_res = post_process_omf.AllResultier(opt_omf_es)

        print(all_res.node_load['MV-Bus'])
        print(all_res.node_load['HV-Bus'])

    3. Visualize the tessif energy system as generic graph:

    >>> import tessif.visualize.dcgrph as dcv  # nopep8
    >>> app = dcv.draw_generic_graph(
    ...     energy_system=msc,
    ...     color_group={
    ...         'HV-Demand': '#ff9900',
    ...         'HV-BS': '#ff9900',
    ...         'HV-XS': '#ff9900',
    ...         'HV-Source': '#ff9900',
    ...         'H2M': '#ffcc00',
    ...         'M2H': '#ffcc00',
    ...         'MV-Bus': '#ffcc00',
    ...         'HV-Bus': '#ffcc00',
    ...         'MV-Demand': '#ff6600',
    ...         'MV-Source': '#ff6600',
    ...         'MV-BS': '#ff6600',
    ...         'MV-XS': '#ff6600',
    ...     },
    ... )

    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: ../images/simple_transformer_grid_es.png
        :align: center
        :alt: Image showing the simple transformer grid es generic graph
"""

    # predefine high -> med and med -> high efficiencies for cleaner
    # code and integer results
    eta_h2m = 10/12
    eta_m2h = 10/11

    # define optimization timespan
    opt_timespan = pd.date_range('7/13/1990', periods=6, freq='H')

    # 3. Creating the individual energy system components:
    hv_source = components.Source(
        name='HV-Source',
        outputs=('hv-electricity',),
        flow_rates={"hv-electricity": nts.MinMax(min=0, max=30)},
        # Minimum number of arguments required
        timeseries={
            'hv-electricity': nts.MinMax(
                min=[10+10/eta_h2m, 30, 10, 0, 0, 0],
                max=[10+10/eta_h2m, 30, 10, 0, 0, 0],
            ),
        },
    )

    mv_source = components.Source(
        name='MV-Source',
        outputs=('mv-electricity',),
        flow_rates={"mv-electricity": nts.MinMax(min=0, max=30)},
        timeseries={
            'mv-electricity': nts.MinMax(
                min=[0, 0, 0, 10+10/eta_m2h, 30, 10, ],
                max=[0, 0, 0, 10+10/eta_m2h, 30, 10, ],
            ),
        },
    )

    hv_balance_source = components.Source(
        name="HV-BS",
        outputs=("hv-electricity",),
        flow_rates={"hv-electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"hv-electricity": 10},
    )

    mv_balance_source = components.Source(
        name="MV-BS",
        outputs=("mv-electricity",),
        flow_rates={"mv-electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"mv-electricity": 10},
    )

    high_to_med = components.Transformer(
        name='H2M',
        inputs=('hv-electricity',),
        outputs=('mv-electricity',),
        conversions={('hv-electricity', 'mv-electricity'): eta_h2m},
        flow_rates={
            'hv-electricity': nts.MinMax(min=0, max=float("+inf")),
            'mv-electricity': nts.MinMax(min=0, max=10),
        },
        expandable={
            'hv-electricity': False,
            'mv-electricity': expansion,
        },
        expansion_costs={
            'hv-electricity': 0,
            'mv-electricity': 5,
        },
        expansion_limits={
            'hv-electricity': nts.MinMax(min=10, max=float("+inf")),
            'mv-electricity': nts.MinMax(min=10, max=float("+inf")),
        },
    )

    med_to_high = components.Transformer(
        name='M2H',
        inputs=('mv-electricity',),
        outputs=('hv-electricity',),
        conversions={('mv-electricity', 'hv-electricity'): eta_m2h},
        flow_rates={
            'mv-electricity': nts.MinMax(min=0, max=float("+inf")),
            'hv-electricity': nts.MinMax(min=0, max=10),
        },
        expandable={
            'mv-electricity': False,
            'hv-electricity': expansion,
        },
        expansion_costs={
            'mv-electricity': 0,
            'hv-electricity': 100,
        },
        expansion_limits={
            'hv-electricity': nts.MinMax(min=10, max=float("+inf")),
            'mv-electricity': nts.MinMax(min=10, max=float("+inf")),
        },
    )

    mv_demand = components.Sink(
        name='MV-Demand',
        inputs=('mv-electricity',),
        # Minimum number of arguments required
        flow_rates={'mv-electricity': nts.MinMax(min=10, max=10)},
        timeseries={
            'mv-electricity': nts.MinMax(
                min=[10, 12, 10, 10, 10, 10],
                max=[10, 12, 10, 10, 10, 10],
            ),
        },
    )

    hv_demand = components.Sink(
        name='HV-Demand',
        inputs=('hv-electricity',),
        # Minimum number of arguments required
        flow_rates={'hv-electricity': nts.MinMax(min=10, max=10)},
        timeseries={
            'hv-electricity': nts.MinMax(
                min=[10, 10, 10, 10, 12, 10],
                max=[10, 10, 10, 10, 12, 10],
            ),
        },
    )

    hv_excess_sink = components.Sink(
        name="HV-XS",
        inputs=("hv-electricity",),
        flow_rates={"hv-electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"hv-electricity": 10},
    )

    mv_excess_sink = components.Sink(
        name="MV-XS",
        inputs=("mv-electricity",),
        flow_rates={"mv-electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"mv-electricity": 10},
    )

    hv_bus = components.Bus(
        name='HV-Bus',
        inputs=(
            'HV-Source.hv-electricity',
            'M2H.hv-electricity',
            "HV-BS.hv-electricity",
        ),
        outputs=(
            'H2M.hv-electricity',
            "HV-Demand.hv-electricity",
            "HV-XS.hv-electricity",
        ),
    )

    mv_bus = components.Bus(
        name='MV-Bus',
        inputs=(
            "MV-Source.mv-electricity",
            'H2M.mv-electricity',
            "MV-BS.mv-electricity",
        ),
        outputs=(
            'M2H.mv-electricity',
            "MV-Demand.mv-electricity",
            "MV-XS.mv-electricity",
        ),
    )

    # 4. Creating the actual energy system:
    model_scenario_combination = energy_system.AbstractEnergySystem(
        uid='Two Transformer Grid Example',
        busses=(hv_bus, mv_bus),
        sinks=(hv_demand, mv_demand, hv_excess_sink, mv_excess_sink),
        sources=(hv_source, mv_source, hv_balance_source, mv_balance_source),
        transformers=(med_to_high, high_to_med),
        timeframe=opt_timespan,
    )

    return model_scenario_combination


def create_losslc_es(periods=24,):
    """
    Create the TransCnE system model scenarios combinations.

    Parameters
    ----------
    periods : int, default=24
        Number of time steps of the evaluated timeframe (one time step is one
        hour)

    Note
    ----
    Changes compared to `Hanke Project Thesis
    <https://tore.tuhh.de/handle/11420/11759>`_:

        1. Rename ``"[High/Mid/Low] Voltage Powerline"`` to ``"[High/Mid/Low]
           Voltage Grid"``
        2. Rename ``"[High/Low] Voltage Transformator"`` to ``"[High/Low]
           Voltage Transfer Grid"``

    Return
    ------
    es: :class:`tessif.model.energy_system.AbstractEnergySystem`
        Tessif energy system.

    Examples
    --------
    Visualize the energy system:

    >>> import tessif.visualize.dcgrph as dcv  # nopep8
    >>> app = dcv.draw_generic_graph(
    ...     energy_system=create_losslc_es(),
    ...     color_group={
    ...         'Coal Supply': '#666666',
    ...         'Coal Supply Line': '#666666',
    ...         'HKW': '#666666',
    ...         'HKW2': '#666666',
    ...         'Solar Thermal': '#b30000',
    ...         'Heat Storage': '#cc0033',
    ...         'District Heating': 'Red',
    ...         'District Heating Demand': 'Red',
    ...         'Power to Heat': '#b30000',
    ...         'Biogas plant': '#006600',
    ...         'Biogas': '#006600',
    ...         'BHKW': '#006600',
    ...         'Onshore Wind Power': '#99ccff',
    ...         'Offshore Wind Power': '#00ccff',
    ...         'Gas Station': '#336666',
    ...         'Gaspipeline': '#336666',
    ...         'GuD': '#336666',
    ...         'Solar Panel': '#ffe34d',
    ...         'Commercial Demand': '#ffe34d',
    ...         'Household Demand': '#ffe34d',
    ...         'Industrial Demand': '#ffe34d',
    ...         'Car charging Station': '#669999',
    ...         'Low Voltage Grid': '#ffcc00',
    ...         'Medium Voltage Grid': '#ffcc00',
    ...         'High Voltage Grid': '#ffcc00',
    ...         'High Voltage Transfer Grid': 'yellow',
    ...         'Low Voltage Transfer Grid': 'yellow',
    ...     },
    ...     node_size={
    ...         'High Voltage Transfer Grid': 150,
    ...         'Low Voltage Transfer Grid': 150,
    ...         'District Heating': 150,
    ...     },
    ... )

    >>> # commented out for doctesting. Uncomment to serve interactive drawing
    >>> # to http://127.0.0.1:8050/
    >>> # app.run_server(debug=False)

    .. image:: ../images/losslc_es.png
        :align: center
        :alt: Image showing the Loss less commitment grid es generic graph
    """
    # 2. Create a simulation time frame as a :class:`pandas.DatetimeIndex`:
    timeframe = pd.date_range('10/13/2030', periods=periods, freq='H')

    # 3. Parse csv files with the demand and renewables load data:
    d = os.path.join(example_dir, 'data', 'tsf', 'load_profiles')

    # solar:
    pv = pd.read_csv(os.path.join(d, 'Renewable_Energy.csv'),
                     index_col=0, sep=';')
    pv = pv['pv_load'].values.flatten()[0:periods]
    max_pv = np.max(pv)

    # wind onshore:
    w_on = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_on = w_on['won_load'].values.flatten()[0:periods]
    max_w_on = np.max(w_on)

    # wind offshore:
    w_off = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    w_off = w_off['woff_load'].values.flatten()[0:periods]
    max_w_off = np.max(w_off)

    # solar thermal:
    s_t = pd.read_csv(os.path.join(
        d, 'Renewable_Energy.csv'), index_col=0, sep=';')
    s_t = s_t['st_load'].values.flatten()[0:periods]
    max_s_t = np.max(s_t)

    # household demand
    h_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    h_d = h_d['household_demand'].values.flatten()[0:periods]
    max_h_d = np.max(h_d)

    # industrial demand
    i_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    i_d = i_d['industrial_demand'].values.flatten()[0:periods]
    max_i_d = np.max(i_d)

    # commercial demand
    c_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    c_d = c_d['commercial_demand'].values.flatten()[0:periods]
    max_c_d = np.max(c_d)

    # district heating demand
    dh_d = pd.read_csv(os.path.join(d, 'Loads.csv'), index_col=0, sep=';')
    dh_d = dh_d['heat_demand'].values.flatten()[0:periods]
    max_dh_d = np.max(dh_d)

    # car charging demand
    cc_d = pd.read_csv(os.path.join(d, 'Car_Charging.csv'),
                       index_col=0, sep=';')
    cc_d = cc_d['cc_demand'].values.flatten()[0:periods]
    max_cc_d = np.max(cc_d)

    # 4. Create the individual energy system components:
    global_constraints = {
        'name': 'default',
        'emissions': float('+inf'),
    }

    # -------------Low Voltage and heat ------------------

    solar_panel = components.Source(
        name='Solar Panel',
        outputs=('electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_pv)},
        flow_costs={'electricity': 60.85},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=pv, max=pv)},

    )

    biogas_supply = components.Source(
        name='Biogas plant',
        outputs=('fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=25987.87879)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
    )

    bhkw_generator = components.Transformer(
        name='BHKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.33, ('fuel', 'heat'): 0.52},
        # Minimum number of arguments required
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=25987.87879),
            'electricity': nts.MinMax(min=0, max=8576),
            'heat': nts.MinMax(min=0, max=13513.69697)},
        flow_costs={'fuel': 0, 'electricity': 124.4, 'heat': 31.1},
        flow_emissions={'fuel': 0, 'electricity': 0.1573, 'heat': 0.0732},
    )

    household_demand = components.Sink(
        name='Household Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_h_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=h_d, max=h_d)},
    )

    commercial_demand = components.Sink(
        name='Commercial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_c_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=c_d, max=c_d)},
    )

    heat_demand = components.Sink(
        name='District Heating Demand',
        inputs=('heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='hot Water',
        node_type='demand',
        flow_rates={'heat': nts.MinMax(min=0, max=max_dh_d)},
        flow_costs={'heat': 0},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=dh_d, max=dh_d)},
    )

    gas_supply_line = components.Bus(
        name='Gaspipeline',
        inputs=('Gas Station.fuel',),
        outputs=('GuD.fuel',),
        # Minimum number of arguments required
        sector='Power',
        carrier='gas',
        node_type='bus',
    )

    biogas_supply_line = components.Bus(
        name='Biogas',
        inputs=('Biogas plant.fuel',),
        outputs=('BHKW.fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='gas',
        node_type='bus',
    )

    low_electricity_line = components.Bus(
        name='Low Voltage Grid',
        inputs=(
            'BHKW.electricity',
            'Battery.electricity',
            'Solar Panel.electricity',
        ),
        outputs=(
            'Household Demand.electricity',
            'Commercial Demand.electricity',
            'Battery.electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    heat_line = components.Bus(
        name='District Heating',
        inputs=(
            'BHKW.heat',
            'Solar Thermal.heat',
            'Heat Storage.heat',
            'Power to Heat.heat',
            'HKW.heat',
        ),
        outputs=(
            'District Heating Demand.heat',
            'Heat Storage.heat',
        ),
        # Minimum number of arguments required
        sector='Heat',
        carrier='hot Water',
        node_type='bus',
    )

    # ----- -------Medium Voltage and Heat ------------------

    onshore_wind_power = components.Source(
        name='Onshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_on)},
        flow_costs={'electricity': 61.1},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_on, max=w_on)},
    )

    solar_thermal = components.Source(
        name='Solar Thermal',
        outputs=('heat',),
        # Minimum number of arguments required
        sector='Heat',
        carrier='Hot Water',
        node_type='Renewable',
        flow_rates={'heat': nts.MinMax(min=0, max=max_s_t)},
        flow_costs={'heat': 73},
        flow_emissions={'heat': 0},
        timeseries={'heat': nts.MinMax(min=s_t, max=s_t)},
    )

    industrial_demand = components.Sink(
        name='Industrial Demand',
        inputs=('electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_i_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=i_d, max=i_d)},
    )

    car_charging_station_demand = components.Sink(
        name='Car charging Station',
        inputs=('electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='demand',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_cc_d)},
        flow_costs={'electricity': 0},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=cc_d, max=cc_d)},
    )

    power_to_heat = components.Transformer(
        name='Power to Heat',
        inputs=('electricity',),
        outputs=('heat',),
        conversions={('electricity', 'heat'): 1.00},
        # Minimum number of arguments required
        carrier='Hot Water',
        node_type='transformer',
        flow_rates={
            'electricity': nts.MinMax(min=0, max=50000),
            'heat': nts.MinMax(min=0, max=50000),
        },
        flow_costs={'electricity': 0, 'heat': 0},
        flow_emissions={'electricity': 0, 'heat': 0},
    )

    medium_electricity_line = components.Bus(
        name='Medium Voltage Grid',
        inputs=('Onshore Wind Power.electricity',),
        outputs=(
            'Car charging Station.electricity',
            'Industrial Demand.electricity',
            'Power to Heat.electricity',
        ),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    low_medium_transformator = components.Connector(
        name='Low Voltage Transfer Grid',
        interfaces=(
            'Medium Voltage Grid',
            'Low Voltage Grid'),
        conversions={
            ('Medium Voltage Grid', 'Low Voltage Grid'): 1,
            ('Low Voltage Grid', 'Medium Voltage Grid'): 1,
        },
        node_type='connector',
    )

    # ----------------- High Voltage -------------------------

    offshore_wind_power = components.Source(
        name='Offshore Wind Power',
        outputs=('electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='Electricity',
        node_type='Renewable',
        flow_rates={'electricity': nts.MinMax(min=0, max=max_w_off)},
        flow_costs={'electricity': 106.4},
        flow_emissions={'electricity': 0},
        timeseries={'electricity': nts.MinMax(min=w_off, max=w_off)},
    )

    coal_supply = components.Source(
        name='Coal Supply',
        outputs=('fuel',),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=102123.3)},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
    )

    gas_supply = components.Source(
        name='Gas Station',
        outputs=('fuel',),
        # Minimum number of arguments required
        sector='Power',
        carrier='Gas',
        node_type='source',
        flow_rates={'fuel': nts.MinMax(min=0, max=float('+inf'))},
        flow_costs={'fuel': 0},
        flow_emissions={'fuel': 0},
    )

    hkw_generator = components.Transformer(
        name='HKW',
        inputs=('fuel',),
        outputs=('electricity', 'heat'),
        conversions={('fuel', 'electricity'): 0.24, ('fuel', 'heat'): 0.6},
        # Minimum number of arguments required
        sector='Coupled',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=24509.6),
            'heat': nts.MinMax(min=0, max=61273.96)},
        flow_costs={'fuel': 0, 'electricity': 80.65, 'heat': 20.1625},
        flow_emissions={'fuel': 0, 'electricity': 0.5136, 'heat': 0.293},
    )

    hkw_generator_2 = components.Transformer(
        name='HKW2',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.43},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='connector',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=102123.3),
            'electricity': nts.MinMax(min=0, max=43913)},
        flow_costs={'fuel': 0, 'electricity': 80.65},
        flow_emissions={'fuel': 0, 'electricity': 0.5136},
    )

    gud_generator = components.Transformer(
        name='GuD',
        inputs=('fuel',),
        outputs=('electricity',),
        conversions={('fuel', 'electricity'): 0.59},
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='transformer',
        flow_rates={
            'fuel': nts.MinMax(min=0, max=45325.42373),
            'electricity': nts.MinMax(min=0, max=26742)},
        flow_costs={'fuel': 0, 'electricity': 88.7},
        flow_emissions={'fuel': 0, 'electricity': 0.3366},
    )

    coal_supply_line = components.Bus(
        name='Coal Supply Line',
        inputs=('Coal Supply.fuel',),
        outputs=('HKW.fuel', 'HKW2.fuel'),
        # Minimum number of arguments required
        sector='Coupled',
        carrier='Coal',
        node_type='bus',
    )

    high_electricity_line = components.Bus(
        name='High Voltage Grid',
        inputs=(
            'Offshore Wind Power.electricity',
            'GuD.electricity',
            'HKW.electricity',
            'HKW2.electricity',
        ),
        outputs=('Power Sink.electricity',),
        # Minimum number of arguments required
        sector='Power',
        carrier='electricity',
        node_type='bus',
    )

    high_medium_transformator = components.Connector(
        name='High Voltage Transfer Grid',
        interfaces=(
            'Medium Voltage Grid',
            'High Voltage Grid',
        ),
        conversions={
            ('Medium Voltage Grid', 'High Voltage Grid'): 1,
            ('High Voltage Grid', 'Medium Voltage Grid'): 1,
        },
        node_type='connector',
    )

    # 4. Create the actual energy system:
    es = energy_system.AbstractEnergySystem(
        uid="LossLC",
        busses=(
            gas_supply_line,
            low_electricity_line,
            heat_line,
            medium_electricity_line,
            high_electricity_line,
            coal_supply_line,
            biogas_supply_line,
        ),
        sinks=(
            household_demand,
            commercial_demand,
            heat_demand,
            industrial_demand,
            car_charging_station_demand,
        ),
        sources=(
            solar_panel,
            gas_supply,
            onshore_wind_power,
            offshore_wind_power,
            coal_supply,
            solar_thermal,
            biogas_supply,
        ),
        transformers=(
            bhkw_generator,
            power_to_heat,
            gud_generator,
            hkw_generator,
            hkw_generator_2,
        ),
        connectors=(
            low_medium_transformator,
            high_medium_transformator,
        ),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return es
