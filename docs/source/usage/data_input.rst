.. _Data_Input:

Data Input
**********

Data input inside :mod:`tessif` is handled by the :mod:`~tessif.parse` module.
It provides read-in capabilities for processing numerous
data types storing energy system information and transforms this information
into a python manageable :class:`mapping<collections.abc.Mapping>`.

Which utility to use depends on the input data format at hand. Usually recognizable
via the `filename extensions
<https://en.wikipedia.org/wiki/Filename_extension>`_.

.. contents::
   :local:
   :depth: 1

.. _SupportedDataFormats_Concept:

Concept
=======

Inside :mod:`tessif` every bulk of logically grouped data is realised as
`mapping <https://en.wikipedia.org/wiki/Associative_array>`_. The main concept
of data input is no different. Hence all of the supported data formats
represent a kind of mapping. These mappings are
transformable by tessif's :mod:`parse <tessif.parse>` functions.

All of them return a nested :any:`dictionairy <dict>` (one of python's native
forms of mappings) with a :class:`pandas.DataFrame` (one of python's
`spreadsheet <https://en.wikipedia.org/wiki/Spreadsheet>`_ like objects) for
each group of :ref:`energy system component <Models_Tessif_Concept_ESC>` at it's
core.

.. _SupportedDataformats:

Supported Data Formats
======================
The following sections provides a brief overview of the supported input data formats
as well as consequential links for more detailed information.

.. note::
   The current support of the various input data formats
   (with the exception of :ref:`Hardcoded Python Instance Objects
   <SupportedDataFormats_HardCodedPythonObjects>`) can be gauged and expanded using the
   :mod:`tessif.parse` module.

.. contents::
   :local:


.cfg
----
`Configuration file formats <https://en.wikipedia.org/wiki/Configuration_file#Unix_and_Unix-like_operating_systems>`_ are simple yet powerful data formats for storing key-value pair based information (mappings). They are also editable by most operating systems and softwares. And as such they are an ideal candidate for storing energy system data for tessif, since they are easily read and edited by humans and machines alike.

The most common `filename extensions <https://en.wikipedia.org/wiki/Filename_extension>`_ are:

    - cf
    - cfg
    - cnf
    - conf
    - ini
      
Tessif's support for config files is two folded.

.. _SupportedDataFormats_FlatConfigurationFiles:

1. Flat Configuration Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Flat configuration files in this context are understood as config files with only
one type of :ref:`energy system component <Models_Tessif_Concept_ESC>`. Meaning there
is one file for :class:`Busses <tessif.model.components.Bus>` one for all the
:class:`Sources <tessif.model.components.Source>`, and so on. Additionally there
is one specifying the timeframe.

Each component entity (e.g. ``my_bus_1``, ``my_bus_2``, ...) is seperated by individual `Sections <https://en.wikipedia.org/wiki/INI_file#Sections>`_. An example for this can be found in :ref:`tessif.examples.data.tsf.cfg.flat <Examples_Tessif_Config_Flat>`.

Typical data/folder structures for storing energy system data in flat config files look like::

  energy_systems
  |
  |-my_energy_system_1
  | |-busses.cfg
  | |-sinks.cfg
  | |-storages.cfg
  | |-sources.cfg
  | |-timeframe.cfg
  | |-transformers.cfg
  |
  |-my_energy_system_2
  | |-busses.cfg
  | |-sinks.cfg
  | |-storages.cfg
  | |-sources.cfg
  | |-timeframe.cfg    
  | |-transformers.cfg


The advantages of using flat configuration files (as opposed to :ref:`nested configuration files <SupportedDataFormats_NestedConfigurationFiles>`) are:

  - Existance of a standard library :mod:`parsing utility <configparser>`
  - Data files are shorter/smaller since they are seperated into each
    :ref:`energy system component <Models_Tessif_Concept_ESC>` by design.

Disadvantages are:

  - Need of up to 6 files for storing one energy system and the subsequent file input/output streaming overhang
    
.. _SupportedDataFormats_NestedConfigurationFiles:

2. Nested Configuration Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _SupportedDataFormats_HDF5:

.hdf5
-----

`Hierarchical Data Format 5 (HDF5) <https://en.wikipedia.org/wiki/Hierarchical_Data_Format>`_
is a data format designed to store and organize large amounts of data. One of
its advantages is that it is possible to not load the complete file into the
memory but only the needed parts of a file. HDF5 has a low latency and high
throughput compared with other ways to store data. It is supported by many
programming languages and operating systems.

Tessif expects HDF5 files to be written in such a way that there is a group for
each kind of :ref:`energy system component <Models_Tessif_Concept_ESC>` as well
as one for the timeframe and one defining the global constraints. Each of these
groups has a subgroup for each of that component's entities which contains
groups and datasets that store the parameters of that component.

An example can be found in
:ref:`tessif.examples.data.tsf.hdf5 <Examples_Tessif_HDF5>`.

.json
-----

.py
---
Python files are the most native in regard to tessif since it is written in
python. It is therefore possible to hardcode energy system objects explicitly.

The support for energy system data represented in python files can be seperated
into the following two major categories.

.. _SupportedDataFormats_HardCodedPythonObjects:

1. Hardcoded Python Instance Objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Hardcoded python instance objects representing energy system components of the
energy system simulation model to use are also a valid option for providing
data. Most common use cases for this approach depending on the users python
programing skill level are:

    - Beginning and intermediate skilled python programers:

      - Already existing code due to exclusive use of the supported energy
        system simulation model prior to using tessif
      - Desire to get more familiar with tessif or the energy system
        simulation model of choice

    - Advancedd python programers:
      
      - `Monkey Patching <https://en.wikipedia.org/wiki/Monkey_patch>`_
        the existing infrastructure
      - Automating the input data process generation utilizing instance
        objects directly

Examples can be found :ref:`here (detailed) <Models_Tessif_Fpwe>` and
`here (subsections: 'data/py - hardcoded') <Examples>`_.


.. _SupportedDataFormats_PurePythonMappings:

Once the energy system call instance has been coded, it can be accessed via
(assuming the energy system is created using a function called ``CREATE_MY_ENERGY_SYSTEM``
an the corresponding module is found at ``PATH``)::

  from PATH import CREATE_MY_ENERGY_SYSTEM

For the beforenamed `example hub <Examples>`_ this would result in::

  from tessif.examples.data.tsf.py_hard import create_fpwe
  es = create_fpwe()

2. Pure Python Mappings
^^^^^^^^^^^^^^^^^^^^^^^
In addition to hardcoded python objects, energy systems can also be stored as python
manageable mappings (or pure python mappings). Meaning every energy system can also be represented as nested :any:`dictionairy <dict>`.

Most common use cases (again depending on the programers skill level) are:

    - Beginning an intermediate skilled python programers:
      
      - Having 3rd party or custom written code/libraries returning
        :any:`dictionairies <dict>` (since it's one of the most commonly used
        throughout python projects)
      - Deepening the understanding of the transition from raw data formats
        to actual python obects using a nested :any:`dictionairy <dict>` as a
        raw data set
      - Understanding how almost every energy system data set can be interpreted
        as mapping

    - Advanced python programers:

      - Avoiding object creation overhang (mostly keyword characters) in huge
        datasets
      - Automating the input data process generation utilizing pure python
        mappings directly

Examples can be found
`here (subsections: 'data/py - mapping') <Examples>`_.

Once the energy system mapping has been coded it can accessed via
(assuming the energy system mapping is stored in a variable called
``MY_ENERGY_SYSTEM_MAPPING`` of which the corresponding module can be
found in ``PATH``)::

  from PATH import MY_ENERGY_SYSTEM_MAPPING
  
It then needs to be parsed by :meth:`tessif.parse.python_mapping` to ensure it is ready
to be :mod:`transformed from a mapping to an energy system
<tessif.transform.mapping2es>`::

  import tessif.transform.mapping2es.tsf as tsf
  import tessif.parse as parse
  
  energy_system = tsf.transform(
      parse.python_mapping(MY_ENERGY_SYSTEM_MAPPING))

Where ``tsf`` can also be one of the supported energy system models.

For the beforenamed `example hub <Examples>`_ this would result in::

  from tessif.examples.data.tsf.py_mapping.fpwe import fpwe_mapping
  from tessif.transform.mapping2es import tsf
  import tessif.parse as parse
  
  energy_system = tsf.transform(parse.python_mapping(fpwe_mapping))

.. note::
   This approach also illustrates how all the other mappings of different data
   formats are processed.
   
.sdp
----


.. _SupportedDataFormats_Spreadsheet:
   
.xlsx - like
------------
Within the context of tessif ``xlsx - like`` stands for xml based spreadsheet
representing data like `xlsx (Microsoft Excel)
<https://en.wikipedia.org/wiki/Microsoft_Excel>`_ and
`ods (Open Document Spreadsheet)
<https://en.wikipedia.org/wiki/OpenDocument#Specifications>`_.

Although not an ideal data format from a programers point of view, supporting
spreadsheet like data representations yields following benefits:

    - Decoupling data input and programing skills, which can be useful for:

      - Educational projects
      - Sharing workloads among teams and personel
      - Lowering the threshold for getting familiar with tessif
      - Providing backwards compatability to old-school engineering

    - Enabling `vba
      <https://en.wikipedia.org/wiki/Visual_Basic_for_Applications>`_ based
      preprocessing

    - Building a bridge between `open science
      <https://en.wikipedia.org/wiki/Open_science>`_ and `proprietary
      <https://en.wikipedia.org/wiki/Proprietary_software>`_ helpers


.. _SupportedDataFormats_Xml:

.xml
----
`XML <https://en.wikipedia.org/wiki/XML>`_ is a markup language to write data
in a hierarchical structure. Its flexibility and its widespread use make it a
viable option for storing tessifs energy system mappings.

Tessif expects xml files to be written in such a way that there is an element
for each :ref:`energy system component <Models_Tessif_Concept_ESC>` as well as
one for the timeframe. Each element has a subelement for each entity of the
component/timeframe. Its parameters are stored as the attributes of the
subelement.

An example can be found in :ref:`tessif.examples.data.tsf.xml <Examples_Tessif_Xml>`.

.yaml
-----
