.. _AdddingNewModels:

Adding New Models
=================

.. contents::
   :depth: 1
   :local:
   :backlinks: top
               
Following sections present a conceptual overview, as well as a step by step
example on how to incorporate yet unsupported models into Tessif.

The incorporation procedure is divided into 4 different categories:

   0. Writing a python interface based on :ref:`Tessif's model terminology <Model_Terminology>`
      representing an energy supply system.

      This step is independent of the steps 1 to 3 but a requirement for them. Therfor this
      is usually the first thing to do, if necessary.

      .. note::
         For most python based energy supply system simulation tools such an
         interface already exists. For most non-python based tools however you
         need to write your own interface
      
   1. Adding Tessif's :ref:`Post Processing Capabilities
      <AdddingNewModels_PostProcessing>`

      This step is independent of the following two but required by them. Hence it is
      usually the first thing to implement.
      
   2. Adding :ref:`Full Support <AdddingNewModels_FullSupport>`

      This step includes step 1, but is independent of step 3. It represents
      the standard use case when :ref:`utilizing Tessif for what it was designed
      for <Introduction_Purpose>`, comparing and unifying energy supply system
      simulation models.
      
   3. Adding :ref:`Direct Model Support <AdddingNewModels_Input>`

      This step includes step 1, but is independent of step 2. It basically
      consists of adding Tessif's :ref:`data format specific
      <SupportedDataformats>` input :ref:`parsing capabilities <Data_Input>`
      and a python interface for starting the simulation.

      Standard use case for just implementing step 1 and 3 is
      utilizing Tessif's in- and output capabilities but not caring about
      Tessif's :mod:`energy system <Tessif.model.energy_system>` being
      :mod:`transformable <Tessif.transform.es2es>` into a python based
      :ref:`model <Model_Terminology>` representation.

   
0. Writing a python interface based on :ref:`Tessif's model terminology <Model_Terminology>`
--------------------------------------------------------------------------------------------
Following descriptions give detailed overview on how to write a python
interface for non python based energy supply system simulation code so it can
be utilized in Tessif.

      
.. _AdddingNewModels_PostProcessing:

1. Adding Tessif's Post-Processing Capabilities
-----------------------------------------------
Following paragraphs discuss the topic of incorporating a python based post
processing interface for a new unsupported :ref:`model <Model_Terminology>` using
Tessif.


Use Case
^^^^^^^^
Using Tessif's Post Processing Capabilities like it's :ref:`Visualization` and
:mod:`Data Extraction <tessif.transform.es2mapping>` for:
     
  1. Other python based energy supply system simulation libraries
  2. Numerical optimization tools written in other languages
     (Convention calls for an actual energy system object as input, the code
     written for the :mod:`Data Extraction <tessif.transform.es2mapping>`
     mechanisms, however is just an interface returning a mapping)
     

Recommended Procedure
^^^^^^^^^^^^^^^^^^^^^
Implementing new model support for Tessif's post processing capabilities
includes following steps:

   1. Creating a minimum working example as in
      :meth:`tessif.examples.data.tsf.py_hard.create_mwe` or in
      :meth:`tessif.examples.data.omf.py_hard.create_mwe` and create
      a respective description in
      :ref:`docs/source/usage/supported_models/model_name.rst
      <Models_Tessif_Mwe>`.

      This serves as both, a how to for you and your audiance, as well as a
      doctesting utility for testing and developing any further tessif support.
   2. Implementing a ``model_name`` (or abbrevatiion) module inside
      :mod:`tessif.transform.es2mapping`.

      So for incorporating i.e. `PyPSA <https://pypsa.org/>`_. A
      :mod:`tessif.transform.es2mapping.ppsa` module would be implemented.

      This module's task is to extract the simulation results out of the model's
      python based interface. It does so by providing :class:`Transformer
      <tessif.transform.es2mapping.base.ESTransformer>` child classes which
      specialize on extracting and post processing certain categories of
      results. For a list of :ref:`necessary child classes
      <Resultiers_to_Implement>`, refer to the
      :mod:`es2mapping.base <tessif.transform.es2mapping.base>` module.
      

.. _AdddingNewModels_FullSupport:

2. Adding Full Tessif Support
-----------------------------
The following paragraphs explain how to fully incorporate an unsupported model
into Tessif and why that might be useful.

.. contents::
   :depth: 1
   :local:
   :backlinks: top

Use Case
^^^^^^^^
Implementing full Tessif support is useful for:

   1. Utilizing :mod:`Tessif's Model Comparison Utilities <Tessif.analyze>`
   2. Wrapping other python based energy supply system simulation interfaces in
      Tessif's :mod:`Input Parsing <Data_Input>` and
      :ref:`Visualization Capabilities <Visualization>`.


Recommended Procedure
^^^^^^^^^^^^^^^^^^^^^

In addition to :ref:`Adding Tessif's Post Processing Capabilities
<AdddingNewModels_PostProcessing>` following steps are necessary to
realize a full support:

   1. Eins
   2. Zwei

.. _AdddingNewModels_Input:

3. Adding Direct Model Support / Tessif Input Capabilities
----------------------------------------------------------

Following paragraphs describe how to utilize Tessif's :ref:`data format specific
<SupportedDataformats>` input :ref:`parsing capabilities <Data_Input>` to write
a python interface that reads in model flavored data (as opposed to
:ref:`Tessif flavored <SupportedDataFormats_Concept>` data) as well as a python
interface for conducting the simulation.

.. contents::
   :depth: 1
   :local:
   :backlinks: top

Use Case
^^^^^^^^
Implementing direct model support via Tessif can be useful for:

   1. Utilizing Tessif's in- and output capabilities but not caring about
      Tessif's :mod:`energy system <Tessif.model.energy_system>` being
      :mod:`transformable <Tessif.transform.es2es>` into a python based
      :ref:`model <Model_Terminology>` representation.


Recommended Procedure
^^^^^^^^^^^^^^^^^^^^^

In addition to :ref:`Adding Tessif's Post Processing Capabilities
<AdddingNewModels_PostProcessing>` following steps are necessary to
realize a full support:

   1. Eins
   2. Zwei
