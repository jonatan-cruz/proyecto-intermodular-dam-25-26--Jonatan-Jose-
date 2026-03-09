# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os

# Añadir la carpeta de custom_addons al path para que autodoc encuentre los módulos
sys.path.insert(0, os.path.abspath('../../custom_addons'))

# -- Project information -----------------------------------------------------

project = 'Dalo'
copyright = '2026, Jonatan C. and Jose S.'
author = 'Jonatan C. and Jose S.'
release = '1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',    # Genera docs a partir de los docstrings
    'sphinx.ext.viewcode',   # Añade enlace "Ver código fuente" en cada símbolo
    'sphinx.ext.napoleon',   # Soporte para docstrings NumPy/Google (por si acaso)
]

# Mocks de los paquetes de Odoo y dependencias que no están instalados en Windows.
# Esto evita ImportError al leer los módulos con autodoc.
autodoc_mock_imports = [
    'odoo',
    'odoo.models',
    'odoo.fields',
    'odoo.api',
    'odoo.exceptions',
    'odoo.http',
    'odoo.tools',
    'passlib',
    'passlib.context',
    'jwt',          # PyJWT — usado en auth_controller y login
]

# Mostrar tanto miembros con docstring como sin él
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

templates_path = ['_templates']
exclude_patterns = []

language = 'es'

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_static_path = ['_static']
