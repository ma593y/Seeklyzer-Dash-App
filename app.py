# Standard library imports
import os
from dotenv import load_dotenv

# Dash imports
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

# Import shared components
from components import create_processing_alert

# Load environment variables from .env file
load_dotenv()
print("[INIT] Environment variables loaded")

# Initialize the Dash app with pages
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ],
    suppress_callback_exceptions=True,
    use_pages=True  # Enable pages feature
)

app.title = "Seeklyzer - Find Roles That Truly Fit"
print("[INIT] Dash app initialized with Bootstrap theme and multi-page support")

# Create a navbar for navigation between pages
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Resume Tool", href="/resume")),
        dbc.NavItem(dbc.NavLink("Job Finder", href="/jobs")),
        dbc.NavItem(dbc.NavLink("Analytics", href="/analytics")),
        dbc.NavItem(dbc.NavLink("About", href="/about")),
    ],
    brand="Seeklyzer",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-4"
)

# Main app layout
app.layout = html.Div([
    navbar,
    # Global alert area for application-wide messages
    html.Div(id="global-alert-container", className="mb-3"),
    
    # This is where page content will be rendered
    dash.page_container,
    
    # Hidden div to trigger the welcome message
    html.Div(id='_', style={'display': 'none'})
])

@callback(
    Output('global-alert-container', 'children'),
    Input('_', 'children'),
)
def show_welcome_message(_):
    """Displays a welcome message when the app first loads."""
    return dbc.Alert(
        [
            html.I(className="fas fa-info-circle me-2"),
            html.Strong("Welcome to Seeklyzer! "), 
            "Navigate using the menu above to access different features."
        ],
        className="text-center",
        color="info",
        dismissable=True,
        is_open=True,
        duration=8000
    )

if __name__ == '__main__':
    print("[APP] Starting Seeklyzer Dash App...")
    try:
        print("[APP] Server running at http://127.0.0.1:8050/")
        app.run(debug=True)
        print("[APP] Server has stopped")
    except Exception as e:
        print(f"[APP] Critical error: {str(e)}")