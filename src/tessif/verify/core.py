# tessif/verify/core.py
"""The verify core module holds the Verificer class.

Its main access however is desinged to be via the verify __init__ moduel,
i.e. ``tessif.verify.Verificer``.
"""
from collections import defaultdict
import importlib
import logging
import matplotlib.pyplot as plt
import os

from tessif.frused import defaults
from tessif.frused.paths import example_dir
from tessif import parse
from tessif import simulate
import tessif.transform.mapping2es.tsf as tsf
import tessif.visualize.nxgrph as nxv

logger = logging.getLogger(__name__)


class Verificier:
    """
    Conveniently generate verification result data and plots for assessing
    the proper component bahavior of an energy supply system simulation model.

    Note
    ----
    This class assumes, you prepare a singular :class:`tessif energy system
    <tessif.model.energy_system.AbstractEnergySystem>` for each
    :paramref:`group of constraints <Verificier.constraints>`. It further more
    assumes that all relevant results for verification can be extracted from
    a single :class:`bus object <tessif.model.components.Bus>` carrying the
    :paramref:`~tessif.model.components.Bus.name` ``centralbus``.

    Parameters
    ----------
    path: str, Path, None, default=None
        String representing the top level folder of where the tessif energy
        systems are stored. Verificier expects a singular energy system to be
        present for each combination of :paramref:`~Verificier.components`,
        :paramref:`~Verificier.constraints` and the respected group of
        constraints (e.g. flow rates). Hence the expected folder
        structure would look like::

           /top/level/folder
           |-- source
           |   |-- expansion
           |   |   |-- costs.[hdf5/xlsx/cfg/...]
           |   |   |-- emissions.[hdf5/xlsx/cfg/...]
           |   |-- linear
           |   |   |-- flow_rates.[hdf5/xlsx/cfg/...]
           |   |   |-- gradients.[hdf5/xlsx/cfg/...]
           |   |-- milp
           |   |   |-- status.[hdf5/xlsx/cfg/...]
           |   |   |-- status_changing.[hdf5/xlsx/cfg/...]
           |-- sink
           |   |-- expansion
           |   |   |-- costs.[hdf5/xlsx/cfg/...]
           |   |   |-- emissions.[hdf5/xlsx/cfg/...]
           ...

        An example set of verification scenarios is found in the example
        directory.

        If ``None`` (default) ``application/verification`` inside
        :attr:`~tessif.frused.paths.example_dir` is used.

    model: str
        String specifying one of the
        :attr:`~tessif.frused.defaults.registered_models` representing the
        :ref:`energy system simulation model <SupportedModels>` investigated.

    parser: :class:`~collections.abc.Callable`
        Functional used to read in and parse the energy system data.
        Usually one of the module functions found in :mod:`tessif.parse`

    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used.
        One of ``'primary'``, ``'secondary'``, etc... by convention.

    components: ~collections.abc.Iterable, optional
        Iterable of strings representing the :mod:`~tessif.model.components` to
        be verified. They also represent the first level of folders in which
        the energy systems are to be found for performing the verification
        procedure.

        Default is::

            components=('connector', 'sink',
                        'source', 'storage', 'transformer')

    constraints: ~collections.abc.Mapping, optional
        Mapping of energy system files to constraint group strings. Used
        for aggregating different constraints and constraint groups for each
        :paramref:`component <Verificier.components>`.

        Default is::

            constraints={
                'expansion': ('costs.xml', 'emissions.xml',),
                'linear': ('flow_rates.xml', 'gradients.xml'),
                'milp': ('status.xml', 'status_changing.xml')}

        Note
        ----
        A logger.WARNING is triggered in case non existant constraint files are
        passed.

    Example
    -------

    1. Minimum working example:

        0. (Optional)  Change spellings `logging level
           <https://docs.python.org/3/library/logging.html#logging-levels>`_
           used by :meth:`spellings.get_from
           <tessif.frused.spellings.get_from>` to ``debug`` for decluttering
           output:

            >>> import tessif.frused.configurations as configurations
            >>> configurations.spellings_logging_level = 'debug'

        1. Name the top level folder where your :class:`tessif energy systems
           <tessif.model.energy_system.AbstractEnergySystem>` resides in:

           >>> import os
           >>> from tessif.frused.paths import example_dir
           >>> folder = os.path.join(
           ...     example_dir, 'application', 'verification_scenarios')

        2. Construct the constraint dictionairy according to your needs
           (make sure the lowest level is an iterable of strings to get
           expectred results):

           >>> chosen_constraints = {'linear': ('flow_rates_max.py', )}

        3. Choose a parser depending on your energy system file formats:

           >>> import tessif.parse
           >>> chosen_parser = tessif.parse.python_mapping

        4. Chose the components and the model you wish to verify:

           >>> chosen_components = ('source', )
           >>> chosen_model = 'oemof'

        5. Initialize the Verificier:

           >>> import tessif.verify
           >>> verificier = tessif.verify.Verificier(
           ...     path=folder,
           ...     model=chosen_model,
           ...     components=chosen_components,
           ...     constraints=chosen_constraints,
           ...     parser=chosen_parser)

        6. Show the network graph of the analyzed es:

           >>> import matplotlib.pyplot as plt
           >>> es_graph = verificier.plot_energy_system_graph(
           ...     component='source',
           ...     constraint_type='linear',
           ...     constraint_group='flow_rates_max',
           ...     node_color={
           ...         'centralbus': '#9999ff',
           ...         'source_1': '#ff7f0e',
           ...         'source_2': '#2ca02c',
           ...         'sink': '#1f77b4'
           ...     },
           ...     node_size={'centralbus': 5000},
           ... )
           >>> # es_graph.show()  # commented out for simpler doctesting

          .. image:: verificier_nxgraph_example.png
              :align: center
              :alt: Image of the energy system graph subject to verification

        7. Show the numerical results:

          >>> print(verificier.numerical_results[
          ...     'source']['linear']['flow_rates_max'])
          centralbus           source1  source2  sink1
          2022-01-01 00:00:00    -15.0    -35.0   50.0
          2022-01-01 01:00:00    -15.0    -35.0   50.0
          2022-01-01 02:00:00    -15.0    -35.0   50.0
          2022-01-01 03:00:00    -15.0    -35.0   50.0
          2022-01-01 04:00:00    -15.0    -35.0   50.0
          2022-01-01 05:00:00    -15.0    -35.0   50.0
          2022-01-01 06:00:00    -15.0    -35.0   50.0
          2022-01-01 07:00:00    -15.0    -35.0   50.0
          2022-01-01 08:00:00    -15.0    -35.0   50.0
          2022-01-01 09:00:00    -15.0    -35.0   50.0

        8. Show the graphical results:

           >>> graphical_result_plot = verificier.graphical_results[
           ...     'source']['linear']['flow_rates_max']
           >>> # graphical_result_plot.show()  # commented out for doctesting

          .. image:: verificier_graphical_example.png
              :align: center
              :alt: Image showing the verification plot results
    """

    def __init__(
            self, model, parser,
            path=None,
            timeframe='primary',
            components=(
                'connector',
                'sink',
                'source',
                'storage',
                'transformer',
            ),
            constraints={
                'expansion': (
                    'expansion_costs',
                    'expansion_limits',
                ),
                'linear': (
                    'accumulated_amounts',
                    'flow_rates',
                    'flow_costs',
                    'flow_emissions',
                    'flow_gradients',
                    'gradient_costs',
                    'timeseries',
                ),
                'milp': (
                    'initial_status',
                    'status_inertia',
                    'number_of_status_changes',
                    'costs_for_being_active',
                ),
            },
    ):

        # init stuff
        self._results = defaultdict(dict)
        self._components_to_verify = components
        self._constraints_to_test = constraints
        if path is None:
            path = os.path.join(
                example_dir, 'application', 'verification_scenarios')
        self._path = path
        self._model = model
        self._parser = parser

        # 1.) create mapping of the analyzed energy systems first
        self._analyzed_energy_systems = \
            self._generate_analyzed_energy_systems()

        # 2.) the mapping is used to create nx graph objects...
        self._analyzed_energy_system_graphs = \
            self._generate_analyzed_energy_system_graphs()

        # 3.) ... numerical results...
        self._numerical_results = self._generate_numerical_results()

        # 4.) ... and static graphical_results
        self._graphical_results = self._generate_graphical_results()

        # 5.) its also used for aggregating numerical and graphical results
        self._results = self._generate_result_mapping()

    @property
    def components(self):
        """
        Tuple of strings representing the verified
        :mod:`~tessif.model.components`. ``('connector', 'sink', 'source',
        'storage', 'transformer',)`` at default parameterization.
        """
        return self._components_to_verify

    @components.setter
    def components(self, components_tuple):
        self._components_to_verify = components_tuple

    @property
    def constraints(self):
        """
        Mapping of energy system file names to constraint group strings. Used
        for verification. At default parameterization this looks like::

            constraints={
                'expansion': ('costs.xml', 'emissions.xml',),
                'linear': ('flow_rates.xml', 'gradients.xml'),
                'milp': ('status.xml', 'status_changing.xml')}
        """
        return self._constraints_to_test

    @property
    def constraint_types(self):
        """
        Tuple of strings representing the verified constraint types.
        ``('expansion', 'linear', 'milp')`` at default parameterization.
        """
        return tuple(self._constraints_to_test.keys())

    @property
    def constraint_groups(self):
        """
        Tuple of the constraints and constraint files subject to
        verification.

        At default parameterization this looks like::

            ('costs.xml', 'emissions.xml', 'flow_rates.xml',
             'gradients.xml', 'status.xml', 'status_changing.xml')

        """
        return tuple(*self._constraints_to_test.values())

    @property
    def energy_systems(self):
        """
        Triple nested :class:`~collections.abc.Mapping` of
        :class:`tessif energy system
        <tessif.model.energy_system.AbstractEnergySystem>` objects
        representing the analyzed energy systems.

        At default
        parameterization, this mapping looks like::

            results = {
                'connector': {
                    'expansion': {
                        'costs': Tessif-EnergySystem-Object,
                        'emissions': Tessif-EnergySystem-Object,},
                    'linear': {
                        'flow_rates': Tessif-EnergySystem-Object,
                        'gradients': Tessif-EnergySystem-Object,},
                    'milp': {
                        'status': Tessif-EnergySystem-Object,
                        'status_changing': Tessif-EnergySystem-Object,}
                }
               ' sink': ...
            }
        """
        return self._analyzed_energy_systems

    @property
    def graphs(self):
        """
        Triple nested :class:`~collections.abc.Mapping` of
        :class:`networkx.DiGraph` objects representing the analyzed energy
        systems.

        At default
        parameterization, this mapping looks like::

            results = {
                'connector': {
                    'expansion': {
                        'costs': networkx.DiGraph-Object,
                        'emissions': networkx.DiGraph-Object,},
                    'linear': {
                        'flow_rates': networkx.DiGraph-Object,
                        'gradients': networkx.DiGraph-Object,},
                    'milp': {
                        'status': networkx.DiGraph-Object,
                        'status_changing': networkx.DiGraph-Object,}
                }
                'sink': ...
            }
        """
        return self._analyzed_energy_system_graphs

    @property
    def graphical_results(self):
        """
        Dictionary holding the Verificier's graphical results. At default
        parameterization, this dictionary would look like::

            results = {
                'connector': {
                    'expansion': {
                        'costs': matplotlib.figure.Figure,
                        'emissions': matplotlib.figure.Figure,},
                    'linear': {
                        'flow_rates': matplotlib.figure.Figure,
                        'gradients': matplotlib.figure.Figure,},
                    'milp': {
                        'status': matplotlib.figure.Figure,
                        'status_changing': matplotlib.figure.Figure,}
                }
                'sink': ...
            }
        """
        return self._graphical_results

    @property
    def numerical_results(self):
        """
        Dictionary holding the Verificier's numerical results. At default
        parameterization, this dictionary would look like::

            results = {
                'connector': {
                    'expansion': {
                        'costs': DataFrame,
                        'emissions': DataFrame,},
                    'linear': {
                        'flow_rates': DataFrame,
                        'gradients': DataFrame,},
                    'milp': {
                        'status': DataFrame,
                        'status_changing': DataFrame,}
                }
                'sink': ...
            }
        """
        return self._numerical_results

    @property
    def results(self):
        """
        Dictionary holding all of the Verificier's results. At default
        parameterization, this dictionary would look like::

            results = {
                'connector': {
                    'expansion': {
                        'costs': (DataFrame, matplotlib.figure.Figure),
                        'emissions': (DataFrame, matplotlib.figure.Figure),},
                    'linear': {
                        'flow_rates': (DataFrame, matplotlib.figure.Figure),
                        'gradients': (DataFrame, matplotlib.figure.Figure),},
                    'milp': {
                        'status': (DataFrame, matplotlib.figure.Figure),
                        'status_changing': (...),}
                }
                'sink': ...
            }
        """
        return self._results

    def plot_energy_system_graph(
            self, component, constraint_type, constraint_group,
            title='default',  **kwargs):
        """
        Plot the networkx representation of an energy system subject to
        verification.

        Parameters
        ----------
        component: str
            String specifying a component as in :attr:`~Verificier.components`
            of which the :class:`graph object <networkx.DiGraph>` is to be
            plotted.

            At default parameterization this would be one of::

                {'connector', 'source', 'sink', 'storage', 'transformer'}

        constraint_type: str
            String specifying a constraint type as in
            :attr:`~Verificier.constraint_types` of which the
            :class:`graph object <networkx.DiGraph>` is to be plotted.

            At default parameterization this would be one of::

                {'expansion', 'linear', 'milp'}

        constraint_group: str

            String specifying a constraint group as in
            :attr:`~Verificier.constraint_groups` of which the
            :class:`graph object <networkx.DiGraph>` is to be plotted.

            At default parameterization this would be one of::

                {'costs.xml', 'emissions.xml', 'flow_rates.xml',
                 'gradients.xml', 'status.xml', 'status_changing.xml'}

        title: str, None, default='default'
            String specifying the plot title.

            Defaults to::

                Energy System for Verifying the 'constraint_group' Constraints

        Return
        ------
        nxgraph: matplotlib.figure.Figure
            Created networkx graph object.

        """

        graph = self._analyzed_energy_system_graphs[
            component][constraint_type][constraint_group]

        if title == 'default':
            title = (
                f"Energy System for Verifying the '{constraint_group}' " +
                "Constraints")

        nxv.draw_graph(
            graph,
            title=title,
            **kwargs
        )

        figure = plt.gcf()

        return figure

    def _create_result_mapping(self):
        """Utility for creating the triple nested result dictionary."""
        results_dict = defaultdict(dict)

        return results_dict

    def _generate_analyzed_energy_systems(self):
        # default dict for easier to read code below
        energy_systems_dict = defaultdict(dict)

        # component represents the first level ('source', 'sink', etc
        for component in self._components_to_verify:
            # constraint type is the second level ('expansion', 'linear', ...)
            for ctype, cgroup in self._constraints_to_test.items():
                # the actual constraint group is the third and final layer
                energy_systems_dict[component][ctype] = dict()
                for constraint in cgroup:
                    # construct the energy system data location as described in
                    # 'path' (the parameters of this class)
                    es_path = os.path.join(
                        self._path, component, ctype, constraint)

                    # check if energy system file is present..:
                    if os.path.isfile(es_path):

                        # Read and parse in the tessif energy system data
                        if self._parser == parse.python_mapping:

                            module = parse.python_file(es_path)
                            esm = parse.python_mapping(module.mapping)
                        else:
                            esm = self._parser(es_path)

                        # Create the tessif energy system
                        es = tsf.transform(esm)

                        # remove the file format ending for more intuitive
                        # results
                        energy_systems_dict[
                            component][ctype][constraint.split('.')[0]] = es

                    # .. if not, throw a warning
                    else:
                        logger.warning(
                            "A verification of the energy system data " +
                            "located at:\n '{}'\n was requested. ".format(
                                es_path) +
                            "Yet no such file was found.")

        # turn default dict into standard dict
        return dict(energy_systems_dict)

    def _generate_analyzed_energy_system_graphs(self):
        # default dict for easier to read code below
        energy_system_graphs_dict = defaultdict(dict)

        # component represents the first level ('source', 'sink', etc)
        for component, ctypes in self._analyzed_energy_systems.items():

            # constraint type is the second level ('expansion', 'linear', ...)
            for ctype, cgroups in ctypes.items():

                # the actual constraint group is the third and final layer
                energy_system_graphs_dict[component][ctype] = dict()
                for constraint, es in cgroups.items():

                    # create nx graph objects of the respective energy systems
                    graph = es.to_nxgrph()

                    # store it inside the dict
                    energy_system_graphs_dict[
                        component][ctype][constraint] = graph

        return dict(energy_system_graphs_dict)

    def _generate_graphical_results(self):

        # default dict for easier to read code below
        graphical_results_dict = defaultdict(dict)

        # component represents the first level ('source', 'sink', etc)
        for component, ctypes in self._analyzed_energy_systems.items():

            # constraint type is the second level ('expansion', 'linear', ...)
            for ctype, cgroups in ctypes.items():

                # the actual constraint group is the third and final layer
                graphical_results_dict[component][ctype] = dict()

                for constraint, es in cgroups.items():

                    numerical_results = self._numerical_results[
                        component][ctype][constraint]

                    # TODO this will need to become a step plot
                    # using the tessif.visualize.component_loads
                    # module, as can be seen in
                    # User's Guide/Visualization/Component Behaviour/
                    # Verification

                    numerical_results.plot(
                        kind='line',
                        title=constraint)

                    figure = plt.gcf()

                    graphical_results_dict[
                        component][ctype][constraint] = figure

        return dict(graphical_results_dict)

        # default dict for easier to read code below
        result_dict = defaultdict(dict)

        # component represents the first level ('source', 'sink', etc
        for component in self._components_to_verify:
            # constraint type is the second level ('expansion', 'linear', ...)
            for ctype, cgroup in self._constraints_to_test.items():
                # the actual constraint group is the third and final layer
                result_dict[component][ctype] = dict()
                for constraint in cgroup:
                    # construct the energy system data location as described in
                    # 'path' (the parameters of this class)
                    es_path = os.path.join(
                        self._path, component, ctype, constraint)

                    # check if energy system file is present..:
                    if os.path.isfile(es_path):

                        # remove the file format ending for more intuitive
                        # results
                        result_dict[component][ctype][constraint.split(
                            '.')[0]] = 'image_drawing_functionality_here'

        # turn default dict into standard dict
        return dict(result_dict)

    def _generate_numerical_results(self):

        # default dict for easier to read code below
        numerical_results_dict = defaultdict(dict)

        # component represents the first level ('source', 'sink', etc)
        for component, ctypes in self._analyzed_energy_systems.items():

            # constraint type is the second level ('expansion', 'linear', ...)
            for ctype, cgroups in ctypes.items():

                # the actual constraint group is the third and final layer
                numerical_results_dict[component][ctype] = dict()

                for constraint, es in cgroups.items():

                    tessif_es = self._analyzed_energy_systems[
                        component][ctype][constraint]

                    numerical_results_dict[
                        component][ctype][constraint] = \
                        self._generate_singular_simulation_results(
                            tessif_energy_system=tessif_es,
                            model=self._model).node_load[
                                'centralbus']
                    # assume a 'centralbus' for result extraction

        # turn default dict into standard dict
        return dict(numerical_results_dict)

        # default dict for easier to read code below
        result_dict = defaultdict(dict)

        # component represents the first level ('source', 'sink', etc
        for component in self._components_to_verify:
            # constraint type is the second level ('expansion', 'linear', ...)
            for ctype, cgroup in self._constraints_to_test.items():
                # the actual constraint group is the third and final layer
                result_dict[component][ctype] = dict()
                for constraint in cgroup:
                    # construct the energy system data location as described in
                    # 'path' (the parameters of this class)
                    es_path = os.path.join(
                        self._path, component, ctype, constraint)

                    # check if energy system file is present..:
                    if os.path.isfile(es_path):

                        # use this path to simulate the energy system and
                        # extract the results
                        result_dict[component][ctype][
                            constraint.split('.')[0]] = \
                            self._generate_singular_simulation_results(
                                path=es_path,
                                parser=self._parser,
                                model=self._model).node_load['centralbus']
                        # assume a 'centralbus' for result extraction

        # turn default dict into standard dict:
        return dict(result_dict)

    def _generate_result_mapping(self):
        # default dict for easier to read code below
        result_dict = defaultdict(dict)

        # component represents the first level ('source', 'sink', etc
        for component in self._components_to_verify:
            # constraint type is the second level ('expansion', 'linear', ...)
            for ctype, cgroup in self._constraints_to_test.items():
                # the actual constraint group is the third and final layer
                result_dict[component][ctype] = dict()
                for constraint in cgroup:

                    # check if energy system file is present..:
                    if constraint.split('.')[0] in self._numerical_results[
                            component][ctype]:

                        # Aggregate the numerical and graphical results in a
                        # tuple
                        result_dict[component][ctype][
                            constraint.split('.')[0]] = (
                                self._numerical_results[component][ctype][
                                    constraint.split('.')[0]],
                                self._graphical_results[component][ctype][
                                    constraint.split('.')[0]])

        return dict(result_dict)

    def _generate_singular_simulation_results(
            self, tessif_energy_system, model):

        # figure out model used
        for internal_name, spellings in defaults.registered_models.items():
            if model in spellings:
                used_model = internal_name
                break

        # 1) Transform the energy system into the requested model
        requested_model = importlib.import_module('.'.join([
            'tessif.transform.es2es', used_model]))
        model_es = requested_model.transform(tessif_energy_system)

        self._model_es = model_es

        # 2) Execute simulation
        simulation_utility = getattr(
            simulate, '_'.join([used_model, 'from_es']))
        optimized_es = simulation_utility(model_es)

        # 3) Create result utility
        requested_model_result_parsing_module = importlib.import_module(
            '.'.join(['tessif.transform.es2mapping', used_model]))
        resultier = requested_model_result_parsing_module.AllResultier(
            optimized_es)

        return resultier
