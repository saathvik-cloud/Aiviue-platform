"""
Job API module.

Exports the router for inclusion in main app.
"""

from app.domains.job.api.routes import router

__all__ = ["router"]
