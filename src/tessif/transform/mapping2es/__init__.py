# tessif/transform/mapping2es/__init__.py
"""
Tessif subpackage to transform energy system mappings to ready-to-simulate
energy system models. Mapping in this conntext refers to `data mappings
<https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`_.

The heavy lifting of the transformation process is done by a respective
energy system model module (aka
:mod:`mapping2es.omf<tessif.transform.mapping2es.omf>` for :any:`oemof`).

The module extracts the information out of the mapping and parses the model
parameters to return a ready-to-simulate energy system model for its
repsective api.

The beforementioned approach results in following benefits:

    1. Energy system data input format can be abstracted from the model used.
    2. Adding additonal moduls to transform concrete
       (modules inside :mod:`tessif.transform.mapping2es`)  or abstract
       (:mod:`tessif.transform.mapping2es.tsf`) data mappings
       is enough to support new, yet unsupported energy system simulation
       tools.
"""
