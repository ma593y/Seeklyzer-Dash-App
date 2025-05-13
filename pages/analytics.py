import dash
from dash import html
import dash_bootstrap_components as dbc

# Register the page
dash.register_page(
    __name__,
    path='/analytics',
    title='Seeklyzer - Resume Analytics',
    name='Analytics'
)

# Blank layout
layout = dbc.Container([
    html.H1("Analytics", className="text-center my-4"),
    dbc.Alert(
        "This page is currently under development. Please use the Resume Tool.",
        color="secondary",
        className="text-center"
    )
], fluid=True)