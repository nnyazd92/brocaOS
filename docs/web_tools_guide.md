# Web API Tool Interface Guide

Easy-to-use endpoints for managing reasoning and learning systems through the web API.

## 🎯 Quick Start

### 1. Check Available Tools
```bash
curl http://localhost:8000/api/tools
```

### 2. Add a Priority
```bash
curl -X POST http://localhost:8000/api/priorities \
  -H "Content-Type: application/json" \
  -d '{"name": "web_interface", "description": "Build web interface for tools", "importance": 0.9}'
```

### 3. Check System Status
```bash
curl http://localhost:8000/api/cognitive-architecture/status
```

## 🔧 Tool Endpoints

### Direct Tool Execution
```bash
# Execute any tool with any action
curl -X POST http://localhost:8000/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "reasoning",
    "action": "add_rule",
    "parameters": {
      "rule": {
        "name": "test_rule",
        "conditions": [{"type": "priority", "status": "active"}],
        "actions": [{"type": "add_to_memory", "content": {"type": "test_event"}}]
      }
    }
  }'
```

### Priority Management
- `POST /api/priorities` - Add new priority
- `GET /api/priorities` - List all priorities

### Reasoning System
- `GET /api/reasoning/rules` - List production rules
- `GET /api/reasoning/goals` - List active goals
- `GET /api/cognitive-architecture/status` - Full system status

## 📱 Web UI Examples

### HTML Interface (save as tools.html)
```html
<!DOCTYPE html>
<html>
<head>
    <title>BrocaOS Tool Manager</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .tool { border: 1px solid #ccc; padding: 15px; margin: 10px 0; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>🧠 BrocaOS Cognitive Tools</h1>
    
    <div class="tool">
        <h2>Add Priority</h2>
        <input id="priorityName" placeholder="Priority name">
        <input id="priorityImportance" type="number" min="0" max="1" step="0.1" value="0.5">
        <button onclick="addPriority()">Add Priority</button>
        <div id="priorityResult"></div>
    </div>
    
    <div class="tool">
        <h2>System Status</h2>
        <button onclick="getStatus()">Check Status</button>
        <pre id="statusResult"></pre>
    </div>
    
    <div class="tool">
        <h2>List Priorities</h2>
        <button onclick="listPriorities()">List Priorities</button>
        <pre id="prioritiesResult"></pre>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000/api';
        
        async function addPriority() {
            const name = document.getElementById('priorityName').value;
            const importance = parseFloat(document.getElementById('priorityImportance').value);
            
            const response = await fetch(`${API_BASE}/priorities`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, importance})
            });
            
            const result = await response.json();
            document.getElementById('priorityResult').innerHTML = 
                `<span class="success">✅ Added priority: ${name}</span>`;
        }
        
        async function getStatus() {
            const response = await fetch(`${API_BASE}/cognitive-architecture/status`);
            const result = await response.json();
            document.getElementById('statusResult').innerText = 
                JSON.stringify(result, null, 2);
        }
        
        async function listPriorities() {
            const response = await fetch(`${API_BASE}/priorities`);
            const result = await response.json();
            document.getElementById('prioritiesResult').innerText = 
                JSON.stringify(result, null, 2);
        }
    </script>
</body>
</html>
```

### Python Client
```python
import requests

class BrocaClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def add_priority(self, name, importance=0.5, description=None):
        """Add a priority to reasoning system."""
        data = {"name": name, "importance": importance}
        if description:
            data["description"] = description
        
        response = requests.post(f"{self.base_url}/api/priorities", json=data)
        return response.json()
    
    def list_priorities(self):
        """List all priorities."""
        response = requests.get(f"{self.base_url}/api/priorities")
        return response.json()
    
    def system_status(self):
        """Get cognitive architecture status."""
        response = requests.get(f"{self.base_url}/api/cognitive-architecture/status")
        return response.json()
    
    def execute_tool(self, tool_name, action, **parameters):
        """Execute any tool directly."""
        response = requests.post(f"{self.base_url}/api/tools/execute", json={
            "tool_name": tool_name,
            "action": action,
            "parameters": parameters
        })
        return response.json()

# Usage
client = BrocaClient()
print(client.system_status())
client.add_priority("api_test", 0.7)
print(client.list_priorities())
```

## 🚀 Common Use Cases

### 1. Priority Management Workflow
```python
# Add priority → Check it exists → Monitor system
client.add_priority("bug_fix", 0.8, "Fix critical bug")
priorities = client.list_priorities()
status = client.system_status()
```

### 2. Rule Management
```python
# Add a custom rule
client.execute_tool("reasoning", "add_rule", rule={
    "name": "bug_priority_rule",
    "conditions": [
        {"type": "priority", "name": "bug_fix", "status": "active"}
    ],
    "actions": [
        {"type": "create_goal", "goal": {
            "name": "fix_bug",
            "description": "Fix the critical bug",
            "priority": 0.9
        }}
    ]
})
```

### 3. Learning Integration
```python
# Observe successful pattern
client.execute_tool("learning", "observe_tool_call", 
    tool_call={"type": "priority_management", "action": "add_priority"},
    result={"status": "success", "priority_added": True}
)
```

## 🔍 Monitoring Dashboard

Create a simple monitoring dashboard:

```bash
# Continuous monitoring script
while true; do
    curl -s http://localhost:8000/api/cognitive-architecture/status | \
        jq '.components.reasoning.working_memory_size, .components.reasoning.active_goals_count'
    sleep 5
done
```

## 🛠️ Troubleshooting

### Tool not found?
```bash
# Check registered tools
curl http://localhost:8000/api/tools
```

### Priority not showing?
```bash
# Check reasoning system status
curl http://localhost:8000/api/cognitive-architecture/status
```

### Web API not running?
```bash
# Start the web API
cd /home/wizard/Documents/Code/BrocaOS
python3 -m broca.web_api
```

## 📈 Next Steps

1. **Build React/Vue dashboard** - Full visual interface
2. **Add real-time WebSocket updates** - Live system monitoring
3. **Create command palette** - Quick tool access
4. **Add automation scripts** - Common workflows

## 🎉 You're Ready!

The tools are now accessible through a clean web API. No more Python API wrangling!
