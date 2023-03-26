# tessif/frused/configurations
# -*- coding: utf-8 -*-
"""
:mod:`~tessif.frused.configurations` is a :mod:`tessif` subpackage aggregating
simulation parameters, used naming and unit conventions as well as some
logging behavior.

It serves as main reference point for adjusting tessif's simulative and
parsing behavior.
"""
import os
from tessif.frused.paths import log_dir

temporal_resolution = 'hourly'
"""
Currently used temporal resolution. Must be one of the keys found in
:attr:`~tessif.frused.resolutions.temporals`.
"""

node_uid_style = 'name'
"""
Switch for tweaking internal node uid representation style.

Useful for conveniently changing internal mapping behaviour. Must be one of
:attr:`~tessif.frused.namedtuples.node_uid_styles`.

Somehting like ``name`` allows for quick and intuitive node accessing while
sacrificing the possibility of 2 nodes having the same
:paramref:`~tessif.frused.namedtuples.uid.name`.

``qualname`` on the other hand maps everything to the fully qualified name.
Meaning only ever the full combination of all
:class:`~tessif.frused.namedtuples.uid` attributes has to be unique per
energy system.

.. warning::

    Tessif's doctests assumes ``node_uid_style = 'name'`` which is the most
    basic and intuitive way of mapping nodes. Designed for the use of
    relatively small energy systems (what ever that means).

For a list of available styles and their key (the string set to
:attr:`node_uid_style`) see :attr:`tessif.frused.namedtuples.node_uid_styles`.
"""

node_uid_seperator = '_'
"""
Seperate different tags of the same
:attr:`node uid <tessif.frused.namedtuples.uid>`

Seperate symbol for (uniquely) identifying a node's uid using various tags of
the :attr:`namedtuples implementation <tessif.frused.namedtuples.uid>`.
"""

timeseries_seperator = '.'
"""
Seperate energy system object and timeseries value.

Serperator symbol for identifying energy system object and its timeseries
values when reading in data.

Standard syntax::

    {ES_OBJECT}{SEPERATOR}{TIMESERIES_PARAMETER}.
"""

mimos = 10
"""
Number of seperate inputs/outputs supported for multiple input output energy
system transformers.

Currently set to:
"""

power_reference_unit = 'MW'
"""
Unit to display power results with.
"""

cost_unit = '€'
"""
Unit representing the costs.
"""

#: Dictionairy configuring tessif's logging locations and file names
logging_file_paths = {
    'debug': os.path.join(log_dir, 'debug.log'),
    'content': os.path.join(log_dir, 'content.log'),
    'timings': os.path.join(log_dir, 'timings.log'),
}
"""
Tessif's logging locations and filenames.

Warning
-------
Logging root directory must exist for the logging file location configuration
to work as expected.
"""

spellings_logging_level = 'warning'
"""
`logging level
<https://docs.python.org/3/library/logging.html#logging-levels>`_
used by :meth:`spellings.get_from <tessif.frused.spellings.get_from>`.

Must be one of the keys found in :attr:`~tessif.write.log.logging_levels`.
"""
