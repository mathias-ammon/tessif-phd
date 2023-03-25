from tessif import simulate
from tessif.transform.es2mapping import omf
from tessif.frused.paths import example_dir
from tessif import parse
import os
import functools

es = simulate.omf(
     path=os.path.join(
         example_dir, 'omf', 'xlsx', 'energy_system.ods'),
     parser=functools.partial(parse.xl_like,
                              sheet_name=None,
                              engine='odf'),
     solver='glpk'
)
