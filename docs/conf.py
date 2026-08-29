"""Sphinx configuration for playcricket_stats."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "playcricket_stats"
copyright = "2026, East Lancs Paper Mill CC"
author = "East Lancs Paper Mill CC"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
