# How to Run the DRI Digital Twin Project

This guide explains how to start the Streamlit web dashboard and run project simulations directly from your terminal.

---

## 🚀 Quick Start (One-Liner)

Open your terminal, navigate to this project directory, and run:

```bash
cd project && ./venv/bin/streamlit run app.py
```

Once started, open your browser and navigate to:
👉 **[http://localhost:8501](http://localhost:8501)**

To stop the server at any time, press `Ctrl + C` in the terminal.

---

## 🛠️ Step-by-Step Instructions

### Option A: Direct Execution (Recommended)
You do not need to activate the virtual environment if you call the binary directly:

```bash
cd project
./venv/bin/streamlit run app.py
```

### Option B: Using `venv` Activation
If you prefer activating the Python environment in your shell:

```bash
cd project
source venv/bin/activate
streamlit run app.py
```

To deactivate the virtual environment when you are done:
```bash
deactivate
```

---

## 🧪 Other Useful Commands

All commands below should be executed from the `project/` directory:

| Task | Command | Description |
| :--- | :--- | :--- |
| **Run Tests** | `./venv/bin/python -m pytest tests/ -q` | Runs all 67 test suites |
| **Validate Against Literature** | `./venv/bin/python src/validation/literature_check.py` | Compares model outputs against published literature bands |
| **Run Plant Model Solver** | `./venv/bin/python src/models/plant.py` | Solves coal rate and prints energy/mass balance closure |
| **Regenerate Derived Data** | `./venv/bin/python setup_data.py` | Updates provenance CSVs and validation report |

---

## ❓ Troubleshooting

### 1. Port 8501 is already in use
If another instance is already running on port 8501:
```bash
# Find and terminate process running on port 8501
lsof -ti :8501 | xargs kill -9
```

### 2. Python environment issues
If the virtual environment is broken or moved:
```bash
cd project
python3.14 -m venv venv
./venv/bin/pip install -r requirements.txt
```
