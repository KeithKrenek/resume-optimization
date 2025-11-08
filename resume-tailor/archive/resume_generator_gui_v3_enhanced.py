"""
Resume Generator GUI v3.0 - Visual Layout Editor
COMPREHENSIVE ENHANCEMENT INCLUDING:
- Visual drag-and-drop layout editor
- Flexible section positioning (single, side-by-side, multi-column)
- Width and column controls
- Layout template management
- Live preview of layout structure
- Quick layout presets
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import threading
from pathlib import Path
from datetime import datetime

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
            'projects',
            'education',
            'publications',
            'work_samples'
        ]
        
        self.section_display_names = {
            'professional_summary': 'Professional Summary',
            'technical_expertise': 'Technical Expertise',
            'experience': 'Experience',
            'projects': 'Projects',
            'education': 'Education',
            'publications': 'Publications',
            'work_samples': 'Work Samples'
        }
        
        # Load initial config if provided
        if initial_config:
            self.load_from_config(initial_config)
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
                'sections': ['projects'],
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
    
    def load_from_config(self, config):
        """Load layout from existing config"""
        if 'layout' in config and 'rows' in config['layout']:
            self.layout_rows = config['layout']['rows']
        else:
            self.initialize_default_layout()
    
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
        # Clear existing
        for widget in self.layout_container.winfo_children():
            widget.destroy()
        
        # Draw each row
        for idx, row in enumerate(self.layout_rows):
            self._draw_row(idx, row)
    
    def _draw_row(self, idx, row):
        """Draw a single row in the layout"""
        row_frame = ttk.Frame(self.layout_container, relief=tk.GROOVE, borderwidth=2)
        row_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Row header with controls
        header = ttk.Frame(row_frame)
        header.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header, text=f"Row {idx + 1}", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        
        # Row controls
        controls = ttk.Frame(header)
        controls.pack(side=tk.RIGHT)
        
        ttk.Button(controls, text="↑", command=lambda: self.move_row(idx, -1), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(controls, text="↓", command=lambda: self.move_row(idx, 1), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(controls, text="✎", command=lambda: self.edit_row(idx), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(controls, text="×", command=lambda: self.delete_row(idx), width=3).pack(side=tk.LEFT, padx=1)
        
        # Row content
        content = ttk.Frame(row_frame)
        content.pack(fill=tk.X, padx=5, pady=5)
        
        # Display sections
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
        
        # Row properties
        props_text = f"Type: {row['type']} | Gap: {row.get('column_gap', '20px')} | Break: {row.get('allow_page_break', True)}"
        ttk.Label(content, text=props_text, font=("Helvetica", 7), foreground="#64748b").pack(anchor="w", pady=(5, 0))
    
    def add_row(self):
        """Add a new row"""
        dialog = RowEditorDialog(self, None)
        self.wait_window(dialog)
        
        if dialog.result:
            self.layout_rows.append(dialog.result)
            self.refresh_layout_display()
    
    def edit_row(self, idx):
        """Edit an existing row"""
        dialog = RowEditorDialog(self, self.layout_rows[idx])
        self.wait_window(dialog)
        
        if dialog.result:
            self.layout_rows[idx] = dialog.result
            self.refresh_layout_display()
    
    def delete_row(self, idx):
        """Delete a row"""
        if messagebox.askyesno("Confirm Delete", f"Delete Row {idx + 1}?"):
            del self.layout_rows[idx]
            self.refresh_layout_display()
    
    def move_row(self, idx, direction):
        """Move a row up or down"""
        new_idx = idx + direction
        if 0 <= new_idx < len(self.layout_rows):
            self.layout_rows[idx], self.layout_rows[new_idx] = self.layout_rows[new_idx], self.layout_rows[idx]
            self.refresh_layout_display()
    
    def reset_layout(self):
        """Reset to default layout"""
        if messagebox.askyesno("Reset Layout", "Reset to default layout? This cannot be undone."):
            self.initialize_default_layout()
            self.refresh_layout_display()
    
    def apply_preset(self, preset_name):
        """Apply a layout preset"""
        if preset_name == "Standard":
            self.initialize_default_layout()
        elif preset_name == "Compact":
            self.layout_rows = [
                {'type': 'single', 'sections': ['professional_summary'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'side_by_side', 'sections': ['technical_expertise', 'education'], 'widths': ['60%', '40%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'single', 'sections': ['experience'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True},
                {'type': 'single', 'sections': ['projects'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True}
            ]
            self.compact_mode_var.set(True)
        elif preset_name == "Two-Column":
            self.layout_rows = [
                {'type': 'single', 'sections': ['professional_summary'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'side_by_side', 'sections': ['technical_expertise', 'experience'], 'widths': ['40%', '60%'], 'column_gap': '20px', 'allow_page_break': True},
                {'type': 'side_by_side', 'sections': ['projects', 'education'], 'widths': ['60%', '40%'], 'column_gap': '20px', 'allow_page_break': True}
            ]
            self.tech_columns_var.set(1)
        elif preset_name == "Academic":
            self.layout_rows = [
                {'type': 'single', 'sections': ['professional_summary'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'side_by_side', 'sections': ['education', 'publications'], 'widths': ['50%', '50%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'single', 'sections': ['technical_expertise'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': False},
                {'type': 'single', 'sections': ['experience'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True},
                {'type': 'single', 'sections': ['projects'], 'widths': ['100%'], 'column_gap': '20px', 'allow_page_break': True}
            ]
        
        self.refresh_layout_display()
    
    def preview_config(self):
        """Preview the configuration as JSON"""
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
        """Get the complete configuration"""
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
        """Apply the configuration and close"""
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
        """Create dialog UI"""
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
        """Update the sections listbox"""
        self.sections_listbox.delete(0, tk.END)
        
        for section in self.available_sections:
            display_name = self.section_display_names.get(section, section)
            self.sections_listbox.insert(tk.END, display_name)
            
            if section in self.selected_sections:
                idx = self.available_sections.index(section)
                self.sections_listbox.selection_set(idx)
    
    def ok(self):
        """OK button handler"""
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
        """Cancel button handler"""
        self.result = None
        self.destroy()


class ResumeGeneratorGUI(tk.Tk):
    """Enhanced GUI for resume generation with visual layout editor"""
    
    def __init__(self):
        super().__init__()
        self.title("AI Resume Generator - Multi-Agent Pipeline v3.0")
        self.geometry("950x850")
        
        self.job_folder = None
        self.orchestrator = None
        self.current_resume_json = None
        self.json_edited = False
        self.current_layout_config = None
        
        self.model_presets = {
            "Fast": "claude-3-5-haiku-20241022",
            "Balanced": "claude-sonnet-4-5-20250929",
            "Quality": "claude-opus-4-20250514"
        }
        
        self._configure_styles()
        
        self.notebook = ttk.Notebook(self)
        
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
        
        self._create_layout_tab()
        self._create_console_tab()
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
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
        style.configure("Success.TButton", background="#10b981", foreground="#ffffff")
        style.configure("Primary.TButton", background="#0ea5e9", foreground="#ffffff")
    
    def _create_layout_tab(self):
        """Create enhanced layout tab with visual editor"""
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
        
        self.update_layout_preview()
    
    def _create_console_tab(self):
        """Create console tab"""
        parent = self.tab_console
        
        ttk.Label(parent, text="System Console", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        
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
    
    def _log_console(self, message, tag=None):
        """Log message to console"""
        def update():
            self.console_text.insert(tk.END, message + "\n", tag)
            self.console_text.see(tk.END)
        self.after(0, update)
    
    def open_visual_editor(self):
        """Open the visual layout editor"""
        editor = VisualLayoutEditor(self, self.current_layout_config)
        self.wait_window(editor)
        
        if hasattr(editor, 'result') and editor.result:
            self.current_layout_config = editor.result
            self.update_layout_preview()
            self._log_console("✓ Layout configuration updated", "success")
    
    def update_layout_preview(self):
        """Update the layout preview text"""
        self.layout_preview_text.delete("1.0", tk.END)
        
        if self.current_layout_config:
            preview_text = json.dumps(self.current_layout_config, indent=2)
        else:
            preview_text = "No custom layout configured. Using default layout.\n\nClick 'Open Visual Editor' to customize."
        
        self.layout_preview_text.insert("1.0", preview_text)
    
    def load_template(self):
        """Load a layout template from a file"""
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
        """Save current layout as a template"""
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
                # Add metadata
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


def main():
    """Launch the GUI application"""
    app = ResumeGeneratorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
