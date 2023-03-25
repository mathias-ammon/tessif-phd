# tessif/write/tools.py
# -*- coding: utf-8 -*-
"""
:mod:`tessif.write.tools` is a :mod:`tessif` module for aggregating output
writing tools.
"""
# standard library
import os
import sys


class HideStdoutPrinting:
    """
    ContextManager for temporarily disabeling printing to stdout

    Originally written by `Alexander Chzhen
    <https://stackoverflow.com/a/45669280>`_.

    Examples
    --------
    >>> import tessif.write.tools as write_tools
    >>> with HideStdoutPrinting():
    ...     print("This will not be printed")

    >>> print("This will be printed as before")
    This will be printed as before
    """

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
