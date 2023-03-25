.. _TransCnE_code:

Code Base
*********
Following section display the code snippets that were used to create the
TransC/E results and diagrams.

.. contents:: Contents
   :local:
   :backlinks: top


.. _TransCnE_creation:

System-Model-Scenario-Combination Creation Code
===============================================

Following code snippet shows how to create the TransC/E combinations
  

.. literalinclude::
   ./creation.py   


Generic Graph
=============

.. literalinclude::
   ./generic_graph.py


.. _TransCnE_code_resgen:

Optimization Results
====================   
Shown below, is the code to generate the TransC and TransE results. Use the
``PERIODS`` constant to adjust the simulated time span. And the ``Expansion``
constant to switch between TransC and TransE.

Results displayed were created using ``PERIODS = 24``.

.. _TransCnE_code_resgen_optimize:

Optimize and Post Process via Tessif
------------------------------------
Following script uses the :ref:`TransC/E creation skript <TransCnE_creation>`
above to generate and tessif internally post-process the optimization results,
ready for further analysis.

.. literalinclude::
   ./optimize.py


Aggregate, Compare, and Store Representative Results
----------------------------------------------------
Following script takes the :ref:`stored results
<TransCnE_code_resgen_optimize>` from the optimization process above and turns
them into representative csv files shown in the :ref:`results section
<TransCnE_relevant_results>`.

.. literalinclude::
   ./post_process.py


.. _TransCnE_code_igr_plots:

IGR Bar Plot Code
-----------------
The TransC/E "Integrated Global Result" bar plots are created using following code:

.. literalinclude::
   ./igr_plots.py

Installed Transfer Grid Capacity
--------------------------------
The TransC/E "Installed Transfer Grid Capacities" bar plots are created using
following code:

.. literalinclude::
   ./installed_capacities.py

Summed Load Bar Plots
----------------------
The TransC/E summed load bar plots are created using following code:

.. literalinclude::
   ./summed_load_bar_plots.py

Load Probile Plots
------------------
The TransC/E load profile plots are created using following code:

.. literalinclude::
   ./load_profile_plots.py


.. _TransCnE_code_computational_results:

Redispatch
==========
The redispatch calculations are done using following code:

.. literalinclude::
   ./redispatch.py

Circulation
===========
The energy circulation calculations are done using following code:

.. literalinclude::
   ./circulate.py


Computational Results
=====================

Computational Ressources Estimation Code
----------------------------------------
The computational ressources bar plots are created using following code:

.. literalinclude::
   ./computational.py
   
.. _TransCnE_code_computational_plots:

Computational Ressources Plots
------------------------------
The computational ressources bar plots are created using following code:

.. literalinclude::
   ./computational_graphs.py   
