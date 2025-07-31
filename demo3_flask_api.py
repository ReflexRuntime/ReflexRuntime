#!/usr/bin/env python3
"""
Demo 3: Flask API with ReflexRuntime and Real-time Monitoring
============================================================

A Flask API that can inject different types of failures and 
automatically heal them using ReflexRuntime. Includes:

- Division by zero endpoint
- Missing key data processing
- Invalid data type handling  
- Real-time monitoring capabilities

Features:
- Self-healing API endpoints
- Failure injection controls
- Performance metrics
- CORS enabled for frontend
"""

import sys
import os
import time
import random
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
from reflexruntime.core.orchestrator import activate_reflex_runtime
from reflexruntime.core.orchestrator import get_simple_orchestrator

# Activate ReflexRuntime for the Flask app
activate_reflex_runtime(debug=False)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global state for failure injection
failure_modes = {
    'division_by_zero': False,
    'missing_key': False, 
    'wrong_data_type': False,
    'slow_response': False
}

# Metrics tracking
request_metrics = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'avg_response_time': 0,
    'last_error': None,
    'patches_applied': 0
}

def track_request(func):
    """Decorator to track request metrics."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_metrics['total_requests'] += 1
        
        try:
            result = func(*args, **kwargs)
            request_metrics['successful_requests'] += 1
            response_time = (time.time() - start_time) * 1000
            
            # Update average response time
            total_time = (request_metrics['avg_response_time'] * 
                         (request_metrics['total_requests'] - 1) + response_time)
            request_metrics['avg_response_time'] = total_time / request_metrics['total_requests']
            
            return result
        except Exception as e:
            request_metrics['failed_requests'] += 1
            request_metrics['last_error'] = str(e)
            raise
    
    wrapper.__name__ = func.__name__
    return wrapper

# API Functions that will be self-healed

def calculate_division(a: float, b: float) -> float:
    """Division function that can fail with division by zero."""
    if failure_modes['division_by_zero'] and random.random() < 0.3:
        b = 0  # Inject division by zero error
    return a / b

def process_user_data(data: dict) -> dict:
    """Process user data that can have missing keys."""
    if failure_modes['missing_key'] and random.random() < 0.3:
        # Remove a random key to trigger KeyError
        if 'email' in data:
            del data['email']
    
    result = {
        'user_id': data['user_id'],
        'username': data['username'], 
        'email': data['email'],
        'processed_at': datetime.now().isoformat()
    }
    return result

def parse_number_data(value) -> int:
    """Parse number data that can have wrong types."""
    if failure_modes['wrong_data_type'] and random.random() < 0.3:
        value = "not_a_number"  # Inject type error
    return int(value)

def safe_api_call(func, *args, **kwargs):
    """Safely call an API function with ReflexRuntime healing."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"DEBUG: Exception caught in safe_api_call: {type(e).__name__}: {e}")
        
        # Manually trigger ReflexRuntime healing
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(f"DEBUG: Triggering ReflexRuntime for {func.__name__}")
        
        orchestrator = get_simple_orchestrator()
        healed = orchestrator.handle(exc_type, exc_value, exc_tb)
        
        print(f"DEBUG: Healing result: {healed}")
        
        if healed:
            # Update metrics
            request_metrics['patches_applied'] += 1
            print(f"DEBUG: Function healed! Retrying {func.__name__}")
            
            # Try again with healed function
            try:
                func_name = func.__name__
                current_module = sys.modules[__name__]
                patched_func = getattr(current_module, func_name)
                result = patched_func(*args, **kwargs)
                print(f"DEBUG: Retry successful for {func.__name__}")
                return result
            except Exception as retry_error:
                print(f"DEBUG: Retry failed: {retry_error}")
                # If still failing, return a safe default
                return None
        else:
            print(f"DEBUG: Could not heal {func.__name__}, returning default")
            # If couldn't heal, return safe default
            return None

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'reflexruntime': 'active'
    })

@app.route('/api/calculate', methods=['POST'])
@track_request
def calculate():
    """Calculate division with potential division by zero."""
    data = request.get_json()
    
    if failure_modes['slow_response']:
        time.sleep(random.uniform(0.1, 0.5))  # Simulate slow response
    
    a = float(data.get('a', 10))
    b = float(data.get('b', 2))
    
    # Use safe API call for self-healing
    result = safe_api_call(calculate_division, a, b)
    
    # If result is None (error occurred), provide a default
    if result is None:
        result = "Error handled gracefully"
    
    return jsonify({
        'operation': 'division',
        'a': a,
        'b': b,
        'result': result,
        'timestamp': datetime.now().isoformat(),
        'healed': result == "Error handled gracefully" or request_metrics['patches_applied'] > 0
    })

@app.route('/api/process_user', methods=['POST'])
@track_request
def process_user():
    """Process user data with potential missing keys."""
    data = request.get_json()
    
    if failure_modes['slow_response']:
        time.sleep(random.uniform(0.1, 0.5))
    
    # Default user data
    user_data = {
        'user_id': data.get('user_id', random.randint(1000, 9999)),
        'username': data.get('username', f'user_{random.randint(100, 999)}'),
        'email': data.get('email', f'user{random.randint(100, 999)}@example.com')
    }
    
    # Use safe API call for self-healing
    result = safe_api_call(process_user_data, user_data)
    
    # If result is None (error occurred), provide a default
    if result is None:
        result = {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'email': 'default@example.com',
            'processed_at': datetime.now().isoformat(),
            'note': 'Processed with default values after healing'
        }
    
    return jsonify({
        'operation': 'user_processing',
        'input': user_data,
        'result': result,
        'timestamp': datetime.now().isoformat(),
        'healed': 'note' in result or request_metrics['patches_applied'] > 0
    })

@app.route('/api/parse_number', methods=['POST'])
@track_request
def parse_number():
    """Parse number data with potential type errors."""
    data = request.get_json()
    
    if failure_modes['slow_response']:
        time.sleep(random.uniform(0.1, 0.5))
    
    value = data.get('value', random.randint(1, 100))
    
    # Use safe API call for self-healing
    result = safe_api_call(parse_number_data, value)
    
    # If result is None (error occurred), provide a default
    if result is None:
        result = 0  # Default value
    
    return jsonify({
        'operation': 'number_parsing',
        'input': value,
        'result': result,
        'timestamp': datetime.now().isoformat(),
        'healed': result == 0 or request_metrics['patches_applied'] > 0
    })

@app.route('/api/failure_modes', methods=['GET', 'POST'])
def manage_failure_modes():
    """Get or set failure mode toggles."""
    if request.method == 'POST':
        data = request.get_json()
        for key, value in data.items():
            if key in failure_modes:
                failure_modes[key] = bool(value)
        return jsonify({'status': 'updated', 'failure_modes': failure_modes})
    
    return jsonify(failure_modes)

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current API metrics."""
    return jsonify({
        'metrics': request_metrics,
        'failure_modes': failure_modes,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/reset_metrics', methods=['POST'])
def reset_metrics():
    """Reset all metrics."""
    global request_metrics
    request_metrics = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'avg_response_time': 0,
        'last_error': None,
        'patches_applied': 0
    }
    return jsonify({'status': 'metrics_reset'})

@app.route('/')
def index():
    """Serve the frontend HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReflexRuntime API Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007bff;
        }
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .control-group {
            flex: 1;
            min-width: 200px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            padding: 20px;
            background-color: #fff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        .metric-label {
            color: #6c757d;
            margin-top: 5px;
        }
        .chart-container {
            margin: 30px 0;
            height: 400px;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        .toggle {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        .toggle input {
            margin-right: 10px;
            transform: scale(1.2);
        }
        .status {
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.active {
            background-color: #d4edda;
            color: #155724;
        }
        .status.inactive {
            background-color: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ReflexRuntime API Monitor</h1>
            <p>Real-time monitoring of self-healing API endpoints</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <h3>Load Testing</h3>
                <button id="startBtn" class="btn-primary">Start Load Test</button>
                <button id="stopBtn" class="btn-danger" disabled>Stop Load Test</button>
                <button id="resetBtn" class="btn-success">Reset Metrics</button>
                <div class="status inactive" id="loadStatus">Inactive</div>
            </div>

            <div class="control-group">
                <h3>Failure Injection</h3>
                <div class="toggle">
                    <input type="checkbox" id="divisionByZero">
                    <label for="divisionByZero">Division by Zero</label>
                </div>
                <div class="toggle">
                    <input type="checkbox" id="missingKey">
                    <label for="missingKey">Missing Key Errors</label>
                </div>
                <div class="toggle">
                    <input type="checkbox" id="wrongDataType">
                    <label for="wrongDataType">Wrong Data Types</label>
                </div>
                <div class="toggle">
                    <input type="checkbox" id="slowResponse">
                    <label for="slowResponse">Slow Responses</label>
                </div>
            </div>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value" id="totalRequests">0</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="successRate">100%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="avgLatency">0ms</div>
                <div class="metric-label">Avg Latency</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="patchesApplied">0</div>
                <div class="metric-label">Patches Applied</div>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="responseChart"></canvas>
        </div>

        <div id="errorLog" style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
            <h4>Recent Activity</h4>
            <div id="activityList"></div>
        </div>
    </div>

    <script>
        // Chart setup
        const ctx = document.getElementById('responseChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Successful Requests/sec',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true
                }, {
                    label: 'Failed Requests/sec',
                    data: [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true
                }, {
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Requests/sec'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Response Time (ms)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        });

        // Global state
        let loadTestActive = false;
        let loadTestInterval = null;
        let metricsInterval = null;
        let lastMetrics = null;

        // API endpoints to test
        const endpoints = [
            { url: '/api/calculate', method: 'POST', data: { a: 10, b: 2 } },
            { url: '/api/process_user', method: 'POST', data: { user_id: 123 } },
            { url: '/api/parse_number', method: 'POST', data: { value: 42 } }
        ];

        // Utility functions
        function addActivity(message, type = 'info') {
            const activityList = document.getElementById('activityList');
            const time = new Date().toLocaleTimeString();
            const color = type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#007bff';
            
            const activity = document.createElement('div');
            activity.style.cssText = `margin: 5px 0; padding: 5px; border-left: 3px solid ${color}; background-color: white;`;
            activity.innerHTML = `<small style="color: #6c757d;">${time}</small> - ${message}`;
            
            activityList.insertBefore(activity, activityList.firstChild);
            
            // Keep only last 10 activities
            while (activityList.children.length > 10) {
                activityList.removeChild(activityList.lastChild);
            }
        }

        async function makeRequest() {
            const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
            try {
                const response = await fetch(endpoint.url, {
                    method: endpoint.method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(endpoint.data)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                return { success: true, data };
            } catch (error) {
                addActivity(`Request failed: ${error.message}`, 'error');
                return { success: false, error: error.message };
            }
        }

        async function updateFailureModes() {
            const modes = {
                division_by_zero: document.getElementById('divisionByZero').checked,
                missing_key: document.getElementById('missingKey').checked,
                wrong_data_type: document.getElementById('wrongDataType').checked,
                slow_response: document.getElementById('slowResponse').checked
            };

            try {
                await fetch('/api/failure_modes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(modes)
                });
            } catch (error) {
                console.error('Failed to update failure modes:', error);
            }
        }

        async function updateMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                const metrics = data.metrics;

                // Update metric displays
                document.getElementById('totalRequests').textContent = metrics.total_requests;
                const successRate = metrics.total_requests > 0 
                    ? ((metrics.successful_requests / metrics.total_requests) * 100).toFixed(1)
                    : 100;
                document.getElementById('successRate').textContent = successRate + '%';
                document.getElementById('avgLatency').textContent = metrics.avg_response_time.toFixed(1) + 'ms';
                document.getElementById('patchesApplied').textContent = metrics.patches_applied;

                // Update chart
                const now = new Date().toLocaleTimeString();
                const successPerSec = lastMetrics 
                    ? Math.max(0, metrics.successful_requests - lastMetrics.successful_requests)
                    : 0;
                const failedPerSec = lastMetrics 
                    ? Math.max(0, metrics.failed_requests - lastMetrics.failed_requests)
                    : 0;

                chart.data.labels.push(now);
                chart.data.datasets[0].data.push(successPerSec);
                chart.data.datasets[1].data.push(failedPerSec);
                chart.data.datasets[2].data.push(metrics.avg_response_time);

                // Keep only last 20 data points
                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets.forEach(dataset => dataset.data.shift());
                }

                chart.update('none');
                lastMetrics = metrics;

            } catch (error) {
                console.error('Failed to update metrics:', error);
            }
        }

        function startLoadTest() {
            if (loadTestActive) return;
            
            loadTestActive = true;
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('loadStatus').textContent = 'Active';
            document.getElementById('loadStatus').className = 'status active';
            
            addActivity('Load test started - 5 requests/sec', 'success');

            // Send ~5 requests per second
            loadTestInterval = setInterval(async () => {
                for (let i = 0; i < 5; i++) {
                    setTimeout(makeRequest, i * 200);
                }
            }, 1000);

            // Update metrics every second
            metricsInterval = setInterval(updateMetrics, 1000);
        }

        function stopLoadTest() {
            loadTestActive = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('loadStatus').textContent = 'Inactive';
            document.getElementById('loadStatus').className = 'status inactive';
            
            if (loadTestInterval) {
                clearInterval(loadTestInterval);
                loadTestInterval = null;
            }
            
            if (metricsInterval) {
                clearInterval(metricsInterval);
                metricsInterval = null;
            }
            
            addActivity('Load test stopped', 'info');
        }

        async function resetMetrics() {
            try {
                await fetch('/api/reset_metrics', { method: 'POST' });
                chart.data.labels = [];
                chart.data.datasets.forEach(dataset => dataset.data = []);
                chart.update();
                lastMetrics = null;
                document.getElementById('activityList').innerHTML = '';
                addActivity('Metrics reset', 'info');
            } catch (error) {
                console.error('Failed to reset metrics:', error);
            }
        }

        // Event listeners
        document.getElementById('startBtn').addEventListener('click', startLoadTest);
        document.getElementById('stopBtn').addEventListener('click', stopLoadTest);
        document.getElementById('resetBtn').addEventListener('click', resetMetrics);

        // Failure mode toggles
        ['divisionByZero', 'missingKey', 'wrongDataType', 'slowResponse'].forEach(id => {
            document.getElementById(id).addEventListener('change', updateFailureModes);
        });

        // Initialize
        updateMetrics();
        addActivity('ReflexRuntime API Monitor initialized', 'success');
    </script>
</body>
</html>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ReflexRuntime Flask API Demo")
    print("=" * 60)
    print("Starting Flask API with ReflexRuntime...")
    print("Open http://localhost:5000 to access the monitoring dashboard")
    print("The API will automatically heal itself when failures occur!")
    print("=" * 60)
    
    app.run(debug=False, host='0.0.0.0', port=5000) 