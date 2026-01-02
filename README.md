# BrocaOS

BrocaOS is a cognitive architecture designed for building autonomous agents with advanced reasoning, memory, and tool-use capabilities.

## BrocaOS Arhictecture Paper Theory

https://zenodo.org/records/18125645

## Quick Start

### 1. Prerequisites
- Python 3.10+
- An API key for a supported LLM provider (DeepSeek, OpenAI, or Google Gemini)

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/your-repo/BrocaOS.git
cd BrocaOS
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory and add your API keys:
```env
BROCA_LLM_PROVIDER=openai  # or deepseek, gemini
OPENAI_API_KEY=your_key_here
# If using DeepSeek:
# DEEPSEEK_API_KEY=your_key_here
# If using Gemini:
# GEMINI_API_KEY=your_key_here
```

### 4. Running BrocaOS

#### REPL Mode
Interact with BrocaOS directly in your terminal:
```bash
python -m broca.main_repl
```

#### Web API Mode
Start the FastAPI server:
```bash
python -m broca.web_api
```
The API will be available at `http://localhost:8000`.

## Core Features
- **Reasoning Engine**: Multi-step problem solving and planning.
- **Long-term Memory**: Vector-based storage and retrieval of information.
- **Tool Integration**: Built-in support for web search, terminal execution, and file manipulation.
- **Self-Modeling**: Dynamic tracking of system state and capabilities.

## License
This project is licensed under the terms found in the `LICENSE` file.
