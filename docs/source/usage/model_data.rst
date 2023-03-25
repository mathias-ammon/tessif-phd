.. _ModelData:

**********
Model Data
**********

Model Data input and output is handled by the
:mod:`~tessif.transform.mapping2es` and the :mod:`~tessif.transform.es2mapping`
modules inside the :mod:`~tessif.transform` subpackage. Following sections
provide detailed information on how to use them as well as consequential
links for more detailed information.

.. note::
   The current support of the various data transformation capabilities can be
   gauged and expanded using the :mod:`tessif.transform` module.

.. contents::
   :local:

.. _ModelData_Parsed:

Parsed Data
***********
Data parsing is usually the first step in a series of steps for conducting energy supply system simulations. The section about :ref:`data input <Data_Input>` gives detailed information on how :mod:`tessif` helps in reading in data.

Handling the parsed data comes second. This usually involves creating a set of equations formulating an `optimization problem <https://en.wikipedia.org/wiki/Optimization_problem>`_. This mathematical formulation process however is often interfaced by an energy system object trying to make the problem description process more intuitive for engineers. Examples for such interfaces would be :mod:`tessif.model.energy_system`, :mod:`oemof.energy_system`, and :class:`pypsa.Network <https://pypsa.readthedocs.io/en/latest/api_reference.html#pypsa.Network>`.

Consequentially handling the parsed data comes down to creating such energy system objects. Since :mod:`tessif's <tessif>` :ref:`purpose <Introduction_Purpose>` is to simplify using various different simulation tools most often the first energy system object created is of type :mod:`tessif.model.energy_system.AbstractEnergySystem`. Which can then be :ref:`simulated <Simulating_Through_Tessif>` directly and or  :ref:`transformed <Transformation>` into other energy system model objects for performing simulations.

:mod:`Tessif <tessif>` also helps with parsing and :ref:`handling data specificly designed for a single model <ModelData_Specific>`. This is often the case when :mod:`tessif's <tessif>` :ref:`generalization approach <Models_Tessif_Concept>` reduces a model's accuracy or straight up ingores and or oversimplifies it's parts of it by not providing appropriate parameters.

.. note::
   When aiming to perform large scale investigations, involving many different
   kinds of parameterized energy systems it is much more convenient to use
   the :mod:`simulate wrappers <tessif.simulate>`. They perform:
   
       - parsing the read-in data
       - handling it appropriately
       - performing the simulation

   with a single call.


The Steps of reading in and parsing data as creating an energy system object out of it are examplified in following sections. The example shown uses a set of `config files <https://en.wikipedia.org/wiki/INI_file>`_ storing energy system data found in :mod:`tessif's example hub <tessif.examples>`.

1. Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>` logging level to debug for decluttering doctest output:

   >>> from tessif.frused import configurations
   >>> configurations.spellings_logging_level = 'debug'

2. Reading in the data:

   >>> from tessif import parse
   >>> from tessif.frused.paths import example_dir
   >>> import os
   >>> folder = os.path.join(example_dir,
   ...     'data', 'tsf', 'cfg', 'flat', 'basic')
   >>> energy_system_mapping = parse.flat_config_folder(folder)

   Print the the sorted mappings keys for checking succesfull reading:

   >>> keys = list(energy_system_mapping.keys())
   >>> for key in sorted(keys):
   ...     print(key)   
   bus
   global_constraints
   sink
   source
   storage
   timeframe
   transformer

3. Transform the parsed data into an energy system object:
   
   >>> from tessif.transform.mapping2es.tsf import transform
   >>> es = transform(energy_system_mapping)
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

.. _ModelData_Simulated:

Simulated Data
**************
As identified in :ref:`Introduction <Introduction_Purpose>` providing a common interface for various different energy supply system simulation models is one of :mod:`tessif's <tessif>` goals. The interface's implementation can be found in the :mod:`tessif.transform.es2mapping` subpackage. It consists of a collection of small classes extracting specific results from the optimized energy system an transforming them into dictionairies keyed by the :attr:`unique identifiers <tessif.frused.namedtuples.Uid>` of the :ref:`components <Models_Tessif_Concept_ESC>` present in the energy system. These 'mini-classes' are called :class:`Resultiers <tessif.transform.es2mapping.omf.Resultier>` (as in 'Portier' for the results).

Following sections demonstrate how tessif can be used to extract data out of energy systems simulated by oemof. (The conceptual syntax accross different models remains the same. Only the :mod:`es2mapping submodule <tessif.transform.es2mapping>` needs to be adjusted to the model used).

1. Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>`
   logging level to debug for decluttering doctest output:

   >>> from tessif.frused import configurations
   >>> configurations.spellings_logging_level = 'debug'

2. Import all the essentials to use the simulation wrapper:

   >>> import tessif.simulate as simulate
   >>> import tessif.transform.es2mapping.omf as transform_oemof
   >>> from tessif.frused.paths import example_dir
   >>> from tessif import parse
   >>> import os
   >>> import functools

3. Perform simulation :

   >>> es = simulate.omf(
   ...     path=os.path.join(
   ...         example_dir, 'data', 'omf', 'xlsx', 'generic_storage.ods'),
   ...     parser=functools.partial(parse.xl_like, sheet_name=None,
   ...                              engine='odf'),
   ...     solver='glpk')

4. Transform the energy system into objects that can convienently be accessed for the results (load results in this case. See :mod:`tessif.transform.es2mapping.omf` for a complete listing of available Resultiers):

   >>> resultier = transform_oemof.LoadResultier(es)
   >>> print(resultier.node_data().keys())
   dict_keys(['node_inflows', 'node_load', 'node_outflows', 'node_summed_loads'])

5. Query arbitrary energy system components for their load data:

   >>> for node in es.nodes:
   ...     print(node.label)
   Power Grid
   Onshore
   Power
   Power Demand
   Storage
   
   >>> print(resultier.node_inflows['Power Grid'])        
   Power Grid           Onshore  Power  Storage
   2016-01-01 00:00:00    250.0    0.0      0.0
   2016-01-01 01:00:00    250.0    0.0      0.0
   2016-01-01 02:00:00    250.0    0.0      0.0
   2016-01-01 03:00:00    250.0    0.0      0.0
   2016-01-01 04:00:00    250.0    0.0      0.0

   >>> print(resultier.node_load['Power Grid'])
   Power Grid           Onshore  Power  Storage  Power Demand  Storage
   2016-01-01 00:00:00   -250.0   -0.0     -0.0         200.0     50.0
   2016-01-01 01:00:00   -250.0   -0.0     -0.0         200.0     50.0
   2016-01-01 02:00:00   -250.0   -0.0     -0.0         140.0    110.0
   2016-01-01 03:00:00   -250.0   -0.0     -0.0         200.0     50.0
   2016-01-01 04:00:00   -250.0   -0.0     -0.0         200.0     50.0

   >>> print(resultier.node_outflows['Power Demand'])
   Empty DataFrame
   Columns: []
   Index: []


   >>> print(resultier.node_summed_loads['Power Grid'])
   2016-01-01 00:00:00    250.0
   2016-01-01 01:00:00    250.0
   2016-01-01 02:00:00    250.0
   2016-01-01 03:00:00    250.0
   2016-01-01 04:00:00    250.0
   Freq: H, dtype: float64


.. _ModelData_Specific:

Model Specific Data
*******************
Tessif's parsing capabilities can also be used to provide data directly to the model. This however requires a respective submodule to be implemented inside :mod:`~tessif.transform.mapping2es` transforming the parsed in data to actual energy system objects. Following section shows how this is done using oemof.


1. Setting :attr:`spellings.get_from's <tessif.frused.spellings.get_from>`
   logging level to debug for decluttering doctest output:

   >>> from tessif.frused import configurations
   >>> configurations.spellings_logging_level = 'debug'

2. Import all the essentials to use the parsing wrapper:

   >>> from tessif.parse import xl_like
   >>> from tessif.frused.paths import example_dir
   >>> import os
   
3. Parsing the data:
   
   >>> p = os.path.join(example_dir, 'data', 'omf', 'xlsx', 'energy_system.xls')
   >>> energy_system_mapping = xl_like(p, engine='xlrd')
   >>> for key in energy_system_mapping.keys():
   ...     print(key)
   Info
   Grid
   Renewable
   Demand
   Commodity
   mimo_transformers
   global_constraints
   timeframe

4. Tansforming the parsed data:
   
   >>> from tessif.transform.mapping2es.omf import transform
   >>> es = transform(energy_system_mapping)
   >>> for node in es.nodes:
   ...     print(node.label.name)
   Power Grid
   Gas Grid
   Heat Grid
   Coal Grid
   PV
   Onshore
   Offshore
   Gas
   Coal
   Power Demand
   Heat Demand
   Gas_CHP
   Coal_PP
   Gas_HP
