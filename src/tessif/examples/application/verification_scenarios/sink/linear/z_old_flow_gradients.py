import tessif.frused.namedtuples as nts
import numpy as np
import pandas as pd

# flow_gradients

# one source, three sinks
# sinks differ from each other in parametrization of flow_gradients and flow_costs
# flow gradients are chosen to be transient between s1 and s2 but not transient between s2 and s3
# due to the flow cost parameter, two changes are forced: 1) from s1 to s2 and 2) from s2 to s3
# expected behaviour:

# ------------------
# NEEDS MORE TESTING
# maybe work with additional storage, that feeds sinks in case of non matching flow_gradients?
# need to finish scenario for source first
# ------------------

