"""
Vercel Serverless Function: /api/health
"""
try:
    from .index import handler
except ImportError:
    from index import handler
