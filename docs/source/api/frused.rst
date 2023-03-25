frused
======

.. automodule:: tessif.frused
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 1

   frused/configurations
   frused/defaults
   frused/hooks
   frused/namedtuples
   frused/paths
   frused/resolutions
   frused/spellings
   frused/themes

- :mod:`~tessif.frused.configurations` is a :mod:`tessif` subpackage for providing simulative configurations like:

   - Temporal resolution
   - Naming conventions
   - Unit convention

   It serves as main tweaking point for adjusting simulation behavior.


- :mod:`~tessif.frused.defaults` is a :mod:`tessif` subpackage for providing:

   - Fallback values for:
     - Visualization
     - Energy system component parameterization
   - Filter prefixes for result parsing
   - Sorting templates for data input parsing

   It serves as main reference point for how :mod:`tessif` expects user and
   model related data streams to look like.


- :mod:`~tessif.frused.namedtuples` is a :mod:`tessif` subpackage providing
  :attr:`collections.namedtuple` objects for:

   - :ref:`Tessif's labeling concept <Labeling_Concept>`
   - Tessif's model parameterization
   - Result parsing

   It serves as main reference point for how :mod:`tessif` approaches naming
   conventions.

- :mod:`~tessif.frused.paths` is a :mod:`tessif` subpackage providing
  path strings for

   - Accessing :mod:`Tessif's Example Hub <tessif.examples>`
   - Used logging output
   - Used data output
   - Navigating inside tessif's install directory

   It serves as main reference point for software location information.

- :mod:`~tessif.frused.resolutions` is a :mod:`tessif` subpackage providing
  mappings for failsafe and convenient accesss to:

   - Temporal resolution settings
   - Temporal rounding settings

- :mod:`~tessif.frused.spellings` is a :mod:`tessif` subpackage providing

   - Aliases and variations of the parameters tessif expects

   It serves as :mod:`tessif's <tessif>` main data input abstraction mechanism and
   is the main reference point for expanding these capabilities.

- :mod:`~tessif.frused.themes` is a :mod:`tessif` subpackage providing

   - Color and hatch themes
   - Color and hatch maps
   - Color cycles

   Grouped by :attr:`~tessif.frused.namedtuples.NodeColorGroupings` for
   convenient automated access.
   
   It serves as :mod:`tessif's <tessif>` main reference point for automatically
   parsing results into visually distinguishable information.
