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

# Estilo de resaltado de sintaxis para los bloques de código
pygments_style = 'monokai'

html_theme = 'alabaster'
html_static_path = ['_static']

# Logo de la app (dalored.png en _static)
html_logo = '_static/dalored.png'
html_favicon = '_static/dalored.png'

# CSS personalizado con los colores de la app
html_css_files = ['custom.css']

# Opciones del tema alabaster con los colores de la app Dalo (#c22a2a)
html_theme_options = {
    # Cabecera de la sidebar
    'description': 'Documentación técnica del backend Odoo',
    'logo_name': True,
    'logo_text_align': 'center',

    # Colores – paleta real (DaloRed: #c22a2a)
    'body_text_color': '#121212',         # Charcoal
    'link_color': '#8b1e1e',              # primary-dark, máximo contraste sobre blanco
    'link_hover_color': '#c22a2a',        # primary rojo
    'sidebar_header': '#c5a059',          # GoldAccent – headings sidebar
    'sidebar_text': '#f5ede9',            # texto claro sobre fondo oscuro barra lateral
    'sidebar_link': '#f5ede9',
    'sidebar_link_underscore': '0',
    'sidebar_collapse': False,
    'anchor_hover_fg': '#c22a2a',
    
    # Diseño (layout)
    'sidebar_width': '350px',
    'page_width': '1200px',
}
