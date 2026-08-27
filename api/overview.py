"""
Vercel Serverless Function: /api/overview
"""
try:
    from .index import handler
except ImportError:
    from index import handler
