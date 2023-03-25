# tessif/simulate.py
"""
:mod:`~tessif.simulate` is a :mod:`tessif` module to wrap energy system
simulation calls into a convenient and ready to use interface.
energy systems using oemof.

Create powerfull, indepth, hassle-low wrappers that allow simulating the most
common use cases needing only an input location and some remarks on wich parser
and transformers to use.
"""
import numbers

from oemof import solph
# from FINE import energySystemModel as fn_esM

import tessif.transform.mapping2es.omf as tomf
import tessif.transform.mapping2es.tsf as ttsf
import tessif.transform.es2es.omf as tessif_to_oemof
import tessif.write.tools as write_tools
from tessif.frused.paths import write_dir
import logging

logger = logging.getLogger(__name__)


def omf(path, parser, solver='cbc', is_tessif=False, **kwargs):
    """ Optimize an energy system using the `oemof
    <https://oemof.readthedocs.io/en/v0.0.4/index.html>`_ library as well
    data stored somewhere.

    Parameters
    ----------
    path: str
        String representing of the energy system data path.
        Passed to :paramref:`~simulate.parser`.

    parser: :class:`~collections.abc.Callable`
        Functional used to read in and parse the energy system data.
        Usually one found in :mod:`tessif.parse`

        Use :func:`functools.partial` for supplying parameters. See also the
        Examples section.

    solver: str, default='cbc'
        String specifying the solver to be used. For `FOSS
        <https://en.wikipedia.org/wiki/Free_and_open-source_software>`_
        application, this is usually either ``cbc`` or ``glpk``.

        But since `pyomo` is used for interfacing the solver. Any of it's
        `supported solvers
        <https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html#supported-solvers>`_
        can be used.

        Note
        ----
        In case the link above is servered, use the pyomo command::

            pyomo help --solvers

    is_tessif: bool, default=False,
        Boolean indicating if the read in data source is to be interpreted as
        a :class:`tessif energy system
        <tessif.model.energy_system.AbstractEnergySystem>`.

        If ``True`` the energy system data is interpreted as
        :class:`tessif energy system
        <tessif.model.energy_system.AbstractEnergySystem>` and automatically
        :meth:`transformed <tessif.transform.es2es.omf.transform>` into an
        :class:`oemof energy system <oemof.energy_system.EnergySystem>`.

        If ``False`` the energy system data is interpreted as
        :class:`oemof energy system <oemof.energy_system.EnergySystem>`

    kwargs:
        Keywords parameterizing the solver used as well as the energy system
        transformation process.

        Use one of :meth:`solve's <oemof.solph.models.BaseModel.solve>`
        parameters for tweaking the solver. All others will be passed to
        :func:`tessif.transform.mapping2es.omf.transform` (Effectively passing
        it to :meth:`oemof.core.energy_system.EnergySystem.add`)

    Return
    ------
    optimized_es : :class:`~oemof.energy_system.EnergySystem`
        Energy system carrying the optimization results.

    Examples
    --------
    Monkey patch logging level to silence warnings:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'


    Read in the oemof standard enregy system and simulate it:

    >>> from tessif.simulate import omf
    >>> from tessif.parse import xl_like
    >>> from tessif.frused.paths import example_dir
    >>> import os
    >>> es = omf(
    ...     path=os.path.join(example_dir, 'data', 'omf',
    ...         'xlsx', 'energy_system.xlsx'),
    ...     parser=xl_like)
    >>> print(type(es.results))
    <class 'pyomo.opt.results.results_.SolverResults'>
    >>> print(len(es.nodes) is len(es.results['main']))
    True


    Use functools.partial to tweak the parser and use glpk solver:

    >>> import os
    >>> import functools
    >>> from tessif.frused.paths import example_dir
    >>> import tessif.parse as parse
    >>> import tessif.simulate as simulate
    >>> es = simulate.omf(
    ...     path=os.path.join(example_dir, 'data', 'omf',
    ...         'xlsx', 'energy_system.ods'),
    ...     parser=functools.partial(
    ...     parse.xl_like, sheet_name=None, engine='odf'),
    ...     solver='glpk')
    >>> print(type(es.results))
    <class 'pyomo.opt.results.results_.SolverResults'>
    >>> print(len(es.nodes) is len(es.results['main']))
    True

    Use tessif's energy system data interface:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> import tessif.parse as parse
    >>> import tessif.simulate as simulate
    >>> es = simulate.omf(
    ...     path=os.path.join(example_dir, 'data', 'tsf',
    ...                       'cfg', 'flat', 'basic'),
    ...     parser=parse.flat_config_folder,
    ...     solver='cbc',
    ...     is_tessif=True)

    Show some results:

    >>> import tessif.transform.es2mapping.omf as oemof_results
    >>> resultier = oemof_results.LoadResultier(es)
    >>> print(resultier.node_load['Power Line'])
    Power Line           Battery  Generator  Solar Panel  Battery  Demand
    2015-01-01 00:00:00     -0.0       -0.0        -12.0      1.0    11.0
    2015-01-01 01:00:00     -8.0       -0.0         -3.0      0.0    11.0
    2015-01-01 02:00:00     -0.9       -3.1         -7.0      0.0    11.0

    >>> stoRes = oemof_results.StorageResultier(es)
    >>> print(stoRes.node_soc['Battery'])
    2015-01-01 00:00:00    10.0
    2015-01-01 01:00:00     1.0
    2015-01-01 02:00:00     0.0
    Freq: H, Name: Battery, dtype: float64
    """

    # Default solver kwargs
    skwargs = {
        'solver_io': 'lp',
        'solve_kwargs': {},
        'cmdline_options': {},
    }

    # Seperate the kwargs:
    for key in skwargs.keys():
        if key in kwargs.keys():
            skwargs.update({key: kwargs.pop(key)})

    energy_system_mapping = parser(path)
    if is_tessif:
        es = ttsf.transform(energy_system_mapping, **kwargs)
        es = tessif_to_oemof.transform(es)
    else:
        es = tomf.transform(energy_system_mapping, **kwargs)

    # Return the optimized oemof energy system
    return omf_from_es(es, solver=solver, **kwargs, **skwargs)


def omf_from_es(energy_system, solver='cbc', **kwargs):
    """ Optimize an energy system using the `oemof
    <https://oemof.readthedocs.io/en/v0.0.4/index.html>`_ library.

    Parameters
    ----------
    energy_system: ~oemof.energy_system.EnergySystem
        Oemof energy system to be simulated.

    solver: str, default='cbc'
        String specifying the solver to be used. For `FOSS
        <https://en.wikipedia.org/wiki/Free_and_open-source_software>`_
        application, this is usually either ``cbc`` or ``glpk``.

        But since :mod:`pyomo` is used for interfacing the solver. Any of it's
        `supported solvers
        <https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html#supported-solvers>`_
        can be used.

        Note
        ----
        In case the link above is servered, use the pyomo cli command::

            pyomo help --solvers

    kwargs:
        Keywords parameterizing the solver used as well as the energy system
        transformation process.

        Use one of :meth:`solve's <oemof.solph.models.BaseModel.solve>`
        parameters for tweaking the solver.

    Return
    ------
    optimized_es : :class:`~oemof.energy_system.EnergySystem`
        Energy system carrying the optimization results.

    Examples
    --------
    Use the :mod:`oemof example hub <tessif.examples.data.omf>` to generate an
    energy system that can be optimized:

    Setting spellings.get_from's logging level to debug for decluttering
    doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'

    Import and parse the data:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> from tessif.parse import xl_like

    >>> p = os.path.join(example_dir,
    ...     'data', 'omf', 'xlsx', 'energy_system.xls')
    >>> energy_system_mapping = xl_like(p, engine='xlrd')

    Transform the parsed data into an energy system:

    >>> from tessif.transform.mapping2es.omf import transform
    >>> energy_system = transform(energy_system_mapping)

    Simulate the energy system:

    >>> optimized_es = omf_from_es(energy_system)

    Roughly verify that everything went as expected:

    >>> print(type(optimized_es.results))
    <class 'pyomo.opt.results.results_.SolverResults'>
    >>> print(len(optimized_es.nodes) is len(optimized_es.results['main']))
    True
    """
    # Default solver kwargs
    skwargs = {
        'solver_io': 'lp',
        'solve_kwargs': {},
        'cmdline_options': {},
    }

    # Seperate the kwargs:
    for key in skwargs.keys():
        if key in kwargs.keys():
            skwargs.update({key: kwargs.pop(key)})

    # enforce solver from argument:
    skwargs['solver'] = solver

    # Prepare the optimization problem
    om = solph.Model(energy_system)

    # Parse global constraints (potentially added by a tessif transformation)
    if hasattr(energy_system, 'global_constraints'):
        for constraint, value in energy_system.global_constraints.items():

            if isinstance(value, numbers.Number):
                om = solph.constraints.generic_integral_limit(
                    om=om,
                    keyword=constraint,
                    limit=value)

    om.solve(**skwargs)

    # Pump results into the model:
    energy_system.results['main'] = solph.processing.results(om)
    energy_system.results['meta'] = solph.processing.meta_results(om)

    # parse global results
    energy_system.results['global'] = dict()

    # Parse global constraint results (potentially added by a tessif
    # transformation)
    if hasattr(energy_system, 'global_constraints'):
        for constraint, value in energy_system.global_constraints.items():

            if isinstance(value, numbers.Number):
                energy_system.results['global'][constraint] = getattr(
                    om, 'integral_limit_{}'.format(constraint))()

    # # Parse global (constraint) results not added by tessif:
    # # 1. get all attributes of this instance as a list of (name, value):
    # attribute_names = dir(om)

    # # get all attribute names starting with integral_limit
    # global_constraint_names = list(
    #     a[0] for a in attribute_names
    #     if 'integral_limit' in a[0] and '_constraint' not in a[0])

    # # compile dict entries for the global results:
    # for attr_name in global_constraint_names:

    #     # only overwrite if not a duplicate
    #     if attr_name not in energy_system.results['global'].keys():
    #         energy_system.results['global'][
    #             attr_name] = getattr(om, attr_name)

    energy_system.results['global']['costs'] = energy_system.results[
        'meta']['objective']

    # Return the optimized oemof energy system
    return energy_system


def tsf(path, parser, **kwargs):
    """ Optimize an energy system using the :mod:`Tessif
    <tessif.model>` library.

    Warning
    -------
    Not yet implemented!
    """
    raise NotImplementedError("Someday it'll be there")


def ppsa_from_es(energy_system, solver='cbc', **kwargs):
    """ Optimize an energy system using `Pypsa
    <https://pypsa.readthedocs.io/en/latest/index.html>`_ .

    Parameters
    ----------
    energy_system: pypsa.Network
        Pypsa energy system to be simulated

    solver: str, default='cbc'
        String specifying the solver to be used. For `FOSS
        <https://en.wikipedia.org/wiki/Free_and_open-source_software>`_
        application, this is usually either ``cbc`` or ``glpk``.

        But since :mod:`pyomo` is used for interfacing the solver. Any of it's
        `supported solvers
        <https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html#supported-solvers>`_
        can be used.

        Pypsa also allows using its own solver. Archieved by passing ``pypsa``.

        Note
        ----
        In case the link above is servered, use the pyomo command::

            pyomo help --solvers

    kwargs:
        Keywords parameterizing the solver used as well as the energy system
        transformation process.

        Use one of :meth:`lopf's <pypsa.Network.lopf>`
        parameters for tweaking the solver.

    Return
    ------
    optimized_es : :class:`~oemof.energy_system.EnergySystem`
        Energy system carrying the optimization results.

    Examples
    --------
    Setting spellings.get_from's logging level to debug for decluttering
    doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'

    Use the :mod:`pypsa example hub <tessif.examples.data.pypsa>` to
    create an energy system that can be optimized:

    >>> import tessif.examples.data.pypsa.py_hard as pypsa_hardcoded_examples
    >>> pypsa_energy_system = pypsa_hardcoded_examples.create_mwe()

    Simulate the energy system:

    >>> optimized_pypsa_es = ppsa_from_es(pypsa_energy_system)

    Roughly verify that everything went as expected:

    >>> print(optimized_pypsa_es.objective)
    190.0
    """

    if solver == "pypsa":
        pyomo = False
    else:
        pyomo = True

    kwargs["solver_name"] = solver

    # 5.) Optimize model:
    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        energy_system.lopf(pyomo=pyomo, **kwargs)

    return energy_system


def fine_from_es(energy_system, solver='cbc', tsa=False, **kwargs):
    """ Optimize an energy system using `fine
    <https://vsa-fine.readthedocs.io/en/latest/index.html>`_ .

    Parameters
    ----------
    energy_system: fine energy system model
        fine energy system to be simulated

    solver: str, default='cbc'
        String specifying the solver to be used. For `FOSS
        <https://en.wikipedia.org/wiki/Free_and_open-source_software>`_
        application, this is usually either ``cbc`` or ``glpk``.

        But since :mod:`pyomo` is used for interfacing the solver. Any of it's
        `supported solvers
        <https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html#supported-solvers>`_
        can be used.

        Note
        ----
        In case the link above is servered, use the pyomo command::

            pyomo help --solvers

    kwargs:
        Keywords parameterizing the solver used as well as the energy system
        transformation process.


    Return
    ------
    optimized_es : energy system model
        Energy system carrying the optimization results.

    Examples
    --------
    Setting spellings.get_from's logging level to debug for decluttering
    doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'

    Use the :mod:`fine example hub <tessif.examples.data.fine>` to
    create an energy system that can be optimized:

    >>> import tessif.examples.data.fine.py_hard as fine_hardcoded_examples
    >>> fine_energy_system = fine_hardcoded_examples.create_mwe()

    Simulate the energy system:

    >>> optimized_fine_es = fine_from_es(fine_energy_system)

    Roughly verify that everything went as expected:

    >>> print(round(optimized_fine_es.objectiveValue * optimized_fine_es.numberOfYears,0))
    78.0
    """

    kwargs['solver'] = solver
    # states if the optimization of the energy system model should be done with (a) the full time series (False)
    # or (b) clustered time series data (True).
    if tsa is True:
            kwargs['timeSeriesAggregation'] = True
            energy_system.cluster()
    else:
        kwargs['timeSeriesAggregation'] = False

    # supress solver results getting printed to stdout
    with write_tools.HideStdoutPrinting():
        energy_system.optimize(**kwargs)

    return energy_system


def cllp_from_es(energy_system, solver='cbc', save=False, **kwargs):
    """ Optimize an energy system using `Calliope
    <https://calliope.readthedocs.io/en/stable/>`_ .

    Parameters
    ----------
    energy_system: calliope.core.model.Model
        Calliope energy system to be simulated

    solver: str, default='cbc'
        String specifying the solver to be used. For `FOSS
        <https://en.wikipedia.org/wiki/Free_and_open-source_software>`_
        application, this is usually either ``cbc`` or ``glpk``.

        But since :mod:`pyomo` is used for interfacing the solver. Any of it's
        `supported solvers
        <https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html#supported-solvers>`_
        can be used.

        Note
        ----
        In case the link above is servered, use the pyomo command::

            pyomo help --solvers

    save: boolean, default=False
        Boolean deciding whether the optimized energy system (energy system data
        as well as results) is gonna be saved in csv-files or not.

        Note
        ----
        Earlier saves do not get overwritten.

    kwargs:
        Keywords parameterizing the solver used as well as the energy system
        transformation process.

    Return
    ------
    optimized_es : :class:`~calliope.core.model.Model`
        Energy system carrying the optimization results.

    Examples
    --------
    Setting spellings.get_from's logging level to debug for decluttering
    doctest output:

    >>> from tessif.frused import configurations
    >>> configurations.spellings_logging_level = 'debug'

    Use the :mod:`calliope example hub <tessif.examples.data.calliope>` to
    create an energy system that can be optimized:

    >>> from tessif.frused.paths import example_dir
    >>> import calliope
    >>> calliope_es = calliope.Model(f'{example_dir}/data/calliope/fpwe/model.yaml')

    Simulate the energy system:

    >>> optimized_es = cllp_from_es(calliope_es)

    Roughly verify that everything went as expected:

    >>> print(round(optimized_es.results.objective_function_value), 0)
    105 0
    """

    energy_system.run_config.update({'solver': solver})

    # assuming that the energy system should be run again when the simulate function is called,
    # no matter if it already has been run before or not
    energy_system.run(force_rerun=True, **kwargs)

    # cannot overwrite saves. So this only works the first time the model is run.
    if save:
        energy_system.to_csv(f'{write_dir}/Calliope/{energy_system.model_config["name"]}_csv')

    return energy_system
