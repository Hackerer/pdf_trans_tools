"""Tests for web module"""
import pytest


class TestWeb:
    """Test cases for web module."""

    def test_web_module_exists(self):
        """Test web module can be imported."""
        from pdf_trans_tools import web
        assert web is not None

    def test_app_exists(self):
        """Test Flask app exists."""
        from pdf_trans_tools.web import app
        assert app is not None

    def test_app_has_routes(self):
        """Test Flask app has required routes."""
        from pdf_trans_tools.web import app
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/" in routes
        assert "/api/translate" in routes
        assert "/api/extract" in routes

    def test_index_route_exists(self):
        """Test index route exists."""
        from pdf_trans_tools.web import app
        routes = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
        assert "/" in routes

    def test_translate_api_route(self):
        """Test translate API route exists."""
        from pdf_trans_tools.web import app
        routes = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
        assert "/api/translate" in routes
