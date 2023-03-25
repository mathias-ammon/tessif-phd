# tessif/parse.py
"""
:mod:`~tessif.parse` is a :mod:`tessif` module for reading energy
system data.

Each function returns a mapping representation the read in data ready to
be passed to a :mod:`~tessif.transform.mapping2es` module to turn it into a
ready to simulate energy system model.

In case the stored data representation was designed according to the desired
simulation tool, the respective transformation module can be found in
:mod:`transform.mapping2es <tessif.transform.mapping2es>`).

If not designed to -- or in case of a more general  approach -- an abstract
data format can be used and then be transformed according to the needs of the
desired tool by using one of the transformation engines found in
:mod:`transform.mapping2es.tsf<tessif.transform.mapping2es.tsf>`.
"""
from pathlib import Path
import importlib
import os
import pandas as pd
import numpy as np
import logging
from tessif.frused import spellings, configurations
from tessif.frused.defaults import energy_system_nodes as esn_defs
from tessif.write import log
import tessif.frused.defaults as defaults
import ast
import configparser
import collections
import xml.etree.ElementTree as ET
import h5py
logger = logging.getLogger(__name__)


@log.timings
def flat_config_folder(folder, timeframe='primary',
                       global_constraints='primary', **kwargs):
    """Parse config files inside folder into a dict of pandas.DataFrames.

    Read in flat :any:`mappings <dict>` in `configuration file format
    <https://en.wikipedia.org/wiki/Configuration_file#Unix_and_Unix-like_operating_systems>`_
    and transform them into :class:`pandas.DataFrame` objects keyed by their
    :ref:`energy system components <Models_Tessif_Concept_ESC>` (i.e.
    'sources', 'busses', etc..). As well as a :class:`pandas.DataFrame`
    object keyed by :attr:`~tessif.frused.spellings.timeframe`.

    Parameters
    ----------
    folder: ~pathlib.Path, str
        Path or string representation of a path specifying a folder containing
        flat :any:`mappings <dict>` in `configuration file format
        <https://en.wikipedia.org/wiki/Configuration_file#Unix_and_Unix-like_operating_systems>`_

    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used. Expected to correspond with
        `section <https://en.wikipedia.org/wiki/INI_file#Sections>`_ headers.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'tf1'`` if the corresponding
        section header is named ``'tf1'``)

    global_constraints: str, default='primary'
        String specifying which of the (potentially multiple) set of
        constraints passed is to be used. Expected to correspond with
        `section <https://en.wikipedia.org/wiki/INI_file#Sections>`_ headers.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'global_constraints_1'`` if the
        corresponding section header is named ``'global_constraints_1'``)

    kwargs:
        warning
        -------
        Not implemented yet.

    Return
    ------
    mapping: :class:`~collections.abc.Mapping`
        of :class:`DataFrames<pandas.DataFrame>` to their
        :ref:`energy system component identifier
        <Models_Tessif_Concept_ESC>` ('sources', 'storages' etc..)
        As well as a singular :class:`~pandas.DataFrame` mapped to
        :attr:`~tessif.frused.spellings.timeframe`.

    Note
    ----
    For more on flat config data formats see :ref:`Flat Configuration Files
    <SupportedDataFormats_FlatConfigurationFiles>`

    Example
    -------
    Read in tessif's :ref:`fully parameterized working example
    <Models_Tessif_Fpwe>` in flat configuration file format:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> import tessif.parse as parse
    >>> es_dict = parse.flat_config_folder(
    ...     folder=os.path.join(example_dir, 'data', 'tsf',
    ...                         'cfg', 'flat', 'basic'))
    >>> print(type(es_dict))
    <class 'collections.OrderedDict'>
    """
    extensions = ['.cf', '.cfg', '.conf', '.ini', '.config', 'txt']
    configuration_files = [os.path.join(folder, f)
                           for f in os.listdir(os.path.abspath(folder))
                           if any(ext in f for ext in extensions)]

    # Figure out the component names by looking it up in spellings
    component_names = \
        spellings.energy_system_component_identifiers.component.keys()

    # create the initial mapping
    mapping = collections.OrderedDict()

    # iterate through component
    for component in component_names:

        # iterate through each configuration file
        for configuration_file in configuration_files:

            config_file_name = os.path.basename(configuration_file)
            # accept any spelling of component as found in frused.spellings
            if any(variation in config_file_name for variation in getattr(
                    spellings, component)):
                # allow separate iteration by individually creating parsers:
                config = configparser.ConfigParser()
                config.read(configuration_file)

                # mapping holding individual entities for each component
                entities = {}
                for component_entity in config.sections():

                    # mapping holding the entities parameters
                    parameters = {}

                    for parameter, value in config.items(component_entity):
                        param = ast.literal_eval(parameter)
                        val = ast.literal_eval(value)

                        if param == "timeseries":
                            if val:
                                val = _unstringify_timeseries(val)

                        parameters[param] = val

                    # fill the entities mapping with the parameters dict
                    entities[component_entity] = parameters
                # fill the energy system mapping with the components
                mapping[component] = entities

    # optimizatin time span parsing is handled separately
    # because it's a 'one column' DF
    for configuration_file in configuration_files:

        # allow different spellings of timeframe.cfg
        config_file_name = os.path.basename(configuration_file)
        if any(variation in config_file_name for variation in getattr(
                spellings, 'timeframe')):

            # create a new config parser to only parse the timeframe file
            config = configparser.ConfigParser()
            config.read(configuration_file)

            # create the 'timeseries': DateTimeIndex mapping
            mapping['timeframe'] = {timeframe: pd.date_range(
                start=ast.literal_eval(config[timeframe]['start']),
                periods=ast.literal_eval(config[timeframe]['periods']),
                freq=ast.literal_eval(config[timeframe]['freq']))}

        # allow different spellings of global_constraints.cfg
        if any(variation in configuration_file for variation in getattr(
                spellings, 'global_constraints')):

            # create a new config parser to only parse the constraints file
            config = configparser.ConfigParser()
            config.read(configuration_file)

            constraint_dict = {}
            for key, value in config[global_constraints].items():

                # most of the values are float, so try that first
                try:
                    value = float(ast.literal_eval(value))
                    constraint_dict[key] = value
                except ValueError:
                    # this one was not, so take it as it is
                    # (usually something like 'name': 'default'
                    constraint_dict[key] = ast.literal_eval(value)

            mapping['global_constraints'] = {
                global_constraints: constraint_dict}

    return python_mapping(mapping, timeframe=timeframe,
                          global_constraints=global_constraints)


def python_file(path):
    """Import a python file from path using python."""

    # Deal with paths starting with "~"
    input_path = Path(path).expanduser()

    # Import the file aka module
    spec = importlib.util.spec_from_file_location(
        input_path.stem,
        str(input_path),
    )
    python_file = importlib.util.module_from_spec(spec)

    # Execute the module, so the namespace gets acticated
    spec.loader.exec_module(python_file)

    return python_file


def python_mapping(mapping, timeframe='primary',
                   global_constraints='primary', **kwargs):
    """
    Parse a python mapping and transform into a dict of pandas.DataFrames.

    (with the exception of the
    :paramref:`~tessif.model.energy_system.AbstractEnergySystem.global_constraints`
    mapping, which is preserved as mapping)

    Read in a nested :any:`mapping <dict>` in pure python and transform it into
    :class:`pandas.DataFrame` objects keyed by their
    :ref:`energy system components <Models_Tessif_Concept_ESC>`
    (i.e. 'sources', 'busses', etc..). As well as a :class:`pandas.DataFrame`
    object keyed by :attr:`~tessif.frused.spellings.timeframe`.


    Parameters
    ----------
    mapping: dict
        Nested :any:`mapping <dict>` in pure python representing an energy
        system.

    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used. Expected to correspond with sublevel keys.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'tf1'`` if the corresponding
        sublevel key is named ``'tf1'``)

    global_constraints: str, default='primary'
        String specifying which of the (potentially multiple) set of
        constraints passed is to be used. Expected to correspond with
        provided sublevel keys

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'global_constraints_1'`` if the
        corresponding sublevel key is named ``'global_constraints_1'``)

    kwargs:
        warning
        -------
        Not implemented yet.

    Return
    ------
    mapping: :class:`~collections.abc.Mapping`
        of :class:`DataFrames<pandas.DataFrame>` to their
        :ref:`energy system component identifier
        <Models_Tessif_Concept_ESC>` ('sources', 'storages' etc..)
        As well as a singular :class:`~pandas.DataFrame` mapped to
        :attr:`~tessif.frused.spellings.timeframe`.

    Note
    ----
    For more on pure python mapping data formats see :ref:`Pure Python Mappings
    <SupportedDataFormats_PurePythonMappings>`

    Example
    -------
    Folowing example illustrates how a pure nested python mapping is
    transformed into string keyed :class:`DataFrame objects<pandas.DataFrame>`
    (with the exception of the
    :paramref:`~tessif.model.energy_system.AbstractEnergySystem.global_constraints`
    mapping).

    >>> from tessif.examples.data.tsf.py_mapping import fpwe as fpwe
    >>> import tessif.parse as parse
    >>> mapping = parse.python_mapping(fpwe.mapping)
    >>> for nested_mapping in mapping.values():
    ...     print(type(nested_mapping))
    <class 'pandas.core.frame.DataFrame'>
    <class 'pandas.core.frame.DataFrame'>
    <class 'pandas.core.frame.DataFrame'>
    <class 'pandas.core.frame.DataFrame'>
    <class 'pandas.core.frame.DataFrame'>
    <class 'pandas.core.frame.DataFrame'>
    <class 'dict'>
    """
    esm = collections.OrderedDict()
    # iterate through each category of the mapping
    # most likely component_categories and a timeframe
    for category in mapping:

        # the timeframe information is transformed into a one column DataFrame
        # (emulating it being the (supposedly) first column of the
        # timeseries data sheet) (yes, engineers do ANYTHING with spreadsheets)
        # timeframe argument allows for different timeframes provided by the
        # same mapping
        if category in spellings.timeframe:
            esm['timeframe'] = mapping[category][timeframe].to_series(
                name='timeindex',
                index=range(len(mapping[category][timeframe]))).to_frame()

        # the constraints information is transformed into a one column DF
        # (emulating it being the (supposedly) first column of the
        # timeseries data sheet) (yes, engineers do ANYTHING with spreadsheets)
        # global_constraints argument allows for different constraints
        # provided by the same mapping
        elif category in spellings.global_constraints:
            # df = pd.DataFrame.from_dict(
            #     data=, orient='columns')
            esm[category] = mapping[category][global_constraints]

        # component_categories should be transformed into one big DataFrame
        # with one component for each row
        else:
            df = pd.DataFrame.from_dict(
                data=mapping[category], orient='index')

            df = _replace_infinity_strings(df)

            esm[category] = df

    return esm


@log.timings
def xl_like(io, timeframe='primary',
            global_constraints='primary', **kwargs):
    """
    :func:`pandas.read_excel` convenience wrapper.

    Reads in spreadsheet datatypes and returns a respective dictionairy.
    Defaults are tweaked to allow this function to be used as
    only providing a path to the file in :paramref:`xl_like.io` for most
    of its use cases.

    Parameters
    ----------
    io : str, ExcelFile, xlrd.Book, path object or file-like object
        Any valid string path is acceptable. The string could be a URL.
        Valid URL schemes include http, ftp, s3, and file. For file URLs,
        a host is expected.
        A local file could be: file://localhost/path/to/table.xlsx.

        If you want to pass in a path object, pandas accepts any os.PathLike.

        By file-like object, we refer to objects with a read() method, such as
        a file handler (e.g. via builtin open function) or StringIO.

    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used. Expected to correspond with spreadsheet column headers
        of the 'timeframe' data sheet.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'tf1'`` if the corresponding
        column header is ``'tf1'``)

    global_constraints: str, default='primary'
        String specifying which of the (potentially multiple) set of
        constraints passed is to be used. Expected to correspond with
        spreadsheet column headers of the 'global_constraints' data sheet.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'global_constraints_1'`` if the
        corresponding column header is named ``'global_constraints_1'``)

    sheet_name: str, int, list, None, default=0
        Strings are used for sheet names. Integers are used in zero-indexed
        sheet positions. Lists of strings/integers are used to request
        multiple sheets. Specify None to get all sheets.
        Available cases:

            * Defaults to ``0``: 1st sheet as a `DataFrame`
            * ``1``: 2nd sheet as a `DataFrame`
            * ``"Sheet1"``: Load sheet with name "Sheet1"
            * ``[0, 1, "Sheet5"]``: Load first, second and sheet named "Sheet5"
              as a dict of `DataFrame`
            * None: All sheets.
    skiprows : list-like
        Rows to skip at the beginning (0-indexed).

    kwargs:
        Key word arguments are passed to :func:`pandas.read_excel`

    Return
    ------
    mapping: :class:`~collections.abc.Mapping`
        of :class:`DataFrames<pandas.DataFrame>` to their
        :ref:`energy system component identifier
        <Models_Tessif_Concept_ESC>` ('sources', 'storages' etc..)
        As well as a singular :class:`~pandas.DataFrame` mapped to
        :attr:`~tessif.frused.spellings.timeframe`.

    Note
    ----
    If you want to read in open datatypes formats use ``engine='odf'``.

    Examples
    --------
    Change spellings `logging level
    <https://docs.python.org/3/library/logging.html#logging-levels>`_
    used by :meth:`spellings.get_from <tessif.frused.spellings.get_from>` to
    debug for decluttering output:

    >>> import tessif.frused.configurations as configurations
    >>> configurations.spellings_logging_level = 'debug'

    Read in tessif's oemof standard energy system model as an
    excel spreadsheet:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> import tessif.parse as parse
    >>> es_dict = parse.xl_like(
    ...     io=os.path.join(
    ...         example_dir, 'data', 'omf', 'xlsx', 'energy_system.xlsx'))
    >>> print(type(es_dict))
    <class 'dict'>

    Read in tessif's oemof standard energy system model as an
    Open Documents spreadsheet:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> import tessif.parse as parse
    >>> es_dict = parse.xl_like(
    ...     io=os.path.join(
    ...         example_dir, 'data', 'omf', 'xlsx', 'energy_system.ods'),
    ...     engine='odf')
    >>> print(type(es_dict))
    <class 'dict'>
    """
    defaults = {
        'engine': 'openpyxl',
        'sheet_name': None,
        'skiprows': list(range(3)),
    }

    for k, v in defaults.items():
        if k not in kwargs:
            kwargs.update({k: v})

    # first run of the parsing
    # esm = energy system dictionary
    esm = pd.read_excel(io, **kwargs)

    # refine the global constraints option
    constraint_key = [variant for variant in spellings.global_constraints
                      if variant in esm.keys()][0]

    constraint_df = esm.pop(constraint_key)

    # figure out the index
    idx = spellings.get_from(constraint_df, smth_like='name').name

    # set index of the df to 'primary','secondary', or whatever its id is:
    constraint_df = constraint_df.set_index([idx])

    # enforce global constraints key and turn it into a dict ...
    esm['global_constraints'] = constraint_df.loc[
        global_constraints].to_dict()

    # refine the timeframe option
    # find out which expression of 'Timeframe' was used
    tf_key = [variant for variant in spellings.timeframe
              if variant in esm.keys()][0]

    timeframe_df = esm.pop(tf_key)
    # print(timeframe_dataframe[timeframe])

    # enforce timeframe key...
    esm['timeframe'] = pd.DataFrame(
        data=timeframe_df[timeframe])
    # ...and pass the desired timeframe (the argument)
    esm['timeframe'].columns = ['timeindex']

    # Write the timeseries data directly into the component mapping...
    # ... by iterating over the timeframe data frames column headers...
    for column_header in timeframe_df.columns:
        # ... to further down in the loop match the requested component
        # iterate over each component type and its data...
        for component_type, components_df in esm.copy().items():

            # ... to enforce a default on all 'timeseries' values
            if component_type not in [*spellings.timeframe, *spellings.global_constraints]:
                components_df['timeseries'] = esn_defs['timeseries']

                # ... and to iterate over each component ...
                for row, component in components_df.iterrows():
                    component_name = spellings.get_from(
                        component, smth_like='name', dflt=esn_defs['name'])

                    # ... to check if component is requested to have a timeseries..
                    if column_header.split(
                            configurations.timeseries_seperator)[
                                0] == component_name:
                        # ... yes it is so create a 'timeseries' cell entry

                        # ... with the specified parameter to replace
                        #     (min/max/actual_value) ...
                        represented_value = column_header.split(
                            configurations.timeseries_seperator)[1]

                        # .. and the read out series...
                        series = list(timeframe_df[column_header])

                        # ... by packing it inside a dict written into the df cell

                        # find out which variation of 'name' was used as
                        # column header
                        name_key = spellings.match_key_from(
                            esm[component_type], smth_like='name',
                            dflt=esn_defs['name'])

                        # get the index of the row, the component is in:
                        df = esm[component_type]
                        idx = df.loc[
                            df[name_key] == component_name].index.values[0]

                        # set the new timeseries value:
                        esm[component_type].at[idx, 'timeseries'] = {
                            str(represented_value): series}

    return esm


def xml(path, timeframe='primary', global_constraints='primary', **kwargs):
    """Parse xml file into a dict of pandas.DataFrames.

    Read in :any:`mappings <dict>` in `xml format
    <https://en.wikipedia.org/wiki/XML>`_ and transform them into
    :class:`pandas.DataFrame` objects keyed by their :ref:`energy system
    components <Models_Tessif_Concept_ESC>` (i.e. 'sources', 'busses', etc..).
    As well as a :class:`pandas.DataFrame` object keyed by
    :attr:`~tessif.frused.spellings.timeframe`.

    Parameters
    ----------
    path: ~pathlib.Path, str
        Path or string representation of a path specifying an `xml file
        <https://en.wikipedia.org/wiki/XML>`_ containing energy system
        :any:`mappings <dict>`

    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used. Expected to correspond with child elements of the
        'timeframe' element of the xml file.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'tf1'`` if the corresponding
        element is named ``'tf1'``)

    global_constraints: str, default='primary'
        String specifying which of the (potentially multiple) set of
        constraints passed is to be used. Expected to correspond with child
        elements of the 'global_constraints' element of the xml file.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'gc1'`` if the corresponding
        element is named ``'gc1'``)

    kwargs:
        warning
        -------
        Not implemented yet.

    Return
    ------
    mapping: :class:`~collections.abc.Mapping`
        of :class:`DataFrames<pandas.DataFrame>` to their
        :ref:`energy system component identifier
        <Models_Tessif_Concept_ESC>` ('sources', 'storages' etc..)
        As well as a singular :class:`~pandas.DataFrame` mapped to
        :attr:`~tessif.frused.spellings.timeframe`.

    Note
    ----
    For more on xml see :ref:`.xml
    <SupportedDataFormats_Xml>`

    Example
    -------
    Read in tessif's :ref:`fully parameterized working example
    <Models_Tessif_Fpwe>` in xml format:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> import tessif.parse as parse
    >>> es_dict = parse.xml(
    ...     path=os.path.join(example_dir, 'data', 'tsf', 'xml', 'fpwe.xml'))
    >>> print(type(es_dict))
    <class 'collections.OrderedDict'>
    """
    # Parse xml file into element tree
    element_tree = ET.parse(path)
    root_element = element_tree.getroot()

    # Figure out the component names by looking it up in spellings
    component_names = spellings.energy_system_component_identifiers.component.keys()

    # create the initial mapping
    mapping = collections.OrderedDict()

    # iterate through components
    for component in component_names:

        # find component in element tree
        for variation in getattr(spellings, component):
            if root_element.find(variation):

                # mapping holding individual entities for each component
                entities = {}

                # iterate through the component's entities
                for component_entity in root_element.find(variation):

                    # mapping holding the entities parameters
                    parameters = {}

                    # iterate through the entities parameters and add them to
                    # the parameters dict
                    for parameter, value in component_entity.attrib.items():
                        parameters[parameter] = ast.literal_eval(value)

                    # fill the entities mapping with the parameters dict
                    entities[component_entity.tag] = parameters

                # fill the energy system mapping with the components
                mapping[component] = entities

    # timeseries parsing is handled seperately because it's a 'one column' DF
    for variation in getattr(spellings, 'timeframe'):
        if root_element.find(variation):

            # create variable pointing to the element containing the timeframe
            timeframe_element = root_element.find(variation).find(timeframe)

            # create the 'timeseries': DateTimeIndex mapping
            mapping['timeframe'] = {timeframe: pd.date_range(
                start=ast.literal_eval(timeframe_element.get('start')),
                periods=ast.literal_eval(timeframe_element.get('periods')),
                freq=ast.literal_eval(timeframe_element.get('freq')))}

    # global constraints parsing ist also handled seperately
    for variation in getattr(spellings, 'global_constraints'):
        if root_element.find(variation):

            # create variable pointing to the element containing the
            # global_constraints
            constraints_element = root_element.find(
                variation).find(global_constraints)

            # create the constraints mapping
            glob_consts = dict()
            for key, value in constraints_element.items():
                value = ast.literal_eval(value)
                if value == '+inf':
                    value = float(value)
                glob_consts[key] = value

            mapping['global_constraints'] = {
                global_constraints: glob_consts}

            # mapping['global_constraints'] = {
            #     global_constraints: {
            #         key: ast.literal_eval(value)
            #         for key, value in constraints_element.items()}}

    return python_mapping(mapping, timeframe=timeframe,
                          global_constraints=global_constraints)


def hdf5(path, timeframe='primary', global_constraints='primary', **kwargs):
    """Parse hdf5 file into a dict of pandas.DataFrames.

    Read in :any:`mappings <dict>` in `hdf5 format
    <https://en.wikipedia.org/wiki/Hierarchical_Data_Format>`_ and transform
    them into :class:`pandas.DataFrame` objects keyed by their :ref:`energy
    system components <Models_Tessif_Concept_ESC>` (i.e. 'sources', 'busses',
    etc..). As well as a :class:`pandas.DataFrame` object keyed by
    :attr:`~tessif.frused.spellings.timeframe`.

    Parameters
    ----------
    path: ~pathlib.Path, str
        Path or string representation of a path specifying a `hdf5 file
        <https://en.wikipedia.org/wiki/Hierarchical_Data_Format>`_ containing
        energy system :any:`mappings <dict>`

    timeframe: str, default='primary'
        String specifying which of the (potentially multiple) timeframes passed
        is to be used. Expected to correspond with subgroups of the 'timeframe'
        group of the hdf5 file.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'tf1'`` if the corresponding
        group is named ``'tf1'``)

    global_constraints: str, default='primary'
        String specifying which of the (potentially multiple) set of
        constraints passed is to be used. Expected to correspond with subgroups
        of the 'timeframe' group of the hdf5 file.

        One of ``'primary'``, ``'secondary'``, etc... by convention. Designed
        to be tweaked arbitrarily (e.g. pass ``'gc1'`` if the corresponding
        group is named ``'gc1'``)

    kwargs:
        warning
        -------
        Not implemented yet.

    Return
    ------
    mapping: :class:`~collections.abc.Mapping`
        of :class:`DataFrames<pandas.DataFrame>` to their
        :ref:`energy system component identifier
        <Models_Tessif_Concept_ESC>` ('sources', 'storages' etc..)
        As well as a singular :class:`~pandas.DataFrame` mapped to
        :attr:`~tessif.frused.spellings.timeframe`.

    Note
    ----
    For more on hdf5 see :ref:`.hdf5
    <SupportedDataFormats_HDF5>`

    Example
    -------
    Read in tessif's :ref:`fully parameterized working example
    <Models_Tessif_Fpwe>` in hdf5 format:

    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> import tessif.parse as parse
    >>> es_dict = parse.hdf5(
    ...     path=os.path.join(
    ...     example_dir, 'data', 'tsf', 'hdf5', 'fpwe.hdf5'))
    >>> print(type(es_dict))
    <class 'collections.OrderedDict'>
    """
    def recursively_load_dict_contents(h5file, path):
        """Load the contents of a group inside a hdf5 file into a dict.

        The values of datasets get mapped to the datasets name. For
        each group inside the group, this function calls itself and
        maps the returned dictionary to the group's name.

        An energy system may have parameters that are dicts with tuples as
        keys. When the energy system ist stored as a hdf5 file, those tuple
        type keys are converted to strings, as the keys of the mentioned dicts
        become the names of datasets or groups in the hdf5 file and those can't
        be tuples. This function therefore has to turn those stringified tuples
        back to actual tuples.
        """
        ans = {}
        for key, item in h5file[path].items():
            if isinstance(item, h5py._hl.dataset.Dataset):
                # Try to convert stringified tuples back to actual tuples (see
                # function docstring). ast.literal_eval gives out an error, if
                # a string can't be converted. This can be ignored as key will
                # just stay unchanged in that case.
                try:
                    ast.literal_eval(key)
                except ValueError:
                    pass
                else:
                    key = ast.literal_eval(key)

                # Convert bytes into str
                if isinstance(item[()], bytes):
                    ans[key] = item.asstr()[()]
                elif isinstance(item[()], np.ndarray):
                    # Convert (nested) numpy arrays into (nested) lists.
                    temp_list = item[()]
                    temp_list = [list(i) if isinstance(i, np.ndarray) else i
                                 for i in temp_list]
                    ans[key] = [i.decode('UTF-8')
                                if isinstance(i, bytes) else i
                                for i in temp_list]
                else:
                    ans[key] = item[()]
            elif isinstance(item, h5py._hl.group.Group):
                ans[key] = recursively_load_dict_contents(
                    h5file, path + key + '/')
        return ans

    # create the initial mapping
    mapping = collections.OrderedDict()

    # fill the mapping with the contents of the hdf5 file
    with h5py.File(path, 'r') as h5file:
        mapping = recursively_load_dict_contents(h5file, '/')

    # Figure out the component names by looking it up in spellings
    component_names = \
        spellings.energy_system_component_identifiers.component.keys()

    # create a list with all the valid keys
    valid_keys = []
    for component in component_names:
        valid_keys.extend(getattr(spellings, component))
    valid_keys.extend(getattr(spellings, 'timeframe'))
    valid_keys.extend(getattr(spellings, 'global_constraints'))

    # keep only valid keys
    for key in list(mapping.keys()):
        if key not in valid_keys:
            del mapping[key]

    # create the 'timeseries': DateTimeIndex mapping
    for variation in getattr(spellings, 'timeframe'):
        if variation in mapping:
            mapping['timeframe'] = {timeframe: pd.date_range(
                start=mapping[variation][timeframe]["start"],
                periods=mapping[variation][timeframe]["periods"],
                freq=str(mapping[variation][timeframe]["freq"]))}

    return python_mapping(mapping, timeframe=timeframe,
                          global_constraints=global_constraints)


def reorder_esm(esm, order=None):
    """
    Reorder the energy system mapping based on the given order.

    Design case is to reorder the energy system mapping, so that every
    :ref:`energy system component<Models_Tessif_Concept_ESC>` is mappped to its
    respective :ref:`identifier <Spellings_EnergySystemComponentIdentifiers>`.
    (i.e all sources are mapped to ``'source'``).

    Parameters
    ----------
    esm: ~collections.abc.Mapping
        Mapping of which the keys are to be changes.
    order: ~collections.abc.Mapping, None, dflt=None
        Mapping of which the keys are used to reorder the
        :paramref:`~reorder_esm.esm`. Whereas the values are used to identify
        which original keys of the :paramref:`~reorder_esm.esm` belong to which
        new key. Meaning if the old key (i.e ``import``) is to be found in
        one of the :paramref:`~reorder_esm.order` mapping (i.e.
        ``{'sink': 'import', 'commodity'}`` values, it is replaced (i.e
        ``'sink'`` in this case).

        If ``None`` is used (the default)
        :attr:`tesssif.frused.registered_component_types` is used as order
        mapping. (Which is it's design case)

    Example
    -------
    Change spellings `logging level
    <https://docs.python.org/3/library/logging.html#logging-levels>`_
    used by :meth:`spellings.get_from <tessif.frused.spellings.get_from>` to
    debug for decluttering output:

    >>> import tessif.frused.configurations as configurations
    >>> configurations.spellings_logging_level = 'debug'

    Reading in the oemof default example and order the energy system mapping
    according to tessif's :ref:`convention <Models_Tessif_Concept_ESC>`

    >>> import tessif.parse as parse
    >>> import os
    >>> from tessif.frused.paths import example_dir
    >>> esm = parse.xl_like(
    ...     io=os.path.join(
    ...     example_dir, 'data', 'omf', 'xlsx', 'energy_system.xlsx'))

    The unordered energy system mapping:

    >>> for key in esm.keys():
    ...     print(key)
    Info
    Grid
    Renewable
    Demand
    Commodity
    mimo_transformers
    global_constraints
    timeframe

    The reordered energy system mapping:

    >>> esm = parse.reorder_esm(esm)
    >>> for key in esm.keys():
    ...     print(key)
    bus
    sink
    source
    transformer
    timeframe
    """
    if not order:
        order = {
            **defaults.registered_component_types,
            **defaults.addon_component_types,
        }

    # all parsers read in ordered dicts, so preserve this type
    sorted_esm = collections.OrderedDict()
    for identifier in order.keys():
        sorted_esm[identifier] = collect_component_types(
            esm, identifier, mapping=order)

    # manually copy the timeframe data
    sorted_esm['timeframe'] = spellings.get_from(
        esm, smth_like='timeframe', dflt=esn_defs['timeseries'])

    # remove all unused identifiers
    for identifier in sorted_esm.copy().keys():
        if sorted_esm[identifier].empty:
            sorted_esm.pop(identifier)

    return sorted_esm


def collect_component_types(esm, identifier, mapping=None):

    if not mapping:
        mapping = defaults.registered_component_types.copy()

    kinds_of_components = [
        spellings.get_from(
            esm, smth_like=component_type, dflt=pd.DataFrame())
        for component_type in mapping[identifier]]

    collected = pd.concat(kinds_of_components, sort=True)

    return collected


def _replace_infinity_strings(df):
    infinity_strings = ('inf', '+inf', '-inf')

    for row_tuple in df.itertuples():
        for i, element in enumerate(row_tuple):

            # check if its a tuple containing an infinity string
            if (isinstance(element, tuple) and
                    any(inf in element for inf in infinity_strings)):

                # temp list for creating a new tuple
                lst = list()

                for tple_pos, value in enumerate(element):

                    # replace infinity string by its float representation
                    if value in infinity_strings:
                        logger.debug(
                            "replaced df['{}']['{}'][{}]".format(
                                row_tuple.Index, row_tuple._fields[i],
                                tple_pos) +
                            "'s value: '{}' with '{}'".format(
                                value, float(value)))
                        value = float(value)

                    # at tuple value to list
                    lst.append(value)

                # add parsed infinity values to dataframe
                df.at[row_tuple.Index,
                      row_tuple._fields[i]] = tuple(lst)

            elif isinstance(element, dict):
                for key, value in element.copy().items():

                    if (isinstance(value, tuple) and
                            np.any(inf in value for inf in infinity_strings)):

                        lst = list()
                        for tple_pos, subelement in enumerate(value):

                            # replace infinity string by its float repr

                            # watch out for numpy arrays aka, timeseries:
                            if (not isinstance(subelement, np.ndarray) and
                                    subelement in infinity_strings):
                                logger.debug(
                                    "replaced df['{}']['{}']['{}'][{}]".format(
                                        row_tuple.Index, row_tuple._fields[i],
                                        key, tple_pos) +
                                    "'s value: '{}' with '{}'".format(
                                        subelement, float(subelement)))
                                subelement = float(subelement)

                            # at tuple value to list
                            lst.append(subelement)

                        df.at[
                            row_tuple.Index,
                            row_tuple._fields[i]][key] = tuple(lst)

    return df


def _unstringify_timeseries(ts_dict):
    """Makes sure tuples are returned instead of strings of containers"""
    unstringified_dict = {}
    for key, value in ts_dict.items():
        if isinstance(value, str):
            unstringified_dict[key] = ast.literal_eval(value)
        elif isinstance(value, collections.abc.Iterable):
            tmp_list = []
            for item in value:
                # to_cfg genrated items are strings
                if isinstance(item, str):
                    tmp_list.append(ast.literal_eval(item))
                # user created may not, so distinguish:
                else:
                    tmp_list.append(item)
            tpl = tuple(tmp_list)
            unstringified_dict[key] = tpl
        else:
            unstringified_dict[key] = value

    return unstringified_dict
