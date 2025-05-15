import os
import sys


project = "Caldav-Tasks-API"
copyright = "2025, thiswillbeyourgithub"
author = "thiswillbeyourgithub"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",  # for markdown support
    "sphinx.ext.autosectionlabel",
]

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": True,
    "special-members": True,
    "show-inheritance": True,
    "imported-members": True,
}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_preserve_defaults = True
autodoc_inherit_docstrings = True
autodoc_docstring_signature = True

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_attr_annotations = True
napoleon_preprocess_types = True

templates_path = ["_templates"]
exclude_patterns = []
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "flyout_display": "attached",
    "language_selector": False,
    "style_external_links": True,
    "prev_next_buttons_location": "both",
    "analytics_anonymize_ip": True,
    #
    # 'navigation_depth': -1,
    # 'sidebar_hide_name': True,  # Less aggressive, just hides the project name
    #
    # # specific to pydata theme
    # # source: https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/navigation.html
    "show_nav_level": 6,
    "collapse_navigation": False,
}
