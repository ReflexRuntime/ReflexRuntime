"""
Pydantic schemas for ReflexRuntime data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback for basic functionality
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    def Field(**kwargs):
        return None


class PatchStatus(str, Enum):
    """Status of a patch operation."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ErrorContext(BaseModel):
    """Context information about an exception that needs fixing."""
    
    exception_type: str
    exception_message: str
    traceback_str: str
    target_fqn: str
    source_code: str
    file_path: str
    line_number: int
    local_vars: Dict[str, Any]
    
    @classmethod
    def from_traceback(cls, exc_type, exc_value, tb) -> 'ErrorContext':
        """Create ErrorContext from exception traceback info."""
        
        # Handle case where tb is None
        if tb is None:
            return cls(
                exception_type=exc_type.__name__,
                exception_message=str(exc_value),
                target_fqn="unknown",
                file_path="unknown",
                line_number=0,
                source_code="",
                traceback_str=f"{exc_type.__name__}: {exc_value}",
                local_vars={}
            )
        
        # Get the frame where the exception occurred
        frame = tb.tb_frame
        
        # Extract local variables
        local_vars = {}
        try:
            local_vars = dict(frame.f_locals)
        except Exception:
            local_vars = {}
        
        # Get file path and line number
        file_path = frame.f_code.co_filename
        line_number = tb.tb_lineno
        
        # Try to get the function name and build FQN
        func_name = frame.f_code.co_name
        
        # Build a reasonable FQN
        if func_name == '<module>':
            target_fqn = "unknown.module"
        else:
            # Try to get module name
            module_name = frame.f_globals.get('__name__', 'unknown')
            target_fqn = f"{module_name}.{func_name}"
        
        # Get source code around the error
        source_code = ""
        try:
            import linecache
            # Get a few lines around the error
            lines = []
            for i in range(max(1, line_number - 2), line_number + 3):
                line = linecache.getline(file_path, i)
                if line:
                    prefix = ">>> " if i == line_number else "    "
                    lines.append(f"{prefix}{i}: {line.rstrip()}")
            source_code = "\n".join(lines)
        except Exception:
            source_code = f"Could not retrieve source code for {file_path}:{line_number}"
        
        # Get full traceback string
        import traceback as tb_module
        traceback_str = ''.join(tb_module.format_exception(exc_type, exc_value, tb))
        
        return cls(
            exception_type=exc_type.__name__,
            exception_message=str(exc_value),
            target_fqn=target_fqn,
            file_path=file_path,
            line_number=line_number,
            source_code=source_code,
            traceback_str=traceback_str,
            local_vars=local_vars
        )


class PatchProposal(BaseModel):
    """A proposed code patch from the LLM."""
    
    patch_code: str
    explanation: str
    confidence: float = 0.8
    test_cases: List[str] = []


class PatchResult(BaseModel):
    """Result of applying a patch."""
    
    patch_id: str
    status: PatchStatus
    original_code: str
    patched_code: str
    target_fqn: str
    applied_at: datetime = None
    error_message: str = None
    original_function: Any = None
    patched_function: Any = None
