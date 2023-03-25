.. _Secondary_Objectives:

********************
Secondary Objectives
********************

:mod:`Tessif <tessif>` allows defining secondary objectives i.e. constraining global emissions to 0.

This is archieved by using the :class:`energy system's <tessif.model.energy_system.AbstractEnergySystem>` :paramref:`~tessif.model.energy_system.AbstractEnergySystem.global_constraints` parameter. Which allows to formulate any number of global constraints, like for example in the :ref:`fully parameterized working example (fpwe) <examples_transformation_comparison_igr>`.


Examples
********
Following sections demonstate the basic use of secondary objectives as well as some use case approaches for conveniently deploying different constraints and timeframes using the same externalized data set

Basic
=====
Following example illustrates the basic use of global constraints for
limiting an energy systems emissions.

1. Utilizing the :ref:`example hub's <Examples>`
   :meth:`~tessif.examples.data.tsf.py_hard.emission_objective` utility for
   conveniently accessing basic :class:`tessif energy system
   <tessif.model.energy_system.AbstractEnergySystem>` instance:

   >>> from tessif.examples.data.tsf.py_hard import emission_objective
   >>> tessif_es = emission_objective()

2. Display it's global constraints:

   >>> print(tessif_es.global_constraints)
   {'emissions': 60}
   
3. Transform the :mod:`tessif energy system
   <tessif.model.energy_system.AbstractEnergySystem>` into an
   :class:`oemof energy system <oemof.energy_system.EnergySystem>` for
   examplifying the perserverence of the global constraints:
   

   >>> from tessif.transform.es2es.omf import transform
   >>> oemof_es = transform(tessif_es)
   >>> print(oemof_es.global_constraints)
   {'emissions': 60}

    >>> import tessif.examples.data.tsf.py_hard as tsf_py
    >>> es = tsf_py.emission_objective()
    >>> print(es.global_constraints['emissions'])
    60

4. :mod:`Visualize <tessif.visualize.nxgrph>` the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph, node_color='orange')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: images/emission_objective_example.png
        :align: center
        :alt: alternate text    
    
5. Optimize the energy system to see the constraint's consequences:

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

    Note how during the first 3 timesteps the more expensive wind power
    supply is used due to the emission constriants

6. Check global results using the dedicated resultier:

   >>> ig_resultier = oemof_results.IntegratedGlobalResultier(optimized_oemof_es)
   >>> import pprint
   >>> pprint.pprint(ig_resultier.global_results)
   {'capex (ppcd)': 0.0,
    'costs (sim)': 252.0,
    'emissions (sim)': 60.0,
    'opex (ppcd)': 252.0}

   check the initial constraint:
   
   >>> print(tessif_es.global_constraints)
   {'emissions': 60}

Variable timeframes and constraints
===================================
Following example demonstrates how :ref:`tessifs parsing <ModelData_Parsed>` capabilities simplify deploying different timeframes and sets of constraints to the same energy system. It also illustrates how expansion problems can be solved differently depending on the constraints stated.

1. Utilizing the :ref:`example hub's <Examples>`
   flat config files located in
   ``tessif/examples/data/tsf/cfg/flat/objectives``
   for conveniently accessing basic :class:`tessif energy system
   <tessif.model.energy_system.AbstractEnergySystem>` data:

   a. Create access to the path:

      >>> import os
      >>> from tessif.frused.paths import example_dir
      >>> path = os.path.join(example_dir,
      ...     'data', 'tsf', 'cfg', 'flat', 'objectives')

   b. silence the logger warnings:

      >>> import tessif.frused.configurations as configurations
      >>> configurations.spellings_logging_level = 'debug'

   c. Create the actual energy system:

      >>> import tessif.transform.mapping2es.tsf as ttsf
      >>> import tessif.parse as parse
      >>> tessif_es = ttsf.transform(
      ...     parse.flat_config_folder(
      ...        path,
      ...        timeframe='secondary',
      ...        global_constraints='primary'))

      Note how the ``timeframe`` key ``'secondary'`` correspond
      to the section header found in
      ``tessif/examples/data/tsf/cfg/flat/objectives``.
      
2. :mod:`Visualize <tessif.visualize.nxgrph>` the energy system for better understanding what the output means:

    >>> import matplotlib.pyplot as plt
    >>> import tessif.visualize.nxgrph as nxv
    >>> grph = tessif_es.to_nxgrph()
    >>> drawing_data = nxv.draw_graph(
    ...     grph, node_color='orange')
    >>> # plt.show()  # commented out for simpler doctesting

    .. image:: images/emission_objective_example_advanced.png
        :align: center
        :alt: alternate text    

3. Display it's global constraints:

   >>> print(tessif_es.global_constraints)
   {'name': 'default', 'emissions': inf, 'resources': inf}

   
4. Transform the :mod:`tessif energy system
   <tessif.model.energy_system.AbstractEnergySystem>` into an
   :class:`oemof energy system <oemof.energy_system.EnergySystem>` for
   examplifying the perserverence of the global constraints:
   

   >>> from tessif.transform.es2es.omf import transform
   >>> oemof_es = transform(tessif_es)
   >>> print(oemof_es.global_constraints)
   {'name': 'default', 'emissions': inf, 'resources': inf}

5. Optimize the energy system to see the constraint's consequences:

   >>> import tessif.simulate as simulate
   >>> optimized_oemof_es = simulate.omf_from_es(oemof_es, solver='cbc')
   
   >>> import tessif.transform.es2mapping.omf as oemof_results
   >>> resultier = oemof_results.LoadResultier(optimized_oemof_es)

   >>> # Generator costs/emissions are 1/10 units respectively
   >>> # Solar Power costs/emissions are 0/0 units respectively
   >>> # but only 15 units are installed, expansion costs are 10 per unit
   >>> print(resultier.node_load['Power Line'])
   Power Line           Battery  Generator  Solar Power  Battery  Demand
   2019-10-03 00:00:00     -0.0       -5.0        -15.0      0.0    20.0
   2019-10-03 01:00:00     -0.0       -5.0        -15.0      0.0    20.0
   2019-10-03 02:00:00     -0.0       -5.0        -15.0      0.0    20.0

6. Check global results using the dedicated resultier:

   >>> ig_resultier = oemof_results.IntegratedGlobalResultier(optimized_oemof_es)
   >>> import pprint
   >>> pprint.pprint(ig_resultier.global_results)
   {'capex (ppcd)': 0.0,
    'costs (sim)': 15.0,
    'emissions (sim)': 150.0,
    'opex (ppcd)': 15.0}

   >>> # check the initial constraint:
   >>> print(tessif_es.global_constraints)
   {'name': 'default', 'emissions': inf, 'resources': inf}

7. Data file for reference:

   .. literalinclude::
      ../../../src/tessif/examples/data/tsf/cfg/flat/objectives/sources.cfg

8. Change the parsed constraints:
   
   >>> tessif_es = ttsf.transform(
   ...     parse.flat_config_folder(
   ...        path,
   ...        timeframe='secondary',
   ...        global_constraints='tertiary'))

   >>> print(tessif_es.global_constraints)
   {'name': '100% Reduction', 'emissions': 0.0, 'resources': inf}

9. Resimulate:

   >>> oemof_es = transform(tessif_es)
   >>> optimized_oemof_es = simulate.omf_from_es(oemof_es, solver='cbc')


10. Note how the emission constraint leads to the solar power beeing expanded
    (altough more expensive):

   >>> resultier = oemof_results.LoadResultier(optimized_oemof_es)
   >>> print(resultier.node_load['Power Line'])
   Power Line           Battery  Generator  Solar Power  Battery  Demand
   2019-10-03 00:00:00     -0.0       -0.0        -20.0      0.0    20.0
   2019-10-03 01:00:00     -0.0       -0.0        -20.0      0.0    20.0
   2019-10-03 02:00:00     -0.0       -0.0        -20.0      0.0    20.0

11. Recheck global results using the dedicated resultier
    (Note how the emissions are now 0 but the costs increased by 35 units
    and shifted from opex to capex):

   >>> ig_resultier = oemof_results.IntegratedGlobalResultier(optimized_oemof_es)
   >>> import pprint
   >>> pprint.pprint(ig_resultier.global_results)
   {'capex (ppcd)': 50.0,
    'costs (sim)': 50.0,
    'emissions (sim)': 0.0,
    'opex (ppcd)': 0.0}



   # check the initial constraint:
   >>> print(tessif_es.global_constraints)
   {'name': '100% Reduction', 'emissions': 0.0, 'resources': inf}

