# tessif/model/__init__.py
"""
:mod:`~tessif.model` is a :mod:`tessif` subpackage providing tessif's own
:mod:`energy system simulation model <tessif.model.energy_system>`.

The model serves several purposes:

    1. To provide an engineering friendly interface for parameterizing
       :mod:`energy system components <tessif.model.components>`.

       Meaning parameters are attributed directly to the components as opposed
       to the more optimization-problem oriented approach of providing
       interfaces designed to match solver needs.

       This also means that there is quite some redundancy in hardcoding the
       :mod:`energy system components <tessif.model.components>`, making it
       easier for engineers to tinker with and expand the code without breaking
       other components.

    2. To provide a simple yet powerful data input interface being both
       machine **and** human friendly.

    3. To be an abstract base model serving as base for the automated
       :mod:`transformation
       <tessif.model.energy_system.AbstractEnergySystem.to_nxgrph>` process of
       energy system data into other
       :mod:`energy system simulation models <tessif.simulate>`.
"""
