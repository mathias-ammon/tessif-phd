# tessif/examples/data/omf/py_hard.py
"""
:mod:`~tessif.examples.data.omf.py_hard` is a :mod:`tessif` module for giving
examples on how to create an :class:`oemof energy system
<oemof.core.energy_system.EnergySystem>`.

It collects minimum working examples, meaningful working
examples and full fledged use case wrappers for common scenarios.
"""

# 1.) Handle imports:
# standard library
import pathlib
import os

# third party
from oemof import solph
import pandas as pd
import numpy as np

# local imports
import tessif.frused.namedtuples as nts
from tessif.frused.paths import write_dir
from tessif.frused.paths import example_dir
import tessif.simulate as optimize


def create_mwe(directory=None, filename=None):
    r"""
    Create a minimum working example using :any:`oemof`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_mwe.directory` as
    :paramref:`~create_mwe.filename`

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~oemof.core.energy_system.EnergySystem.dump`.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~create_mwe.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/omf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``mwe.oemof``.


    Return
    ------
    optimized_es : :class:`~oemof.core.energy_system.EnergySystem`
        Energy system carrying the optimization results.


    Examples
    --------
    Using :func:`create_mwe` to quickly access an optimized oemof energy system
    to use for doctesting, or trying out this frameworks utilities.
    (For a step by step explanation see :ref:`Models_Oemof_Examples_Mwe`):

    >>> import tessif.examples.data.omf.py_hard as omf_py
    >>> optimized_es = omf_py.create_mwe()
    """
    # 2.) Create a simulation time frame of 2 timesteps of hourly resolution
    simulation_time = pd.date_range('7/13/1990', periods=2, freq='H')

    # 3.) Create an energy system object:
    es = solph.EnergySystem(timeindex=simulation_time)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using namedtuples to store location (latt/long) region, carrier and
    # sector categorization as all oemof simulations do in this framework)

    # 4.1) Power Line
    power_line = solph.Bus(
        label=nts.Uid('Power Line', 53, 10, 'Germany',
                      'Power', 'Electricity', 'bus'))

    # 4.2) Demand needing 10 energy units
    demand = solph.Sink(
        label=nts.Uid('Demand', 53, 10, 'Germany',
                      'Power', 'Electricity', 'sink'),
        inputs={power_line: solph.Flow(nominal_value=10, fix=[1, 1])})

    # 4.3) Renewable source producing 8 and 2 energy units with a cost of 9
    renewable = solph.Source(
        label=nts.Uid('Renewable', 53, 10, 'Germany',
                      'Power', 'Electricity', 'source'),
        outputs={power_line: solph.Flow(
            nominal_value=10, fix=[0.8, 0.2], variable_costs=9)})

    # 4.4) Chemically Bound Energy Transport
    cbet = solph.Bus(
        label=nts.Uid('CBET', 53, 10, 'Germany',
                      'Power', 'Electricity', 'bus'))

    # 4.5) Chemically Bound Energy Source
    cbe = solph.Source(
        label=nts.Uid('CBE', 53, 10, 'Germany',
                      'Power', 'Electricity', 'source'),
        outputs={cbet: solph.Flow()})

    # 4.6) Conventional Engergy Transformer
    #      producing up to 10 energy units for a cost of 10
    conventional = solph.Transformer(
        label=nts.Uid('Transformer', 53, 10, 'Germany',
                      'Power', 'Electricity', 'transformer'),
        inputs={cbet: solph.Flow()},
        outputs={power_line: solph.Flow(nominal_value=10, variable_costs=10)},
        conversion_factors={power_line: 0.6})

    # 5.) Adding nodes to energy system
    es.add(power_line, demand, renewable, cbet, cbe, conventional)

    # 6.) Create an energy system model
    esm = solph.Model(es)

    # 7.) Optimize model:
    esm.solve(solver='glpk')

    # 8.) Pump results into the energy system object to utilize its dump
    #     functionality for saving the data
    es.results['main'] = solph.processing.results(esm)
    es.results['meta'] = solph.processing.meta_results(esm)

    # 9.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'omf')
    else:
        d = directory

    # create output directory if necessary
    pathlib.Path(os.path.abspath(d)).mkdir(
        parents=True, exist_ok=True)

    # Set default filename if necessary, using the isoformat
    if not filename:
        f = 'mwe.oemof'
    else:
        f = filename

    es.dump(dpath=d, filename=f)

    # 10.) Return the mwe oemof energy system
    return es


def create_star(directory=None, filename=None):
    r"""
    Create a star like energy system using the :any:`oemof` library.

    Creates a simple energy system simulation to potentially store it on disc
    in :paramref:`~create_mwe.directory` as :paramref:`~create_mwe.filename`.

    Usefull for testing behaviour of nodes with more than 1 inflow **and**
    outflow.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~oemof.core.energy_system.EnergySystem.dump`.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~create_mwe.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/omf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``star.oemof``.

    Return
    ------
    optimized_es : :class:`~oemof.core.energy_system.EnergySystem`
        Energy system carrying the optimization results.

    Examples
    --------
    Using :func:`create_star` to quickly access an optimized oemof energy
    system to use for doctesting, or trying out this frameworks utilities.
    (For a step by step explanation see :ref:`Models_Oemof_Examples_Mwe`):

    >>> import tessif.examples.data.omf.py_hard as omf_py
    >>> optimized_es = omf_py.create_star()
    """
    # 2.) Create a simulation time frame of 2 timesteps of hourly resolution
    simulation_time = pd.date_range('7/13/1990', periods=2, freq='H')

    # 3.) Create an energy system object:
    es = solph.EnergySystem(timeindex=simulation_time)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using namedtuples to store location (latt/long) region, carrier and
    # sector categorization as all oemof simulations do in this framework)

    # 4.1) Power Line
    power_line = solph.Bus(
        label=nts.Uid('Power Line', 53, 10, 'Germany',
                      'Power', 'Electricity', 'bus'))

    # 4.2) Demand needing 13 energy units
    demand13 = solph.Sink(
        label=nts.Uid('Demand13', 53, 10, 'Germany',
                      'Power', 'Electricity', 'sink'),
        inputs={power_line: solph.Flow(
            nominal_value=10, fix=[1, 1], emissions=2)})

    # 4.3) Demand needing 7 energy units
    demand7 = solph.Sink(
        label=nts.Uid('Demand7', 53, 10, 'Germany',
                      'Power', 'Electricity', 'sink'),
        inputs={power_line: solph.Flow(
            nominal_value=7, fix=[1, 1], emissions=1)})

    # 4.2) Demand needing 90 energy units
    demand90 = solph.Sink(
        label=nts.Uid('Demand90', 53, 10, 'Germany', 'Power', 'Electricity',
                      'sink'),
        inputs={power_line: solph.Flow(
            nominal_value=90, fix=[1, 1], emissions=3)})

    # 3.4) Endless energy source
    ulp = solph.Source(
        label=nts.Uid('Unlimited Power', 53, 10,
                      'Germany', 'Power', 'Electricity', 'source'),
        outputs={power_line: solph.Flow(variable_costs=2, emissions=1)})

    # 3.4) Depletive energy source
    lp = solph.Source(
        label=nts.Uid('Limited Power', 53, 10,
                      'Germany', 'Power', 'Electricity', 'source'),
        outputs={power_line: solph.Flow(
            nominal_value=20, fix=[1, 0.5], variable_costs=1, emissions=0.5)})

    # 5.) Adding nodes to energy system
    es.add(power_line, demand13, demand7, demand90, ulp, lp)

    # # 6.) Create an energy system model
    # esm = solph.Model(es)

    # # 7.) Optimize model:
    # esm.solve(solver='glpk')

    # # 8.) Pump results into the energy system object to utilize its dump
    # #     functionality for saving the data
    # es.results['main'] = solph.processing.results(esm)
    # es.results['meta'] = solph.processing.meta_results(esm)

    es = optimize.omf_from_es(es)
    # 9.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'omf')
    else:
        d = directory

    # create output directory if necessary
    pathlib.Path(os.path.abspath(d)).mkdir(
        parents=True, exist_ok=True)

    # Set default filename if necessary, using the isoformat
    if not filename:
        f = 'star.oemof'
    else:
        f = filename

    es.dump(dpath=d, filename=f)

    # 10.) Return the mwe oemof energy system
    return es


def emission_objective(directory=None, filename=None):
    r"""
    Create a small working example using :any:`oemof`. Optimizing it for
    costs and keeping the total emissions below an emission objective.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~emission_objective.directory` as
    :paramref:`~emission_objective.filename`

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~oemof.core.energy_system.EnergySystem.dump`.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~emission_objective.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/omf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``mwe.oemof``.


    Return
    ------
    optimized_es : :class:`~oemof.core.energy_system.EnergySystem`
        Energy system carrying the optimization results.


    Examples
    --------
    Using :func:`emission_objective` to quickly access an optimized oemof
    energy system to use for doctesting, or trying out this frameworks
    utilities.

    (For a step by step explanation on how to create an oemof minimum working
    example see :ref:`Models_Oemof_Examples_Mwe`):

    >>> import tessif.examples.data.omf.py_hard as omf_py
    >>> optimized_es = omf_py.emission_objective()

    Conduct the post processing:

    >>> import tessif.transform.es2mapping.omf as post_process_oemof
    >>> global_resultier = post_process_oemof.IntegratedGlobalResultier(
    ...     optimized_es)
    >>> load_resultier = post_process_oemof.LoadResultier(optimized_es)

    And access some post processed results:

    >>> import pprint
    >>> pprint.pprint(global_resultier.global_results)
    {'capex (ppcd)': 0.0,
     'costs (sim)': 110.0,
     'emissions (sim)': 30.0,
     'opex (ppcd)': 110.0}

    >>> for load_results in load_resultier.node_load.values():
    ...     print(load_results)
    Power Line           Renewable  Transformer  Demand
    1990-07-13 00:00:00       -0.0        -10.0    10.0
    1990-07-13 01:00:00       -0.0        -10.0    10.0
    1990-07-13 02:00:00       -0.0        -10.0    10.0
    1990-07-13 03:00:00      -10.0         -0.0    10.0
    Demand               Power Line
    1990-07-13 00:00:00       -10.0
    1990-07-13 01:00:00       -10.0
    1990-07-13 02:00:00       -10.0
    1990-07-13 03:00:00       -10.0
    Renewable            Power Line
    1990-07-13 00:00:00         0.0
    1990-07-13 01:00:00         0.0
    1990-07-13 02:00:00         0.0
    1990-07-13 03:00:00        10.0
    CBET                       CBE  Transformer
    1990-07-13 00:00:00 -23.809524    23.809524
    1990-07-13 01:00:00 -23.809524    23.809524
    1990-07-13 02:00:00 -23.809524    23.809524
    1990-07-13 03:00:00  -0.000000     0.000000
    CBE                       CBET
    1990-07-13 00:00:00  23.809524
    1990-07-13 01:00:00  23.809524
    1990-07-13 02:00:00  23.809524
    1990-07-13 03:00:00   0.000000
    Transformer               CBET  Power Line
    1990-07-13 00:00:00 -23.809524        10.0
    1990-07-13 01:00:00 -23.809524        10.0
    1990-07-13 02:00:00 -23.809524        10.0
    1990-07-13 03:00:00  -0.000000         0.0

    See user's guide on :ref:`Secondary_Objectives` for more on this example.
    """
    # 2.) Create a simulation time frame of four timesteps of hourly resolution
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3.) Create an energy system object:
    es = solph.EnergySystem(timeindex=timeframe)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using namedtuples to store location (latt/long) region, carrier and
    # sector categorization as all oemof simulations do in this framework)

    # 4.1) Power Line
    power_line = solph.Bus(
        label=nts.Uid('Power Line', 53, 10, 'Germany',
                      'Power', 'Electricity', 'Bus', 'Powerline'))

    # 4.2) Demand needing 10 energy units per time step
    demand = solph.Sink(
        label=nts.Uid('Demand', 53, 10, 'Germany', 'Power', 'Electricity',
                      'Sink', 'Demand'),
        inputs={power_line: solph.Flow(nominal_value=10, fix=[1, 1, 1, 1])})

    # 4.3) Renewable power is more expensive but has no emissions allocated
    renewable = solph.Source(
        label=nts.Uid('Renewable', 53, 10, 'Germany',
                      'Power', 'Electricity', 'source', 'Renewable'),
        outputs={power_line: solph.Flow(
            variable_costs=5)})

    # 4.4) Chemically Bound Energy Transport
    cbet = solph.Bus(
        label=nts.Uid('CBET', 53, 10, 'Germany', 'Power', 'Electricity',
                      'Bus', 'Pipeline'))

    # 3.4) Chemically Bound Energy Source
    cbe = solph.Source(
        label=nts.Uid('CBE', 53, 10, 'Germany', 'Power',
                      'Electricity', 'Source', 'Gas'),
        outputs={cbet: solph.Flow()})

    # 4.5) Conventional power supply is cheaper but has emissions allocated
    conventional = solph.Transformer(
        label=nts.Uid('Transformer', 53, 10, 'Germany', 'Power',
                      'Electricity', 'Transformer', 'Gas Power Plant'),
        inputs={cbet: solph.Flow()},
        outputs={power_line: solph.Flow(variable_costs=2, emissions=1)},
        conversion_factors={power_line: 0.42})

    # 5.) Adding nodes to energy system
    es.add(power_line, demand, renewable, cbet, cbe, conventional)

    # 6.) Create an energy system model
    esm = solph.Model(es)

    # 7.) Add an emisions limit of 30 units in total
    esm = solph.constraints.generic_integral_limit(
        om=esm, keyword='emissions', limit=30)

    # 8.) Optimize model:
    esm.solve(solver='glpk')

    # 9.) Pump results into the energy system object to utilize its dump
    #     functionality for saving the data
    es.results['main'] = solph.processing.results(esm)
    es.results['meta'] = solph.processing.meta_results(esm)
    es.results['global'] = {
        'emissions': esm.integral_limit_emissions(),
        'costs': es.results['meta']['objective'],
    }

    # 10.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'omf')
    else:
        d = directory

    # create output directory if necessary
    pathlib.Path(os.path.abspath(d)).mkdir(
        parents=True, exist_ok=True)

    # Set default filename if necessary, using the isoformat
    if not filename:
        f = 'emission_objective.oemof'
    else:
        f = filename

    es.dump(dpath=d, filename=f)

    # 10.) Return the mwe oemof energy system
    return es


def undeclared_emission_objective():
    r"""
    Create a minimum working example using :any:`oemof`. Optimizing it for
    costs and keeping the total emissions below an emission objective.

    This energy system however however does not store the emission results
    back into the actual energy system (compared to
    :meth:`emission_objective`).

    Designed to test out the automated post processing of global constraints
    using :func:`tessif.simualte.omf_from_es`.

    Return
    ------
    unoptimized_es : :class:`~oemof.core.energy_system.EnergySystem`
        Energy system on which no simulation/optimization has been performed


    Examples
    --------
    Using :func:`emission_objective` to quickly access an **unoptimized** oemof
    energy system to use for doctesting, or trying out this frameworks
    utilities.

    (For a step by step explanation on how to create an oemof minimum working
    example see :ref:`Models_Oemof_Examples_Mwe`):

    >>> import tessif.examples.data.omf.py_hard as omf_py
    >>> unoptimized_es = omf_py.undeclared_emission_objective()
    >>> print(hasattr(unoptimized_es, 'global_constraints'))
    False

    Conduct the simulation:

    >>> import tessif.simulate as simulate
    >>> optimized_es = simulate.omf_from_es(unoptimized_es)

    And the post processing:

    >>> import tessif.transform.es2mapping.omf as post_process_oemof
    >>> global_resultier = post_process_oemof.IntegratedGlobalResultier(
    ...     optimized_es)

    >>> import pprint
    >>> pprint.pprint(global_resultier.global_results)
    {'capex (ppcd)': 0.0,
     'costs (sim)': 80.0,
     'emissions (sim)': 40.0,
     'opex (ppcd)': 80.0}

    Note how their are no emisison results, since the emission objective was
    not declared for tessif to understand it.



    """
    # 2.) Create a simulation time frame of four timesteps of hourly resolution
    timeframe = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3.) Create an energy system object:
    es = solph.EnergySystem(timeindex=timeframe)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using namedtuples to store location (latt/long) region, carrier and
    # sector categorization as all oemof simulations do in this framework)

    # 4.1) Power Line
    power_line = solph.Bus(
        label=nts.Uid('Power Line', 53, 10, 'Germany',
                      'Power', 'Electricity', 'Bus', 'Powerline'))

    # 4.2) Demand needing 10 energy units per time step
    demand = solph.Sink(
        label=nts.Uid('Demand', 53, 10, 'Germany', 'Power', 'Electricity',
                      'Sink', 'Demand'),
        inputs={power_line: solph.Flow(nominal_value=10, fix=[1, 1, 1, 1])})

    # 4.3) Renewable power is more expensive but has no emissions allocated
    renewable = solph.Source(
        label=nts.Uid('Renewable', 53, 10, 'Germany',
                      'Power', 'Electricity', 'source', 'Renewable'),
        outputs={power_line: solph.Flow(
            variable_costs=5)})

    # 4.4) Chemically Bound Energy Transport
    cbet = solph.Bus(
        label=nts.Uid('CBET', 53, 10, 'Germany', 'Power', 'Electricity',
                      'Bus', 'Pipeline'))

    # 3.4) Chemically Bound Energy Source
    cbe = solph.Source(
        label=nts.Uid('CBE', 53, 10, 'Germany', 'Power',
                      'Electricity', 'Source', 'Gas'),
        outputs={cbet: solph.Flow()})

    # 4.5) Conventional power supply is cheaper but has emissions allocated
    conventional = solph.Transformer(
        label=nts.Uid('Transformer', 53, 10, 'Germany', 'Power',
                      'Electricity', 'Transformer', 'Gas Power Plant'),
        inputs={cbet: solph.Flow()},
        outputs={power_line: solph.Flow(variable_costs=2, emissions=1)},
        conversion_factors={power_line: 0.42})

    # 5.) Adding nodes to energy system
    es.add(power_line, demand, renewable, cbet, cbe, conventional)

    # 10.) Return the unoptimized oemof energy system
    return es


def create_commitment_scenario(periods=3, directory=None, filename=None):
    """
    Create a model of a generic component based energy system
    using :any:`oemof`.

    Parameters
    ----------
    periods : int, default=3
        Number of time steps of the evaluated timeframe
        (one time step is one hour)
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~oemof.core.energy_system.EnergySystem.dump`.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~create_commitment_scenario.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/omf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``commitment_scenario.oemof``.

    Return
    ------
    optimized_es : :class:`~oemof.core.energy_system.EnergySystem`
        Energy system carrying the optimization results.


    Examples
    --------
    Using :func:`create_commitment_scenario` to quickly access an optimized oemof energy system
    to use for doctesting, or trying out this frameworks utilities.
    (For a step by step explanation see :ref:`Models_Oemof_Examples_Mwe`):

    >>> import tessif.examples.data.omf.py_hard as omf_py
    >>> optimized_es = omf_py.create_commitment_scenario()
    """

    # Create a simulation time frame
    timeframe = pd.date_range(
        '1/1/2019', periods=periods, freq='H')  # month/day/year

    # Create an energy system object
    my_energysystem = solph.EnergySystem(timeindex=timeframe)

    # create busses and add them to the energy system
    lignite_bus = solph.Bus('lignite')
    hard_coal_bus = solph.Bus(label='hard_coal')
    biogas_bus = solph.Bus(label='biogas')
    gas_bus = solph.Bus(label='gas')
    electricity_bus = solph.Bus(label='electricity')
    heat_bus = solph.Bus(label='hot_water')
    my_energysystem.add(lignite_bus, hard_coal_bus,
                        biogas_bus, gas_bus, electricity_bus, heat_bus)

    # add prerequisites for sinks
    csv_data = pd.read_csv(os.path.join(example_dir, 'data', 'tsf', 'load_profiles',
                                        'component_scenario_profiles.csv'), index_col=0, sep=';')

    # electricity demand:
    el_demand = csv_data['el_demand'].values.flatten()[0:periods]
    max_el = np.max(el_demand)
    for i in range(0, periods):
        el_demand[i] = el_demand[i]/max_el

    # heat demand:
    th_demand = csv_data['th_demand'].values.flatten()[0:periods]
    max_th = np.max(th_demand)
    for i in range(0, periods):
        th_demand[i] = th_demand[i]/max_th

    # create sinks and add them to the energy system
    electricity_demand = solph.Sink(label='electricity_demand', inputs={electricity_bus: solph.Flow(
        fix=el_demand, nominal_value=max_el)})
    heat_demand = solph.Sink(label='thermal_demand', inputs={heat_bus: solph.Flow(
        fix=th_demand, nominal_value=max_th)})
    my_energysystem.add(electricity_demand, heat_demand)

    # create fossil sources
    gas_source = solph.Source(
        label='gas_supply',
        outputs={gas_bus: solph.Flow()})
    lignite_source = solph.Source(
        label='lignite_supply',
        outputs={lignite_bus: solph.Flow()})
    hard_coal_source = solph.Source(
        label='hard_coal_supply',
        outputs={hard_coal_bus: solph.Flow()})
    biogas_source = solph.Source(
        label='biogas_supply',
        outputs={biogas_bus: solph.Flow()})

    # add prerequisite for fluctuating sources

    # solar:
    series_pv = csv_data['pv'].values.flatten()[0:periods]
    # wind onshore:
    series_wind_onshore = csv_data['wind_on'].values.flatten()[0:periods]
    # wind offshore:
    series_wind_offshore = csv_data['wind_off'].values.flatten()[0:periods]

    # create fluctuating sources and add all sources to energy system
    wind_off_source = solph.Source(label='wind_off', outputs={electricity_bus: solph.Flow(
        max=series_wind_offshore, nominal_value=150, variable_costs=105, emission_factor=0.02)})

    wind_on_source = solph.Source(label='wind_on', outputs={electricity_bus: solph.Flow(
        max=series_wind_onshore, nominal_value=1100, variable_costs=60, emission_factor=0.02)})

    pv_source = solph.Source(label='pv', outputs={electricity_bus: solph.Flow(
        max=series_pv, nominal_value=1100, variable_costs=80, emission_factor=0.05)})

    my_energysystem.add(gas_source, lignite_source, biogas_source, hard_coal_source,
                        wind_on_source, wind_off_source, pv_source)

    # create transformers
    gas_pp = solph.Transformer(
        label="pp_gas",
        inputs={gas_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(
            nominal_value=600, variable_costs=90, emission_factor=0.35)},
        conversion_factors={electricity_bus: 0.6})

    lignite_pp = solph.Transformer(
        label="pp_lignite",
        inputs={lignite_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(
            nominal_value=500, variable_costs=65, emission_factor=1)},
        conversion_factors={electricity_bus: 0.4})

    hard_coal_pp = solph.Transformer(
        label="pp_hard_coal",
        inputs={hard_coal_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(
            nominal_value=500, variable_costs=80, emission_factor=0.8)},
        conversion_factors={electricity_bus: 0.43})

    hard_coal_chp = solph.Transformer(
        label='chp_hard_coal',
        inputs={hard_coal_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(nominal_value=300, variable_costs=80, emission_factor=0.8),
                 heat_bus: solph.Flow(nominal_value=300, variable_costs=6, emission_factor=0.06)},
        conversion_factors={electricity_bus: 0.4, heat_bus: 0.4})

    biogas_chp = solph.Transformer(
        label='chp_biogas',
        inputs={biogas_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(nominal_value=200, variable_costs=150, emission_factor=0.25),
                 heat_bus: solph.Flow(nominal_value=250, variable_costs=11.25, emission_factor=0.01875)},
        conversion_factors={electricity_bus: 0.4, heat_bus: 0.5})

    heat_plant = solph.Transformer(
        label="heat_plant",
        inputs={gas_bus: solph.Flow()},
        outputs={heat_bus: solph.Flow(
            nominal_value=450, variable_costs=35, emission_factor=0.23)},
        conversion_factors={heat_bus: 0.9})

    p2h = solph.Transformer(
        label="p2h",
        inputs={electricity_bus: solph.Flow()},
        outputs={heat_bus: solph.Flow(
            nominal_value=100, variable_costs=20, emission_factor=0.0007)},
        conversion_factors={heat_bus: 0.99})

    # create storages
    battery = solph.GenericStorage(
        label='battery',
        inputs={electricity_bus: solph.Flow(
            nominal_value=33, variable_costs=0)},
        outputs={electricity_bus: solph.Flow(
            nominal_value=33, variable_costs=400, emission_factor=0.06)},
        loss_rate=0.005, nominal_storage_capacity=100,
        initial_storage_level=0, balanced=False,
        inflow_conversion_factor=0.95, outflow_conversion_factor=0.95)

    heat_storage = solph.GenericStorage(
        label='heat_storage',
        inputs={heat_bus: solph.Flow(nominal_value=10, variable_costs=0)},
        outputs={heat_bus: solph.Flow(nominal_value=10, variable_costs=20)},
        loss_rate=0.005, nominal_storage_capacity=50,
        initial_storage_level=0, balanced=False,
        inflow_conversion_factor=0.95, outflow_conversion_factor=0.95)

    # add transformers and storages to energy system
    my_energysystem.add(lignite_pp, hard_coal_pp, gas_pp, heat_plant, p2h,
                        hard_coal_chp, biogas_chp,
                        battery, heat_storage)

    # Create an energy system model
    esm = solph.Model(my_energysystem)

    # create emission constraint so oemof aknowledges the emissions and returns them
    esm = solph.constraints.generic_integral_limit(
        om=esm, keyword='emission_factor', limit=float('+inf'))

    # Optimize model:
    esm.solve(solver='cbc')

    # Pump results into the energy system object to utilize its dump
    # functionality for saving the data
    my_energysystem.results['main'] = solph.processing.results(esm)
    my_energysystem.results['meta'] = solph.processing.meta_results(esm)
    my_energysystem.results['global'] = {
        'emissions': esm.integral_limit_emission_factor(),
        'costs': my_energysystem.results['meta']['objective'],
    }

    # Store result pumped energy system:
    if not filename:
        filename = 'commitment_es.oemof'

    my_energysystem.dump(dpath=directory, filename=filename)

    return my_energysystem


def create_expansion_scenario(periods=3, directory=None, filename=None):
    """
    Create a model of a generic component based energy system
    using :any:`oemof`. Basically the same energy system as :func:`create_commitment_scenario`
    but with expansions and emission constraint.

    Parameters
    ----------
    periods : int, default=3
        Number of time steps of the evaluated timeframe
        (one time step is one hour)
    directory : str, default=None
        String representing of the path the created energy system is dumped to.
        Passed to :meth:`~oemof.core.energy_system.EnergySystem.dump`.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~create_expansion_scenario.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/omf
        will be the chosen directory.

    filename : str, default=None
        :func:`~pickle.dump` the energy system using this name.

        If set to ``None`` (default) filename will be ``expansion_scenario.oemof``.

    Return
    ------
    optimized_es : :class:`~oemof.core.energy_system.EnergySystem`
        Energy system carrying the optimization results.


    Examples
    --------
    Using :func:`create_expansion_scenario` to quickly access an optimized oemof energy system
    to use for doctesting, or trying out this frameworks utilities.
    (For a step by step explanation see :ref:`Models_Oemof_Examples_Mwe`):

    >>> import tessif.examples.data.omf.py_hard as omf_py
    >>> optimized_es = omf_py.create_expansion_scenario()
    """

    # Create a simulation time frame
    timeframe = pd.date_range(
        '1/1/2019', periods=periods, freq='H')  # month/day/year

    # Create an energy system object
    my_energysystem = solph.EnergySystem(timeindex=timeframe)

    # create busses and add them to the energy system
    lignite_bus = solph.Bus(label='lignite')
    hard_coal_bus = solph.Bus(label='hard_coal')
    biogas_bus = solph.Bus(label='biogas')
    gas_bus = solph.Bus(label='gas')
    electricity_bus = solph.Bus(label='electricity')
    heat_bus = solph.Bus(label='hot_water')
    my_energysystem.add(lignite_bus, hard_coal_bus,
                        biogas_bus, gas_bus, electricity_bus, heat_bus)

    # add prerequisites for sinks
    csv_data = pd.read_csv(os.path.join(example_dir, 'data', 'tsf', 'load_profiles',
                                        'component_scenario_profiles.csv'), index_col=0, sep=';')

    # electricity demand:
    el_demand = csv_data['el_demand'].values.flatten()[0:periods]
    max_el = np.max(el_demand)
    for i in range(0, periods):
        el_demand[i] = el_demand[i]/max_el

    # heat demand:
    th_demand = csv_data['th_demand'].values.flatten()[0:periods]
    max_th = np.max(th_demand)
    for i in range(0, periods):
        th_demand[i] = th_demand[i]/max_th

    # create sinks and add them to the energy system
    electricity_demand = solph.Sink(label='electricity_demand', inputs={electricity_bus: solph.Flow(
        fix=el_demand, nominal_value=max_el)})
    heat_demand = solph.Sink(label='thermal_demand', inputs={heat_bus: solph.Flow(
        fix=th_demand, nominal_value=max_th)})
    my_energysystem.add(electricity_demand, heat_demand)

    # create fossil sources
    gas_source = solph.Source(
        label='gas_supply',
        outputs={gas_bus: solph.Flow()})
    lignite_source = solph.Source(
        label='lignite_supply',
        outputs={lignite_bus: solph.Flow()})
    hard_coal_source = solph.Source(
        label='hard_coal_supply',
        outputs={hard_coal_bus: solph.Flow()})
    biogas_source = solph.Source(
        label='biogas_supply',
        outputs={biogas_bus: solph.Flow()})

    # create fluctuating sources and add all sources to energy system

    # solar:
    series_pv = csv_data['pv'].values.flatten()[0:periods]

    pv_source = solph.Source(label='pv', outputs={electricity_bus: solph.Flow(
        max=series_pv, variable_costs=80, emission_factor=0.05,
        investment=solph.Investment(maximum=None, minimum=0, ep_costs=1000000, existing=1100))})

    # wind onshore:
    series_wind_onshore = csv_data['wind_on'].values.flatten()[0:periods]

    wind_on_source = solph.Source(label='wind_on', outputs={electricity_bus: solph.Flow(
        max=series_wind_onshore, variable_costs=60, emission_factor=0.02,
        investment=solph.Investment(maximum=None, minimum=0, ep_costs=1750000, existing=1100))})

    # wind offshore:
    series_wind_offshore = csv_data['wind_off'].values.flatten()[0:periods]

    wind_off_source = solph.Source(label='wind_off', outputs={electricity_bus: solph.Flow(
        max=series_wind_offshore, variable_costs=105, emission_factor=0.02,
        investment=solph.Investment(maximum=None, minimum=0, ep_costs=3900000, existing=150))})

    # add all sources to energy system
    my_energysystem.add(gas_source, lignite_source, biogas_source, hard_coal_source,
                        wind_on_source, wind_off_source, pv_source)

    # create transformers
    gas_pp = solph.Transformer(
        label="pp_gas",
        inputs={gas_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(variable_costs=90, emission_factor=0.35,
                                             investment=solph.Investment(
                                                 maximum=None, minimum=0, ep_costs=950000, existing=600))},
        conversion_factors={electricity_bus: 0.6})

    lignite_pp = solph.Transformer(
        label="pp_lignite",
        inputs={lignite_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(variable_costs=65, emission_factor=1,
                                             investment=solph.Investment(
                                                 maximum=None, minimum=0, ep_costs=1900000, existing=500))},
        conversion_factors={electricity_bus: 0.4})

    hard_coal_pp = solph.Transformer(
        label="pp_hard_coal",
        inputs={hard_coal_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(variable_costs=80, emission_factor=0.8,
                                             investment=solph.Investment(
                                                 maximum=None, minimum=0, ep_costs=1650000, existing=500))},
        conversion_factors={electricity_bus: 0.43})

    hard_coal_chp = solph.Transformer(
        label='chp_hard_coal',
        inputs={hard_coal_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(variable_costs=80, emission_factor=0.8,
                                             investment=solph.Investment(
                                                 maximum=None, minimum=0, ep_costs=1750000, existing=300)),
                 heat_bus: solph.Flow(variable_costs=6, emission_factor=0.06,
                                      investment=solph.Investment(
                                          maximum=None, minimum=0, ep_costs=131250, existing=300)
                                      )},
        conversion_factors={electricity_bus: 0.4, heat_bus: 0.4})

    biogas_chp = solph.Transformer(
        label='chp_biogas',
        inputs={biogas_bus: solph.Flow()},
        outputs={electricity_bus: solph.Flow(variable_costs=150, emission_factor=0.25,
                                             investment=solph.Investment(
                                                 maximum=None, minimum=0, ep_costs=3500000, existing=200)
                                             ),
                 heat_bus: solph.Flow(variable_costs=11.25, emission_factor=0.01875,
                                      investment=solph.Investment(
                                          maximum=None, minimum=0, ep_costs=262500, existing=250)
                                      )},
        conversion_factors={electricity_bus: 0.4, heat_bus: 0.5})

    heat_plant = solph.Transformer(
        label="heat_plant",
        inputs={gas_bus: solph.Flow()},
        outputs={heat_bus: solph.Flow(variable_costs=35, emission_factor=0.23,
                                      investment=solph.Investment(
                                          maximum=None, minimum=0, ep_costs=390000, existing=450))},
        conversion_factors={heat_bus: 0.9})

    p2h = solph.Transformer(
        label="p2h",
        inputs={electricity_bus: solph.Flow()},
        outputs={heat_bus: solph.Flow(variable_costs=20, emission_factor=0.0007,
                                      investment=solph.Investment(
                                          maximum=None, minimum=0, ep_costs=100000, existing=100))},
        conversion_factors={heat_bus: 0.99})

    # create storages
    battery = solph.GenericStorage(
        label='battery',
        inputs={electricity_bus: solph.Flow(variable_costs=0)},
        outputs={electricity_bus: solph.Flow(
            variable_costs=400, emission_factor=0.06)},
        loss_rate=0.005, inflow_conversion_factor=0.95, outflow_conversion_factor=0.95,
        initial_storage_level=0, balanced=False,
        invest_relation_input_capacity=1/3,
        invest_relation_output_capacity=1/3,
        investment=solph.Investment(
            maximum=None, minimum=0, ep_costs=1630000, existing=100)
    )

    heat_storage = solph.GenericStorage(
        label='heat_storage',
        inputs={heat_bus: solph.Flow(variable_costs=0)},
        outputs={heat_bus: solph.Flow(variable_costs=20, emission_factor=0)},
        loss_rate=0.005, inflow_conversion_factor=0.95, outflow_conversion_factor=0.95,
        initial_storage_level=0, balanced=False,
        invest_relation_input_capacity=1/5,
        invest_relation_output_capacity=1/5,
        investment=solph.Investment(
            maximum=None, minimum=0, ep_costs=4500, existing=50)
    )

    # add transformers and storages to energy system
    my_energysystem.add(lignite_pp, hard_coal_pp, gas_pp, heat_plant, p2h,
                        hard_coal_chp, biogas_chp,
                        battery, heat_storage)

    # Create an energy system model
    esm = solph.Model(my_energysystem)

    # Add constraints
    esm = solph.constraints.generic_integral_limit(
        om=esm, keyword='emission_factor', limit=250000)  # 22000 bei 720 steps, 250000 bei 8760
    esm = solph.constraints.additional_investment_flow_limit(
        model=esm, keyword='investment', limit=float('+inf'))

    # Optimize model:
    esm.solve(solver='cbc')

    # Pump results into the energy system object to utilize its dump
    # functionality for saving the data
    my_energysystem.results['main'] = solph.processing.results(esm)
    my_energysystem.results['meta'] = solph.processing.meta_results(esm)
    my_energysystem.results['global'] = {
        'emissions': esm.integral_limit_emission_factor(),
        'costs': my_energysystem.results['meta']['objective'],
        'capex': esm.InvestmentFlow.investment_costs.expr() + esm.GenericInvestmentStorageBlock.investment_costs.expr()
    }

    # Store result pumped energy system:
    if not filename:
        filename = 'expansion_es.oemof'
    else:
        filename = filename

    my_energysystem.dump(dpath=directory, filename=filename)

    return my_energysystem
