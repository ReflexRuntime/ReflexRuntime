"""
Debug logging system for ReflexRuntime AI analysis and patches.
"""

import os
import time
from datetime import datetime
from typing import Optional
from .schemas import ErrorContext, PatchProposal


class DebugLogger:
    """Logs AI analysis sessions and patches for debugging and audit purposes."""
    
    def __init__(self, debug_dir: str = "debug"):
        """Initialize debug logger.
        
        Args:
            debug_dir: Directory to store debug logs
        """
        self.debug_dir = debug_dir
        self.ensure_debug_dir()
    
    def ensure_debug_dir(self):
        """Create debug directory if it doesn't exist."""
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            print(f"Created debug directory: {self.debug_dir}")
    
    def log_ai_session(self, 
                      error_context: ErrorContext, 
                      patch_proposal: Optional[PatchProposal],
                      success: bool,
                      llm_response_raw: str = None,
                      error_message: str = None):
        """Log a complete AI analysis session.
        
        Args:
            error_context: The original exception context
            patch_proposal: AI-generated patch proposal (if any)
            success: Whether the patch was successfully applied
            llm_response_raw: Raw LLM response for debugging
            error_message: Error message if patch failed
        """
        try:
            # Generate filename: program_function_epoch.md
            program_name = self._extract_program_name(error_context.file_path)
            function_name = error_context.target_fqn.split('.')[-1]
            epoch = int(time.time())
            
            filename = f"{program_name}_{function_name}_{epoch}.md"
            filepath = os.path.join(self.debug_dir, filename)
            
            # Generate markdown content
            content = self._generate_debug_markdown(
                error_context, patch_proposal, success, llm_response_raw, error_message
            )
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Debug session logged: {filename}")
            return filepath
            
        except Exception as e:
            print(f"WARNING: Failed to log debug session: {e}")
            return None
    
    def _extract_program_name(self, file_path: str) -> str:
        """Extract program name from file path."""
        if not file_path:
            return "unknown"
        
        # Get filename without extension
        filename = os.path.basename(file_path)
        program_name = os.path.splitext(filename)[0]
        
        # Clean up name for filename
        program_name = program_name.replace(' ', '_').replace('-', '_')
        
        return program_name
    
    def _generate_debug_markdown(self, 
                                error_context: ErrorContext,
                                patch_proposal: Optional[PatchProposal],
                                success: bool,
                                llm_response_raw: str = None,
                                error_message: str = None) -> str:
        """Generate markdown content for debug log."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Status indicator
        status_indicator = "SUCCESS" if success else "FAILED"
        status_text = "SUCCESS" if success else "FAILED"
        
        content = f"""# ReflexRuntime Debug Session - {status_indicator}

**Status:** {status_text}  
**Timestamp:** {timestamp}  
**Program:** {self._extract_program_name(error_context.file_path)}  
**Function:** {error_context.target_fqn}  
**File:** {error_context.file_path}  
**Line:** {error_context.line_number}  

---

## Exception Details

**Type:** `{error_context.exception_type}`  
**Message:** `{error_context.exception_message}`  

### Full Traceback
```
{error_context.traceback_str}
```

### Local Variables at Error
```json
{self._format_local_vars(error_context.local_vars)}
```

---

## Original Code

```python
{error_context.source_code}
```

---

## AI Analysis

"""

        if patch_proposal:
            content += f"""
### AI Recommendation
**Confidence:** {patch_proposal.confidence:.1%}  
**Explanation:** {patch_proposal.explanation}

### AI-Generated Patch
```python
{patch_proposal.patch_code}
```

### Test Cases Suggested
"""
            for i, test_case in enumerate(patch_proposal.test_cases, 1):
                content += f"{i}. {test_case}\n"
        else:
            content += "\n**Result:** AI could not generate a patch for this exception.\n"
        
        if llm_response_raw:
            content += f"""
### Raw LLM Response
```json
{llm_response_raw}
```
"""

        content += "\n---\n\n## Patch Application\n\n"
        
        if success:
            content += "**Patch applied successfully!**\n\n"
            content += "The function was hot-swapped in memory and is now handling the error case gracefully.\n"
        else:
            content += "**Patch application failed.**\n\n"
            if error_message:
                content += f"**Error:** {error_message}\n\n"
            content += "The original function remains unchanged.\n"
        
        ai_confidence = f"{patch_proposal.confidence:.1%}" if patch_proposal else "N/A"
        patch_status = "Applied" if success else "Failed"
        
        content += f"""
---

## Session Summary

- **Exception Type:** {error_context.exception_type}
- **AI Confidence:** {ai_confidence}
- **Patch Status:** {patch_status}
- **Function:** {error_context.target_fqn}

---

*Generated by ReflexRuntime Debug Logger*
"""
        
        return content
    
    def _format_local_vars(self, local_vars: dict) -> str:
        """Format local variables for display."""
        if not local_vars:
            return "{}"
        
        import json
        try:
            return json.dumps(local_vars, default=str, indent=2)
        except Exception:
            # Fallback to string representation
            return str(local_vars)
    
    def list_debug_sessions(self) -> list:
        """List all debug session files."""
        if not os.path.exists(self.debug_dir):
            return []
        
        files = [f for f in os.listdir(self.debug_dir) if f.endswith('.md')]
        files.sort(reverse=True)  # Most recent first
        return files
    
    def get_session_stats(self) -> dict:
        """Get statistics about debug sessions."""
        files = self.list_debug_sessions()
        
        total_sessions = len(files)
        successful_sessions = 0
        
        for filename in files:
            filepath = os.path.join(self.debug_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "**Status:** SUCCESS" in content:
                        successful_sessions += 1
            except Exception:
                continue
        
        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "failed_sessions": total_sessions - successful_sessions,
            "success_rate": (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
        }


# Global debug logger instance
_global_debug_logger = None


def get_debug_logger() -> DebugLogger:
    """Get or create the global debug logger instance."""
    global _global_debug_logger
    if _global_debug_logger is None:
        _global_debug_logger = DebugLogger()
    return _global_debug_logger 