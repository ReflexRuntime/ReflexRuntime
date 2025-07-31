"""
LLM client for analyzing exceptions and generating code patches.
"""

import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from .schemas import ErrorContext, PatchProposal

# Load environment variables from .env file
load_dotenv()


class LLMClient:
    """Client for interacting with LLM APIs to analyze exceptions and generate patches."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY in environment.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')  # Using GPT-4 by default for better code analysis
    
    def analyze_exception_and_generate_patch_with_raw(self, error_context: ErrorContext) -> Optional[tuple]:
        """Analyze an exception and generate a code patch, returning both proposal and raw response.
        
        Args:
            error_context: Context information about the exception
            
        Returns:
            Tuple of (PatchProposal, raw_response) or None if LLM couldn't generate a fix
        """
        try:
            prompt = self._create_analysis_prompt(error_context)
            
            print(f"DEBUG: Sending to LLM:")
            print(f"DEBUG: Model: {self.model}")
            print(f"DEBUG: Prompt length: {len(prompt)} characters")
            print(f"DEBUG: Prompt preview: {prompt[:200]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python developer who analyzes exceptions and generates safe, minimal code patches. Always respond with valid JSON containing the patch code, explanation, and confidence score."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent, reliable output
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            print(f"DEBUG: LLM Response received:")
            print(f"DEBUG: Response length: {len(response_text)} characters")
            print(f"DEBUG: Full response:")
            print(f"DEBUG: {response_text}")
            
            # Parse the JSON response
            try:
                patch_data = json.loads(response_text)
                proposal = PatchProposal(
                    patch_code=patch_data.get('patch_code', ''),
                    explanation=patch_data.get('explanation', ''),
                    confidence=float(patch_data.get('confidence', 0.5)),
                    test_cases=patch_data.get('test_cases', [])
                )
                return (proposal, response_text)
            except json.JSONDecodeError:
                print(f"ERROR: LLM returned invalid JSON: {response_text}")
                # Try to extract JSON from response if it's wrapped in markdown
                try:
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        patch_data = json.loads(json_match.group(1))
                        proposal = PatchProposal(
                            patch_code=patch_data.get('patch_code', ''),
                            explanation=patch_data.get('explanation', ''),
                            confidence=float(patch_data.get('confidence', 0.5)),
                            test_cases=patch_data.get('test_cases', [])
                        )
                        return (proposal, response_text)
                    else:
                        print(f"ERROR: Could not extract valid JSON from LLM response")
                        return None
                except (json.JSONDecodeError, AttributeError):
                    print(f"ERROR: Failed to parse LLM response as JSON")
                    return None
                
        except Exception as e:
            print(f"ERROR: LLM API error: {e}")
            # Return None to allow fallback behavior
            return None

    def analyze_exception_and_generate_patch(self, error_context: ErrorContext) -> Optional[PatchProposal]:
        """Analyze an exception and generate a code patch to fix it (backward compatibility).
        
        Args:
            error_context: Context information about the exception
            
        Returns:
            PatchProposal with the suggested fix, or None if LLM couldn't generate a fix
        """
        result = self.analyze_exception_and_generate_patch_with_raw(error_context)
        if result:
            return result[0]  # Return just the proposal
        return None
    
    def _create_analysis_prompt(self, error_context: ErrorContext) -> str:
        """Create a prompt for the LLM to analyze the exception and generate a patch."""
        prompt = f"""
You are ReflexRuntime, an AI system that automatically fixes Python code at runtime. A Python function has thrown an exception and you need to generate a replacement function that handles this error gracefully.

**CRITICAL REQUIREMENTS:**
1. You MUST respond with ONLY valid JSON - no markdown, no explanations outside the JSON
2. The "patch_code" field must contain a complete, executable Python function
3. The function must have the EXACT same name and signature as the original
4. Add proper error handling to prevent the same exception
5. Include a docstring mentioning this is AI-patched

**Exception Analysis:**
- Exception Type: {error_context.exception_type}
- Exception Message: {error_context.exception_message}
- Failed Function: {error_context.target_fqn}
- Error Location: Line {error_context.line_number}

**Original Function Source Code:**
```python
{error_context.source_code}
```

**Full Traceback:**
```
{error_context.traceback_str}
```

**Local Variables at Time of Error:**
{json.dumps(error_context.local_vars, default=str, indent=2)}

**Your Task:**
Analyze this exception and create a patched version of the function that:
- Handles the specific error case that occurred
- Returns a reasonable value instead of crashing
- Preserves normal operation for valid inputs
- Includes appropriate error messaging

**Required JSON Response Format:**
{{
    "patch_code": "def exact_function_name(same, parameters):\\n    \\\"\\\"\\\"AI-patched function that handles {error_context.exception_type}.\\\"\\\"\\\"\\n    # Add your error handling logic here\\n    # Return appropriate values for both error and normal cases",
    "explanation": "Concise explanation of what was fixed and how the error is now handled",
    "confidence": 0.85,
    "test_cases": ["describe a test case that would trigger the original error", "describe a test case that should work normally"]
}}

Respond with ONLY the JSON - no additional text:
"""
        return prompt


# Global LLM client instance
_global_llm_client = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _global_llm_client
    if _global_llm_client is None:
        _global_llm_client = LLMClient()
    return _global_llm_client 