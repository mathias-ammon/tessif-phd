# tessif/transform/es2es/__init.py
# -*- coding: utf-8 -*-

"""
:mod:`~tessif.transform.es2es` is a :mod:`tessif` subpackage for handling the
transformation in between supported energy system models.

The heavy lifting of the transformation process is done by a respective energy
system model module i.e. :mod:`es2es.omf <tessif.transform.es2es.omf>` for
:any:`oemof`.
"""
import tessif.frused.defaults as defaults


def infer_software_from_es(energy_system, first_split="<class '", second_split="."):
    """Infer string specifying the software the energy system was created with.

    Uses 2 ``split`` operations on ``str(type(energy_system))`` to isolate
    model string.

    Parameters
    ----------
    energy_system
        Energy system object of one of the :ref:`SupportedModels`.
    first_split: str, default="<class '"
        String specifying the 'overhead' str(type) 'overhead' in front of the
        actual software specifier.

        ``str(type(energy_system)).split(first_split)[1]`` is used as input for
        the secondn split.

    second_split: str, default="."
        String specifying the str(type) 'overhead' in front of the
        actual software specifier.

        ``split(second_split)[0]`` is used to isolate the software specifier.

    Returns
    -------
    str
        Inferred software string using
        ``str(type(energy_system)).split(first_split)[1].split(second_split)[0]``

    Examples
    --------
    Infer software strings, by using the ``create_mwe`` functionalities of the
    :ref:`SupportedModels`:

    >>> import importlib  # used for dynamic imports below
    >>> from tessif.transform.es2es import infer_software_from_es
    >>> models = ['omf', 'pypsa', 'fine']
    >>> for model in models:
    ...     hardcoded_examples = importlib.import_module(".".join([
    ...         "tessif.examples.data", model, "py_hard"]))
    ...     mwe_es = hardcoded_examples.create_mwe()
    ...     print(infer_software_from_es(mwe_es))
    oemof
    pypsa
    FINE
    """
    first_split_result = str(type(energy_system)).split(first_split)[1]
    second_split_result = first_split_result.split(second_split)[0]
    return second_split_result


def infer_registered_model(model):
    """Try to infer registered model name.

    Parameters
    ----------
    model: str
        String specifying the registered model name to be inferred.
        Must be found inside :attr:tessif.frused.defaults.registered_models`.

    Returns
    -------
    str
        String of the registered model, i.e. one of the keys found in
        :attr:`tessif.frused.defaults.registered_models`.

    Raises
    ------
    ValueError
        Raise ValueError when no inferred model can be found. Error message
        states a list of inferrable model strings.

    Examples
    --------
    Design Case Usage:

    >>> from tessif.transform.es2es import (
    ...     infer_registered_model,
    ...     infer_software_from_es,
    ... )
    >>> from tessif.examples.data.omf.py_hard import create_star
    >>> #
    >>> omf_es = create_star()
    >>> es_software = infer_software_from_es(omf_es)
    >>> inferred_model = infer_registered_model(es_software)
    >>> print(inferred_model)
    omf

    Default Usage:

    >>> from tessif.transform.es2es import infer_registered_model
    >>> print(infer_registered_model('fn'))
    fine
    """
    for internal_name, spellings in defaults.registered_models.items():
        if model in spellings:
            used_model = internal_name
            break
    else:
        msg1 = f"Unknown model specifier: '{model}'. "
        msg2 = f"Use one of {defaults.registered_models.values()}."
        raise ValueError(msg1 + msg2)

    return used_model
