"""
Python exception hook installer for automatic patching.
"""

def install():
    """Install the ReflexRuntime exception hook for automatic patching."""
    from ...core.orchestrator import install_autopatch
    install_autopatch()
