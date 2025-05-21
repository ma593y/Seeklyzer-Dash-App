"""
Seeklyzer - A Dash application for job search and analysis.
Main application file that sets up the Dash app and its core components.
"""

# Standard library imports
import os
import logging
from typing import Optional

# Third-party imports
from dotenv import load_dotenv
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

# Local imports
from components import create_processing_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

def create_navbar() -> dbc.NavbarSimple:
    """Create the application navigation bar."""
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Resume Tool", href="/resume")),
            dbc.NavItem(dbc.NavLink("Job Finder", href="/jobs")),
            dbc.NavItem(dbc.NavLink("Scripts", href="/scripts")),
            dbc.NavItem(dbc.NavLink("About", href="/about")),
        ],
        brand="Seeklyzer",
        brand_href="/",
        color="primary",
        dark=True,
        className="mb-4"
    )

def create_app_layout() -> html.Div:
    """Create the main application layout."""
    return html.Div([
        create_navbar(),
        html.Div(id="global-alert-container", className="mb-3"),
        dash.page_container,
        html.Div(id='_', style={'display': 'none'})
    ])

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ],
    suppress_callback_exceptions=True,
    use_pages=True
)

app.title = "Seeklyzer - Find Roles That Truly Fit"
app.layout = create_app_layout()
logger.info("Dash app initialized with Bootstrap theme and multi-page support")

@callback(
    Output('global-alert-container', 'children'),
    Input('_', 'children'),
)
def show_welcome_message(_) -> Optional[dbc.Alert]:
    """
    Display a welcome message when the app first loads.
    
    Args:
        _: Unused input trigger
        
    Returns:
        Optional[dbc.Alert]: The welcome message alert component
    """
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

def main() -> None:
    """Main entry point for the application."""
    try:
        logger.info("Starting Seeklyzer Dash App...")
        logger.info("Server running at http://127.0.0.1:8050/")
        app.run(debug=True)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
    finally:
        logger.info("Server has stopped")

if __name__ == '__main__':
    main()