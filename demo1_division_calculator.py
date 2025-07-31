#!/usr/bin/env python3
"""
Demo 1: Simple Division Calculator with Self-Healing
===================================================

A simple calculator that automatically fixes itself when you divide by zero.
"""

import sys
import os
import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reflexruntime.core.orchestrator import activate_reflex_runtime

# Activate ReflexRuntime 
activate_reflex_runtime(debug=False)

def divide_numbers(a: float, b: float) -> float:
    """Simple division function that will self-heal."""
    return a / b

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\nGoodbye! 👋")
    sys.exit(0)

def main():
    """Interactive calculator that shows self-healing."""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🧮 ReflexRuntime Calculator")
    print("=" * 40)
    print("Try dividing by zero to see the magic!")
    print("Press Ctrl+C to exit\n")
    
    calculation_count = 0
    
    while True:
        calculation_count += 1
        print(f"--- Calculation #{calculation_count} ---")
        
        try:
            a = float(input("First number:  "))
            b = float(input("Second number: "))
        except ValueError:
            print("Please enter valid numbers")
            continue
        except KeyboardInterrupt:
            break
        
        # Let division errors bubble up to ReflexRuntime
        try:
            result = divide_numbers(a, b)
            print(f"Result: {a} ÷ {b} = {result}")
            
            if b == 0:
                print("✨ Amazing! Division by zero was automatically fixed!")
        except ZeroDivisionError as e:
            print(f"⚡ Caught {type(e).__name__}: {e}")
            print("🔧 Triggering ReflexRuntime healing...")
            
            # Manually trigger ReflexRuntime 
            import sys
            from reflexruntime.core.orchestrator import get_simple_orchestrator
            
            exc_type, exc_value, exc_tb = sys.exc_info()
            orchestrator = get_simple_orchestrator()
            healed = orchestrator.handle(exc_type, exc_value, exc_tb)
            
            if healed:
                print("✅ Function healed! Trying again...")
                # Try again with healed function
                try:
                    result = divide_numbers(a, b)
                    print(f"🎉 Healed result: {a} ÷ {b} = {result}")
                except Exception as e2:
                    print(f"⚠️ Still having issues: {e2}")
            else:
                print("❌ Could not heal the function")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        print()

if __name__ == "__main__":
    main() 