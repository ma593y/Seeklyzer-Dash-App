"""
Shared components and utilities for the Seeklyzer application.
This module contains reusable UI components used across different pages.
"""

from typing import Union, List
from dash import html
import dash_bootstrap_components as dbc

def create_processing_alert(message: str) -> dbc.Alert:
    """
    Creates a standardized processing alert with a loading spinner.
    
    Args:
        message (str): The message to display in the alert
        
    Returns:
        dbc.Alert: A Bootstrap alert component with a spinner and message
    """
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

def create_error_alert(message: str, is_open: bool = True) -> dbc.Alert:
    """
    Creates a standardized error alert.
    
    Args:
        message (str): The error message to display
        is_open (bool, optional): Whether the alert should be visible. Defaults to True.
        
    Returns:
        dbc.Alert: A Bootstrap alert component for error messages
    """
    return dbc.Alert(
        [
            html.I(className="fas fa-exclamation-circle me-2"),
            message
        ],
        className="text-center",
        color="danger",
        dismissable=True,
        is_open=is_open
    )

def create_success_alert(message: str, is_open: bool = True) -> dbc.Alert:
    """
    Creates a standardized success alert.
    
    Args:
        message (str): The success message to display
        is_open (bool, optional): Whether the alert should be visible. Defaults to True.
        
    Returns:
        dbc.Alert: A Bootstrap alert component for success messages
    """
    return dbc.Alert(
        [
            html.I(className="fas fa-check-circle me-2"),
            message
        ],
        className="text-center",
        color="success",
        dismissable=True,
        is_open=is_open
    )