"""
Resume Generator GUI v3.0 - Complete Integration
INCLUDES ALL ORIGINAL FUNCTIONALITY PLUS:
- Visual drag-and-drop layout editor
- Flexible section positioning (single, side-by-side, multi-column)
- Width and column controls
- Layout template management
- All original tabs (Job Input, Pipeline, Layout, Generate, Console)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import threading
import sys
import re
from io import StringIO
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Import orchestrator
try:
    from orchestrator import ResumeOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    print("Warning: orchestrator.py not found - demo mode only")


class VisualLayoutEditor(tk.Toplevel):
    """Visual editor for complex layout configurations"""
    
    def __init__(self, parent, initial_config=None):
        super().__init__(parent)
        self.title("Visual Layout Editor")
        self.geometry("1100x750")
        self.parent = parent
        
        # Current layout configuration
        self.layout_rows = []
        self.available_sections = [
            'professional_summary',
            'technical_expertise',
            'experience',
            'bulleted_projects',
            'education',
            'publications',
            'work_samples'
        ]
        
        self.section_display_names = {
            'professional_summary': 'Professional Summary',
            'technical_expertise': 'Technical Expertise',
            'experience': 'Experience',
            'bulleted_projects': 'Projects',
            'education': 'Education',
            'publications': 'Publications',
            'work_samples': 'Work Samples'
        }
        
        # Load initial config if provided
        if initial_config and 'layout' in initial_config and 'rows' in initial_config['layout']:
            self.layout_rows = initial_config['layout']['rows']
        else:
            self.initialize_default_layout()
        
        self._create_ui()
        self.refresh_layout_display()
    
    def initialize_default_layout(self):
        """Initialize with default layout"""
        self.layout_rows = [
            {
                'type': 'single',
                'sections': ['professional_summary'],
                'widths': ['100%'],
                'column_gap': '20px',
                'allow_page_break': False
            },
            {
                'type': 'single',
                'sections': ['technical_expertise'],
                'widths': ['100%'],
                'column_gap': '20px',
                'allow_page_break': False
            },
            {
                'type': 'single',
                'sections': ['experience'],
                'widths': ['100%'],
                'column_gap': '20px',
                'allow_page_break': True
            },
            {
                'type': 'single',
                'sections': ['bulleted_projects'],
                'widths': ['100%'],
                'column_gap': '20px',
                'allow_page_break': True
            },
            {
                'type': 'side_by_side',
                'sections': ['education', 'publications'],
                'widths': ['50%', '50%'],
                'column_gap': '20px',
                'allow_page_break': False
            }
        ]
    
    def _create_ui(self):
        """Create the UI layout"""
        # Main container with paned window
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Layout builder
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=2)
        
        # Right panel - Properties & presets
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)
        
        self._create_left_panel(left_frame)
        self._create_right_panel(right_frame)
        
        # Bottom button bar
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Apply & Close", command=self.apply_and_close, style="Success.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Preview Config", command=self.preview_config).pack(side=tk.LEFT, padx=5)
    
    def _create_left_panel(self, parent):
        """Create layout builder panel"""
        ttk.Label(parent, text="Layout Builder", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="➕ Add Row", command=self.add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Reset", command=self.reset_layout).pack(side=tk.LEFT, padx=2)
        
        # Scrollable layout display
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.layout_container = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=self.layout_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.layout_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.layout_canvas = canvas
    
    def _create_right_panel(self, parent):
        """Create properties and presets panel"""
        # Quick presets
        presets_frame = ttk.LabelFrame(parent, text="Quick Presets", padding=10)
        presets_frame.pack(fill=tk.X, pady=(0, 10))
        
        presets = [
            ("Standard", "Standard 2-page layout"),
            ("Compact", "Dense 1-page layout"),
            ("Two-Column", "Skills-heavy side-by-side"),
            ("Academic", "Research-focused layout")
        ]
        
        for name, description in presets:
            btn_frame = ttk.Frame(presets_frame)
            btn_frame.pack(fill=tk.X, pady=2)
            ttk.Button(btn_frame, text=name, command=lambda n=name: self.apply_preset(n), width=12).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Label(btn_frame, text=description, font=("Helvetica", 8), foreground="#64748b").pack(side=tk.LEFT)
        
        # Section options
        options_frame = ttk.LabelFrame(parent, text="Section Options", padding=10)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Column configuration
        ttk.Label(options_frame, text="Technical Skills Columns:", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.tech_columns_var = tk.IntVar(value=2)
        col_frame = ttk.Frame(options_frame)
        col_frame.pack(fill=tk.X, pady=(0, 10))
        for i in range(1, 5):
            ttk.Radiobutton(col_frame, text=str(i), variable=self.tech_columns_var, value=i).pack(side=tk.LEFT, padx=5)
        
        # Summary style
        ttk.Label(options_frame, text="Summary Style:", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.summary_style_var = tk.StringVar(value="paragraph")
        summary_frame = ttk.Frame(options_frame)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Radiobutton(summary_frame, text="Paragraph", variable=self.summary_style_var, value="paragraph").pack(anchor="w")
        ttk.Radiobutton(summary_frame, text="Bullets", variable=self.summary_style_var, value="bullets").pack(anchor="w")
        
        # Spacing mode
        ttk.Label(options_frame, text="Spacing:", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.compact_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Compact mode (reduce spacing)", variable=self.compact_mode_var).pack(anchor="w")
        
        # Center align skills
        ttk.Label(options_frame, text="Skills Display:", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(10, 5))
        self.center_skills_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Center-align skills", variable=self.center_skills_var).pack(anchor="w")
    
    def refresh_layout_display(self):
        """Refresh the visual layout display"""
        for widget in self.layout_container.winfo_children():
            widget.destroy()
        
        for idx, row in enumerate(self.layout_rows):
            self._draw_row(idx, row)
    
    def _draw_row(self, idx, row):
        """Draw a single row in the layout"""
        row_frame = ttk.Frame(self.layout_container, relief=tk.GROOVE, borderwidth=2)
        row_frame.pack(fill=tk.X, pady=5, padx=5)
        
        header = ttk.Frame(row_frame)
        header.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header, text=f"Row {idx + 1}", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        
        controls = ttk.Frame(header)
        controls.pack(side=tk.RIGHT)
        
        ttk.Button(controls, text="↑", command=lambda: self.move_row(idx, -1), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(controls, text="↓", command=lambda: self.move_row(idx, 1), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(controls, text="✎", command=lambda: self.edit_row(idx), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(controls, text="×", command=lambda: self.delete_row(idx), width=3).pack(side=tk.LEFT, padx=1)
        
        content = ttk.Frame(row_frame)
        content.pack(fill=tk.X, padx=5, pady=5)
        
        sections_frame = ttk.Frame(content)
        sections_frame.pack(fill=tk.X)
        
        for i, section in enumerate(row['sections']):
            width = row.get('widths', [])[i] if i < len(row.get('widths', [])) else '100%'
            
            section_box = ttk.Frame(sections_frame, relief=tk.RAISED, borderwidth=1)
            section_box.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.BOTH, expand=True)
            
            ttk.Label(section_box, text=self.section_display_names.get(section, section), 
                     font=("Helvetica", 8, "bold"), foreground="#0ea5e9").pack(pady=5)
            ttk.Label(section_box, text=f"Width: {width}", 
                     font=("Helvetica", 7), foreground="#64748b").pack(pady=2)
        
        props_text = f"Type: {row['type']} | Gap: {row.get('column_gap', '20px')} | Break: {row.get('allow_page_break', True)}"
        ttk.Label(content, text=props_text, font=("Helvetica", 7), foreground="#64748b").pack(anchor="w", pady=(5, 0))
    
    def add_row(self):
        dialog = RowEditorDialog(self, None)
        self.wait_window(dialog)
        if dialog.result:
            self.layout_rows.append(dialog.result)
            self.refresh_layout_display()
    
    def edit_row(self, idx):
        dialog = RowEditorDialog(self, self.layout_rows[idx])
        self.wait_window(dialog)
        if dialog.result:
            self.layout_rows[idx] = dialog.result
            self.refresh_layout_display()
    
    def delete_row(self, idx):
        if messagebox.askyesno("Confirm Delete", f"Delete Row {idx + 1}?"):
            del self.layout_rows[idx]
            self.refresh_layout_display()
    
    def move_row(self, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(self.layout_rows):
            self.layout_rows[idx], self.layout_rows[new_idx] = self.layout_rows[new_idx], self.layout_rows[idx]
            self.refresh_layout_display()
    
    def reset_layout(self):
        if messagebox.askyesno("Reset Layout", "Reset to default layout? This cannot be undone."):
            self.initialize_default_layout()
            self.refresh_layout_display()
    
    def apply_preset(self, preset_name):
        if preset_name == "Standard":
            self.initialize_default_layout()
        elif preset_name == "Compact":
            self.layout_rows = [
                {'type': 'single', 'sections': ['professional_summary'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'side_by_side', 'sections': ['technical_expertise', 'education'], 'widths': ['65%', '35%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'single', 'sections': ['experience'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True},
                {'type': 'single', 'sections': ['bulleted_projects'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True}
            ]
            self.compact_mode_var.set(True)
        elif preset_name == "Two-Column":
            self.layout_rows = [
                {'type': 'single', 'sections': ['professional_summary'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'side_by_side', 'sections': ['technical_expertise', 'experience'], 'widths': ['40%', '60%'], 'column_gap': '20px', 'allow_page_break': True},
                {'type': 'side_by_side', 'sections': ['bulleted_projects', 'education'], 'widths': ['60%', '40%'], 'column_gap': '20px', 'allow_page_break': True}
            ]
            self.tech_columns_var.set(1)
        elif preset_name == "Academic":
            self.layout_rows = [
                {'type': 'single', 'sections': ['professional_summary'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'side_by_side', 'sections': ['education', 'publications'], 'widths': ['50%', '50%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'single', 'sections': ['technical_expertise'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'single', 'sections': ['experience'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True},
                {'type': 'single', 'sections': ['bulleted_projects'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True}
            ]
        
        self.refresh_layout_display()
    
    def preview_config(self):
        config = self.get_config()
        
        preview = tk.Toplevel(self)
        preview.title("Preview Configuration")
        preview.geometry("600x500")
        
        text = scrolledtext.ScrolledText(preview, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", json.dumps(config, indent=2))
        text.config(state=tk.DISABLED)
        
        ttk.Button(preview, text="Close", command=preview.destroy).pack(pady=10)
    
    def get_config(self):
        return {
            'layout': {
                'rows': self.layout_rows,
                'auto_layout': False
            },
            'sections': {
                'technical_expertise': {
                    'columns': self.tech_columns_var.get(),
                    'center_align': self.center_skills_var.get()
                },
                'professional_summary': {
                    'style': self.summary_style_var.get()
                }
            },
            'spacing': {
                'compact_mode': self.compact_mode_var.get()
            }
        }
    
    def apply_and_close(self):
        self.result = self.get_config()
        self.destroy()


class RowEditorDialog(tk.Toplevel):
    """Dialog for editing a single row"""
    
    def __init__(self, parent, initial_row=None):
        super().__init__(parent)
        self.title("Edit Row")
        self.geometry("500x400")
        self.parent = parent
        self.result = None
        
        self.available_sections = parent.available_sections
        self.section_display_names = parent.section_display_names
        
        if initial_row:
            self.row_type = tk.StringVar(value=initial_row['type'])
            self.selected_sections = initial_row['sections'].copy()
            self.widths = initial_row.get('widths', ['100%'] * len(initial_row['sections'])).copy()
            self.column_gap = tk.StringVar(value=initial_row.get('column_gap', '20px'))
            self.allow_page_break = tk.BooleanVar(value=initial_row.get('allow_page_break', True))
        else:
            self.row_type = tk.StringVar(value='single')
            self.selected_sections = []
            self.widths = []
            self.column_gap = tk.StringVar(value='20px')
            self.allow_page_break = tk.BooleanVar(value=True)
        
        self._create_ui()
        self.update_section_list()
    
    def _create_ui(self):
        # Row type
        type_frame = ttk.LabelFrame(self, text="Row Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Radiobutton(type_frame, text="Single (full width)", variable=self.row_type, 
                       value='single', command=self.update_section_list).pack(anchor="w")
        ttk.Radiobutton(type_frame, text="Side by Side (2 sections)", variable=self.row_type, 
                       value='side_by_side', command=self.update_section_list).pack(anchor="w")
        ttk.Radiobutton(type_frame, text="Multi-Column (2+ sections)", variable=self.row_type, 
                       value='multi_column', command=self.update_section_list).pack(anchor="w")
        
        # Section selection
        sections_frame = ttk.LabelFrame(self, text="Sections", padding=10)
        sections_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.sections_listbox = tk.Listbox(sections_frame, selectmode=tk.MULTIPLE, height=8)
        self.sections_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Options
        options_frame = ttk.LabelFrame(self, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(options_frame, text="Column Gap:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(options_frame, textvariable=self.column_gap, width=10).grid(row=0, column=1, sticky="w", pady=2)
        
        ttk.Checkbutton(options_frame, text="Allow page break", variable=self.allow_page_break).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
    
    def update_section_list(self):
        self.sections_listbox.delete(0, tk.END)
        
        for section in self.available_sections:
            display_name = self.section_display_names.get(section, section)
            self.sections_listbox.insert(tk.END, display_name)
            
            if section in self.selected_sections:
                idx = self.available_sections.index(section)
                self.sections_listbox.selection_set(idx)
    
    def ok(self):
        selected_indices = self.sections_listbox.curselection()
        selected = [self.available_sections[i] for i in selected_indices]
        
        if not selected:
            messagebox.showwarning("No Sections", "Please select at least one section")
            return
        
        row_type = self.row_type.get()
        if row_type == 'single' and len(selected) > 1:
            messagebox.showwarning("Too Many Sections", "Single row type can only have one section")
            return
        
        if row_type == 'side_by_side' and len(selected) != 2:
            messagebox.showwarning("Invalid Count", "Side by side requires exactly 2 sections")
            return
        
        # Generate widths
        if row_type == 'single':
            widths = ['100%']
        elif row_type == 'side_by_side':
            widths = ['50%', '50%']
        else:
            equal_width = f"{100 // len(selected)}%"
            widths = [equal_width] * len(selected)
        
        self.result = {
            'type': row_type,
            'sections': selected,
            'widths': widths,
            'column_gap': self.column_gap.get(),
            'allow_page_break': self.allow_page_break.get()
        }
        
        self.destroy()
    
    def cancel(self):
        self.result = None
        self.destroy()


class ResumeGeneratorGUI(tk.Tk):
    """Enhanced GUI for resume generation with multi-agent pipeline"""
    
    def __init__(self):
        super().__init__()
        self.title("AI Resume Generator - Multi-Agent Pipeline v3.0")
        self.geometry("800x850")
        
        # Instance variables
        self.job_folder = None
        self.orchestrator = None
        self.current_resume_json = None
        self.json_edited = False
        self.current_layout_config = None
        
        # Model presets
        self.model_presets = {
            "Fast": "claude-3-5-haiku-20241022",
            "Balanced": "claude-sonnet-4-5-20250929",
            "Quality": "claude-opus-4-20250514"
        }
        
        # Style configuration
        self._configure_styles()
        
        # Create main UI
        self.notebook = ttk.Notebook(self)
        
        # Create tabs
        self.tab_job_input = ttk.Frame(self.notebook, padding=15)
        self.tab_pipeline = ttk.Frame(self.notebook, padding=15)
        self.tab_layout = ttk.Frame(self.notebook, padding=15)
        self.tab_generate = ttk.Frame(self.notebook, padding=15)
        self.tab_console = ttk.Frame(self.notebook, padding=15)
        
        self.notebook.add(self.tab_job_input, text="1. Job Description")
        self.notebook.add(self.tab_pipeline, text="2. Run Pipeline")
        self.notebook.add(self.tab_layout, text="3. Customize Layout")
        self.notebook.add(self.tab_generate, text="4. Generate PDF")
        self.notebook.add(self.tab_console, text="Console")
        
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Build each tab
        self._create_job_input_tab()
        self._create_pipeline_tab()
        self._create_layout_tab()
        self._create_generate_tab()
        self._create_console_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Initialize orchestrator if available
        if ORCHESTRATOR_AVAILABLE:
            try:
                self.orchestrator = ResumeOrchestrator()
                self.status_var.set("✓ Multi-agent pipeline ready")
                self._log_console("✓ Multi-agent pipeline initialized", "success")
            except Exception as e:
                self.status_var.set(f"Warning: {str(e)}")
                self._log_console(f"⚠ Warning: {str(e)}", "warning")
    
    def _configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style(self)
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"), foreground="#0f172a")
        style.configure("Subheader.TLabel", font=("Helvetica", 11, "bold"), foreground="#334155")
        style.configure("Info.TLabel", font=("Helvetica", 9), foreground="#64748b")
        
        # Fixed button styles
        style.configure("Success.TButton", background="#10b981", foreground="#0f172a")
        style.configure("Primary.TButton", background="#0ea5e9", foreground="#0f172a")
        style.configure("Warning.TButton", background="#f59e0b", foreground="#0f172a")
        
        style.map("Success.TButton",
                  foreground=[('active', '#ffffff'), ('disabled', '#9ca3af')])
        style.map("Primary.TButton",
                  foreground=[('active', '#ffffff'), ('disabled', '#9ca3af')])
        style.map("Warning.TButton",
                  foreground=[('active', '#ffffff'), ('disabled', '#9ca3af')])
    
    # ========================================================================
    # CONSOLE TAB
    # ========================================================================
    
    def _create_console_tab(self):
        """Create console tab for master progress logging"""
        parent = self.tab_console
        
        ttk.Label(parent, text="System Console", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(parent, text="View all system output and agent progress", style="Info.TLabel").pack(anchor="w", pady=(0, 15))
        
        console_frame = ttk.Frame(parent)
        console_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(console_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.console_text = tk.Text(
            console_frame,
            wrap="word",
            font=("Courier", 9),
            background="#1e1e1e",
            foreground="#d4d4d4",
            yscrollcommand=scrollbar.set
        )
        self.console_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.console_text.yview)
        
        self.console_text.tag_config("success", foreground="#10b981")
        self.console_text.tag_config("error", foreground="#ef4444")
        self.console_text.tag_config("warning", foreground="#f59e0b")
        self.console_text.tag_config("info", foreground="#3b82f6")
        self.console_text.tag_config("dim", foreground="#6b7280")
        
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Clear Console", command=self._clear_console).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Log", command=self._save_console_log).pack(side="left", padx=5)
    
    def _log_console(self, message, tag=None):
        """Log message to console tab"""
        def update():
            self.console_text.insert(tk.END, message + "\n", tag)
            self.console_text.see(tk.END)
        self.after(0, update)
    
    def _clear_console(self):
        """Clear console output"""
        self.console_text.delete("1.0", tk.END)
        self._log_console(f"Console cleared at {datetime.now().strftime('%H:%M:%S')}", "dim")
    
    def _save_console_log(self):
        """Save console log to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.console_text.get("1.0", tk.END))
            messagebox.showinfo("Saved", f"Console log saved to:\n{filename}")
    
    # ========================================================================
    # TAB 1: JOB DESCRIPTION INPUT (ENHANCED)
    # ========================================================================
    
    def _create_job_input_tab(self):
        """Create enhanced job description input interface"""
        parent = self.tab_job_input
        
        ttk.Label(parent, text="Job Description Input", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Input method selection (simplified)
        input_frame = ttk.LabelFrame(parent, text="Input Method", padding=10)
        input_frame.pack(fill="x", pady=(0, 15))
        
        self.input_method = tk.StringVar(value="url_or_text")
        self.input_method.trace_add('write', lambda *args: self._update_input_visibility())
        
        ttk.Radiobutton(input_frame, text="URL or Text (auto-detect)", variable=self.input_method, value="url_or_text").pack(anchor="w")
        ttk.Radiobutton(input_frame, text="Text File", variable=self.input_method, value="file").pack(anchor="w")
        ttk.Radiobutton(input_frame, text="Load Existing Folder", variable=self.input_method, value="folder").pack(anchor="w")
        
        # URL or Text input (merged)
        self.url_text_frame = ttk.Frame(parent)
        self.url_text_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ttk.Label(self.url_text_frame, text="Job Description URL or Text:").pack(anchor="w")
        ttk.Label(self.url_text_frame, text="Paste a URL or the full job description text", 
                 style="Info.TLabel").pack(anchor="w", pady=(0, 5))
        self.jd_url_text = scrolledtext.ScrolledText(self.url_text_frame, height=6, wrap="word")
        self.jd_url_text.pack(fill="both", expand=True, pady=5)
        
        # File input
        self.file_frame = ttk.Frame(parent)
        self.file_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(self.file_frame, text="Job Description File:").pack(anchor="w")
        file_input_frame = ttk.Frame(self.file_frame)
        file_input_frame.pack(fill="x", pady=5)
        self.jd_file_var = tk.StringVar()
        ttk.Entry(file_input_frame, textvariable=self.jd_file_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(file_input_frame, text="Browse...", command=self._browse_jd_file).pack(side="left", padx=(5, 0))
        
        # Folder input
        self.folder_frame = ttk.Frame(parent)
        self.folder_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(self.folder_frame, text="Existing Job Folder:").pack(anchor="w")
        folder_input_frame = ttk.Frame(self.folder_frame)
        folder_input_frame.pack(fill="x", pady=5)
        self.job_folder_var = tk.StringVar()
        ttk.Entry(folder_input_frame, textvariable=self.job_folder_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_input_frame, text="Browse...", command=self._browse_job_folder).pack(side="left", padx=(5, 0))
        
        # Company info with AI extraction
        company_frame = ttk.LabelFrame(parent, text="Company Information", padding=10)
        company_frame.pack(fill="x", pady=(0, 15))
        
        # Extract button
        extract_frame = ttk.Frame(company_frame)
        extract_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(extract_frame, text="🤖 Extract Company & Job Info", 
                  command=self._extract_company_info, style="Warning.TButton").pack(side="left")
        ttk.Label(extract_frame, text="(Uses AI to extract from job description)", 
                 style="Info.TLabel").pack(side="left", padx=(10, 0))
        
        ttk.Label(company_frame, text="Company Name:").pack(anchor="w")
        self.company_name_var = tk.StringVar()
        ttk.Entry(company_frame, textvariable=self.company_name_var, width=50).pack(fill="x", pady=(2, 8))
        
        ttk.Label(company_frame, text="Job Title:").pack(anchor="w")
        self.job_title_var = tk.StringVar()
        ttk.Entry(company_frame, textvariable=self.job_title_var, width=50).pack(fill="x", pady=(2, 8))
        
        ttk.Label(company_frame, text="Company Website URL (optional):").pack(anchor="w")
        self.company_url_var = tk.StringVar()
        ttk.Entry(company_frame, textvariable=self.company_url_var, width=50).pack(fill="x", pady=(2, 8))
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Clear All", command=self._clear_job_input).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Next: Run Pipeline →", command=self._proceed_to_pipeline, 
                  style="Primary.TButton").pack(side="right", padx=5)
        
        self._update_input_visibility()
    
    def _update_input_visibility(self):
        """Show/hide input fields based on selected method"""
        method = self.input_method.get()
        
        self.url_text_frame.pack_forget()
        self.file_frame.pack_forget()
        self.folder_frame.pack_forget()
        
        radio_frame = self.tab_job_input.winfo_children()[1]
        
        if method == "url_or_text":
            self.url_text_frame.pack(fill="both", expand=True, pady=(0, 10), after=radio_frame)
        elif method == "file":
            self.file_frame.pack(fill="x", pady=(0, 10), after=radio_frame)
        elif method == "folder":
            self.folder_frame.pack(fill="x", pady=(0, 10), after=radio_frame)
    
    def _is_url(self, text):
        """Check if text is a URL"""
        text = text.strip()
        return bool(re.match(r'https?://', text, re.IGNORECASE)) or urlparse(text).scheme in ['http', 'https']
    
    def _extract_company_info(self):
        """Use AI to extract company name and job title from job description"""
        if not ORCHESTRATOR_AVAILABLE:
            messagebox.showwarning("Not Available", "Orchestrator required for AI extraction")
            return
        
        method = self.input_method.get()
        jd_text = ""
        
        if method == "url_or_text":
            jd_text = self.jd_url_text.get("1.0", tk.END).strip()
            if not jd_text:
                messagebox.showwarning("No Input", "Please enter a job description first")
                return
        elif method == "file":
            file_path = self.jd_file_var.get()
            if not file_path:
                messagebox.showwarning("No File", "Please select a file first")
                return
            with open(file_path, 'r', encoding='utf-8') as f:
                jd_text = f.read()
        else:
            messagebox.showinfo("Not Needed", "Extraction only works with job description text or URL")
            return
        
        self._log_console("🤖 Extracting company and job info...", "info")
        self.status_var.set("Extracting info...")
        
        def extract_thread():
            try:
                # Use orchestrator's extract method (we'll need to add this)
                info = self.orchestrator.extract_company_job_info(jd_text)
                
                def update_fields():
                    self.company_name_var.set(info.get('company', ''))
                    self.job_title_var.set(info.get('job_title', ''))
                    if info.get('company_url'):
                        self.company_url_var.set(info['company_url'])
                    
                    self.status_var.set("✓ Info extracted")
                    self._log_console(f"✓ Extracted: {info.get('company')} - {info.get('job_title')}", "success")
                    messagebox.showinfo("Success", f"Extracted:\nCompany: {info.get('company')}\nTitle: {info.get('job_title')}\n\nYou can edit these fields before proceeding.")
                
                self.after(0, update_fields)
                
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Extraction Failed", f"Could not extract info:\n{str(e)}"))
                self.after(0, lambda: self.status_var.set("Extraction failed"))
                self._log_console(f"✗ Extraction failed: {str(e)}", "error")
        
        thread = threading.Thread(target=extract_thread, daemon=True)
        thread.start()
    
    def _browse_jd_file(self):
        """Browse for job description file"""
        filename = filedialog.askopenfilename(
            title="Select Job Description File",
            filetypes=[("Text files", "*.txt *.md"), ("All files", "*.*")]
        )
        if filename:
            self.jd_file_var.set(filename)
            self._log_console(f"Selected file: {filename}", "info")
    
    def _browse_job_folder(self):
        """Browse for existing job folder"""
        folder = filedialog.askdirectory(title="Select Existing Job Folder")
        if folder:
            self.job_folder_var.set(folder)
            self.job_folder = folder
            self._log_console(f"Selected folder: {folder}", "info")
            # Try to load existing resume JSON
            self._load_resume_json()
    
    def _clear_job_input(self):
        """Clear all job input fields"""
        self.jd_url_text.delete("1.0", tk.END)
        self.jd_file_var.set("")
        self.job_folder_var.set("")
        self.company_name_var.set("")
        self.job_title_var.set("")
        self.company_url_var.set("")
        self._log_console("Cleared all input fields", "dim")
    
    def _proceed_to_pipeline(self):
        """Validate input and move to pipeline tab"""
        method = self.input_method.get()
        
        if method == "url_or_text":
            text = self.jd_url_text.get("1.0", tk.END).strip()
            if not text:
                messagebox.showwarning("Missing Input", "Please enter a URL or job description text")
                return
        elif method == "file" and not self.jd_file_var.get().strip():
            messagebox.showwarning("Missing Input", "Please select a job description file")
            return
        elif method == "folder" and not self.job_folder_var.get().strip():
            messagebox.showwarning("Missing Input", "Please select an existing job folder")
            return
        
        self._log_console(f"✓ Input validated - proceeding to pipeline execution", "success")
        self.notebook.select(self.tab_pipeline)
    
    # ========================================================================
    # TAB 2: PIPELINE EXECUTION (WITH MODEL SELECTION)
    # ========================================================================
    
    def _create_pipeline_tab(self):
        """Create pipeline execution interface with model selection"""
        parent = self.tab_pipeline
        
        ttk.Label(parent, text="Multi-Agent Pipeline Execution", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Model selection
        model_frame = ttk.LabelFrame(parent, text="Model Configuration", padding=10)
        model_frame.pack(fill="x", pady=(0, 15))
        
        # Preset selector
        preset_frame = ttk.Frame(model_frame)
        preset_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(preset_frame, text="Preset:").pack(side="left", padx=(0, 10))
        self.model_preset_var = tk.StringVar(value="Balanced")
        for preset in ["Fast", "Balanced", "Quality"]:
            ttk.Radiobutton(preset_frame, text=preset, variable=self.model_preset_var, 
                          value=preset, command=self._apply_model_preset).pack(side="left", padx=5)
        
        ttk.Label(preset_frame, text="  |  Advanced:", style="Info.TLabel").pack(side="left", padx=(20, 5))
        self.show_advanced_models = tk.BooleanVar(value=False)
        ttk.Checkbutton(preset_frame, text="Per-agent selection", 
                       variable=self.show_advanced_models,
                       command=self._toggle_advanced_models).pack(side="left")
        
        # Per-agent model selection (initially hidden)
        self.advanced_model_frame = ttk.Frame(model_frame)
        
        agents = [
            ("Job Analyzer", "job_analyzer_model"),
            ("Content Selector", "content_selector_model"),
            ("Resume Drafter", "resume_drafter_model"),
            ("Fabrication Validator", "fabrication_validator_model"),
            ("Voice & Style Editor", "voice_style_editor_model"),
            ("Final QA", "final_qa_model")
        ]
        
        self.agent_model_vars = {}
        for i, (agent_name, var_name) in enumerate(agents):
            row_frame = ttk.Frame(self.advanced_model_frame)
            row_frame.grid(row=i, column=0, columnspan=2, sticky="ew", pady=2)
            
            ttk.Label(row_frame, text=f"{agent_name}:", width=20).pack(side="left")
            var = tk.StringVar(value="claude-sonnet-4-5-20250929")
            self.agent_model_vars[var_name] = var
            ttk.Combobox(row_frame, textvariable=var, 
                        values=list(self.model_presets.values()),
                        state="readonly", width=40).pack(side="left", padx=5)
        
        # Pipeline options
        options_frame = ttk.LabelFrame(parent, text="Pipeline Options", padding=10)
        options_frame.pack(fill="x", pady=(0, 15))
        
        self.run_phase1 = tk.BooleanVar(value=True)
        self.run_phase2 = tk.BooleanVar(value=True)
        self.run_phase3 = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Phase 1: Job Analysis + Content Selection", variable=self.run_phase1).pack(anchor="w", pady=2)
        ttk.Checkbutton(options_frame, text="Phase 2: Resume Generation + Validation", variable=self.run_phase2).pack(anchor="w", pady=2)
        ttk.Checkbutton(options_frame, text="Phase 3: Style Polish + Final QA", variable=self.run_phase3).pack(anchor="w", pady=2)
        
        ttk.Separator(options_frame, orient="horizontal").pack(fill="x", pady=10)
        
        self.skip_style_editing = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Skip style editing (Agent 5) if draft is already good", 
                       variable=self.skip_style_editing).pack(anchor="w", pady=2)
        
        self.use_parallel_selection = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Use parallel content selection (faster)", 
                       variable=self.use_parallel_selection).pack(anchor="w", pady=2)
        
        # Progress display
        progress_frame = ttk.LabelFrame(parent, text="Pipeline Progress", padding=10)
        progress_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=15, state="disabled", wrap="word")
        self.progress_text.pack(fill="both", expand=True)
        
        ttk.Label(progress_frame, text="💡 Tip: Check the Console tab for detailed agent output", 
                 style="Info.TLabel").pack(anchor="w", pady=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="← Back", command=lambda: self.notebook.select(self.tab_job_input)).pack(side="left", padx=5)
        self.run_button = ttk.Button(button_frame, text="Run Pipeline", command=self._run_pipeline, style="Success.TButton")
        self.run_button.pack(side="right", padx=5)
        ttk.Button(button_frame, text="Skip to Layout →", command=lambda: self.notebook.select(self.tab_layout)).pack(side="right", padx=5)
    
    def _apply_model_preset(self):
        """Apply selected model preset to all agents"""
        preset = self.model_preset_var.get()
        model = self.model_presets[preset]
        for var in self.agent_model_vars.values():
            var.set(model)
        self._log_console(f"Applied {preset} preset: {model}", "info")
    
    def _toggle_advanced_models(self):
        """Show/hide per-agent model selection"""
        if self.show_advanced_models.get():
            self.advanced_model_frame.pack(fill="x", pady=(10, 0))
        else:
            self.advanced_model_frame.pack_forget()
    
    def _run_pipeline(self):
        """Execute the multi-agent pipeline"""
        if not ORCHESTRATOR_AVAILABLE:
            messagebox.showerror("Not Available", "Orchestrator not found. Please deploy orchestrator_enhanced.py")
            return
        
        self.run_button.config(state="disabled", text="Running...")
        self.progress_text.config(state="normal")
        self.progress_text.delete("1.0", tk.END)
        
        self._log_console("\n" + "="*70, "dim")
        self._log_console("PIPELINE EXECUTION STARTED", "info")
        self._log_console("="*70 + "\n", "dim")
        
        thread = threading.Thread(target=self._execute_pipeline_thread, daemon=True)
        thread.start()
    
    def _execute_pipeline_thread(self):
        """Execute pipeline in separate thread with console redirection"""
        try:
            old_stdout = sys.stdout
            
            class TeeOutput:
                def __init__(self, gui_ref):
                    self.gui = gui_ref
                
                def write(self, text):
                    if text.strip():
                        self.gui._log_console(text.rstrip(), "dim")
                        self.gui._log_progress(text.rstrip())
                    old_stdout.write(text)
                
                def flush(self):
                    old_stdout.flush()
            
            sys.stdout = TeeOutput(self)
            
            self._log_progress("Starting multi-agent pipeline...")
            
            method = self.input_method.get()
            jd_input = None
            
            if method == "url_or_text":
                jd_input = self.jd_url_text.get("1.0", tk.END).strip()
                if self._is_url(jd_input):
                    self._log_progress(f"Fetching from URL: {jd_input}")
                else:
                    self._log_progress("Using pasted job description text")
            elif method == "file":
                with open(self.jd_file_var.get(), 'r', encoding='utf-8') as f:
                    jd_input = f.read()
                self._log_progress(f"Loaded from file: {self.jd_file_var.get()}")
            elif method == "folder":
                self.job_folder = self.job_folder_var.get()
                self._log_progress(f"Resuming from folder: {self.job_folder}")
            
            if method == "folder":
                if self.run_phase2.get():
                    self._log_progress("\n=== Phase 2: Resume Generation ===")
                    self.orchestrator.run_phase2(job_folder=self.job_folder)
                    self._log_progress("✓ Phase 2 complete")
                
                if self.run_phase3.get():
                    self._log_progress("\n=== Phase 3: Polish & QA ===")
                    self.orchestrator.run_phase3(
                        job_folder=self.job_folder,
                        skip_style_editing=self.skip_style_editing.get()
                    )
                    self._log_progress("✓ Phase 3 complete")
            else:
                results = self.orchestrator.generate_resume(
                    jd_input=jd_input,
                    company_name=self.company_name_var.get().strip() or None,
                    job_title=self.job_title_var.get().strip() or None,
                    company_url=self.company_url_var.get().strip() or None,
                    skip_style_editing=self.skip_style_editing.get()
                )
                
                self.job_folder = results['folder_path']
                self._log_progress(f"\n✓ Pipeline complete!")
                self._log_progress(f"Results saved to: {self.job_folder}")
            
            self._load_resume_json()
            
            self._log_progress("\n✓ Ready for layout customization")
            self._log_console("✓ PIPELINE COMPLETED SUCCESSFULLY", "success")
            
            sys.stdout = old_stdout
            
            self.after(100, lambda: self.run_button.config(state="normal", text="Run Pipeline"))
            self.after(100, lambda: messagebox.showinfo("Success", "Pipeline completed successfully!\n\nProceed to Layout tab to customize."))
            
        except Exception as e:
            sys.stdout = old_stdout
            error_msg = str(e)  # ← ADD THIS LINE
            
            self._log_progress(f"\n✗ Error: {error_msg}")  # ← CHANGE str(e) to error_msg
            self._log_console(f"✗ PIPELINE ERROR: {error_msg}", "error")  # ← CHANGE str(e) to error_msg
            self.after(100, lambda: self.run_button.config(state="normal", text="Run Pipeline"))
            self.after(100, lambda: messagebox.showerror("Pipeline Error", f"An error occurred:\n\n{error_msg}"))  # ← CHANGE str(e) to error_msg

    def _log_progress(self, message):
        """Log message to progress text widget"""
        def update():
            self.progress_text.config(state="normal")
            self.progress_text.insert(tk.END, message + "\n")
            self.progress_text.see(tk.END)
            self.progress_text.config(state="disabled")
        self.after(0, update)
    
    def _load_resume_json(self):
        """Load the generated resume JSON"""
        if not self.job_folder:
            return
        
        patterns = ["resume_final.json", "resume_validated.json", "resume.json"]
        for pattern in patterns:
            json_path = os.path.join(self.job_folder, pattern)
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.current_resume_json = json.load(f)
                self.json_edited = False
                self._log_progress(f"Loaded: {pattern}")
                self._log_console(f"✓ Loaded resume JSON: {pattern}", "success")
                return
        
        self._log_console("⚠ No resume JSON found in folder", "warning")
    
    # ========================================================================
    # LAYOUT TAB (ENHANCED WITH VISUAL EDITOR)
    # ========================================================================
    
    def _create_layout_tab(self):
        """Create layout customization interface"""
        parent = self.tab_layout
        
        ttk.Label(parent, text="Visual Layout Editor", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(parent, text="Configure section positioning and layout", style="Info.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Quick actions
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(actions_frame, text="🎨 Open Visual Editor", command=self.open_visual_editor, 
                  style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="📁 Load Template", command=self.load_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="💾 Save Template", command=self.save_template).pack(side=tk.LEFT, padx=5)
        
        # Current layout preview
        preview_frame = ttk.LabelFrame(parent, text="Current Layout", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.layout_preview_text = scrolledtext.ScrolledText(preview_frame, height=20, wrap=tk.WORD)
        self.layout_preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Navigation buttons
        nav_frame = ttk.Frame(parent)
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(nav_frame, text="← Back to Pipeline", command=lambda: self.notebook.select(self.tab_pipeline)).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next: Generate PDF →", command=lambda: self.notebook.select(self.tab_generate), 
                  style="Primary.TButton").pack(side=tk.RIGHT, padx=5)
        
        self.update_layout_preview()
    
    def open_visual_editor(self):
        editor = VisualLayoutEditor(self, self.current_layout_config)
        self.wait_window(editor)
        
        if hasattr(editor, 'result') and editor.result:
            self.current_layout_config = editor.result
            self.update_layout_preview()
            self._log_console("✓ Layout configuration updated", "success")
    
    def update_layout_preview(self):
        self.layout_preview_text.delete("1.0", tk.END)
        
        if hasattr(self, 'current_layout_config') and self.current_layout_config:
            preview_text = json.dumps(self.current_layout_config, indent=2)
        else:
            preview_text = "No custom layout configured. Using default layout.\n\nClick 'Open Visual Editor' to customize."
        
        self.layout_preview_text.insert("1.0", preview_text)
    
    def load_template(self):
        filename = filedialog.askopenfilename(
            title="Load Layout Template",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.current_layout_config = config
                self.update_layout_preview()
                self._log_console(f"✓ Loaded template from {filename}", "success")
                messagebox.showinfo("Success", "Template loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load template:\n{str(e)}")
                self._log_console(f"✗ Failed to load template: {str(e)}", "error")
    
    def save_template(self):
        if not self.current_layout_config:
            messagebox.showwarning("No Configuration", "No layout configuration to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Layout Template",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                config = self.current_layout_config.copy()
                if 'metadata' not in config:
                    config['metadata'] = {}
                config['metadata']['saved_at'] = datetime.now().isoformat()
                config['metadata']['template_name'] = Path(filename).stem
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                
                self._log_console(f"✓ Saved template to {filename}", "success")
                messagebox.showinfo("Success", "Template saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save template:\n{str(e)}")
                self._log_console(f"✗ Failed to save template: {str(e)}", "error")
    
    # ========================================================================
    # TAB 4: PDF GENERATION (FIXED PDF POPUP, ADDED JSON EDITOR)
    # ========================================================================
    
    def _create_generate_tab(self):
        """Create PDF generation interface with JSON editor"""
        parent = self.tab_generate
        
        ttk.Label(parent, text="Generate PDF Resume", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Options
        options_frame = ttk.LabelFrame(parent, text="Generation Options", padding=10)
        options_frame.pack(fill="x", pady=(0, 15))
        
        self.auto_open_pdf = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Automatically open PDF after generation", 
                       variable=self.auto_open_pdf).pack(anchor="w", pady=2)
        
        self.sync_edited_json = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Save edited JSON back to file", 
                       variable=self.sync_edited_json).pack(anchor="w", pady=2)
        
        output_frame = ttk.Frame(options_frame)
        output_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(output_frame, text="Output location:").pack(anchor="w")
        self.output_path_var = tk.StringVar(value="(will be generated in job folder)")
        ttk.Entry(output_frame, textvariable=self.output_path_var, state="readonly").pack(fill="x", pady=5)
        
        # Preview/Edit frame
        preview_frame = ttk.LabelFrame(parent, text="Resume JSON (Editable)", padding=10)
        preview_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # FIXED: Use normal Text widget (not disabled) for editing
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=20, wrap="word")
        self.preview_text.pack(fill="both", expand=True)
        
        # Track edits
        self.preview_text.bind('<<Modified>>', self._on_json_modified)
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="← Back to Layout", command=lambda: self.notebook.select(self.tab_layout)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Load JSON", command=self._preview_json).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Validate JSON", command=self._validate_json_edits).pack(side="left", padx=5)
        self.generate_button = ttk.Button(button_frame, text="Generate PDF", command=self._generate_pdf, style="Success.TButton")
        self.generate_button.pack(side="right", padx=5)
    
    def _on_json_modified(self, event=None):
        """Track that JSON has been edited"""
        if self.preview_text.edit_modified():
            self.json_edited = True
            self.preview_text.edit_modified(False)
    
    def _preview_json(self):
        """Preview/load the resume JSON"""
        # FIXED: Load JSON even when folder is loaded without running pipeline
        if not self.current_resume_json:
            if self.job_folder:
                self._load_resume_json()
                if not self.current_resume_json:
                    messagebox.showinfo("No Data", "No resume JSON found in folder. Please run the pipeline first.")
                    return
            else:
                messagebox.showinfo("No Data", "No resume data loaded. Please run the pipeline first or load an existing folder.")
                return
        
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", json.dumps(self.current_resume_json, indent=2))
        self.json_edited = False
        self._log_console("Loaded resume JSON for preview/editing", "info")
    
    def _validate_json_edits(self):
        """Validate edited JSON"""
        try:
            json_text = self.preview_text.get("1.0", tk.END)
            parsed = json.loads(json_text)
            self.current_resume_json = parsed
            self.json_edited = True
            messagebox.showinfo("Valid", "JSON is valid! Changes will be used for PDF generation.")
            self._log_console("✓ JSON validated successfully", "success")
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"JSON syntax error:\n{str(e)}")
            self._log_console(f"✗ JSON validation failed: {str(e)}", "error")
    
    def _generate_pdf(self):
        """Generate PDF with current configuration"""
        if not self.job_folder:
            messagebox.showwarning("No Job Folder", "Please run the pipeline first or load an existing folder")
            return
        
        try:
            # Save edited JSON if requested
            if self.json_edited and self.sync_edited_json.get():
                json_text = self.preview_text.get("1.0", tk.END)
                try:
                    parsed = json.loads(json_text)
                    self.current_resume_json = parsed
                    
                    # Save to file
                    json_path = os.path.join(self.job_folder, "resume_edited.json")
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed, f, indent=2)
                    
                    self._log_console(f"✓ Saved edited JSON to: resume_edited.json", "success")
                except json.JSONDecodeError as e:
                    messagebox.showerror("Invalid JSON", f"Cannot generate PDF with invalid JSON:\n{str(e)}")
                    return
            
            # Save layout config
            if self.current_layout_config:
                config_path = os.path.join(self.job_folder, "resume_layout_config.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_layout_config, f, indent=2)
            
            self.status_var.set("Generating PDF...")
            self.generate_button.config(state="disabled", text="Generating...")
            self._log_console("Generating PDF...", "info")
            
            import subprocess
            result = subprocess.run(
                ["node", "generate-pdf-enhanced.js", self.job_folder],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                pdf_files = list(Path(self.job_folder).glob("*.pdf"))
                pdf_path = str(pdf_files[-1]) if pdf_files else None
                
                self.status_var.set("✓ PDF generated successfully")
                self._log_console(f"✓ PDF generated: {pdf_path}", "success")
                
                # FIXED: Just open PDF directly, no popup
                # if self.auto_open_pdf.get() and pdf_path:
                #     import platform
                #     if platform.system() == 'Windows':
                #         os.startfile(pdf_path)
                #     elif platform.system() == 'Darwin':
                #         subprocess.run(['open', pdf_path])
                #     else:
                #         subprocess.run(['xdg-open', pdf_path])
                #     self._log_console(f"✓ Opened PDF: {pdf_path}", "success")
                # else:
                #     # Only show message if not auto-opening
                #     messagebox.showinfo("Success", f"PDF generated successfully!\n\nLocation: {pdf_path}")
            else:
                error_msg = result.stderr or "Unknown error"
                messagebox.showerror("PDF Generation Failed", f"Error:\n{error_msg}")
                self.status_var.set("PDF generation failed")
                self._log_console(f"✗ PDF generation failed: {error_msg}", "error")
            
            self.generate_button.config(state="normal", text="Generate PDF")
            
        except FileNotFoundError:
            messagebox.showerror("Node.js Not Found", "Node.js is required for PDF generation.\n\nPlease install Node.js from nodejs.org")
            self.generate_button.config(state="normal", text="Generate PDF")
            self.status_var.set("Node.js not found")
            self._log_console("✗ Node.js not found", "error")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Timeout", "PDF generation timed out")
            self.generate_button.config(state="normal", text="Generate PDF")
            self.status_var.set("PDF generation timed out")
            self._log_console("✗ PDF generation timed out", "error")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
            self.generate_button.config(state="normal", text="Generate PDF")
            self.status_var.set(f"Error: {str(e)}")
            self._log_console(f"✗ PDF generation error: {str(e)}", "error")
    
    def _load_resume_json(self):
        """Load resume JSON from job folder"""
        if not self.job_folder:
            return
        
        # Try different filenames
        filenames = ['resume_final.json', 'resume_edited.json', 'resume_validated.json']
        
        for filename in filenames:
            json_path = os.path.join(self.job_folder, filename)
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        self.current_resume_json = json.load(f)
                    self._log_console(f"✓ Loaded {filename}", "success")
                    return
                except Exception as e:
                    self._log_console(f"⚠ Failed to load {filename}: {str(e)}", "warning")
        
        self._log_console("No resume JSON found in folder", "warning")


def main():
    """Launch the GUI application"""
    app = ResumeGeneratorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
