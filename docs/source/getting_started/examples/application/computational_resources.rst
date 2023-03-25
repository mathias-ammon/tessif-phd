.. _Examples_Application_Computational:

Estimating Computational Resources
**********************************

When comparing energy system simulation models it is often of great interest on how efficient they utilize memory and cpu power.

The :mod:`Application/computational_resources <tessif.examples.application.computational_resources>` example module aggregates explanatory details on how to use tessif's :mod:`analyzing <tessif.analyze>` utilities.
Further more it illustrates how these utilities can be used in a scientific context.


.. contents:: Contents
   :local:
   :backlinks: top

Introduction
============


Analyzed Energy System
======================

Short description and a nxgraph chart


Resource Comparision
====================

Time
----
Code snippet using tessif.analyze.Comparatier.bar_chart(resutls_to_compare=time)

Memory
------
Code snippet using tessif.analyze.Comparatier.bar_chart(resutls_to_compare=memory)

Scalability
-----------
Code snippet using tessif.analyze.Comparatier.scalability_charts_2D()
Code snippet using tessif.analyze.Comparatier.scalability_charts_3D()

Table containing the model name and their evaluated big o notation
(https://en.wikipedia.org/wiki/Big_O_notation)

+-----+--------+----+
|model|N       |T   |
+=====+========+====+
|oemof|O(n^1.2)|O(n)|
+-----+--------+----+
|pypsa|O(n^1)  |O(n)|
+-----+--------+----+


Used Utilities
==============

.. automodule:: tessif.examples.application.computational_resources
   :members:

