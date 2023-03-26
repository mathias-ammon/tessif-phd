# tessif/model/energy_system.py
"""
:mod:`~tessif.model.energy_system` is a :mod:`tessif` module
transforming the abstract data representation of an energy system stored as
`mapping
<https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`_ into
an actual object. This object in turn can than very conveniently be transformed
into other energy system models or beeing simulated using tessif's simulation
engine.

Note
----
Mapping like representations are usually returned by utilities part of the
:mod:`~tessif.parse` module.

Example
-------
Using the hardcoded :mod:`example
<tessif.examples.data.tsf.py_hard.create_fpwe>` (thoroughly explained
:ref:`here <Models_Tessif_Fpwe>`):

>>> import tessif.examples.data.tsf.py_hard as tsf_examples
>>> es = tsf_examples.create_fpwe()
>>> for node in es.nodes:
...    print(node.uid.name)
Pipeline
Powerline
Gas Station
Solar Panel
Demand
Generator
Battery
"""

import os
import pathlib
import pickle
from collections.abc import Iterable

import h5py
import networkx as nx
import numpy as np
import pandas as pd

import tessif.frused.namedtuples as nts
from tessif.frused.paths import write_dir, example_dir
import tessif.model.components as tessif_components
from tessif.transform.es2mapping.tsf import extract_parameters
from tessif.transform.mapping2es import tsf
import tessif.transform.nxgrph as nxgrph


class AbstractEnergySystem:
    """
    Aggregate tessif's abstract components into an energy system.

    Parameters
    ----------
    uid: ~collections.abc.Hashable
        Hashable unique identifier. Usually a string aka a name.
    busses: ~collections.abc.Iterable
        Iterable of :class:`~tessif.model.components.Bus`
        objects to be added to the energy system
    sinks: ~collections.abc.Iterable
        Iterable of :class:`~tessif.model.components.Sink`
        objects to be added to the energy system
    sources: ~collections.abc.Iterable
        Iterable of :class:`~tessif.model.components.Source`
        objects to be added to the energy system
    transformers: ~collections.abc.Iterable
        Iterable of
        :class:`~tessif.model.components.Transformer`
        objects to be added to the energy system
    storages: ~collections.abc.Iterable
        Iterable of
        :class:`~tessif.model.components.Storage`
        objects to be added to the energy system
    timeframe: pandas.DatetimeIndex
        Datetime index representing the evaluated timeframe. Explicitly
        stating:

            - initial datatime
              (0th element of the :class:`pandas.DatetimeIndex`)
            - number of timesteps (length of :class:`pandas.DatetimeIndex`)
            - temporal resolution (:attr:`pandas.DatetimeIndex.freq`)

        For example::

            idx = pd.DatetimeIndex(
                data=pd.date_range(
                    '2016-01-01 00:00:00', periods=11, freq='H'))

    global_constraints: dict, default={'emissions': float('+inf')}
        Dictionary of :class:`numeric <numbers.Number>` values mapped to
        global constraint naming :class:`strings <str>`.

        Recognized constraint keys are:

            - ``emissions``
            - ...

        For a more detailed explanation see the user guide's section:
        :ref:`Secondary_Objectives`

    """

    def __init__(self, uid, *args, **kwargs):

        self._uid = uid

        kwargs_and_defaults = {
            'busses': (),
            'chps': (),
            'connectors': (),
            'sinks': (),
            'sources': (),
            'transformers': (),
            'storages': (),
            'timeframe': pd.Series(),
            'global_constraints': {'emissions': float('+inf')}}

        for kwarg, default in kwargs_and_defaults.copy().items():

            # overwrite default if user provided key word argument:
            kwargs_and_defaults[kwarg] = kwargs.get(kwarg, default)

            # initialize instance respective instance attribute:
            if kwarg == 'global_constraints':
                setattr(self, '_{}'.format(kwarg), kwargs_and_defaults[kwarg])

            elif kwarg != 'timeframe':
                setattr(self, '_{}'.format(kwarg),
                        tuple(kwargs_and_defaults[kwarg]))
            else:
                self._timeframe = kwargs_and_defaults[kwarg]

        self._es_attributes = tuple(kwargs_and_defaults.keys())

    def __repr__(self):
        return '{!s}({!r})'.format(self.__class__, self.__dict__)

    def __str__(self):
        return '{!s}(\n'.format(self.__class__) + ',\n'.join([
            *['    {!r}={!r}'.format(
                k.lstrip('_'), v) for k, v in self.__dict__.items()],
            ')'
        ])

    @property
    def uid(self):
        """:class:`~collections.abc.Hashable` unique identifier. Usually a
        string aka a name.
        """
        return self._uid

    @property
    def busses(self):
        """:class:`~collections.abc.Generator` of
        :class:`~tessif.model.components.Bus` objects part
        of the energy system.
        """
        for bus in self._busses:
            yield bus

    @property
    def chps(self):
        """:class:`~collections.abc.Generator` of
        :class:`~tessif.model.components.CHP`
        objects part of the energy system.
        """
        for chp in self._chps:
            yield chp

    @property
    def connectors(self):
        """ :class:`~collections.abc.Generator` of
        :class:`~tessif.model.components.Connectors` objects part
        of the energy system.
        """

        for connector in self._connectors:
            yield connector

    @property
    def sources(self):
        """:class:`~collections.abc.Generator` of
        :class:`~tessif.model.components.Source` objects
        part of the energy system.
        """
        for source in self._sources:
            yield source

    @property
    def sinks(self):
        """:class:`~collections.abc.Generator` of
        :class:`~tessif.model.components.Sink` objects part
        of the energy system.
        """
        for sink in self._sinks:
            yield sink

    @property
    def transformers(self):
        """:class:`~collections.abc.Generator` of
        :class:`~tessif.model.components.Transformer`
        objects part of the energy system.
        """
        for transformer in self._transformers:
            yield transformer

    @property
    def storages(self):
        """:class:`~collections.abc.Generator` of
        :class:`~tessif.model.components.Storage` objects
        part of the energy system.
        """
        for storage in self._storages:
            yield storage

    @property
    def nodes(self):
        """
        :class:`~collections.abc.Generator` yielding this energy system's
        components.
        """

        component_types = ['busses', 'chps', 'sources',
                           'sinks', 'transformers', 'storages',
                           'connectors']

        for component_type in component_types:
            for component in getattr(self, component_type):
                yield component

    @property
    def edges(self):
        """:class:`~collections.abc.Generator` of
        :class:`~tessif.frused.namedtuples.Edge`
        :class:`NamedTuples<typing.Namedtuple>` representing graph like `edges
        <https://en.wikipedia.org/wiki/Glossary_of_graph_theory_terms#edge>`_.
        """
        # All edge information are stored inside the bus objects..
        for bus in self.busses:
            # Bus incoming edge should contain node.uid and bus.uid:
            for inflow in bus.inputs:
                # so find out node uid by string comparison with
                # every single node:
                for node in self.nodes:
                    if inflow.split('.')[0] == node.uid.name:
                        edge = nts.Edge(str(node.uid), str(bus.uid))
                        yield edge

            # Bus leaving edges should contain bus.uid and node.uid:
            for outflow in bus.outputs:
                # so find out node uid by string comparison with
                # every single node:
                for node in self.nodes:
                    if outflow.split('.')[0] == node.uid.name:
                        edge = nts.Edge(str(bus.uid), str(node.uid))
                        yield edge

        # ... except for the edges build by the connectors
        for connector in self.connectors:
            for inflow in connector.inputs:
                edge = nts.Edge(inflow, str(connector.uid))
                yield edge

            for outflow in connector.outputs:
                edge = nts.Edge(str(connector.uid), outflow)
                yield edge

    @property
    def global_constraints(self):
        """
        :class:`Dictionary <dict>` of :class:`numeric <numbers.Number>`
        values mapped to global constraint naming :class:`strings <str>`
        currently respected by the energy system.
        """
        return self._global_constraints

    def _edge_carriers(self):
        """
        Extract carrier information out of busses and connectors.
        """
        _ecarriers = {}
        # All edge information are stored inside the bus objects
        for bus in self.busses:
            # Bus incoming edge should contain node.uid and bus.uid:
            for inflow in bus.inputs:
                # so find out node uid by string comparison with
                # every single node:
                for node in self.nodes:
                    if inflow.split('.')[0] == node.uid.name:
                        edge = nts.Edge(str(node.uid), str(bus.uid))
                        _ecarriers[edge] = inflow.split('.')[1]

            # Bus leaving edges should contain bus.uid and node.uid:
            for outflow in bus.outputs:
                # so find out node uid by string comparison with
                # every single node:
                for node in self.nodes:
                    if outflow.split('.')[0] == node.uid.name:
                        edge = nts.Edge(str(bus.uid), str(node.uid))
                        _ecarriers[edge] = inflow.split('.')[1]

        for connector in self.connectors:
            for inflow in connector.inputs:
                for bus in self.busses:
                    if inflow == str(bus.uid):
                        edge = nts.Edge(inflow, str(connector.uid))
                        _ecarriers[edge] = list(bus.outputs)[0].split('.')[1]

            for outflow in connector.outputs:
                for bus in self.busses:
                    if outflow == str(bus.uid):
                        edge = nts.Edge(str(connector.uid), outflow)
                        _ecarriers[edge] = list(bus.inputs)[0].split('.')[1]

        return _ecarriers

    @property
    def timeframe(self):
        return self._timeframe

    def connect(self, energy_system, connecting_busses, connection_uid):
        """
        Connect another :class:`AbstractEnergySystem` object to this one.

        Parameters
        ----------
        energy_system: tessif.model.energy_system.AbstractEnergySystem
            Energy system object to be connected to this energy system via the
            respective :paramref:`~connect_energy_systems.connecting_busses`.

            The :paramref:`energy_system's <connect.energy_system>`
            :class:`~tessif.model.components.Bus` specified in
            :paramref:`connecting_busses[1] <connect.connecting_busses>` will
            be connected to this energy system's
            :class:`~tessif.model.components.Bus` specified in
            :paramref:`connecting_busses[0] <connect.connecting_busses>`. So
            it's :attr:`~tessif.model.components.AbstractEsComponent.uid`
            must be found in this energy system.

        connecting_busses: ~collections.abc.tuple
            Tuple of :attr:`Uids <tessif.frused.namedtuples.Uid>` string
            representation specifying the busses with which the energy systems
            will be connected.

            The :paramref:`energy_system's <connect.energy_system>`
            :class:`~tessif.model.components.Bus` specified in
            :paramref:`connecting_busses[1] <connect.connecting_busses>` will
            be connected to this energy system's
            :class:`~tessif.model.components.Bus` specified in
            :paramref:`connecting_busses[0] <connect.connecting_busses>`.

        connection_uid: tessif.frused.namedtuples.Uid
            Uid of the :class:`~tessif.model.components.Connector` object
            created for connecting the energy system.


        Return
        ------
        tessif.model.energy_system.AbstractEnergySystem
            The energy system created by connecting the
            :paramref:`~connect.energy_system` to this energy system.

        Example
        -------
        Connect instances of hard coded tessif energy systems:

            0. Setting spellings.get_from's logging level to debug for
               decluttering doctest output:

            >>> from tessif.frused import configurations
            >>> configurations.spellings_logging_level = 'debug'

            1. Create the energy systems:

            >>> import tessif.examples.data.tsf.py_hard as coded_examples
            >>> mwe = coded_examples.create_mwe()
            >>> mssesu = coded_examples._create_minimal_es_unit(0, seed=42)

            2. Connect the energy systems:

            >>> from tessif.frused.namedtuples import Uid
            >>> ces = mwe.connect(
            ...     energy_system=mssesu,
            ...     connecting_busses=('Powerline', 'Central Bus 0'),
            ...     connection_uid=Uid(name='connector'))

            3. Transform the connected energy system to e.g omeof to see
               if the connection holds:

            >>> from tessif.transform.es2es.omf import transform
            >>> oemof_es = transform(ces)
            >>> for node in oemof_es.nodes:
            ...     if str(node.label) == 'connector':
            ...         print(node)
            connector

            4. Perform a simulation to check if es is optimizable:

            >>> import tessif.simulate as simulate
            >>> optimized_oemof_es = simulate.omf_from_es(oemof_es)

            5. Show some results:

            >>> import tessif.transform.es2mapping.omf as oemof_results
            >>> resultier = oemof_results.LoadResultier(optimized_oemof_es)
            >>> print(resultier.node_load['Powerline'])
            Powerline            Battery  Generator  connector  Battery  Demand  connector
            1990-07-13 00:00:00    -10.0      -73.0       -0.0      0.0    10.0       73.0
            1990-07-13 01:00:00     -0.0      -84.0       -0.0      0.0    10.0       74.0
            1990-07-13 02:00:00     -0.0      -84.0       -0.0      0.0    10.0       74.0
            1990-07-13 03:00:00     -0.0      -84.0       -0.0      0.0    10.0       74.0

            >>> print(resultier.node_load['Central Bus 0'])
            Central Bus 0        Excess Source 0  Power Generator 0  Renewable Source 0  Storage 0  connector  Excess Sink 0  Sink 0  Storage 0  connector
            1990-07-13 00:00:00             -0.0               -0.0                -8.0       -1.0      -73.0            0.0    82.0        0.0        0.0
            1990-07-13 01:00:00             -0.0               -0.0                -8.0       -0.0      -74.0            0.0    82.0        0.0        0.0
            1990-07-13 02:00:00             -0.0               -0.0                -8.0       -0.0      -74.0            0.0    82.0        0.0        0.0
            1990-07-13 03:00:00             -0.0               -0.0                -8.0       -0.0      -74.0            0.0    82.0        0.0        0.0

            6. Plot the energy system for better understanding the defaults:

            >>> import matplotlib.pyplot as plt
            >>> import tessif.visualize.nxgrph as nxv
            >>> grph = ces.to_nxgrph()
            >>> drawing_data = nxv.draw_graph(
            ...     grph,
            ...     node_color={'connector': '#9999ff',
            ...                 'Powerline': '#cc0033',
            ...                 'central_bus_0': '#00ccff'},
            ...     node_size={'connector': 5000},
            ...     edge_color='pink',
            ...     layout='neato')
            >>> # plt.show()  # commented out for better doctesting

            IGNORE:
            >>> title = plt.gca().set_title('connected_es example')
            >>> plt.draw()
            >>> plt.pause(4)
            >>> plt.close('all')

            IGNORE

            .. image:: images/connect_example.png
                :align: center
                :alt: Image showing the connected es.
        """

        components_to_add = list()

        for component in energy_system.nodes:
            # is current component to be connected ?
            if not str(component.uid) == connecting_busses[1]:
                # no, so just prepare it for adding to the new es
                components_to_add.append(component)
            else:
                # yes it's to be connected, so create a connector:
                connector = tessif_components.Connector(
                    **connection_uid._asdict(),
                    interfaces=(connecting_busses[0],
                                connecting_busses[1]))

                components_to_add.append(connector)
                components_to_add.append(component)

        connected_es = self.from_components(
            uid=self.uid,
            timeframe=self.timeframe,
            global_constraints=self.global_constraints,
            components=set([*self.nodes, *components_to_add]))

        return connected_es

    def dump(self, directory=None, filename=None):
        """
        Store (dump) the energy system into ``directory.filename``.

        Parameters
        ----------
        directory : str, default=None
            Path the created energy system is dumped to.
            Passed to :meth:`pickle.dump`.

            Will be :func:`joined <os.path.join>` with
            :paramref:`~dump.filename`. To create an `absolute path
            <https://docs.python.org/3.8/library/os.path.html#os.path.abspath>`_.

            If set to ``None`` (default)
            :attr:`tessif.frused.paths.write_dir`/tsf will be the chosen
            directory.
        filename : str, default=None
            :func:`~pickle.dump` the energy system using this name.

            If set to ``None`` (default) filename will be
            ``energy_system.tsf``.

        Example
        -------
        Using the :attr:`hardcoded fully parameterized example
        <tessif.examples.data.tsf.py_hard.create_fpwe>`

        >>> import tessif.examples.data.tsf.py_hard as tsf_examples
        >>> es = tsf_examples.create_fpwe()
        >>> msg = es.dump()

        Default storage location (relative to tessif's :attr:`root directory
        <tessif.frused.paths.root_dir>`):

        >>> print("Stored Tessif Energy System to", os.path.join(
        ...    'tessif', *msg.split('tessif')[-1].split(os.path.sep)))
        Stored Tessif Energy System to tessif/write/tsf/energy_system.tsf
        """
        # Set default directory if necessary
        if not directory:
            d = os.path.join(write_dir, 'tsf')
        else:
            d = directory

        # create output directory if necessary
        pathlib.Path(os.path.abspath(d)).mkdir(
            parents=True, exist_ok=True)

        # Set default filename if necessary, using the isoformat
        if not filename:
            f = 'energy_system.tsf'
        else:
            f = filename

        pickle.dump(self.__dict__, open(os.path.join(d, f), 'wb'))

        msg = 'Stored Tessif Energy System in {}'.format(
            os.path.join(d, f))

        return msg

    def duplicate(self, prefix='', separator='_', suffix='copy'):
        """
        Duplicate the energy system and return it. Potentially modify
        the node names.

        Parameters
        ----------
        prefix: str, default=''
           String added to the beginning of every node's :attr:`Uid.name
           <tessif.frused.namedtuples.Uid>`, separated by
           :paramref:`~duplicate.seperator`.

        separator: str, default='_'
           String used for adding the :paramref:`~duplicate.prefix` and the
           :paramref:`~duplicate.suffix` to every node's :attr:`Uid.name
           <tessif.frused.namedtuples.Uid>`.

        suffix: str, default=''
           String added to the beginning of every node's :attr:`Uid.name
           <tessif.frused.namedtuples.Uid>`, separated by
           :paramref:`~duplicate.seperator`.
        """
        duplicated_nodes = list()
        for node in self.nodes:
            duplicated_nodes.append(node.duplicate(
                prefix=prefix,
                separator=separator,
                suffix=suffix))

        return self.from_components(
            uid=self.uid,
            components=duplicated_nodes,
            timeframe=self.timeframe,
            global_constraints=self.global_constraints)

    def to_hdf5(self, directory=None, filename=None):
        """
        Store (dump) the energy system info as a hdf5 file.

        Parameters
        ----------
        directory : str, default=None
            String representing of a path the created energy system is dumped
            to. Passed to :meth:`recursively_save_dict_contents`.

            Will be :func:`joined <os.path.join>` with
            :paramref:`~to_hdf5.filename` to create an `absolute path
            <https://docs.python.org/3.8/library/os.path.html#os.path.abspath>`_.

            If set to ``None`` (default)
            :attr:`tessif.frused.paths.write_dir`/tsf will be the chosen
            directory.
        filename : str, default=None
            Save the energy system to a hdf5 file with this name.

            If set to ``None`` (default) filename will be
            ``energy_system.hdf5``.

        Example
        -------
        Using the :attr:`hardcoded fully parameterized example
        <tessif.examples.data.tsf.py_hard.create_fpwe>`

        >>> import tessif.examples.data.tsf.py_hard as tsf_examples
        >>> es = tsf_examples.create_fpwe()
        >>> msg = es.to_hdf5()

        Default storage location (relative to tessif's :attr:`root directory
        <tessif.frused.paths.root_dir>`):

        >>> print("Stored Tessif Energy System to", os.path.join(
        ...    'tessif', *msg.split('tessif')[-1].split(os.path.sep)))
        Stored Tessif Energy System to tessif/write/tsf/energy_system.hdf5
        """
        # Set default directory if necessary
        if not directory:
            d = os.path.join(write_dir, 'tsf')
        else:
            d = directory

        # create output directory if necessary
        pathlib.Path(os.path.abspath(d)).mkdir(
            parents=True, exist_ok=True)

        # Set default filename if necessary, using the isoformat
        if not filename:
            f = 'energy_system.hdf5'
        else:
            f = filename

        # generate a mapping with the energy system parameters
        dic = extract_parameters(self)

        def recursively_save_dict_contents(h5file, path, dic):
            """
            Save each item of a dict into a group inside of a hdf5 file.

            If an item's value is of a supported type, it is saved as a
            dataset named after that item's key. If the item's value is
            a dictionary, this function calls itself to save that
            dictionary as a Group named after that item's key.
            """
            supported_types = (
                str,
                bytes,
                int,
                float,
                list)

            for key, item in dic.items():
                if isinstance(item, supported_types):
                    # Replace None with np.nan in lists, because hdf5 doesn't
                    # support None values.
                    if isinstance(item, list):
                        item = [np.nan if i is None else i for i in item]
                    # key may be a tuple, needs to be converted back when hdf5
                    # file is parsed.
                    h5file[path + str(key)] = item
                elif isinstance(item, dict):
                    recursively_save_dict_contents(
                        h5file, path + key + '/', item)
                elif item is None:
                    pass
                else:
                    raise ValueError(
                        'Cannot save %s, %s type is not supported' % (
                            item, type(item)))

        with h5py.File(os.path.join(d, f), 'w') as h5file:
            recursively_save_dict_contents(h5file, '/', dic)

        msg = 'Stored Tessif Energy System in {}'.format(
            os.path.join(d, f))

        return msg

    def to_cfg(self, directory=None):
        """
        Store (dump) the energy system info as a hdf5 file.

        Parameters
        ----------
        directory : str, Path default=None
            Path/String representation of a path the created cfg files are
            stored in.

            If set to ``None`` (default)
            :attr:`tessif.frused.paths.write_dir`/tsf/cfg will be the chosen
            directory.

            Directory created if not present.

        Example
        -------
        Using the :attr:`hardcoded fully parameterized example
        <tessif.examples.data.tsf.py_hard.create_fpwe>`

        >>> import tessif.examples.data.tsf.py_hard as tsf_examples
        >>> es = tsf_examples.create_fpwe()
        >>> msg = es.to_cfg()

        Write a little test functionality for checking if to and from conifg
        file parsing are succesfull:

        >>> from tessif.model.energy_system import AbstractEnergySystem as AES
        >>> from tessif import parse
        >>> import tempfile

        Declutter logging output:

        >>> import tessif.frused.configurations as configurations
        >>> configurations.spellings_logging_level = "debug"

        Define the mentioned helper function:

        >>> def test_to_cfg(es, folder):
        ...     es.to_cfg(folder)
        ...     parsed_es = AES.from_external(
        ...         path=folder,
        ...         parser=parse.flat_config_folder
        ...     )
        ...
        ...     for es_attr in es._es_attributes:
        ...         if es_attr == "timeframe":
        ...             assert getattr(es, es_attr).equals(
        ...                 getattr(parsed_es, es_attr))
        ...         elif es_attr == "global_constraints":
        ...             if not getattr(es, es_attr) == getattr(
        ...                     parsed_es, es_attr):
        ...                 print("original:", getattr(es, es_attr))
        ...                 print("parsed:", getattr(parsed_es, es_attr))
        ...         else:
        ...             for es_node, pes_node in zip(
        ...                     getattr(es, es_attr), getattr(es, es_attr)):
        ...                 for es_attr, pes_attr in zip(
        ...                     es_node.attributes.values(),
        ...                     pes_node.attributes.values()
        ...                 ):
        ...                     if not es_attr == pes_attr:
        ...                         print("original:", es_attr)
        ...                         print("parsed:", pes_attr)

        Utilize above function to check hardcoded examples parsing:

        >>> import tessif.examples.data.tsf.py_hard as example_module
        >>> import_aliases = [
        ...     "create_mwe",
        ...     "create_fpwe",
        ...     "emission_objective",
        ...     "create_connected_es",
        ...     "create_chp",
        ...     "create_variable_chp",
        ...     "create_storage_example",
        ...     "create_expansion_plan_example",
        ...     "create_simple_transformer_grid_es",
        ... ]
        >>> for alias in import_aliases:
        ...     energy_system = getattr(example_module, alias)()
        ...     print(energy_system.uid, "..")
        ...     with tempfile.TemporaryDirectory() as tempdir:
        ...         test_to_cfg(energy_system, folder=tempdir)
        ...     print(".. parsed succesfully!")
        Minimum_Working_Example ..
        .. parsed succesfully!
        Fully_Parameterized_Working_Example ..
        .. parsed succesfully!
        Emission_Objective_Example ..
        .. parsed succesfully!
        Connected-Energy-Systems-Example ..
        .. parsed succesfully!
        CHP_Example ..
        .. parsed succesfully!
        CHP_Example ..
        .. parsed succesfully!
        Storage-Energysystem-Example ..
        .. parsed succesfully!
        Expansion Plan Example ..
        .. parsed succesfully!
        Two Transformer Grid Example ..
        .. parsed succesfully!
        """
        # Set default directory if necessary
        if not directory:
            storage_folder = os.path.join(write_dir, "tsf", "cfg")
        else:
            storage_folder = directory

        # create output directory if necessary
        pathlib.Path(os.path.abspath(storage_folder)).mkdir(
            parents=True, exist_ok=True)

        for es_attr in self._es_attributes:

            stor_path = pathlib.Path(storage_folder) / \
                ".".join([es_attr, "cfg"])
            with open(stor_path, "w+") as io_handle:
                if es_attr == "timeframe":
                    start = self.timeframe[0].strftime('%m/%d/%Y, %H:%M:%S')
                    io_handle.writelines(
                        [
                            "[primary]\n",
                            f"start = '{start}'\n",
                            f"periods = {len(self.timeframe)}\n",
                            f"freq = '{self.timeframe.freq.name}'\n",
                        ],
                    )
                elif es_attr == "global_constraints":
                    io_handle.write(f"[primary]\n")
                    for key, value in self.global_constraints.items():
                        io_handle.write(f"{key} = '{value}'\n")

                else:
                    nodes_of_type = getattr(self.duplicate(suffix=''), es_attr)

                    for node in nodes_of_type:
                        io_handle.write(f"[{node.uid}]\n")
                        for label, attribute in node.attributes.items():

                            # modify datatypes for more agnosticism
                            if isinstance(attribute, frozenset):
                                # frozensets -> tuple
                                attribute = tuple(attribute)
                            if isinstance(attribute, (nts.Uid, str)):
                                # Uid -> str(Uid)
                                attribute = f"'{attribute}'"
                            if isinstance(attribute, dict):
                                for key, value in attribute.items():
                                    # float("inf") -> str(float("inf")) inside tuples
                                    if isinstance(value, tuple):
                                        new_tuple = []
                                        for tpl_val in value:
                                            if isinstance(tpl_val, float):
                                                if tpl_val == float('inf'):
                                                    new_tuple.append(
                                                        str(tpl_val))
                                                else:
                                                    new_tuple.append(tpl_val)
                                            elif isinstance(tpl_val, Iterable):
                                                # turn series values to tuples
                                                # new_tuple.append(
                                                #     str(tuple(tpl_val)))
                                                new_tuple.append(
                                                    tuple(tpl_val))
                                            else:
                                                new_tuple.append(tpl_val)
                                        attribute[key] = tuple(new_tuple)
                            if isinstance(attribute, tuple):
                                # float("inf") -> str(float("inf"))
                                new_tuple = []
                                for tpl_val in attribute:
                                    if tpl_val == float('inf'):
                                        new_tuple.append(f"'{tpl_val}'")
                                    else:
                                        new_tuple.append(tpl_val)
                                    attribute = tuple(new_tuple)

                            io_handle.write(f"'{label}' = {attribute}\n")
                        io_handle.write(f"\n")

    def restore(self, directory=None, filename=None):
        """
        Restore a dumped energy system ``directory.filename``.

        Parameters
        ----------
        directory : str, default=None
            Path the created energy system was dumped to.
            Passed to :meth:`pickle.restore`.

            Will be :func:`joined <os.path.join>` with
            :paramref:`~restore.filename`. To create an `absolute path
            <https://docs.python.org/3.8/library/os.path.html#os.path.abspath>`_.

            If set to ``None`` (default)
            :attr:`tessif.frused.paths.write_dir`/tsf will be the chosen
            directory.
        filename : str, default=None
            :func:`~pickle.load` the energy system using this name.

            If set to ``None`` (default) filename will be
            ``energy_system.tsf``.


        Example
        -------
        Using the :attr:`hardcoded fully parameterized example
        <tessif.examples.data.tsf.py_hard.create_fpwe>` ...

        >>> import tessif.examples.data.tsf.py_hard as tsf_examples
        >>> es = tsf_examples.create_fpwe()

        ... to dump it into Tessif's default storage location
        (relative to tessif's :attr:`root directory
        <tessif.frused.paths.root_dir>`) ...

        >>> msg = es.dump()

        ... and restore it:

        >>> msg = es.restore()

        >>> print("Restored Tessif Energy System from", os.path.join(
        ...    'tessif', *msg.split('tessif')[-1].split(os.path.sep)))
        Restored Tessif Energy System from tessif/write/tsf/energy_system.tsf


        Use Case:

        >>> from tessif.model.energy_system import AbstractEnergySystem
        >>> restored_es = AbstractEnergySystem('This Instance Is Restored')
        >>> msg = restored_es.restore()
        >>> for node in restored_es.nodes:
        ...     print(node.uid.name)
        Pipeline
        Powerline
        Gas Station
        Solar Panel
        Demand
        Generator
        Battery
        """
        # Set default directory if necessary
        if not directory:
            d = os.path.join(write_dir, 'tsf')
        else:
            d = directory

        # Set default filename if necessary, using the isoformat
        if not filename:
            f = 'energy_system.tsf'
        else:
            f = filename

        self.__dict__ = pickle.load(open(os.path.join(d, f), "rb"))

        msg = 'Restored Tessif Energy System from {}'.format(
            os.path.join(d, f))

        return msg

    @classmethod
    def from_pickle(cls, directory=None, filename=None):
        """
        Create an energy system instance from a pickle dumped binary.

        Parameters
        ----------
        directory : str, default=None
            String representing of a path the created energy system was dumped
            to. Passed to :meth:`pickle.restore`.

            Will be :func:`joined <os.path.join>` with
            :paramref:`~restore.filename`. To create an `absolute path
            <https://docs.python.org/3.8/library/os.path.html#os.path.abspath>`_.

            If set to ``None`` (default)
            :attr:`tessif.frused.paths.write_dir`/tsf will be the chosen
            directory.
        filename : str, default=None
            :func:`~pickle.load` the energy system using this name.

            If set to ``None`` (default) filename will be
            ``energy_system.tsf``

        Example
        -------
        Restoring a tessif energy system model from tessif's default location:

        >>> from tessif.model.energy_system import AbstractEnergySystem
        >>> es = AbstractEnergySystem.from_pickle()
        >>> for node in es.nodes:
        ...     print(node.uid.name)
        Pipeline
        Powerline
        Gas Station
        Solar Panel
        Demand
        Generator
        Battery

        Note
        ----
        See :meth:`dump's <AbstractEnergySystem.dump>` Example on how the
        pickled energy system got there in the first place.
        """
        # Set default directory if necessary
        if not directory:
            d = os.path.join(write_dir, 'tsf')
        else:
            d = directory

        # Set default filename if necessary, using the isoformat
        if not filename:
            f = 'energy_system.tsf'
        else:
            f = filename

        es = cls('DePickled')
        es.__dict__ = pickle.load(open(os.path.join(d, f), "rb"))

        return es

    @classmethod
    def from_external(cls, path, parser, **kwargs):
        """
        Create an energy system using a nested mapping from an external data
        source.

        Note
        ----
        For more on nested :any:`mappings <dict>` refer to tessif's concept
        section. A list of supported datatypes can be found :ref:`here
        <SupportedDataFormats>`.

        Parameters
        ----------
        path: str, ~pathlib.Path
            Path or string representation of a path specifying the location
            of the file from which the energy system is to be created.

            For a list of supported datatypes see :ref:`SupportedDataFormats`.

        parser: :class:`~collections.abc.Callable`
            Functional used to read in and parse the energy system data.
            Usually one of the module functions found in :mod:`tessif.parse`

            Use :func:`functools.partial` for supplying parameters. See also
            the Example section.

        Example
        -------
        Creating an energy system out of a folder of :ref:`flat config files
        <Examples_Tessif_Config_Flat>`:

        >>> from tessif.parse import flat_config_folder
        >>> from tessif.model.energy_system import AbstractEnergySystem
        >>> from tessif.frused.paths import example_dir
        >>> import os

        >>> es = AbstractEnergySystem.from_external(
        ...     path=os.path.join(example_dir, 'data', 'tsf',
        ...                       'cfg', 'flat', 'basic'),
        ...     parser=flat_config_folder)
        >>> print(es.uid)
        es_from_external_source

        >>> for node in es.nodes:
        ...     print(node.uid.name)
        Pipeline
        Power Line
        Air Chanel
        Gas Station
        Solar Panel
        Air
        Demand
        Generator
        Battery
        """
        es = tsf.transform(
            energy_system_mapping=parser(path),
            uid=kwargs.pop('uid', 'es_from_external_source'),
        )

        return es

    @classmethod
    def from_components(cls, uid, components, timeframe,
                        global_constraints={'emissions': float('+inf')},
                        **kwargs):
        """
        Create an energy system from a collection of component instances.

        Particularly usefull when creating energy systems out of existing ones.

        Parameters
        ----------
        uid: ~collections.abc.Hashable
            Hashable unique identifier. Usually a string aka a name.

        components: `~collections.abc.Iterable`
            Iterable of :mod:`tessif.model.components.AbstractEsComponent`
            objects the energy system will be created of.

        timeframe: pandas.DatetimeIndex, optional
            Datetime index representing the evaluated timeframe. Explicitly
            stating:

                - initial datatime
                  (0th element of the :class:`pandas.DatetimeIndex`)
                - number of timesteps (length of :class:`pandas.DatetimeIndex`)
                - temporal resolution (:attr:`pandas.DatetimeIndex.freq`)

            For example::

                idx = pd.DatetimeIndex(
                    data=pd.date_range(
                        '2016-01-01 00:00:00', periods=11, freq='H'))

        global_constraints: dict, default={'emissions': float('+inf')}
            Dictionairy of :class:`numeric <numbers.Number>` values mapped to
            global constraint naming :class:`strings <str>`.

            Recognized constraint keys are:

                - ``emissions``
                - ...

            For a more detailed explanation see the user guide's section:
            :ref:`Secondary_Objectives`

        Return
        ------
        :class:`AbstractEnergySystem`
            The newly constructed energy system containing each component
            found in :paramref:`~from_components.components`.

        Example
        -------
        1. Use a hard coded example:

        >>> import tessif.examples.data.tsf.py_hard as coded_examples
        >>> mwe = coded_examples.create_mwe()
        >>> print(mwe.uid)
        Minimum_Working_Example

        >>> for node in mwe.nodes:
        ...     print(node.uid)
        Pipeline
        Powerline
        Gas Station
        Demand
        Generator
        Battery


        2. Reconstruct the es by using the mwe:

        >>> from tessif.model.energy_system import AbstractEnergySystem
        >>> es = AbstractEnergySystem.from_components(
        ...          uid='from_components_examples',
        ...          components=mwe.nodes,
        ...          timeframe=mwe.timeframe,
        ...          global_constraints=mwe.global_constraints)

        >>> print(es.uid)
        from_components_examples

        >>> for node in es.nodes:
        ...     print(node.uid)
        Pipeline
        Powerline
        Gas Station
        Demand
        Generator
        Battery

        """
        busses, chps, sinks, sources, transformers = [], [], [], [], []
        connectors, storages = [], []

        for c in components:
            if isinstance(c, tessif_components.Bus):
                busses.append(c)
            elif isinstance(c, tessif_components.CHP):
                chps.append(c)
            elif isinstance(c, tessif_components.Sink):
                sinks.append(c)
            elif isinstance(c, tessif_components.Source):
                sources.append(c)
            elif isinstance(c, tessif_components.Transformer):
                transformers.append(c)
            elif isinstance(c, tessif_components.Connector):
                connectors.append(c)
            elif isinstance(c, tessif_components.Storage):
                storages.append(c)

        es = AbstractEnergySystem(
            uid=uid,
            busses=busses,
            chps=chps,
            sinks=sinks,
            sources=sources,
            transformers=transformers,
            connectors=connectors,
            storages=storages,
            timeframe=timeframe,
            global_constraints=global_constraints,
        )

        return es

    def to_nxgrph(self):
        """
        Transform the :class:`AbstractEnergySystem` object into a
        :class:`networkx.DiGraph` object.

        Return
        ------
        directional_graph: networkx.DiGraph
            Networkx Directional Graph representing the abstract energy system.
        """
        grph = nx.DiGraph(name=self._uid)
        for node in self.nodes:
            grph.add_node(
                str(node.uid),
                **node.attributes,
            )

        nxgrph.create_edges(grph, self.edges, carrier=self._edge_carriers())
        return grph
