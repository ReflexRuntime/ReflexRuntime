"""
ReflexRuntime - AI-powered runtime reflexes for your code.

A self-healing framework that catches exceptions, analyzes them with LLMs,
and hot-swaps code to fix issues at runtime with zero downtime.
"""

__version__ = "0.1.0"

from .agents.python.hook import install as install_autopatch

__all__ = ["install_autopatch"]
