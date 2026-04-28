"""Integration smoke test — verifies all routers are registered"""
import pytest


def test_all_routes_registered():
    """Verify all expected routes are registered in the app"""
    from app.main import app

    routes = [route.path for route in app.routes]

    # Auth routes
    assert "/api/auth/login" in routes
    assert "/api/auth/me" in routes

    # Dashboard route
    assert "/api/dashboard" in routes

    # Discovery routes
    assert "/api/discovery" in routes
    assert "/api/discovery/config" in routes

    # Outlines routes
    assert "/api/outlines" in routes
    assert "/api/outlines/{outline_id}" in routes
    assert "/api/outlines/generate" in routes

    # Workbench routes
    assert "/api/workbench/articles" in routes
    assert "/api/workbench/articles/{article_id}" in routes


def test_app_metadata():
    """Verify app metadata is correctly set"""
    from app.main import app

    assert app.title == "NewsRadar API Server"
    assert app.version == "0.1.0"