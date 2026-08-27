"""
Vercel Serverless Function: /api/scan
"""
try:
    from .index import handler
except ImportError:
    from index import handler
