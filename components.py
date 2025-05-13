"""Shared components and utilities for the Seeklyzer application."""

from dash import html
import dash_bootstrap_components as dbc

def create_processing_alert(message):
    """Creates a standardized processing alert with spinner."""
    return dbc.Alert(
        [
            html.Span(
                [
                    html.I(className="fas fa-spinner fa-spin me-2"),
                    message
                ]
            )
        ],
        className="text-center",
        color="info",
        dismissable=False,
        is_open=True
    )