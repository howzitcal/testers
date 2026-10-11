"""Deprecated in-process worker.

Background jobs now use the SQLite queue processed by `leads_app.worker`
in a separate container (see docker-compose.yml), comparable to Django-Q.
"""
