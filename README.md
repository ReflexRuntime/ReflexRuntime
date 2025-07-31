# ReflexRuntime

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Intelligent runtime error recovery through AI-powered code analysis and dynamic patching

ReflexRuntime is an experimental framework that leverages large language models to automatically analyze runtime exceptions and attempt to generate corrective patches. When an exception occurs, the system captures the execution context, sends it to an AI model for analysis, and dynamically applies suggested fixes without requiring application restarts.

## Features

### Automatic Error Analysis
- Captures detailed exception context including stack traces, variable states, and code snippets
- Sends comprehensive error information to AI models for intelligent analysis
- Generates contextual patches based on error patterns and code structure

### Dynamic Code Patching  
- Hot-swaps functions in memory using Python's dynamic execution capabilities
- Preserves application state during the patching process
- Maintains execution flow without service interruption

### Comprehensive Logging
- Detailed session logs for every AI interaction and patch attempt
- Markdown-formatted reports with full context and reasoning
- Debug viewer for analyzing patch success rates and error patterns

### Production Scenarios
ReflexRuntime can potentially handle various runtime issues:
- Division by zero and mathematical errors
- Missing dictionary keys and attribute errors  
- Type conversion failures
- API response format inconsistencies

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/ReflexRuntime.git
cd ReflexRuntime
pip install -r requirements.txt
```

### Configuration

Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### Basic Usage

```python
from reflexruntime.core.orchestrator import activate_reflex_runtime

# Enable automatic error handling
activate_reflex_runtime(debug=True)

def divide_numbers(a, b):
    return a / b

# When this raises ZeroDivisionError, ReflexRuntime will:
# 1. Capture the exception context
# 2. Send details to AI for analysis  
# 3. Generate and apply a potential fix
# 4. Retry the operation

result = divide_numbers(10, 0)  # Triggers AI healing
```

## Demonstrations

### Demo 1: Division Calculator (`demo1_division_calculator.py`)

Interactive calculator demonstrating automatic handling of division by zero errors:

```bash
python demo1_division_calculator.py
```

Features:
- Real-time error detection and recovery
- Interactive command-line interface
- Visible healing process with status updates

### Demo 2: Missing Key Handler (`demo2_missing_key_handler.py`)

Shows automatic recovery from missing dictionary key errors in user data processing:

```bash
python demo2_missing_key_handler.py
```

Features:
- Simulates real-world data processing scenarios
- Demonstrates handling of KeyError exceptions
- Shows graceful degradation with default values

### Demo 3: Flask API Monitor (`demo3_flask_api.py`)

Comprehensive Flask API with failure injection and real-time monitoring:

```bash
python demo3_flask_api.py
```

Then open http://localhost:5000 in your browser.

Features:
- Live monitoring dashboard with metrics and charts
- Configurable failure injection for testing
- Real-time visualization of error rates and healing success
- Multiple API endpoints demonstrating different error scenarios
- Load testing capabilities

## Architecture

### Core Components

```
reflexruntime/
├── core/
│   ├── orchestrator.py    # Exception handling and coordination
│   ├── llm_client.py      # AI model integration
│   ├── debug_logger.py    # Session logging and analytics  
│   └── schemas.py         # Data structures and types
└── agents/
    └── python/
        └── hook.py        # Exception hook installation
```

### How It Works

1. **Exception Capture**: Custom exception hooks intercept runtime errors and collect execution context
2. **AI Analysis**: Exception details are sent to language models for analysis and patch generation  
3. **Dynamic Patching**: Generated code is validated and hot-swapped into the running application
4. **Execution Retry**: The original operation is retried with the patched function
5. **Session Logging**: All interactions are logged for analysis and debugging

## Debug and Monitoring

### Debug Viewer

View detailed logs of all AI interactions:

```bash
python debug_viewer.py
```

Features:
- Session analytics and success rate tracking
- Interactive session browser with filtering
- Exception type analysis and patterns
- Patch effectiveness metrics

### Session Logs

All AI interactions are automatically logged to the `debug/` directory in markdown format, including:
- Complete exception context and stack traces
- AI model responses and reasoning  
- Generated patches and validation results
- Success/failure status and execution timing

## Limitations and Considerations

### Important Notes

- **Experimental Technology**: This is a research project exploring AI-powered error recovery
- **Security Considerations**: Dynamic code execution introduces potential security risks
- **Production Readiness**: Not recommended for production environments without thorough testing
- **AI Model Dependency**: Requires access to language models (OpenAI API) for functionality
- **Success Rates**: Effectiveness varies significantly based on error type and code complexity

### Best Practices

- Use in development and testing environments initially
- Review generated patches before deploying to production
- Monitor debug logs for unexpected behavior
- Implement proper error handling as a primary strategy
- Consider ReflexRuntime as a fallback mechanism, not a primary solution

## Contributing

We welcome contributions! Please see our contributing guidelines and:

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests  
4. Submit a pull request with a clear description

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project explores the intersection of AI and runtime systems, inspired by advances in large language models and their potential applications in software engineering.

---

**⚠️ Disclaimer**: ReflexRuntime is an experimental project. Use caution when deploying in production environments and always implement proper error handling as your primary strategy.
