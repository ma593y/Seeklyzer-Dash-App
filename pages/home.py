import dash
from dash import html
import dash_bootstrap_components as dbc

# Register the page
dash.register_page(
    __name__,
    path='/',
    title='Seeklyzer - Home',
    name='Home'
)

# Blank layout
layout = dbc.Container([
    html.H1("Home", className="text-center my-4"),
    dbc.Alert(
        "This page is currently under development. Please use the Resume Tool.",
        color="secondary",
        className="text-center"
    )
], fluid=True)