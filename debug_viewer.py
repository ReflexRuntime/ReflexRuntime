#!/usr/bin/env python3
"""
Debug Session Viewer for ReflexRuntime
=====================================

View and analyze AI debug sessions logged by ReflexRuntime.
"""

import sys
import os
from pathlib import Path

# Add reflexruntime to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reflexruntime.core.debug_logger import get_debug_logger


def main():
    """Main debug viewer interface."""
    debug_logger = get_debug_logger()
    
    print("ReflexRuntime Debug Session Viewer")
    print("=" * 50)
    
    # Get statistics
    stats = debug_logger.get_session_stats()
    print(f"Session Statistics:")
    print(f"   Total Sessions: {stats['total_sessions']}")
    print(f"   Successful: {stats['successful_sessions']}")
    print(f"   Failed: {stats['failed_sessions']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    
    # List recent sessions
    sessions = debug_logger.list_debug_sessions()
    
    if not sessions:
        print("\nNo debug sessions found.")
        print("Run some ReflexRuntime demos to generate debug logs!")
        return
    
    print(f"\nRecent Debug Sessions ({len(sessions)} total):")
    print("-" * 50)
    
    for i, session_file in enumerate(sessions[:10], 1):  # Show last 10
        # Parse filename: program_function_epoch.md
        parts = session_file.replace('.md', '').split('_')
        if len(parts) >= 3:
            program = parts[0]
            function = parts[1]
            epoch = parts[2]
            
            # Check if successful
            filepath = os.path.join(debug_logger.debug_dir, session_file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    status = "[SUCCESS]" if "**Status:** SUCCESS" in content else "[FAILED]"
            except Exception:
                status = "[UNKNOWN]"
            
            print(f"{i:2d}. {status} {program}.{function} ({session_file})")
        else:
            print(f"{i:2d}. {session_file}")
    
    if len(sessions) > 10:
        print(f"    ... and {len(sessions) - 10} more sessions")
    
    print(f"\nDebug files location: {debug_logger.debug_dir}/")
    print("Use any markdown viewer to see detailed session reports!")
    
    # Interactive mode
    while True:
        print("\n" + "=" * 50)
        choice = input("Enter session number to view (1-10), 'stats' for statistics, or 'quit': ").strip()
        
        if choice.lower() in ['quit', 'q', 'exit']:
            break
        elif choice.lower() == 'stats':
            show_detailed_stats(debug_logger)
        else:
            try:
                session_num = int(choice)
                if 1 <= session_num <= min(10, len(sessions)):
                    show_session_summary(debug_logger, sessions[session_num - 1])
                else:
                    print(f"ERROR: Invalid session number. Please enter 1-{min(10, len(sessions))}")
            except ValueError:
                print("ERROR: Invalid input. Please enter a number, 'stats', or 'quit'")


def show_detailed_stats(debug_logger):
    """Show detailed statistics about debug sessions."""
    sessions = debug_logger.list_debug_sessions()
    
    if not sessions:
        print("No sessions to analyze.")
        return
    
    print("\nDetailed Statistics:")
    print("-" * 30)
    
    # Analyze sessions
    by_exception = {}
    by_program = {}
    successful_patches = 0
    
    for session_file in sessions:
        try:
            filepath = os.path.join(debug_logger.debug_dir, session_file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract exception type and program
                lines = content.split('\n')
                exc_type = None
                program = None
                success = "**Status:** SUCCESS" in content
                
                for line in lines:
                    if line.startswith('**Type:**'):
                        exc_type = line.split('`')[1] if '`' in line else 'Unknown'
                    elif line.startswith('**Program:**'):
                        program = line.split('**Program:**')[1].strip()
                
                if exc_type:
                    if exc_type not in by_exception:
                        by_exception[exc_type] = {'total': 0, 'success': 0}
                    by_exception[exc_type]['total'] += 1
                    if success:
                        by_exception[exc_type]['success'] += 1
                        successful_patches += 1
                
                if program:
                    if program not in by_program:
                        by_program[program] = {'total': 0, 'success': 0}
                    by_program[program]['total'] += 1
                    if success:
                        by_program[program]['success'] += 1
                        
        except Exception as e:
            continue
    
    print(f"Exception Types:")
    for exc_type, stats in by_exception.items():
        success_count = stats['success']
        total_count = stats['total']
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        print(f"   {exc_type}: {total_count} occurrences ({success_count} fixed, {success_rate:.1f}%)")


def show_session_summary(debug_logger, session_file):
    """Show a summary of a specific debug session."""
    try:
        filepath = os.path.join(debug_logger.debug_dir, session_file)
        
        print(f"\nSession Summary: {session_file}")
        print("-" * 50)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract key information
            lines = content.split('\n')
            
            for line in lines:
                if line.startswith('**Status:**'):
                    print(f"Status: {line.split('**Status:**')[1].strip()}")
                elif line.startswith('**Timestamp:**'):
                    print(f"Timestamp: {line.split('**Timestamp:**')[1].strip()}")
                elif line.startswith('**Function:**'):
                    print(f"Function: {line.split('**Function:**')[1].strip()}")
                elif line.startswith('**Type:**'):
                    print(f"Exception: {line.split('**Type:**')[1].strip()}")
                elif line.startswith('**Confidence:**'):
                    print(f"AI Confidence: {line.split('**Confidence:**')[1].strip()}")
                elif line.startswith('**Explanation:**'):
                    explanation = line.split('**Explanation:**')[1].strip()
                    print(f"AI Explanation: {explanation}")
            
            print(f"\nFull report available at: {filepath}")
            
    except Exception as e:
        print(f"ERROR: Error reading session file: {e}")


if __name__ == "__main__":
    main() 