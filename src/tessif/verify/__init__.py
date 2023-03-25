# tessif/verify/__init__.py
"""
:mod:`~tessif.verify` is a :mod:`tessif` subpackage aggregating functionalities
to verify expected software integration. It offers simple tools to
automate testing for correct implementations. It does so by providing a set of
simplified energy system model scenario combinations isolating individual
behavioural constriants in conjunction with a respective set of expected
results.

To test for expected behaviour is as simple as creating a Verificer object
stating the desired constraints and softwares.
"""
from .core import Verificier
from .create import ScenarioJuggler
