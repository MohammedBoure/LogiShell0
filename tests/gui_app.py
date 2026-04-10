import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QLineEdit, QRadioButton,
    QButtonGroup, QTextEdit, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

# Importing the backend logic
from LogiShell0 import Session, GoalNotFoundError, InvalidRuleFormatError
from LogiShell0.exceptions import FileNotFoundError as ESFileNotFoundError

class ExpertSystemGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LogiShell 0 - Expert System Interface")
        self.resize(850, 700)
        
        self.kb_path = None
        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # ==========================================
        # 1. Knowledge Base Section
        # ==========================================
        kb_group = QGroupBox("1. Knowledge Base Configuration")
        kb_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("Load KB File (.json)")
        self.btn_load.clicked.connect(self.load_kb)
        
        self.lbl_kb_path = QLabel("No file loaded.")
        self.lbl_kb_path.setStyleSheet("color: gray;")
        
        kb_layout.addWidget(self.btn_load)
        kb_layout.addWidget(self.lbl_kb_path, stretch=1)
        kb_group.setLayout(kb_layout)
        main_layout.addWidget(kb_group)

        # ==========================================
        # 2. Inference Settings Section
        # ==========================================
        settings_group = QGroupBox("2. Reasoning Parameters")
        settings_layout = QVBoxLayout()

        # Mode Selection
        mode_layout = QHBoxLayout()
        self.radio_forward = QRadioButton("Forward Chaining (Data-Driven)")
        self.radio_backward = QRadioButton("Backward Chaining (Goal-Driven)")
        self.radio_forward.setChecked(True) # Default
        
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_forward)
        self.mode_group.addButton(self.radio_backward)
        
        mode_layout.addWidget(self.radio_forward)
        mode_layout.addWidget(self.radio_backward)
        mode_layout.addStretch()
        settings_layout.addLayout(mode_layout)

        # Input Data
        form_layout = QFormLayout()
        self.input_data = QLineEdit()
        self.input_data.setPlaceholderText("Forward: fact1, fact2 | Backward: single_goal")
        form_layout.addRow("Input Facts/Goal:", self.input_data)
        settings_layout.addLayout(form_layout)

        # Run Button
        self.btn_run = QPushButton("Run Inference Engine")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.setStyleSheet("font-weight: bold;")
        self.btn_run.clicked.connect(self.run_inference)
        settings_layout.addWidget(self.btn_run)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # ==========================================
        # 3. Trace & Output Section
        # ==========================================
        output_group = QGroupBox("3. Execution Trace & Results")
        output_layout = QVBoxLayout()
        
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setStyleSheet("font-family: Consolas, monospace; background-color: #1e1e1e; color: #d4d4d4;")
        
        output_layout.addWidget(self.text_output)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

    # ==========================================
    # Logical Methods
    # ==========================================
    def load_kb(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Knowledge Base", "", "JSON Files (*.json)"
        )
        if file_path:
            self.kb_path = file_path
            self.lbl_kb_path.setText(os.path.basename(file_path))
            self.lbl_kb_path.setStyleSheet("color: blue; font-weight: bold;")
            self.print_to_console(f"SYSTEM: Loaded Knowledge Base -> {self.kb_path}")

    def run_inference(self):
        if not self.kb_path:
            QMessageBox.warning(self, "Error", "Please load a Knowledge Base (.json) first!")
            return

        raw_input = self.input_data.text().strip()
        self.text_output.clear()

        try:
            if self.radio_forward.isChecked():
                self.execute_forward(raw_input)
            else:
                self.execute_backward(raw_input)
                
        except ESFileNotFoundError:
            QMessageBox.critical(self, "Error", "The specified JSON file was not found.")
        except InvalidRuleFormatError as e:
            QMessageBox.critical(self, "KB Error", f"Invalid rule format in JSON:\n{e}")
        except GoalNotFoundError as e:
            self.print_to_console(f"ERROR: {e}")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred:\n{e}")

    def execute_forward(self, raw_input):
        # Parse comma-separated facts
        extra_facts = {fact.strip() for fact in raw_input.split(',')} if raw_input else set()
        
        session = Session(self.kb_path, extra_facts=extra_facts)
        self.print_to_console(f"--- STARTING FORWARD CHAINING ---")
        self.print_to_console(f"Initial Added Facts: {list(extra_facts)}\n")
        
        result = session.run_forward()
        
        # Print Trace
        for entry in result.trace:
            self.print_to_console(str(entry))
            
        self.print_to_console("\n--- CONCLUSION ---")
        self.print_to_console(f"Success: {result.success}")
        self.print_to_console(f"Newly Deduced Facts: {list(result.new_facts)}")
        self.print_to_console(f"Final Working Memory: {list(result.derived_facts)}")

    def execute_backward(self, goal):
        if not goal:
            QMessageBox.warning(self, "Input Error", "Backward chaining requires a specific goal to prove.")
            return

        session = Session(self.kb_path)
        self.print_to_console(f"--- STARTING BACKWARD CHAINING ---")
        self.print_to_console(f"Goal to prove: '{goal}'\n")
        
        result = session.run_backward(goal=goal)
        
        # Print Trace
        for entry in result.trace:
            self.print_to_console(str(entry))
            
        self.print_to_console("\n--- CONCLUSION ---")
        self.print_to_console(f"Goal Proven: {result.success}")

    def print_to_console(self, text):
        self.text_output.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Gives a clean, cross-platform look
    window = ExpertSystemGUI()
    window.show()
    sys.exit(app.exec())