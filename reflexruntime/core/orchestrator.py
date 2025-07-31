"""
Main orchestrator for exception handling and patch coordination.
"""

import sys
import uuid
import traceback
import re
from datetime import datetime
from .llm_client import get_llm_client
from .debug_logger import get_debug_logger
from .schemas import ErrorContext, PatchProposal


class SimpleOrchestrator:
    """Simplified orchestrator for Phase 1 demo with detailed debugging."""
    
    def __init__(self):
        self._active_patches = {}
        self.patches_applied = 0
        self.debug = True
    
    def handle(self, exc_type, exc_value, tb) -> bool:
        """Handle an exception by applying a simple fix."""
        try:
            if self.debug:
                print(f"\nDEBUG: Exception handler triggered")
                print(f"DEBUG: Exception type: {exc_type.__name__}")
                print(f"DEBUG: Exception message: {str(exc_value)}")
                print(f"DEBUG: Traceback:")
                traceback.print_tb(tb)
            
            # Create error context
            ctx = ErrorContext.from_traceback(exc_type, exc_value, tb)
            
            if self.debug:
                print(f"DEBUG: Error context created")
                print(f"DEBUG: Target FQN: {ctx.target_fqn}")
                print(f"DEBUG: File path: {ctx.file_path}")
                print(f"DEBUG: Line number: {ctx.line_number}")
                print(f"DEBUG: Source code preview:")
                print(f"DEBUG: {ctx.source_code[:200]}...")
            
            print(f"ReflexRuntime: Analyzing {ctx.exception_type}")
            print(f"Sending exception to LLM for analysis...")
            
            if self.debug:
                print(f"DEBUG: Full error context:")
                print(f"DEBUG: Exception type: {ctx.exception_type}")
                print(f"DEBUG: Exception message: {ctx.exception_message}")
                print(f"DEBUG: Target function: {ctx.target_fqn}")
                print(f"DEBUG: Source code length: {len(ctx.source_code)} chars")
            
            # Get LLM client and analyze
            llm_client = get_llm_client()
            if llm_client is None:
                print(f"ERROR: LLM client not available - cannot analyze {ctx.exception_type}")
                error_message = "LLM client not available"
                success = False
                patch_proposal = None
                llm_response_raw = None
            else:
                try:
                    # Call LLM to analyze and generate patch
                    response_data = llm_client.analyze_exception_and_generate_patch_with_raw(ctx)
                    
                    if response_data:
                        patch_proposal, llm_response_raw = response_data
                    else:
                        patch_proposal = None
                        llm_response_raw = "No response from LLM"
                    
                    if patch_proposal is None:
                        print(f"FAILED: LLM could not generate a patch for {ctx.exception_type}")
                        error_message = "LLM could not generate a patch"
                        success = False
                    else:
                        print(f"LLM Analysis Complete!")
                        print(f"LLM Explanation: {patch_proposal.explanation}")
                        print(f"LLM Confidence: {patch_proposal.confidence:.1%}")
                        
                        if self.debug:
                            print(f"DEBUG: Generated patch code:")
                            print(f"DEBUG: {patch_proposal.patch_code}")
                        
                        # Apply the LLM-generated patch
                        success = self._apply_llm_patch(ctx, patch_proposal)
                        
                        if success:
                            print(f"SUCCESS: LLM patch applied successfully! Function is now self-healing.")
                            self.patches_applied += 1
                            error_message = None  # No error
                        else:
                            if self.debug:
                                print("DEBUG: LLM patch application failed")
                            print("FAILED: Failed to apply LLM patch")
                            error_message = "Patch application failed"
                    
                    # Log the session regardless of success/failure
                    debug_logger = get_debug_logger()
                    debug_logger.log_ai_session(
                        error_context=ctx,
                        patch_proposal=patch_proposal,
                        success=success,
                        llm_response_raw=llm_response_raw,
                        error_message=error_message
                    )
                    
                    return success
                        
                except Exception as llm_error:
                    print(f"ERROR: LLM integration error: {llm_error}")
                    if self.debug:
                        traceback.print_exc()
                    print(f"FAILED: No fallback available - LLM integration required")
                    success = False
                    error_message = f"LLM integration error: {llm_error}"
                    
                    # Still log the failed session
                    try:
                        debug_logger = get_debug_logger()
                        debug_logger.log_ai_session(
                            error_context=ctx,
                            patch_proposal=None,
                            success=False,
                            llm_response_raw=None,
                            error_message=error_message
                        )
                    except Exception as log_error:
                        print(f"WARNING: Failed to log debug session: {log_error}")
                    
                    return False
                    
        except Exception as e:
            if self.debug:
                print(f"DEBUG: Internal ReflexRuntime error: {e}")
                traceback.print_exc()
            return False
    
    def _apply_llm_patch(self, error_context: ErrorContext, patch_proposal) -> bool:
        """Apply LLM-generated patch to the original function."""
        try:
            if self.debug:
                print(f"DEBUG: Applying LLM patch for {error_context.target_fqn}")
            
            # Extract function name from the patch
            func_name = self._extract_function_name(patch_proposal.patch_code)
            if not func_name:
                print("ERROR: Could not extract function name from LLM patch")
                return False
            
            if self.debug:
                print(f"DEBUG: Extracted function name: {func_name}")
            
            # Get the target namespace where the function lives
            namespace = self._get_function_namespace(error_context.target_fqn)
            if namespace is None:
                print(f"ERROR: Could not find namespace for {error_context.target_fqn}")
                return False
            
            # Check if function exists in namespace
            if not hasattr(namespace, func_name):
                print(f"ERROR: Function '{func_name}' not found in target namespace")
                return False
            
            if self.debug:
                original_func = getattr(namespace, func_name)
                print(f"DEBUG: Original function: {original_func}")
            
            # Execute the patch code in the namespace
            try:
                exec(patch_proposal.patch_code, namespace.__dict__)
            except Exception as exec_error:
                # Check if the function was created despite the error
                if hasattr(namespace, func_name):
                    if self.debug:
                        print(f"DEBUG: Function created despite execution error: {exec_error}")
                else:
                    print(f"ERROR: LLM patch did not create function '{func_name}'")
                    return False
            except SyntaxError as exec_error:
                print(f"ERROR: Error executing LLM patch: {exec_error}")
                return False
            
            # Verify the patch was applied
            new_func = getattr(namespace, func_name, None)
            if new_func is None:
                print(f"ERROR: Function '{func_name}' not found after patch application")
                return False
            
            if self.debug:
                print(f"DEBUG: Function hot-swapped successfully")
                print(f"DEBUG: New function: {getattr(namespace, func_name)}")
            
            return True
            
        except Exception as e:
            if self.debug:
                traceback.print_exc()
            return False
    
    def _extract_function_name(self, patch_code):
        """Extract the function name from patch code."""
        try:
            # Look for function definition using regex
            match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', patch_code)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None
    
    def _get_function_namespace(self, fqn):
        """Get the namespace where the function is defined based on its FQN."""
        try:
            # Try __main__ first (most common for demo scripts)
            import __main__
            func_name = fqn.split('.')[-1]
            if hasattr(__main__, func_name):
                return __main__
            
            # Try to find the module from the FQN
            module_path = fqn.rsplit('.', 1)[0]
            if module_path != 'unknown':
                try:
                    import importlib
                    module = importlib.import_module(module_path)
                    return module
                except ImportError:
                    pass
            
            return __main__  # Fallback to __main__
            
        except Exception:
            return None
    

    def install_hook(self):
        """Install the global exception hook."""
        original_excepthook = sys.excepthook
        orchestrator = self
        
        def reflex_excepthook(exc_type, exc_value, tb):
            if orchestrator.debug:
                print(f"\nDEBUG: sys.excepthook called")
                print(f"DEBUG: Exception: {exc_type.__name__}: {exc_value}")
            
            # Try to handle the exception
            handled = orchestrator.handle(exc_type, exc_value, tb)
            
            if handled:
                if orchestrator.debug:
                    print(f"DEBUG: Exception was handled by ReflexRuntime")
            else:
                if orchestrator.debug:
                    print(f"DEBUG: Exception not handled, falling back to default behavior")
                # Fall back to original exception handling only if not handled
                original_excepthook(exc_type, exc_value, tb)
        
        sys.excepthook = reflex_excepthook
        print("ReflexRuntime: Exception hook installed with debug mode")


# Global orchestrator instance
_global_orchestrator = None


def get_orchestrator():
    """Get or create the global orchestrator instance."""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = SimpleOrchestrator()
    return _global_orchestrator


def get_simple_orchestrator():
    """Get or create the global orchestrator instance (alias for compatibility)."""
    return get_orchestrator()


def install_autopatch():
    """Install automatic patching for the current program."""
    orchestrator = get_orchestrator()
    orchestrator.install_hook()


def activate_reflex_runtime(debug=True):
    """Activate ReflexRuntime with the specified debug mode."""
    orchestrator = get_orchestrator()
    orchestrator.debug = debug
    orchestrator.install_hook()
