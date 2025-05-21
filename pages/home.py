"""
Home page for the Seeklyzer application.
This is the landing page that introduces users to the application's features.
"""

from typing import List
from dash import html
import dash_bootstrap_components as dbc
import dash

# Register the page
dash.register_page(
    __name__,
    path='/',
    title='Seeklyzer - Home',
    name='Home'
)

def create_feature_card(title: str, description: str, icon: str, href: str) -> dbc.Card:
    """
    Create a feature card for the home page.
    
    Args:
        title (str): The title of the feature
        description (str): Description of the feature
        icon (str): Font Awesome icon class
        href (str): Link to the feature page
        
    Returns:
        dbc.Card: A Bootstrap card component
    """
    return dbc.Card(
        dbc.CardBody([
            html.I(className=f"fas {icon} fa-3x mb-3 text-primary"),
            html.H4(title, className="card-title"),
            html.P(description, className="card-text"),
            dbc.Button("Learn More", href=href, color="primary", className="mt-3")
        ]),
        className="h-100 text-center"
    )

# Define the features
FEATURES: List[dict] = [
    {
        "title": "Resume Analysis",
        "description": "Upload your resume and get instant feedback on how to improve it for better job matches.",
        "icon": "fa-file-alt",
        "href": "/resume"
    },
    {
        "title": "Job Finder",
        "description": "Search and filter through job listings to find positions that match your skills and preferences.",
        "icon": "fa-search",
        "href": "/jobs"
    },
    {
        "title": "Analytics",
        "description": "View insights and trends in the job market to make informed career decisions.",
        "icon": "fa-chart-line",
        "href": "/analytics"
    }
]

# Create the layout
layout = dbc.Container([
    # Hero section
    dbc.Row([
        dbc.Col([
            html.H1("Welcome to Seeklyzer", className="text-center display-4 mb-4"),
            html.P(
                "Your intelligent job search companion. Find roles that truly fit your skills and aspirations.",
                className="text-center lead mb-5"
            )
        ], width=12)
    ])

    
], fluid=True, className="py-5")