# LogiShell 0 - Expert System Shell

**LogiShell 0** is a professional, generic Expert System Shell based on **Propositional Logic (Order 0)**. It features a robust inference engine capable of both **Forward and Backward Chaining**, complete with an advanced dynamic graphical user interface (GUI) built with PySide6.

This project was developed as part of the Artificial Intelligence (AI) module practical work (TP).

---

## ✨ Features

*   **Generic Knowledge Base (KB):** Rules and facts are not hardcoded. The system dynamically loads Horn clauses from standard `.json` files.
*   **Forward Chaining (Data-Driven):** Implements an irrevocable and monotonic inference regime to deduce all possible facts from an initial state.
*   **Backward Chaining (Goal-Driven):** Uses Depth-First Search (DFS) with backtracking to prove specific goals based on the loaded rules.
*   **Smart Conflict Resolution:** When multiple rules are applicable, the engine strictly prioritizes the most specific rule (highest number of premises). In case of a tie, it selects the rule with the smallest/lowest ID.
*   **Detailed Execution Trace:** Generates step-by-step reasoning logs (evaluations, conflict resolutions, derived facts, and backtracking) for academic and debugging purposes.
*   **Advanced GUI:** Features a dark-themed, tabbed interface that dynamically generates input fields (checkboxes and dropdowns) based on the loaded JSON file.

---

## 📁 Project Structure

```text
LogiShell0/
├── LogiShell0/                 # Core Backend Library
│   ├── __init__.py             # Package initialization
│   ├── exceptions.py           # Custom exception handling
│   ├── inference_engine.py     # Forward & Backward chaining algorithms
│   ├── knowledge_base.py       # JSON parsing and validation
│   ├── models.py               # Data structures (Rule, TraceEntry, Result)
│   └── session.py              # Session manager linking KB and Engine
├── tests/                      # Execution and Testing Environment
│   ├── animal_kb.json          # Demo KB 1: Animal Classification
│   ├── pc_troubleshooting.json # Demo KB 2: PC Hardware Diagnostics
│   ├── example_usage.py        # CLI script demonstrating backend features
│   └── gui_app.py              # Advanced PySide6 Graphical Interface
└── README.md                   # Project documentation
```

---

## 🚀 Installation & Setup

1.  **Clone or Extract the Project:**
    Ensure all files are organized as shown in the directory structure above.

2.  **Set up a Virtual Environment (Recommended):**

    ```bash
    python -m venv venv
    # Activate the virtual environment
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install Requirements:**
    The backend relies only on standard Python libraries. However, the GUI requires PySide6.

    ```bash
    pip install PySide6
    ```

---

## 🖥️ Usage Guide

### 1. Running the Advanced GUI

The most interactive way to test the shell is via the graphical interface.

Navigate to the `tests` directory and run:

```bash
python tests/gui_app.py
```

*   **Step 1:** Click "Load Knowledge Base" and select either `animal_kb.json` or `pc_troubleshooting.json`.
*   **Step 2:** Use the "Forward Chaining" tab to select initial facts and watch the system deduce conclusions.
*   **Step 3:** Use the "Backward Chaining" tab to select a specific goal and watch the system attempt to prove it via backtracking.

### 2. Running the CLI Demo

To see a programmatic demonstration of the library, conflict resolution, and error handling straight in the terminal:

```bash
python tests/example_usage.py
```

---

## 🧠 Knowledge Base Format

LogiShell 0 uses a strict JSON schema for defining Knowledge Bases. Rules must be defined as Horn Clauses (a list of premises and a single conclusion).

**Example (`test_kb.json`):**

```json
{
    "_comment": "Optional description of the KB",
    "facts": [
        "A",
        "B"
    ],
    "rules": [
        {
            "id": "R1",
            "description": "If A and B are true, deduce C",
            "premises": ["A", "B"],
            "conclusion": "C"
        }
    ]
}
```

*   `facts`: A list of strings representing absolutely true initial states. Leave empty `[]` if relying entirely on user inputs (e.g., in diagnostics).
*   `premises`: The conditions that must be met.
*   `conclusion`: The newly deduced fact if the rule fires.

---

## ⚙️ Conflict Resolution Strategy

As per the academic requirements, the inference engine implements a strict conflict resolution protocol during both Forward and Backward chaining:

1.  **Specificity:** The engine counts the number of premises in each applicable rule. The rule with the highest count fires first.
2.  **Index Priority:** If two rules have the same number of premises, the engine parses the `id` (e.g., R5 vs R12) and prioritizes the smaller index.

---

*Developed for the Artificial Intelligence Module (2025-2026) Université Mohammed Seddik Ben Yahia - Jijel*