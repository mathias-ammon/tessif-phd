# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import pathlib
import sys
# import sphinx
# import easydev
# import shutil
from sphinx.ext.autodoc import between


# sys.path.insert(1, os.path.abspath('../..'))
src_path = pathlib.Path(__file__).resolve() / ".." / ".." / "src"
sys.path.insert(0, os.path.abspath(src_path))


# -- Project information -----------------------------------------------------

project = 'Tessif-PHD - Transforming Energy Supply System Modell I ng Framework'
copyright = '2023, Mathias Ammon'
author = 'Mathias Ammon'

# The full version, including alpha/beta/rc tags
release = '0.0.1alpha'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',  # enable docstring documentation
    'sphinx.ext.napoleon',  # enable numpy style docstring syntax
    'sphinx.ext.intersphinx',  # allow :mod: references to interlinked docs
    'sphinx.ext.viewcode',  # enable source links
    'sphinx.ext.autosummary',  # create linked tables for documented attributes

    # 3rd party extensions
    'sphinx_paramlinks',  # enable :param: cross referencing
    # 'sphinx_exec_code',  # execute code
    # 'sphinxcontrib.excel_table',  # show xlsx exceltables
    # 'sphinxcontrib.exceltable',  # show xls exceltables
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# Sort the documentation
html_theme_options = {
    'canonical_url': "https://github.com/tZ3ma/tessif-phd/",
    'display_version': True,
    'sticky_navigation': True,
}

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'networkx': ('https://networkx.org/documentation/stable/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'matplotlib': ('https://matplotlib.org/stable', None),

    'oemof': ('https://oemof-solph.readthedocs.io/en/stable/',
              (None,
               'https://oemof-solph.readthedocs.io/en/stable/objects.inv')),
    'pyomo': ('https://pyomo.readthedocs.io/en/stable/', None),
    'h5py': ('https://docs.h5py.org/en/stable/', None),
    'pypsa': ('https://pypsa.readthedocs.io/en/stable', None),
    'calliope': ('https://calliope.readthedocs.io/en/stable', None),
}

autodoc_member_order = 'bysource'


def setup(app):
    # Register a sphinx.ext.autodoc.between listener to ignore everything
    # between lines that contain the word IGNORE
    app.connect('autodoc-process-docstring',
                between('^.*IGNORE.*$', exclude=True))
    return app
