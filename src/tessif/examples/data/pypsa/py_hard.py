# tessif/examples/data/pypsa/py_hard.py
# -*- coding: utf-8 -*-
"""
:mod:`~tessif.examples.data.pypsa.py_hard` is a :mod:`tessif` module for giving
examples on how to create a :class:`pypsa energy system <pypsa.Network>`
It collects minimum working examples, meaningful working
examples and full fledged use case wrappers for common scenarios.
"""

# standard library
import os
import pathlib

# third pary
import pypsa
import pandas as pd
import numpy as np

# local
import tessif.frused.namedtuples as nts
from tessif.frused.paths import write_dir
import tessif.write.tools as write_tools
from tessif.frused.paths import example_dir
import tessif.frused.hooks.ppsa as pypsa_hooks


def create_mwe(directory=None):
    r"""
    Create a minimum working example using :mod:`pypsa`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_mwe.directory` as
    :paramref:`~create_mwe.filename`

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is stored in.
        Passed to :meth:`pypsa.Network.export_to_csv_folder`.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/pypsa/mwe will be the chosen
        directory.


    Return
    ------
    optimized_es : :class:`~pypsa.Network`
        Energy system carrying the optimization results.

    Examples
    --------
    Using :func:`create_mwe` to quickly access a tessif energy system
    to use for doctesting, or trying out this frameworks utilities.

    (For a step by step explanation see :ref:`Models_Pypsa_Examples_Mwe`):

    >>> import tessif.examples.data.pypsa.py_hard as pypsa_coded_examples
    >>> import sys
    >>> pypsa_es = pypsa_coded_examples.create_mwe()

    Show the exported directory's content:

    >>> import os
    >>> from tessif.frused.paths import write_dir
    >>> for fle in sorted(os.listdir(os.path.join(write_dir, 'pypsa', 'mwe'))):
    ...     print(fle)
    buses-marginal_price.csv
    buses.csv
    generators-p.csv
    generators-p_max_pu.csv
    generators.csv
    investment_periods.csv
    loads-p.csv
    loads.csv
    network.csv
    snapshots.csv
    """

    # 2.) Create a simulation time frame of 2 timesteps
    # pypsa is not designed to handle any form of real-time.
    # It assumes hourly resolution and only cares about the number of steps.
    # Until now however, no drawback in using a pandas.date_range was detected

    # timesteps = range(2)
    timesteps = pd.date_range('7/13/1990', periods=2, freq='H')

    # 3.) Create an energy system / network object:
    es = pypsa.Network()

    # 3.1) enforce the number of timesteps
    es.set_snapshots(timesteps)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using component attributes to store location (latt/long) region,
    # carrier and sector categorization as all pypsa simulations do in this
    # framework)

    power_bus_uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')

    # 4.1) Ideal power line
    es.add(class_name='Bus',
           # tessif's uid representation
           name=power_bus_uid,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    # 4.2) Demand needing 10 energy units per timestep
    es.add(class_name='Load',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Demand', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink'),
           p_set=10,
           )

    # 4.3) Renewable source producing 8 and 2 energy units with a cost of 9
    es.add(class_name='Generator',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Renewable', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source'),
           p_nom=10, p_max_pu=[0.8, 0.2], marginal_cost=9
           )

    # # 4.4) Chemically Bound Energy Transport
    # chemical_bus_uid = nts.Uid(
    #     name='CBET', latitude=53, longitude=10,
    #     region='Germany', sector='Power', carrier='gas',
    #     component='Bus', node_type='commodity_bus')

    # es.add(clas_name='Bus',
    #        name=chemical_bus_uid,
    #        x=10, y=53, carrier='gas',
    #        )

    # # 4.5) Chemically Bound Energy Source
    # es.add(class_name='Generator',
    #        bus=str(chemical_bus_uid),
    #        name=nts.Uid(
    #            name='CBE', latitude=53, longitude=10,
    #            region='Germany', sector='Power', carrier='gas',
    #            component='source', node_type='commodity_source')
    #        )

    # 4.6) Conventional Engergy Transformer
    #      producing up to 10 energy units for a cost of 10
    es.add(class_name='Generator',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Gas Generator', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='gas',
               component='Transformer', node_type='gas-powerplant'),
           p_nom=10, marginal_cost=10)

    # 5.) Optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        es.lopf()

    # 6.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'pypsa', 'mwe')
    else:
        d = directory

    # Make sure the write path exists.
    pathlib.Path(d).mkdir(
        parents=True,  # create parent directories if necessary
        exist_ok=True,  # directory already existing is OK
    )

    es.export_to_csv_folder(d)

    return es


def emission_objective(directory=None):
    """
    Create a minimum working example using :mod:`pypsa`.

    Optimizing it for costs and keeping the total emissions below an emission
    objective.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is stored in.
        Passed to :meth:`pypsa.Network.export_to_csv_folder`.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/pypsa/emission_objective will be
        the chosen  directory.


    Return
    ------
    optimized_es : :class:`~pypsa.Network`
        Energy system carrying the optimization results.

    Examples
    --------
    Using :func:`emission_objective` to quickly access an optimized pypsa
    energy system to use for doctesting, or trying out this frameworks
    utilities.

    (For a step by step explanation on how to create an oemof minimum working
    example see :ref:`Models_Pypsa_Examples_Mwe`):

    >>> import tessif.examples.data.pypsa.py_hard as coded_examples
    >>> optimized_es = coded_examples.emission_objective()

    Show the emission constraint:

    >>> import pprint
    >>> pprint.pprint(optimized_es.global_constraints)
    attribute            type  investment_period carrier_attribute sense  constant   mu
    name                                                                               
    co2_limit  primary_energy                NaN     co2_emissions    <=      30.0  3.0

    Note how utilizing the generator is cheaper, but due to the emission
    constraint the renewable is used during the last timestep:

    >>> print(optimized_es.generators_t.p)
    name                 Renewable  Gas Generator
    snapshot                                     
    1990-07-13 00:00:00        0.0           10.0
    1990-07-13 01:00:00        0.0           10.0
    1990-07-13 02:00:00        0.0           10.0
    1990-07-13 03:00:00       10.0            0.0

    See user's guide on :ref:`Secondary_Objectives` for more on this example.
    """
    # 2.) Create a simulation time frame of four timesteps of hourly resolution
    timesteps = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3.) Create an energy system / network object:
    es = pypsa.Network()

    # 3.1) enforce the number of timesteps
    es.set_snapshots(timesteps)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using component attributes to store location (latt/long) region,
    # carrier and sector categorization as all pypsa simulations do in this
    # framework)

    power_bus_uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')

    # 4.1) Ideal power line
    es.add(class_name='Bus',
           # tessif's uid representation
           name=power_bus_uid,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    # 4.2) Demand needing 10 energy units per timestep
    es.add(class_name='Load',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Demand', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink'),
           p_set=10,
           )

    # 4.3) Renewable power is more expensive but has no emissions allocated
    es.add(class_name='Generator',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Renewable', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source'),
           marginal_cost=5, p_nom=999999999999,
           )

    # 4.4) Conventional Engergy Transformer
    #      producing up to 10 energy units for a cost of 2
    #      at an efficiency of 0.42 using gas as fuel
    es.add(class_name='Generator',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Gas Generator', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='gas',
               component='Transformer', node_type='gas-powerplant'),
           p_nom=10, marginal_cost=2, efficiency=0.42, carrier='gas')

    # adding CO2 emissions to gas fuled power plants:
    es.add(class_name="Carrier",
           name='gas',
           co2_emissions=0.42,
           # 0.42 unit_CO2/unit_Energy to match the efficiency and emission
           # of other models emission_objective examples
           )

    # Add emission constraint
    es.add(class_name='GlobalConstraint',
           name="co2_limit",
           sense="<=",
           constant=30)

    # 5.) Optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        es.lopf()

    # 6.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'pypsa', 'emission_objective')
    else:
        d = directory

    # Make sure the write path exists.
    pathlib.Path(d).mkdir(
        parents=True,  # create parent directories if necessary
        exist_ok=True,  # directory already existing is OK
    )

    es.export_to_csv_folder(d)

    return es


def create_transshipment_problem(directory=None):
    """
    Create a `transshipment problem
    <https://en.wikipedia.org/wiki/Transshipment_problem>`_. using
    :mod:`pypsa`.

    Optimizing it for costs.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is stored in.
        Passed to :meth:`pypsa.Network.export_to_csv_folder`.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/pypsa/transshipment will be
        the chosen  directory.


    Return
    ------
    optimized_es : :class:`~pypsa.Network`
        Energy system carrying the optimization results.

    Examples
    --------
    Using :func:`create_transshipment_problem` to quickly access an optimized
    pypsa  energy system to use for doctesting, or trying out this frameworks
    utilities.

    (For a step by step explanation see :ref:`Models_Pypsa_Examples_Mwe`):

    >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
    >>> pypsa_es = coded_pypsa_examples.create_transshipment_problem()
    >>> for link in pypsa_es.links.index:
    ...     print(link)
    connector-01->02

    >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
    >>> resultier = post_process_pypsa.LoadResultier(pypsa_es)

    >>> print(resultier.node_load['connector-01->02'])
    connector-01->02     bus-01  bus-02  bus-01  bus-02
    1990-07-13 00:00:00   -10.0    -0.0     0.0    10.0
    1990-07-13 01:00:00    -0.0    -5.0     5.0     0.0
    1990-07-13 02:00:00    -0.0    -0.0     0.0     0.0

    >>> print(resultier.node_load['bus-01'])
    bus-01               connector-01->02  source-01  connector-01->02  sink-01
    1990-07-13 00:00:00              -0.0      -10.0              10.0      0.0
    1990-07-13 01:00:00              -5.0      -10.0               0.0     15.0
    1990-07-13 02:00:00              -0.0      -10.0               0.0     10.0

    >>> print(resultier.node_load['bus-02'])
    bus-02               connector-01->02  source-02  connector-01->02  sink-02
    1990-07-13 00:00:00             -10.0       -5.0               0.0     15.0
    1990-07-13 01:00:00              -0.0       -5.0               5.0      0.0
    1990-07-13 02:00:00              -0.0      -10.0               0.0     10.0

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> import tessif.transform.nxgrph as nxt
    >>> grph = nxt.Graph(resultier)
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'connector-01->02': '#9999ff',
    ...                 'bus-01': '#cc0033',
    ...                 'bus-02': '#00ccff'},
    ...     node_size={'connector': 5000},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    IGNORE:
    >>> title = plt.gca().set_title('Pypsa Transshipment Example')
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: ../images/pypsa_transshipment_example.png
        :align: center
        :alt: Image showing the transhipmet es as a networkx graph.

    """
    # 2.) Create a simulation time frame of four timesteps of hourly resolution
    timesteps = pd.date_range('7/13/1990', periods=3, freq='H')

    # 3.) Create an energy system / network object:
    es = pypsa.Network()

    # 3.1) enforce the number of timesteps
    es.set_snapshots(timesteps)

    # 4.1) Bus 01 Side
    # 4.1.1) bus uid
    bus_01_uid = nts.Uid(
        name='bus-01', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')

    # 4.1.2) bus
    es.add(class_name='Bus',
           # tessif's uid representation
           name=bus_01_uid,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    # 4.1.3) sink needing 0, 15, 10 energy units
    es.add(class_name='Load',
           bus=str(bus_01_uid),
           name=nts.Uid(
               name='sink-01', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink'),
           p_set=[0, 15, 10],
           )

    # 4.1.3) source providing 0 to 10 energy units
    es.add(class_name='Generator',
           bus=str(bus_01_uid),
           name=nts.Uid(
               name='source-01', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source'),
           marginal_cost=0.9, p_nom=10,
           )

    # 4.2) Bus 02 Side
    # 4.2.1) bus uid
    bus_02_uid = nts.Uid(
        name='bus-02', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')

    # 4.2.2) bus
    es.add(class_name='Bus',
           # tessif's uid representation
           name=bus_02_uid,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    # 4.2.3) sink needing 15, 0, 10 energy units
    es.add(class_name='Load',
           bus=str(bus_02_uid),
           name=nts.Uid(
               name='sink-02', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink'),
           p_set=[15, 0, 10],
           )

    # 4.2.3) source providing 0 to 10 energy units
    es.add(class_name='Generator',
           bus=str(bus_02_uid),
           name=nts.Uid(
               name='source-02', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source'),
           marginal_cost=1.1, p_nom=10,
           )

    # 4.3) The connector aka link in pypsa has no bidirectional efficencies
    es.add(class_name='Link',
           name=nts.Uid(
               name='connector-01->02', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Connector', node_type='AC-Link'),
           bus0=str(bus_01_uid),
           bus1=str(bus_02_uid),
           efficiency=1,
           p_nom_extendable=True,
           capital_cost=0,
           p_min_pu=-1,
           marginal_cost=0,
           )

    # 5.) Optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        es.lopf()

    # 6.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'pypsa', 'transshipment')
    else:
        d = directory

    # Make sure the write path exists.
    pathlib.Path(d).mkdir(
        parents=True,  # create parent directories if necessary
        exist_ok=True,  # directory already existing is OK
    )

    es.export_to_csv_folder(d)

    return es


def create_storage_example(directory=None):
    """
    Create a small energy system utilizing a storage using :mod:`pypsa`.

    Optimizing it for costs.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is stored in.
        Passed to :meth:`pypsa.Network.export_to_csv_folder`.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/pypsa/storage will be
        the chosen  directory.


    Return
    ------
    optimized_es : :class:`~pypsa.Network`
        Energy system carrying the optimization results.

    Examples
    --------
    Using :func:`create_storage_example` to quickly access an optimized
    pypsa  energy system to use for doctesting, or trying out this frameworks
    utilities.

    (For a step by step explanation see :ref:`Models_Pypsa_Examples_Mwe`):

    >>> # import the storage example and optimize it:
    >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
    >>> pypsa_es = coded_pypsa_examples.create_storage_example()
    >>> for storage in pypsa_es.storage_units.index:
    ...     print(storage)
    Storage

    >>> # import the post processing utility:
    >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa

    >>> # use it to get the  load results:
    >>> resultier = post_process_pypsa.LoadResultier(pypsa_es)
    >>> for load in resultier.node_load.values():
    ...     print(load)
    Variable Source      Power Line
    1990-07-13 00:00:00        19.0
    1990-07-13 01:00:00        19.0
    1990-07-13 02:00:00        19.0
    1990-07-13 03:00:00         0.0
    1990-07-13 04:00:00         0.0
    Demand               Power Line
    1990-07-13 00:00:00       -10.0
    1990-07-13 01:00:00       -10.0
    1990-07-13 02:00:00        -7.0
    1990-07-13 03:00:00       -10.0
    1990-07-13 04:00:00       -10.0
    Storage              Power Line  Power Line
    1990-07-13 00:00:00        -9.0         0.0
    1990-07-13 01:00:00        -9.0         0.0
    1990-07-13 02:00:00       -12.0         0.0
    1990-07-13 03:00:00        -0.0        10.0
    1990-07-13 04:00:00        -0.0        10.0
    Power Line           Storage  Variable Source  Demand  Storage
    1990-07-13 00:00:00     -0.0            -19.0    10.0      9.0
    1990-07-13 01:00:00     -0.0            -19.0    10.0      9.0
    1990-07-13 02:00:00     -0.0            -19.0     7.0     12.0
    1990-07-13 03:00:00    -10.0             -0.0    10.0      0.0
    1990-07-13 04:00:00    -10.0             -0.0    10.0      0.0

    >>> # use it to get the storage soc results:
    >>> resultier = post_process_pypsa.StorageResultier(pypsa_es)
    >>> print(resultier.node_soc['Storage'])
    1990-07-13 00:00:00     9.0
    1990-07-13 01:00:00    18.0
    1990-07-13 02:00:00    30.0
    1990-07-13 03:00:00    20.0
    1990-07-13 04:00:00    10.0
    Freq: H, Name: Storage, dtype: float64

    >>> # use it to get the storage capacity and characteristic value results:
    >>> resultier = post_process_pypsa.CapacityResultier(pypsa_es)
    >>> # capacity results:
    >>> for node, capacity in resultier.node_installed_capacity.items():
    ...     print(f'{node}: {capacity}')
    Power Line: None
    Variable Source: 19.0
    Demand: 10.0
    Storage: 30.0

    >>> # characteristic value results:
    >>> for node, cv in resultier.node_characteristic_value.items():
    ...     if cv is not None:
    ...         cv = round(cv, 2)
    ...     print(f'{node}: {cv}')
    Power Line: None
    Variable Source: 0.6
    Demand: 0.94
    Storage: 0.58

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> import tessif.transform.nxgrph as nxt
    >>> grph = nxt.Graph(resultier)
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Power Line': '#009900',
    ...                 'Storage': '#cc0033',
    ...                 'Demand': '#00ccff',
    ...                 'Variable Source': '#ffD700',},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    IGNORE:
    >>> title = plt.gca().set_title('Pypsa Storage Example')
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: ../images/pypsa_storage_example.png
        :align: center
        :alt: Image showing the storage es as a networkx graph.



    """
    # 2.) Create a simulation time frame of four timesteps of hourly resolution
    timesteps = pd.date_range('7/13/1990', periods=5, freq='H')

    # 3.) Create an energy system / network object:
    es = pypsa.Network()

    # 3.1) enforce the number of timesteps
    es.set_snapshots(timesteps)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using component attributes to store location (latt/long) region,
    # carrier and sector categorization as all pypsa simulations do in this
    # framework)

    power_bus_uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')

    # 4.1) Ideal power line
    es.add(class_name='Bus',
           # tessif's uid representation
           name=power_bus_uid,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    # 4.2) Demand needing 10 energy units per timestep
    es.add(class_name='Load',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Demand', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink'),
           p_set=[10, 10, 7, 10, 10]
           )

    # 4.3) Constant power supply that needs to be used
    es.add(class_name='Generator',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Variable Source', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source'),
           marginal_cost=2,
           p_nom=19, p_min_pu=[1, 1, 1, 0, 0],
           )

    # 4.4 Storage for decoupling constant supply and varying demand
    es.add(class_name='StorageUnit',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Storage', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Storage', node_type='AC-AC-Storage'),
           p_nom_extendable=True, max_hours=1,
           marginal_cost=1,
           )

    # 5.) Optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        es.lopf()

    # 6.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'pypsa', 'storage')
    else:
        d = directory

    # Make sure the write path exists.
    pathlib.Path(d).mkdir(
        parents=True,  # create parent directories if necessary
        exist_ok=True,  # directory already existing is OK
    )

    es.export_to_csv_folder(d)

    return es


def create_transformer_example(directory=None):
    """
    Create a small energy system utiulizing an electrical power transformer
    using :mod:`pypsa`.

    Optimizing it for costs.

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is stored in.
        Passed to :meth:`pypsa.Network.export_to_csv_folder`.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/pypsa/transformer will be
        the chosen  directory.


    Return
    ------
    optimized_es : :class:`~pypsa.Network`
        Energy system carrying the optimization results.

    Examples
    --------
    Using :func:`create_transformer_example` to quickly access an optimized
    pypsa  energy system to use for doctesting, or trying out this frameworks
    utilities.

    (For a step by step explanation see :ref:`Models_Pypsa_Examples_Mwe`):

    >>> # import the transformer example and optimize it:
    >>> import tessif.examples.data.pypsa.py_hard as coded_pypsa_examples
    >>> pypsa_es = coded_pypsa_examples.create_transformer_example()
    >>> for transformer in pypsa_es.transformers.index:
    ...     print(transformer)
    Transformer

    >>> # import the post processing utility:
    >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa

    >>> # use it to get the  load results:
    >>> resultier = post_process_pypsa.LoadResultier(pypsa_es)
    >>> for load in resultier.node_load.values():
    ...     print(load)
    ...     print()
    Source-380kV         380kV
    1990-07-13 00:00:00   20.0
    1990-07-13 01:00:00   20.0
    1990-07-13 02:00:00    0.0
    1990-07-13 03:00:00    0.0
    <BLANKLINE>
    Source-110kV         110kV
    1990-07-13 00:00:00    0.0
    1990-07-13 01:00:00    0.0
    1990-07-13 02:00:00   20.0
    1990-07-13 03:00:00   20.0
    <BLANKLINE>
    Demand-380kV         380kV
    1990-07-13 00:00:00  -10.0
    1990-07-13 01:00:00  -10.0
    1990-07-13 02:00:00  -10.0
    1990-07-13 03:00:00  -10.0
    <BLANKLINE>
    Demand-110kV         110kV
    1990-07-13 00:00:00  -10.0
    1990-07-13 01:00:00  -10.0
    1990-07-13 02:00:00  -10.0
    1990-07-13 03:00:00  -10.0
    <BLANKLINE>
    Transformer          110kV  380kV  110kV  380kV
    1990-07-13 00:00:00   -0.0  -10.0   10.0    0.0
    1990-07-13 01:00:00   -0.0  -10.0   10.0    0.0
    1990-07-13 02:00:00  -10.0   -0.0    0.0   10.0
    1990-07-13 03:00:00  -10.0   -0.0    0.0   10.0
    <BLANKLINE>
    380kV                Source-380kV  Transformer  Demand-380kV  Transformer
    1990-07-13 00:00:00         -20.0         -0.0          10.0         10.0
    1990-07-13 01:00:00         -20.0         -0.0          10.0         10.0
    1990-07-13 02:00:00          -0.0        -10.0          10.0          0.0
    1990-07-13 03:00:00          -0.0        -10.0          10.0          0.0
    <BLANKLINE>
    110kV                Source-110kV  Transformer  Demand-110kV  Transformer
    1990-07-13 00:00:00          -0.0        -10.0          10.0          0.0
    1990-07-13 01:00:00          -0.0        -10.0          10.0          0.0
    1990-07-13 02:00:00         -20.0         -0.0          10.0         10.0
    1990-07-13 03:00:00         -20.0         -0.0          10.0         10.0
    <BLANKLINE>

    >>> # use it to get the storage capacity and characteristic value results:
    >>> resultier = post_process_pypsa.CapacityResultier(pypsa_es)
    >>> # capacity results:
    >>> for node, capacity in resultier.node_installed_capacity.items():
    ...     print(f'{node}: {capacity}')
    380kV: None
    110kV: None
    Source-380kV: 20.0
    Source-110kV: 20.0
    Demand-380kV: 10.0
    Demand-110kV: 10.0
    Transformer: 160.0

    >>> # characteristic value results:
    >>> for node, cv in resultier.node_characteristic_value.items():
    ...     if cv is not None:
    ...         cv = round(cv, 2)
    ...     print(f'{node}: {cv}')
    380kV: None
    110kV: None
    Source-380kV: 0.5
    Source-110kV: 0.5
    Demand-380kV: 1.0
    Demand-110kV: 1.0
    Transformer: 0.06

    Visualize the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> import tessif.transform.nxgrph as nxt
    >>> grph = nxt.Graph(resultier)
    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     node_color={'Transformer': '#9999ff',
    ...                 '380kV': '#cc0033',
    ...                 '110kV': '#00ccff'},
    ...     node_size={'Transformer': 5000},
    ...     layout='neato')
    >>> # plt.show()  # commented out for simpler doctesting

    IGNORE:
    >>> title = plt.gca().set_title('Pypsa Transformer Example')
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: ../images/pypsa_transformer_example.png
        :align: center
        :alt: Image showing the storage es as a networkx graph.



    """
    # 2.) Create a simulation time frame of four timesteps of hourly resolution
    timesteps = pd.date_range('7/13/1990', periods=4, freq='H')

    # 3.) Create an energy system / network object:
    es = pypsa.Network()

    # 3.1) enforce the number of timesteps
    es.set_snapshots(timesteps)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using component attributes to store location (latt/long) region,
    # carrier and sector categorization as all pypsa simulations do in this
    # framework)

    power_bus_uid_380kv = nts.Uid(
        name='380kV', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus-380kV')

    # 4.1) 380kV bus
    es.add(class_name='Bus',
           # tessif's uid representation
           name=power_bus_uid_380kv,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    power_bus_uid_110kv = nts.Uid(
        name='110kV', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus-110kV')

    # 4.2) 110kV bus
    es.add(class_name='Bus',
           # tessif's uid representation
           name=power_bus_uid_110kv,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    # 4.2) Demand needing 10 energy units per timestep at 380kV
    es.add(class_name='Load',
           bus=str(power_bus_uid_380kv),
           name=nts.Uid(
               name='Demand-380kV', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink-110kV'),
           p_set=10
           )

    # 4.2) Demand needing 10 energy units per timestep at 110kV
    es.add(class_name='Load',
           bus=str(power_bus_uid_110kv),
           name=nts.Uid(
               name='Demand-110kV', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink-110kV'),
           p_set=10
           )

    # 4.3) Power supply at 380kV
    es.add(class_name='Generator',
           bus=str(power_bus_uid_380kv),
           name=nts.Uid(
               name='Source-380kV', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source-110kV'),
           marginal_cost=1,
           p_nom=20, p_max_pu=[1, 1, 0, 0],
           )

    # 4.3) Power supply at 110kV
    es.add(class_name='Generator',
           bus=str(power_bus_uid_110kv),
           name=nts.Uid(
               name='Source-110kV', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source-110kV'),
           marginal_cost=1,
           p_nom=20, p_max_pu=[0, 0, 1, 1],
           )

    es.add(class_name='Transformer',
           bus0=str(power_bus_uid_380kv),
           bus1=str(power_bus_uid_110kv),
           type='160 MVA 380/110 kV',
           name=nts.Uid(
               name='Transformer', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Connector', node_type='AC-Source-380kV'),
           )

# 5.) Optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        es.lopf()

    # 6.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'pypsa', 'transformer')
    else:
        d = directory

    # Make sure the write path exists.
    pathlib.Path(d).mkdir(
        parents=True,  # create parent directories if necessary
        exist_ok=True,  # directory already existing is OK
    )

    es.export_to_csv_folder(d)

    return es


def create_chp_example(directory=None):
    r"""
    Create a combined heat and power example using :mod:`pypsa`.

    Creates a simple energy system simulation to potentially
    store it on disc in :paramref:`~create_mwe.directory`.

    Warning
    -------
    For :mod:`tessif's post processing <tessif.transform.es2mapping.ppsa>` to
    work as intended a pypsa link intendend to be used as a
    :class:`~tessif.model.components.Transformer` some default behaviour has
    to be overriden. Refer to the source code of this example as well as
    the `pypsa chp example
    <https://www.pypsa.org/examples/chp-fixed-heat-power-ratio.html>`_

    Parameters
    ----------
    directory : str, default=None
        String representing of the path the created energy system is stored in.
        Passed to :meth:`pypsa.Network.export_to_csv_folder`.

        If set to ``None`` (default)
        :attr:`tessif.frused.paths.write_dir`/pypsa/chp will be the chosen
        directory.


    Return
    ------
    optimized_es : :class:`~pypsa.Network`
        Energy system carrying the optimization results.

    Examples
    --------
    Using :func:`create_chp` to quickly access a tessif energy system
    to use for doctesting, or trying out this frameworks utilities.

    (For a step by step explanation see :ref:`Models_Pypsa_Examples_Mwe`):

    >>> import tessif.examples.data.pypsa.py_hard as pypsa_coded_examples
    >>> import sys
    >>> pypsa_es = pypsa_coded_examples.create_chp_example()

    Do some post processing and show the results:

    >>> import tessif.transform.es2mapping.ppsa as post_process_pypsa
    >>> resultier = post_process_pypsa.LoadResultier(pypsa_es)

    >>> print(resultier.node_load['CHP'])
    CHP                  Gas Grid  Heat Grid  Power Line
    1990-07-13 00:00:00     -20.0       10.0         6.0
    1990-07-13 01:00:00     -20.0       10.0         6.0

    >>> print(resultier.node_load['Heat Grid'])
    Heat Grid            Backup Heat   CHP  Heat Demand
    1990-07-13 00:00:00         -0.0 -10.0         10.0
    1990-07-13 01:00:00         -0.0 -10.0         10.0

    >>> print(resultier.node_load['Power Line'])
    Power Line           Backup Power  CHP  Power Demand
    1990-07-13 00:00:00          -4.0 -6.0          10.0
    1990-07-13 01:00:00          -4.0 -6.0          10.0

    Generate a visual representation of the energy system:

    >>> import matplotlib.pyplot as plt 
    >>> import tessif.visualize.nxgrph as nxv
    >>> import tessif.transform.nxgrph as nxt

    >>> grph = nxt.Graph(resultier)
    >>> formatier = post_process_pypsa.NodeFormatier(pypsa_es, cgrp='name')

    >>> drawing_data = nxv.draw_graph(
    ...     grph,
    ...     formatier=formatier,
    ...     node_size={'CHP': 5000},
    ... )
    >>> # plt.show()  # commented out for simpler doctesting

    IGNORE:
    >>> title = plt.gca().set_title('Pypsa CHP Example')
    >>> plt.draw()
    >>> plt.pause(4)
    >>> plt.close('all')

    IGNORE

    .. image:: ../images/pypsa_chp_example.png
        :align: center
        :alt: Image showing the chp es as a networkx graph.


    """

    # 2.) Create a simulation time frame of 2 timesteps
    # pypsa is not designed to handle any form of real-time.
    # It assumes hourly resolution and only cares about the number of steps.
    # Until now however, no drawback in using a pandas.date_range was detected

    # timesteps = range(2)
    timesteps = pd.date_range('7/13/1990', periods=2, freq='H')

    # 3.) Create an energy system / network object:
    # First tell PyPSA that links will have a 2nd bus by
    # overriding the component_attrs. This can be done for
    # as many buses as you need with format busi for i = 2,3,4,5,....

    override_component_attrs = pypsa.descriptors.Dict(
        {k: v.copy() for k, v in pypsa.components.component_attrs.items()})

    # expand the link component into a 2 outputs chp using the appropriate hook
    override_component_attrs.update(
        **pypsa_hooks.extend_number_of_link_interfaces(
            override_component_attrs,
            additional_interfaces=1
        )
    )

    es = pypsa.Network(override_component_attrs=override_component_attrs)

    # 3.1) enforce the number of timesteps
    es.set_snapshots(timesteps)

    # 4.) Create nodes for a simple energy system
    # feeding a demand with conventional source and a renewable source
    # (Using component attributes to store location (latt/long) region,
    # carrier and sector categorization as all pypsa simulations do in this
    # framework)

    power_bus_uid = nts.Uid(
        name='Power Line', latitude=53, longitude=10,
        region='Germany', sector='Power', carrier='Electricity',
        component='Bus', node_type='AC-Bus')

    # 4.1) Ideal power line
    es.add(class_name='Bus',
           # tessif's uid representation
           name=power_bus_uid,
           # pypsa's representation:
           x=10, y=53, carrier='AC'
           )

    # 4.2) Power demand needing 10 energy units per timestep
    es.add(class_name='Load',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Power Demand', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Sink', node_type='AC-Sink'),
           p_set=10,
           )

    # 4.3) Back up power source, more expensive
    es.add(class_name='Generator',
           bus=str(power_bus_uid),
           name=nts.Uid(
               name='Backup Power', latitude=53, longitude=10,
               region='Germany', sector='Power', carrier='Electricity',
               component='Source', node_type='AC-Source'),
           p_nom=10, marginal_cost=10
           )

    # 4.4) Ideal gas grid
    gas_bus_uid = nts.Uid(
        name='Gas Grid', latitude=53, longitude=10,
        region='Germany', sector='Coupled', carrier='Gas',
        component='Bus', node_type='Gas-Grid')

    es.add(class_name='Bus',
           # tessif's uid representation
           name=gas_bus_uid,
           # pypsa's representation:
           x=10, y=53, carrier='Gas',
           )

    es.add(class_name='Generator',
           bus=str(gas_bus_uid),
           name=nts.Uid(
               name='Gas Source', latitude=53, longitude=10,
               region='Germany', sector='Coupled', carrier='Gas',
               component='Source', node_type='AC-Source'),
           p_nom_extendable=True, marginal_cost=0, carrier='Gas',
           )

    # 4.5) Ideal heat grid
    heat_bus_uid = nts.Uid(
        name='Heat Grid', latitude=53, longitude=10,
        region='Germany', sector='Heat', carrier='Hot Water',
        component='Bus', node_type='AC-Bus')

    es.add(class_name='Bus',
           # tessif's uid representation
           name=heat_bus_uid,
           # pypsa's representation:
           x=10, y=53, carrier='Hot Water'
           )

    # 4.6) Heat demand needing 10 energy units per timestep
    es.add(class_name='Load',
           bus=str(heat_bus_uid),
           name=nts.Uid(
               name='Heat Demand', latitude=53, longitude=10,
               region='Germany', sector='Heat', carrier='Hot Water',
               component='Sink', node_type='Heat Sink'),
           p_set=10,
           )

    # 4.6) Back up heat souce, more expensive
    es.add(class_name='Generator',
           bus=str(heat_bus_uid),
           name=nts.Uid(
               name='Backup Heat', latitude=53, longitude=10,
               region='Germany', sector='Heat', carrier='Hot Water',
               component='Source', node_type='Heat Source'),
           p_nom=10, marginal_cost=10
           )

    # 4.6) Pypsa CHP
    es.add(class_name='Link',
           bus0=str(gas_bus_uid),
           bus1=str(power_bus_uid),
           bus2=str(heat_bus_uid),
           name=nts.Uid(
               name='CHP', latitude=53, longitude=10,
               region='Germany', sector='Coupled', carrier='gas',
               component='Transformer', node_type='CHP'),
           efficiency=0.3,  # power efficiency
           efficiency2=0.5,  # heat efficiency
           p_nom_extendable=True, marginal_cost=0,
           mutliple_inputs=False,
           multiple_outputs=True)

    # 5.) Optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        es.lopf()

    # 6.) Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'pypsa', 'mwe')
    else:
        d = directory

    # Make sure the write path exists.
    pathlib.Path(d).mkdir(
        parents=True,  # create parent directories if necessary
        exist_ok=True,  # directory already existing is OK
    )

    es.export_to_csv_folder(d)

    return es


def create_component_scenario(expansion_problem=False, periods=3,
                              directory=None):
    """
        Create a model of a generic component based energy system using :mod:`pypsa`.

        Parameters
        ----------
        expansion_problem : bool, default=False
            Boolean which states whether a commitment problem (False)
            or expansion problem (True) is to be solved

        periods : int, default=3
            Number of time steps of the evaluated timeframe
            (one time step is one hour)

        directory : str, default=None
            String representing of the path the created energy system is stored in.
            Passed to :meth:`pypsa.Network.export_to_csv_folder`.

            If set to ``None`` (default)
            :attr:`tessif.frused.paths.write_dir`/pypsa/component will be the chosen
            directory.


        Return
        ------
        optimized_es : :class:`~pypsa.Network`
            Energy system carrying the optimization results.

        Examples
        --------
        Using :func:`create_component_scenario` to quickly access a pypsa energy system
        to use for doctesting, or trying out this frameworks utilities.

        (For a step by step explanation see :ref:`Models_Pypsa_Examples_Mwe`):

        >>> import tessif.examples.data.pypsa.py_hard as pypsa_coded_examples
        >>> pypsa_es = pypsa_coded_examples.create_component_scenario()
        """

    # Create a simulation time frame
    timesteps = pd.date_range('1/1/2019', periods=periods, freq='H')

    # First tell PyPSA that links will have a 2nd bus by
    # overriding the component_attrs. This can be done for
    #     # as many buses as you need with format busi for i = 2,3,4,5,....
    override_component_attrs = pypsa.descriptors.Dict(
        {k: v.copy() for k, v in pypsa.components.component_attrs.items()})
    override_component_attrs["Link"].loc["bus2"] = [
        "string", np.nan, np.nan, "2nd bus", "Input (optional)"]
    override_component_attrs["Link"].loc["efficiency2"] = [
        "static or series", "per unit", 1., "2nd bus efficiency",
        "Input (optional)"]
    override_component_attrs["Link"].loc["p_nom2"] = [
        "float", "MVA", 0., "2nd p_nom",
        "Input (optional)"]
    override_component_attrs["Link"].loc["p2"] = [
        "series", "MW", 0., "2nd bus output", "Output"]

    # Adding multiple_inputs and multiple_outputs attributes, so post
    # processing works as intended
    override_component_attrs["Link"].loc["multiple_inputs"] = [
        "bool", np.nan, False, "Link uses multiple inputs", "Input (optional)"]
    override_component_attrs["Link"].loc["multiple_outputs"] = [
        "bool", np.nan, False, "Link uses multiple outputs", "Input (optional)"]
    # Using a link as a single input single output transformer
    override_component_attrs["Link"].loc["siso_transformer"] = [
        "bool", np.nan, False,
        "Link is used as single input, single output transformer",
        "Input (optional)"]

    es = pypsa.Network(override_component_attrs=override_component_attrs)

    es.set_snapshots(timesteps)

    # create emission constraint based on the scenario (commitment or expansion)
    # Emission constraint ist choosen to enforce expansion for periods=8760
    if not expansion_problem:
        es.add(class_name='GlobalConstraint',
               name="co2_limit",
               sense="<=",
               constant=float('+inf')
               )
    else:
        es.add(class_name='GlobalConstraint',
               name="co2_limit",
               sense="<=",
               constant=250000
               )

    # create all needed busses
    es.add("Bus", "power_bus", carrier='electricity')
    es.add("Bus", "heat_bus", carrier='heat')
    es.add("Bus", "biogas_bus", )
    es.add("Bus", "hard_coal_bus", )

    # create all needed carriers
    es.add("Carrier", "electricity", )
    es.add("Carrier", "heat", )
    es.add("Carrier", "carrier_wind_onshore", co2_emissions=0.02)
    es.add("Carrier", "carrier_wind_offshore", co2_emissions=0.02)
    es.add("Carrier", "carrier_solar", co2_emissions=0.05)

    # emissions need to be multplied by efficencies for proper calculation
    es.add("Carrier", "carrier_hard_coal_pp", co2_emissions=0.8 * 0.43)
    es.add("Carrier", "carrier_hard_coal_chp",
           co2_emissions=0.8 * 0.4 + 0.06 * 0.4)
    es.add("Carrier", "carrier_lignite", co2_emissions=1 * 0.4)
    es.add("Carrier", "carrier_biogas",
           co2_emissions=0.25 * 0.4 + 0.01875 * 0.5)
    es.add("Carrier", "carrier_gas", co2_emissions=0.35 * 0.6)
    es.add("Carrier", "carrier_gas_heat", co2_emissions=0.23 * 0.9)

    es.add("Carrier", "carrier_p2h", co2_emissions=0.0007 * 0.99)
    # PyPSA calulates emissions only using storages and generators forcing this p2h carrier to be useless

    es.add("Carrier", "carrier_battery_el", co2_emissions=0.06)
    # PyPSA calculates Storage Emissions way different than Tessif.
    # Not over the flow but the initial and final SOC like:  ( in_soc - fin_soc ) * emi
    # this making emissions negativ in case fin_soc > in_soc

    # create loads
    csv_data = pd.read_csv(os.path.join(example_dir, 'data', 'tsf', 'load_profiles',
                                        'component_scenario_profiles.csv'), index_col=0, sep=';')

    # electricity demand:
    el_demand = csv_data['el_demand'].values.flatten()[0:periods]

    es.add('Load',
           'El Demand',
           bus='power_bus', p_set=el_demand)

    # heat demand:
    th_demand = csv_data['th_demand'].values.flatten()[0:periods]

    es.add('Load',
           'Heat Demand',
           bus='heat_bus', p_set=th_demand)

    # create generator
    # renewables:
    series_pv = csv_data['pv'].values.flatten()[0:periods]

    es.add('Generator',
           'PV',
           bus='power_bus',
           carrier='carrier_solar',
           p_nom=1100, p_nom_min=1100, p_nom_extendable=expansion_problem, capital_cost=1000000,
           p_min_pu=0, p_max_pu=series_pv, marginal_cost=80
           )

    series_wind_onshore = csv_data['wind_on'].values.flatten()[0:periods]

    es.add('Generator',
           'Wind_onshore',
           bus='power_bus',
           carrier='carrier_wind_onshore',
           p_nom=1100, p_nom_min=1100, p_nom_extendable=expansion_problem, capital_cost=1750000,
           p_min_pu=0, p_max_pu=series_wind_onshore, marginal_cost=60
           )

    series_wind_offshore = csv_data['wind_off'].values.flatten()[0:periods]

    es.add('Generator',
           'Wind_offshore',
           bus='power_bus',
           carrier='carrier_wind_offshore',
           p_nom=150, p_nom_min=150, p_nom_extendable=expansion_problem, capital_cost=3900000,
           p_min_pu=0, p_max_pu=series_wind_offshore, marginal_cost=105
           )

    # fossil:
    es.add('Generator',
           'lignite_pp',
           bus='power_bus', carrier='carrier_lignite',
           p_nom=500, marginal_cost=65, efficiency=0.4,
           p_nom_min=500, p_nom_extendable=expansion_problem, capital_cost=1900000, )

    es.add('Generator',
           'gas_pp',
           bus='power_bus', carrier='carrier_gas',
           p_nom=600, marginal_cost=90, efficiency=0.6,
           p_nom_min=600, p_nom_extendable=expansion_problem, capital_cost=950000, )

    es.add('Generator',
           'heat_plant',
           bus='heat_bus', carrier='carrier_gas_heat',
           p_nom=450, marginal_cost=35, efficiency=0.9,
           p_nom_min=450, p_nom_extendable=expansion_problem, capital_cost=390000,)

    es.add('Generator',
           'hard_coal_pp',
           bus='power_bus', carrier='carrier_hard_coal_pp',
           p_nom=500, marginal_cost=80, efficiency=0.43,
           p_nom_min=500, p_nom_extendable=expansion_problem, capital_cost=1650000,)

    # create links with their supplies
    es.add('Generator',
           'hard_coal_source',
           bus='hard_coal_bus', carrier='carrier_hard_coal_chp',
           p_nom=0, p_nom_min=0, p_nom_max=float('inf'),
           p_nom_extendable=True, capital_cost=0,
           )
    es.add("Link",
           "hard_coal_chp",
           bus0="hard_coal_bus", bus1="power_bus", bus2="heat_bus",
           efficiency=0.4, efficiency2=0.4, p_nom=300 / 0.4, p_nom2=300 / 0.4, marginal_cost=80 * 0.4 + 6 * 0.4,
           p_nom_min=300 / 0.4, p_nom_extendable=expansion_problem, capital_cost=1750000 * 0.4 + 131250 * 0.4,
           multiple_inputs=False, multiple_outputs=True
           )

    es.add('Generator',
           'biogas_source',
           bus='biogas_bus', carrier='carrier_biogas',
           p_nom=0, p_nom_min=0, p_nom_max=float('inf'),
           p_nom_extendable=True, capital_cost=0,
           )
    es.add("Link",
           "biogas_chp",
           bus0="biogas_bus", bus1="power_bus", bus2="heat_bus",
           efficiency=0.4, efficiency2=0.5, p_nom=200 / 0.4, p_nom2=250 / 0.5, marginal_cost=150 * 0.4 + 11.25 * 0.5,
           p_nom_min=200 / 0.4, p_nom_extendable=expansion_problem, capital_cost=3500000 * 0.4 + 262500 * 0.5,
           multiple_inputs=False, multiple_outputs=True
           )

    es.add("Link",
           "power_to_heat",
           bus0="power_bus", bus1="heat_bus", carrier='carrier_p2h',
           efficiency=0.99, p_nom=100 / 0.99, marginal_cost=20 * 0.99, siso_transformer=True,
           p_nom_min=100 / 0.99, p_nom_extendable=expansion_problem, capital_cost=100000 * 0.99
           )

    # create storage units
    es.add("StorageUnit",
           'Battery',
           bus='power_bus',  carrier='carrier_battery_el',
           p_nom=100, p_min_pu=-0.33, p_max_pu=0.33, marginal_cost=400,
           p_nom_min=100, p_nom_extendable=expansion_problem, capital_cost=1630000,
           standing_loss=0.005, efficiency_store=0.95, efficiency_dispatch=0.95
           )

    es.add("StorageUnit",
           'Heat_Storage',
           bus='heat_bus', p_nom=50, p_min_pu=-0.2, p_max_pu=0.2, marginal_cost=20,
           p_nom_min=50, p_nom_extendable=expansion_problem, capital_cost=4500,
           standing_loss=0.005, efficiency_store=0.95, efficiency_dispatch=0.95
           )

    # optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        es.lopf(es.snapshots, pyomo=True, solver_name='cbc')

    # Store result pumped energy system:
    # Set default diretory if necessary
    if not directory:
        d = os.path.join(write_dir, 'pypsa', 'emission_objective')
    else:
        d = directory

    # Make sure the write path exists.
    pathlib.Path(d).mkdir(
        parents=True,  # create parent directories if necessary
        exist_ok=True,  # directory already existing is OK
    )

    es.export_to_csv_folder(d)

    return es
