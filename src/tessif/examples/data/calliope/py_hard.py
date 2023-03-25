# tessif/examples/data/calliope/py_hard.py
"""
:mod:`~tessif.examples.data.calliope.py_hard` is a :mod:`tessif` module for giving
examples on how to create an :class:`calliope model <calliope.core.model.Model>`.

It collects minimum working examples.

Note that a calliope model can have specific parameters which tessif does not cover.
For further information on how to use those refer to the `calliope documentation
<https://calliope.readthedocs.io/en/stable/user/config_defaults.html>`_.
"""
import pathlib
import os
from tessif.frused.paths import write_dir, example_dir
import pandas as pd
import numpy as np
import calliope


def create_mwe(directory=None, filename=None):
    r"""
    Create a minimum working example using :mod:`calliope`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_mwe.directory`

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is saved to.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~create_mwe.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/calliope
        will be the chosen directory.

    filename : str, default=None
        Save the energy system using this name.

        If set to ``None`` (default) filename will be ``mwe_calliope``.

    Return
    ------
    optimized_es : :class:`~calliope.core.model.Model`
        Energy system carrying the optimization results.

    Note
    ----
    The energysystem to_csv function in calliope does not work if file already exists.
    If changes are done and the csv is wanted to be saved, either another directory should be used,
    or the existing one being deleted.

    Examples
    --------
    Using :func:`create_mwe` to quickly access an optimized calliope energy system
    to use for doctesting, or trying out this frameworks utilities.
    (For a step by step explanation see :ref:`Models_Calliope_Examples_Mwe`):

    >>> import tessif.examples.data.calliope.py_hard as cllp_py
    >>> optimized_es = cllp_py.create_mwe()
    """

    # Create a simulation time frame of 4 timesteps of hourly resolution
    simulation_time = pd.date_range(
        '7/13/1990', periods=4, freq='H')

    # Building the Technologies

    demands = dict()
    demands['electricity_Demand'] = dict(
        essentials=dict(
            name='Demand',
            parent='demand',
            carrier='electricity',
        ),
        constraints=dict(
            resource_unit='energy',
            resource='file=mwe_electricity_Demand.csv:electricity_Demand',
            force_resource=True,
        ),
    )

    # making a timeseries for the demand
    demand_timeseries = np.array(len(simulation_time) * [-10])

    timeseries = pd.DataFrame(
        {'': simulation_time, 'electricity_Demand': demand_timeseries})

    timeseries.to_csv(
        os.path.join(
            example_dir, 'data', 'calliope', 'timeseries_data', f'mwe_electricity_Demand.csv'), index=False)

    sources = dict()
    sources['Gas Station'] = dict(
        essentials=dict(
            name='Gas Station',
            parent='supply',
            carrier='fuel',
        ),
        constraints=dict(
            resource=float('inf'),
            resource_unit='energy',
            energy_ramping=True,
        ),
    )

    transformers = dict()
    transformers['Generator'] = dict(
        essentials=dict(
            name='Generator',
            parent='conversion',
            carrier_in='fuel',
            carrier_out='electricity',
        ),
        constraints=dict(
            energy_eff=0.42,
            energy_ramping=True,
        ),
        costs=dict(
            monetary=dict(
                om_prod=2
            )
        )
    )

    storages = dict()
    storages['Battery'] = dict(
        essentials=dict(
            name='Battery',
            parent='storage',
            carrier='electricity',
        ),
        constraints=dict(
            energy_con=True,
            energy_prod=True,
            storage_cap_max=20,
            energy_cap_min=20,
            energy_cap_max=20,
            energy_eff=1,
            energy_ramping=True,
            storage_cap_min=20,
            storage_initial=0.5,
            storage_loss=0,
            energy_cap_per_storage_cap_min=0,
            energy_cap_per_storage_cap_max=1,
        ),
        costs=dict(
            monetary=dict(
                om_prod=0.1
            )
        )
    )

    transmissions = dict()
    transmissions['fuel transmission'] = dict(
        essentials=dict(
            name='fuel transmission',
            parent='transmission',
            carrier='fuel'
        ),
        constraints=dict(
            one_way=True,
        ),
    )

    transmissions['electricity transmission'] = dict(
        essentials=dict(
            name='electricity transmission',
            parent='transmission',
            carrier='electricity'
        ),
        constraints=dict(
            one_way=True,
        ),
    )

    # Building the Locations

    locations = dict()
    locations['Pipeline'] = dict(
        coordinates=dict(lat=0, lon=0)
    )
    locations['Powerline'] = dict(
        coordinates=dict(lat=0, lon=0)
    )
    locations['electricity_Demand location'] = dict(
        coordinates=dict(lat=0, lon=0),
        techs={'electricity_Demand': {}}
    )
    locations['Gas Station location'] = dict(
        coordinates=dict(lat=0, lon=0),
        techs={'Gas Station': {}}
    )
    locations['Generator location'] = dict(
        coordinates=dict(lat=0, lon=0),
        techs={'Generator': {}}
    )
    locations['Battery location'] = dict(
        coordinates=dict(lat=0, lon=0),
        techs={'Battery': {}}
    )

    # Building the Links

    links = dict()
    links['Gas Station location,Pipeline'] = dict(
        techs=dict({'fuel transmission': {'constraints': {'one_way': True}}})
    )
    links['Pipeline,Generator location'] = dict(
        techs=dict({'fuel transmission': {'constraints': {'one_way': True}}})
    )
    links['Battery location,Powerline'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': False}}})
    )
    links['Generator location,Powerline'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )
    links['Powerline,electricity_Demand location'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )

    # Building the Model data

    model = dict(
        name='Minimum_Working_Example',
        calliope_version='0.6.6.post1',
        timeseries_data_path=f'{example_dir}/data/calliope/timeseries_data',
        # subset_time=[
        #     '1990-07-13 00:00:00',
        #     '1990-07-13 03:00:00'],
    )

    # Building the Run data

    run = dict(solver='cbc', cyclic_storage=False,
               objective_options=dict(cost_class={'monetary': 1}))

    # Building the full Model dictionary

    model_dict = dict(techs=dict(), locations=dict(),
                      links=dict(), model=dict(), run=dict())
    model_dict['techs'].update(demands)
    model_dict['techs'].update(sources)
    model_dict['techs'].update(transformers)
    model_dict['techs'].update(storages)
    model_dict['techs'].update(transmissions)

    model_dict['locations'].update(locations)
    model_dict['links'].update(links)
    model_dict['model'].update(model)
    model_dict['run'].update(run)

    calliope.set_log_verbosity('ERROR', include_solver_output=False)
    # build the calliope model
    es = calliope.Model(model_dict)

    # run the optimization
    es.run(force_rerun=True)

    # Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'calliope')
    else:
        d = directory

    # Set default filename if necessary, using the isoformat
    if not filename:
        f = 'mwe_calliope'
    else:
        f = filename

    # create output directory if necessary
    pathlib.Path(os.path.abspath(d)).mkdir(
        parents=True, exist_ok=True)

    es.save_commented_model_yaml(f'{d}/{f}')
    try:
        es.to_csv(f'{d}/{f}')
    except FileExistsError:
        pass

    # Return the mwe calliope energy system
    return es


def create_fpwe(directory=None, filename=None):
    r"""
    Create a fully parameterized working example using :mod:`calliope`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_mwe.directory`

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is saved to.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~create_mwe.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/calliope
        will be the chosen directory.

    filename : str, default=None
        Save the energy system using this name.

        If set to ``None`` (default) filename will be ``fpwe_calliope``.

    Return
    ------
    optimized_es : :class:`~calliope.core.model.Model`
        Energy system carrying the optimization results.

    Note
    ----
    This example is not actually fully parameterized but the most important parameters
    when using calliope with tessif are shown. For full parameterization and all defaults
    there is a defaults.yaml inside the config folder inside the calliope installation folder.

    Examples
    --------
    Using :func:`create_fpwe` to quickly access an optimized calliope energy system
    to use for doctesting, or trying out this frameworks utilities.
    (For a step by step explanation see :ref:`Models_Calliope_Examples_Mwe`):

    >>> import tessif.examples.data.calliope.py_hard as cllp_py
    >>> optimized_es = cllp_py.create_fpwe()
    """

    # Create a simulation time frame of 4 timesteps of hourly resolution
    simulation_time = pd.date_range(
        '7/13/1990', periods=3, freq='H')

    # Building the Technologies

    demands = dict()
    demands['electricity_Demand'] = dict(
        essentials=dict(
            # This way tessif uid is stored in calliope.
            name='Demand.Germany.Power.electricity.demand',
            parent='demand',
            carrier='electricity',
        ),
        constraints=dict(
            resource_unit='energy',
            resource='file=fpwe_electricity_Demand.csv:electricity_Demand',
            force_resource=True,
        ),
        costs=dict(
            monetary=dict(
                om_con=0,
            ),
            emissions=dict(
                om_con=0,
            )
        )
    )

    # making a timeseries for the demand
    demand_timeseries = np.array(len(simulation_time) * [-11])

    timeseries = pd.DataFrame(
        {'': simulation_time, 'electricity_Demand': demand_timeseries})

    timeseries.to_csv(
        os.path.join(
            example_dir, 'data', 'calliope', 'timeseries_data', f'fpwe_electricity_Demand.csv'), index=False)

    sources = dict()
    sources['Gas Station'] = dict(
        essentials=dict(
            name='Gas Station.Germany.Power.Gas.source',
            parent='supply',
            carrier='fuel',
        ),
        constraints=dict(
            energy_cap_min=100.0,
            energy_cap_max=100.0,
            energy_cap_min_use=0.0,
            energy_eff=1,
            resource=float('inf'),
            resource_unit='energy',
            energy_ramping=True,
            # needed in calliope for expansion costs calculation
            lifetime=len(simulation_time) / 8760,
        ),
        costs=dict(
            monetary=dict(
                om_prod=10,
                energy_cap=0,  # expansion costs
                interest_rate=0,  # needed in calliope for expansion costs calculation
            ),
            emissions=dict(
                om_prod=3,
            )
        )
    )

    sources['Solar Panel'] = dict(
        essentials=dict(
            name='Solar Panel.Germany.Power.electricity.Renewable',
            parent='supply',
            carrier='electricity',
        ),
        constraints=dict(
            energy_cap_min=20.0,
            energy_cap_max=20.0,
            energy_eff=1,
            resource='file=fpwe_Solar Panel.csv:Solar Panel',
            resource_unit='energy_per_cap',
            force_resource=True,  # force this resource since the min and max in tessif are equal
            energy_ramping=True,
            lifetime=len(simulation_time) / 8760,
        ),
        costs=dict(
            monetary=dict(
                om_prod=0,
                energy_cap=0,
                interest_rate=0,
            ),
            emissions=dict(
                om_prod=0,
            )
        )
    )

    # making a timeseries for the demand
    solar_timeseries = np.array([12, 3, 7])

    # calliope needs timeseries relative to energy capacity when resource_unit is energy_per_cap
    # (which is important if expandable)
    solar_timeseries = solar_timeseries / \
        sources['Solar Panel']['constraints']['energy_cap_min']

    timeseries = pd.DataFrame(
        {'': simulation_time, 'Solar Panel': solar_timeseries})

    timeseries.to_csv(
        os.path.join(
            example_dir, 'data', 'calliope', 'timeseries_data', f'fpwe_Solar Panel.csv'), index=False)

    transformers = dict()
    transformers['Generator'] = dict(
        essentials=dict(
            name='Generator.Germany.Power.electricity.transformer',
            parent='conversion',
            carrier_in='fuel',
            carrier_out='electricity',
        ),
        constraints=dict(
            energy_eff=0.42,
            energy_cap_min=15.0,
            energy_cap_max=15.0,
            energy_cap_min_use=0.0,
            energy_ramping=True,
            lifetime=len(simulation_time) / 8760,
        ),
        costs=dict(
            monetary=dict(
                om_con=0,
                om_prod=10,
                energy_cap=0,
                interest_rate=0,
            ),
            emissions=dict(
                om_con=0,
                om_prod=10,
            )
        )
    )

    storages = dict()
    storages['Battery'] = dict(
        essentials=dict(
            name='Battery',
            parent='storage',
            carrier='electricity',
        ),
        constraints=dict(
            energy_con=True,
            energy_prod=True,
            storage_cap_max=10,
            energy_cap_min=10,
            energy_cap_max=10,
            energy_eff=1,
            energy_ramping=True,
            storage_cap_min=10,
            storage_initial=0.9,
            # tsf fpwe example has storage_initial = 1, but doesnt work
            # here cause calliope doesnt have storage loss from timestep -1 (initial) to 0
            storage_loss=0.1,
            energy_cap_per_storage_cap_min=0,
            energy_cap_per_storage_cap_max=1,
        ),
        costs=dict(
            monetary=dict(
                om_prod=0,
            ),
            emissions=dict(
                om_prod=0,
            )
        )
    )

    transmissions = dict()
    transmissions['fuel transmission'] = dict(
        essentials=dict(
            name='fuel transmission',
            parent='transmission',
            carrier='fuel'
        ),
        constraints=dict(
            energy_eff=1,  # no similar thing in tessif exist, thus they are alway 1
            one_way=True,
        ),
    )

    transmissions['electricity transmission'] = dict(
        essentials=dict(
            name='electricity transmission',
            parent='transmission',
            carrier='electricity'
        ),
        constraints=dict(
            energy_eff=1,  # no similar thing in tessif exist, thus they are alway 1
            one_way=True,
        ),
    )

    # Building the Locations

    locations = dict()
    locations['Pipeline'] = dict(
        coordinates=dict(lat=42, lon=42)
    )
    locations['Powerline'] = dict(
        coordinates=dict(lat=42, lon=42)
    )
    locations['electricity_Demand location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'electricity_Demand': {}}
    )
    locations['Gas Station location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Gas Station': {}}
    )
    locations['Solar Panel location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Solar Panel': {}}
    )
    locations['Generator location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Generator': {}}
    )
    locations['Battery location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Battery': {}}
    )

    # Building the Links

    links = dict()
    links['Gas Station location,Pipeline'] = dict(
        techs=dict({'fuel transmission': {'constraints': {'one_way': True}}})
    )
    links['Solar Panel location,Powerline'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )
    links['Pipeline,Generator location'] = dict(
        techs=dict({'fuel transmission': {'constraints': {'one_way': True}}})
    )
    links['Battery location,Powerline'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': False}}})
    )
    links['Generator location,Powerline'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )
    links['Powerline,electricity_Demand location'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )

    # Building the Model data

    subset_time = [str(simulation_time[0]), str(simulation_time[-1])]
    model = dict(
        name='Fully_Parameterized_Working_Example',
        calliope_version='0.6.6-post1',
        timeseries_data_path=f'{example_dir}/data/calliope/timeseries_data',
        # useful e.g. for testing to set timeframe to 3 steps, when csv actually are 8760
        subset_time=subset_time,
    )

    # Building the Run data

    run = dict(
        solver='cbc',
        cyclic_storage=False,
        objective_options=dict(
            cost_class={'monetary': 1}
        )
    )

    # global constraints:
    group_constraints = dict(
        systemwide_emission_cap=dict(
            cost_max=dict(
                emissions=None,  # insert global emissions constraint here or None if infinity
            )
        ),
    )

    # accumulated amounts of sources and sinks are also stored as group constraints:
    group_constraints.update({
        f'Solar Panel_accumulated_amounts_max': dict(
            techs=['Solar Panel'],
            carrier_prod_max=dict(
                electricity=1000,
            ),
        )
    })

    # Building the full Model dictionary

    model_dict = dict(techs=dict(), locations=dict(), links=dict(
    ), model=dict(), run=dict(), group_constraints=dict())
    model_dict['techs'].update(demands)
    model_dict['techs'].update(sources)
    model_dict['techs'].update(transformers)
    model_dict['techs'].update(storages)
    model_dict['techs'].update(transmissions)

    model_dict['locations'].update(locations)
    model_dict['links'].update(links)
    model_dict['model'].update(model)
    model_dict['run'].update(run)
    model_dict['group_constraints'].update(group_constraints)

    calliope.set_log_verbosity('ERROR', include_solver_output=False)
    # build the calliope model
    es = calliope.Model(model_dict)

    # run the optimization
    es.run(force_rerun=True)

    # Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'calliope')
    else:
        d = directory

    # Set default filename if necessary, using the isoformat
    if not filename:
        f = 'fpwe_calliope'
    else:
        f = filename

    # create output directory if necessary
    pathlib.Path(os.path.abspath(d)).mkdir(
        parents=True, exist_ok=True)

    es.save_commented_model_yaml(f'{d}/{f}')
    try:
        es.to_csv(f'{d}/{f}')
    except FileExistsError:
        pass

    # Return the mwe calliope energy system
    return es


def create_chp_expansion(directory=None, filename=None):
    r"""
    Create a fully parameterized working example using :mod:`calliope`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_mwe.directory`

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is saved to.

        Will be :func:`joined
        <os.path.join>` with :paramref:`~create_mwe.filename`.

        If set to ``None`` (default) :attr:`tessif.frused.paths.write_dir`/calliope
        will be the chosen directory.

    filename : str, default=None
        Save the energy system using this name.

        If set to ``None`` (default) filename will be ``chp_calliope``.

    Return
    ------
    optimized_es : :class:`~calliope.core.model.Model`
        Energy system carrying the optimization results.

    Note
    ----
    This energy system model was created to further inspect the parameter
    definitions of CHPs when they are expandable. It can be seen that costs refer to
    the primary output.

    Examples
    --------
    Using :func:`create_chp` to quickly access an optimized calliope energy system
    to use for doctesting, or trying out this frameworks utilities.
    (For a step by step explanation see :ref:`Models_Calliope_Examples_Mwe`):

    >>> import tessif.examples.data.calliope.py_hard as cllp_py
    >>> optimized_es = cllp_py.create_chp_expansion()
    """

    # Create a simulation time frame of 4 timesteps of hourly resolution
    simulation_time = pd.date_range(
        '7/13/1990', periods=4, freq='H')

    # Building the Technologies

    demands = dict()
    demands['Power Demand'] = dict(
        essentials=dict(
            # This way tessif uid is stored in calliope.
            name='Power Demand.Germany.Power.electricity.demand',
            parent='demand',
            carrier='electricity',
        ),
        constraints=dict(
            resource_unit='energy',
            resource='file=chp_Power Demand.csv:Power Demand',
            force_resource=True,
        ),
        costs=dict(
            monetary=dict(
                om_con=0,
            ),
            emissions=dict(
                om_con=0,
            )
        )
    )

    demands['Heat Demand'] = dict(
        essentials=dict(
            # This way tessif uid is stored in calliope.
            name='Heat Demand.Germany.Power.electricity.demand',
            parent='demand',
            carrier='heat',
        ),
        constraints=dict(
            resource_unit='energy',
            resource='file=chp_Heat Demand.csv:Heat Demand',
            force_resource=True,
        ),
        costs=dict(
            monetary=dict(
                om_con=0,
            ),
            emissions=dict(
                om_con=0,
            )
        )
    )

    # making a timeseries for the demand
    power_demand_timeseries = np.array(len(simulation_time) * [-10])
    power_demand_timeseries = pd.DataFrame(
        {'': simulation_time, 'Power Demand': power_demand_timeseries})
    power_demand_timeseries.to_csv(
        os.path.join(
            example_dir, 'data', 'calliope', 'timeseries_data', f'chp_Power Demand.csv'), index=False)

    heat_demand_timeseries = np.array(len(simulation_time) * [-10])
    heat_demand_timeseries = pd.DataFrame(
        {'': simulation_time, 'Heat Demand': heat_demand_timeseries})
    heat_demand_timeseries.to_csv(
        os.path.join(
            example_dir, 'data', 'calliope', 'timeseries_data', f'chp_Heat Demand.csv'), index=False)

    sources = dict()
    sources['Gas Source'] = dict(
        essentials=dict(
            name='Gas Source.Germany.Power.Gas.source',
            parent='supply',
            carrier='gas',
        ),
        constraints=dict(
            energy_cap_min=0.0,
            energy_cap_max=float('inf'),
            energy_cap_min_use=0.0,
            energy_eff=1,
            resource=float('inf'),
            resource_unit='energy',
            energy_ramping=True,
        ),
        costs=dict(
            monetary=dict(
                om_prod=0,
            ),
            emissions=dict(
                om_prod=0,
            )
        )
    )

    sources['Backup Power'] = dict(
        essentials=dict(
            name='Backup Power.Germany.Power.electricity.Renewable',
            parent='supply',
            carrier='electricity',
        ),
        constraints=dict(
            energy_cap_min=0,
            energy_cap_max=float('inf'),
            energy_eff=1,
            resource=float('inf'),
            resource_unit='energy',
            energy_ramping=True,
        ),
        costs=dict(
            monetary=dict(
                om_prod=1000,
            ),
            emissions=dict(
                om_prod=0,
            )
        )
    )

    sources['Backup Heat'] = dict(
        essentials=dict(
            name='Backup Heat.Germany.Power.electricity.Renewable',
            parent='supply',
            carrier='heat',
        ),
        constraints=dict(
            energy_cap_min=0,
            energy_cap_max=float('inf'),
            energy_eff=1,
            resource=float('inf'),
            resource_unit='energy',
            energy_ramping=True,
        ),
        costs=dict(
            monetary=dict(
                om_prod=1000,
            ),
            emissions=dict(
                om_prod=0,
            )
        )
    )

    transformers = dict()
    transformers['CHP'] = dict(
        essentials=dict(
            name='CHP.Germany.Power.electricity.transformer',
            parent='conversion_plus',  # conversion_plus if multi output or multi input
            carrier_in='gas',
            carrier_out='electricity',
            primary_carrier_out='electricity',
            carrier_out_2='heat',
        ),
        constraints=dict(
            carrier_ratios=dict(
                carrier_out_2=dict(
                    heat=0.8  # ratio how much heat is produced when 1 unit primary_carrier_out is produced
                )
            ),
            energy_eff=0.5,
            energy_cap_min=0.0,
            energy_cap_max=8.0,
            energy_cap_min_use=0.0,
            energy_ramping=True,
            lifetime=len(simulation_time)/8760,
        ),
        costs=dict(
            monetary=dict(
                om_con=0,
                om_prod=1,
                energy_cap=1,
                interest_rate=0,
            ),
            emissions=dict(
                om_con=0,
                om_prod=1,
            )
        )
    )

    transmissions = dict()
    transmissions['gas transmission'] = dict(
        essentials=dict(
            name='gas transmission',
            parent='transmission',
            carrier='gas'
        ),
        constraints=dict(
            energy_eff=1,  # no similar thing in tessif exist, thus they are alway 1
            one_way=True,
        ),
    )

    transmissions['electricity transmission'] = dict(
        essentials=dict(
            name='electricity transmission',
            parent='transmission',
            carrier='electricity'
        ),
        constraints=dict(
            energy_eff=1,  # no similar thing in tessif exist, thus they are alway 1
            one_way=True,
        ),
    )

    transmissions['heat transmission'] = dict(
        essentials=dict(
            name='heat transmission',
            parent='transmission',
            carrier='heat'
        ),
        constraints=dict(
            energy_eff=1,  # no similar thing in tessif exist, thus they are alway 1
            one_way=True,
        ),
    )

    # Building the Locations

    locations = dict()
    locations['Gas Grid'] = dict(
        coordinates=dict(lat=42, lon=42)
    )
    locations['Powerline'] = dict(
        coordinates=dict(lat=42, lon=42)
    )
    locations['Heat Grid'] = dict(
        coordinates=dict(lat=42, lon=42)
    )
    locations['Power Demand location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Power Demand': {}}
    )
    locations['Heat Demand location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Heat Demand': {}}
    )
    locations['Gas Source location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Gas Source': {}}
    )
    locations['Backup Power location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Backup Power': {}}
    )
    locations['Backup Heat location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'Backup Heat': {}}
    )
    locations['CHP location'] = dict(
        coordinates=dict(lat=42, lon=42),
        techs={'CHP': {}}
    )

    # Building the Links

    links = dict()
    links['Gas Source location,Gas Grid'] = dict(
        techs=dict({'gas transmission': {'constraints': {'one_way': True}}})
    )
    links['Gas Grid,CHP location'] = dict(
        techs=dict({'gas transmission': {'constraints': {'one_way': True}}})
    )
    links['CHP location,Powerline'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )
    links['CHP location,Heat Grid'] = dict(
        techs=dict({'heat transmission': {'constraints': {'one_way': True}}})
    )
    links['Backup Power location,Powerline'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )
    links['Backup Heat location,Heat Grid'] = dict(
        techs=dict({'heat transmission': {'constraints': {'one_way': True}}})
    )
    links['Heat Grid,Heat Demand location'] = dict(
        techs=dict({'heat transmission': {'constraints': {'one_way': True}}})
    )
    links['Powerline,Power Demand location'] = dict(
        techs=dict({'electricity transmission': {
                   'constraints': {'one_way': True}}})
    )

    # Building the Model data

    subset_time = [str(simulation_time[0]), str(simulation_time[-1])]
    model = dict(
        name='CHP_Expansion_Example',
        calliope_version='0.6.6-post1',
        timeseries_data_path=f'{example_dir}/data/calliope/timeseries_data',
        # useful e.g. for testing to set timeframe to 3 steps, when csv actually are 8760
        subset_time=subset_time,
    )

    # Building the Run data

    run = dict(
        solver='cbc',
        cyclic_storage=False,
        objective_options=dict(
            cost_class={'monetary': 1}
        )
    )

    # global constraints:
    group_constraints = dict(
        systemwide_emission_cap=dict(
            cost_max=dict(
                emissions=None,  # insert global emissions constraint here or None if infinity
            )
        ),
    )

    # Building the full Model dictionary

    model_dict = dict(techs=dict(), locations=dict(), links=dict(
    ), model=dict(), run=dict(), group_constraints=dict())
    model_dict['techs'].update(demands)
    model_dict['techs'].update(sources)
    model_dict['techs'].update(transformers)
    # model_dict['techs'].update(storages)
    model_dict['techs'].update(transmissions)

    model_dict['locations'].update(locations)
    model_dict['links'].update(links)
    model_dict['model'].update(model)
    model_dict['run'].update(run)
    model_dict['group_constraints'].update(group_constraints)

    calliope.set_log_verbosity('ERROR', include_solver_output=False)
    # build the calliope model
    es = calliope.Model(model_dict)

    # run the optimization
    es.run(force_rerun=True)

    # Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'calliope')
    else:
        d = directory

    # Set default filename if necessary, using the isoformat
    if not filename:
        f = 'chp_calliope'
    else:
        f = filename

    # create output directory if necessary
    pathlib.Path(os.path.abspath(d)).mkdir(
        parents=True, exist_ok=True)

    es.save_commented_model_yaml(f'{d}/{f}')
    try:
        es.to_csv(f'{d}/{f}')
    except FileExistsError:
        pass

    # Return the mwe calliope energy system
    return es
