.. _CompCnE_code:

Code Base
*********
Following section display the code snippets that were used to create the
CompC/E results and diagrams.

.. contents:: Contents
   :local:
   :backlinks: top


.. _CompCnE_creation:

System-Model-Scenario-Combination Creation Code
===============================================

Following code snippet shows how to create the CompC/E combinations
  

.. literalinclude::
   ./creation.py   


Generic Graph
=============

.. literalinclude::
   ./generic_graph.py


.. _CompCnE_code_resgen:

Optimization Results
====================   
Shown below, is the code to generate the CompC and CompE results. Use the
``PERIODS`` constant to adjust the simulated time span. And the ``Expansion``
constant to switch between CompC and CompE.

Results displayed were created using ``PERIODS = 24``.

.. _CompCnE_code_resgen_optimize:

Optimize and Post Process via Tessif
------------------------------------
Following script uses the :ref:`CompC/E creation skript <CompCnE_creation>`
above to generate and tessif internally post-process the optimization results,
ready for further analysis.

.. literalinclude::
   ./optimize.py


Aggregate, Compare, and Store Representative Results
----------------------------------------------------
Following script takes the :ref:`stored results
<CompCnE_code_resgen_optimize>` from the optimization process above and turns
them into representative csv files shown in the :ref:`results section
<CompCnE_relevant_results>`.

.. literalinclude::
   ./post_process.py


.. _CompCnE_code_igr_plots:

IGR Bar Plot Code
-----------------
The CompC/E "Integrated Global Result" bar plots are created using following code:

.. literalinclude::
   ./igr_plots.py

Installed Compfer Grid Capacity
--------------------------------
The CompC/E "Installed Compfer Grid Capacities" bar plots are created using
following code:

.. literalinclude::
   ./installed_capacities.py

Summed Load Bar Plots
----------------------
The CompC/E summed load bar plots are created using following code:

.. literalinclude::
   ./summed_load_bar_plots.py

Load Probile Plots
------------------
The CompC/E load profile plots are created using following code:

.. literalinclude::
   ./load_profile_plots.py


.. _CompCnE_code_computational_results:


Computational Results
=====================

Computational Ressources Estimation Code
----------------------------------------
The computational ressources bar plots are created using following code:

.. literalinclude::
   ./computational.py
   
.. _CompCnE_code_computational_plots:

Computational Ressources Plots
------------------------------
The computational ressources bar plots are created using following code:

.. literalinclude::
   ./computational_graphs.py   
