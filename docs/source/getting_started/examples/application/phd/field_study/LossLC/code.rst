.. _LossLC_code:

Code Base
*********
Following section display the code snippets that were used to create the
TransC/E results and diagrams.

.. contents:: Contents
   :local:
   :backlinks: top


.. _LossLC_creation:

System-Model-Scenario-Combination Creation Code
===============================================

Following code snippet shows how to create the TransC/E combinations
  

.. literalinclude::
   ./creation.py   


Generic Graph
=============

The ``LossLC`` :ref:`LossLC_gengraph` image was crated using following code
snippet:

.. literalinclude::
   ./generic_graph.py



Optimization Results
====================
Shown below, is the code to generate the LossLC results. Use the ``PERIODS``
constant to adjust the simulated time span. Results displayed were created
using ``PERIODS = 24``.


.. _LossLC_resgen_optimize:

Optimize and Post Process via Tessif
------------------------------------
Following script uses the :ref:`LossLC creation skript <LossLC_creation>`
above to generate and tessif internally post-process the optimization results,
ready for further analysis.

.. literalinclude::
   ./optimize.py

.. _LossLC_resgen_post_process:

Aggregate, Compare, and Store Representative Results
----------------------------------------------------
Following script takes the :ref:`stored and post processed results
<LossLC_resgen_optimize>` from the optimization process above and turns them
into representative csv files shown in the :ref:`results section
<LossLC_results>`.

.. literalinclude::
   ./post_process.py


.. _LossLC_igr_plots:

IGR Bar Plot Code
-----------------
The Integrated Global Result bar plots from above are created using following code:

.. literalinclude::
   ./igr_plots.py


.. _LossLC_ressources_code:

Comutational Ressources
=======================

Computational Ressources Estimation Code
----------------------------------------
The computational ressources bar plots from above are created using following code:

.. literalinclude::
   ./computational.py
   
.. _LossLC_ressources_plots:

Computational Ressources Plots
------------------------------
The computational ressources bar plots from above are created using following code:

.. literalinclude::
   ./computational_graphs.py   




