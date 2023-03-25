.. _Examples_Application_PHD_RDR:

Result Data Representation
**************************
The developed method for comparing energy supply system models recommends a
specific result data representation based on a directed graph.

Following script shows how to use Tessif's
:mod:`post processing utility <tessif.transform.es2mapping>` to compile
the result data for a singular component. It is intended to serve as copy-paste
template as well as basis for further use.

It is the very same script which was used to generate the generic graph
visualization and tabular result data representation in the phd's subsection:

  ``Theory -> Graph Theory Tools -> Result Data Representation``

The compilation utility can be used via tessif as
:func:`tessif.transform.es2mapping.compile_result_data_representation`.

.. contents:: Contents
   :local:
   :backlinks: top      


Examplary Use
=============

.. literalinclude::
   ./result_data_representation.py

Examplary result
================
The above code snippet prints following result::
  
                               Symbol                                              Value
  Label                                                                                 
  installed capacity        $P_{cap}$                {'Powerline': 4.0, 'Heatline': 5.0}
  original capacity     $P_{origcap}$                {'Powerline': 0.0, 'Heatline': 0.0}
  characteristic value           $cv$                {'Powerline': 1.0, 'Heatline': 1.0}
  energy carrier                    -                                                cbe
  energy sector                     -                                            coupled
  region                            -                                     example region
  component                         -                                        transformer
  node_type                         -                      Combined Heat and Power Plant
  latitude                          -                                           53.46025
  longitude                         -                                           9.969309
  load                         $P(t)$  {'CBE Bus': [-10.0, -10.0, -10.0], 'Heatline':...
  net energy flow       $\sum_t P(t)$              {'Powerline': 12.0, 'Heatline': 15.0}
  specific costs           $c_{flow}$                {'Powerline': 2.0, 'Heatline': 1.0}
  specific emissions       $e_{flow}$                {'Powerline': 0.0, 'Heatline': 0.0}

Compilation Utility Source Code
===============================
The utility can be accessed via tessif as demonstrated above using
:func:`tessif.transform.es2mapping.compile_result_data_representation`.

.. literalinclude::
   ./compile_rdr.py


Raw Energy System Data
======================
Following are the raw data files with which the energy system above was created.

Original Data -- Configuration File **Busses**
----------------------------------------------
.. literalinclude::
   ./esm/busses.cfg

Original Data -- Configuration File **Sources**
-----------------------------------------------
.. literalinclude::
   ./esm/sources.cfg

Original Data -- Configuration File **Sinks**
-----------------------------------------------
.. literalinclude::
   ./esm/sinks.cfg

Original Data -- Configuration File **Transformers**
----------------------------------------------------
.. literalinclude::
   ./esm/transformers.cfg

Original Data -- Configuration File **Timeframe**
-------------------------------------------------
.. literalinclude::
   ./esm/timeframe.cfg

Original Data -- Configuration File **Global Constraints**
-----------------------------------------------------------
.. literalinclude::
   ./esm/global_constraints.cfg   
