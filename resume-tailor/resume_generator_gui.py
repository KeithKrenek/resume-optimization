"""
Resume Generator GUI - Enhanced User Interface
Combines original app.py usability with new multi-agent pipeline
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import threading
from pathlib import Path
from datetime import datetime

# Import orchestrator (will work after deployment)
try:
    from orchestrator_enhanced import ResumeOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    print("Warning: orchestrator_complete.py not found - demo mode only")


class ResumeGeneratorGUI(tk.Tk):
    """
    Enhanced GUI for resume generation with multi-agent pipeline
    """
    
    def __init__(self):
        super().__init__()
        self.title("AI Resume Generator - Multi-Agent Pipeline")
        self.geometry("900x800")
        
        # Instance variables
        self.job_folder = None
        self.orchestrator = None
        self.current_resume_json = None
        
        # Style configuration
        self._configure_styles()
        
        # Create main UI
        self.notebook = ttk.Notebook(self)
        
        # Create tabs
        self.tab_job_input = ttk.Frame(self.notebook, padding=15)
        self.tab_pipeline = ttk.Frame(self.notebook, padding=15)
        self.tab_layout = ttk.Frame(self.notebook, padding=15)
        self.tab_generate = ttk.Frame(self.notebook, padding=15)
        
        self.notebook.add(self.tab_job_input, text="1. Job Description")
        self.notebook.add(self.tab_pipeline, text="2. Run Pipeline")
        self.notebook.add(self.tab_layout, text="3. Customize Layout")
        self.notebook.add(self.tab_generate, text="4. Generate PDF")
        
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Build each tab
        self._create_job_input_tab()
        self._create_pipeline_tab()
        self._create_layout_tab()
        self._create_generate_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Initialize orchestrator if available
        if ORCHESTRATOR_AVAILABLE:
            try:
                self.orchestrator = ResumeOrchestrator()
                self.status_var.set("✓ Multi-agent pipeline ready")
            except Exception as e:
                self.status_var.set(f"Warning: {str(e)}")
    
    def _configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style(self)
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"), foreground="#0f172a")
        style.configure("Subheader.TLabel", font=("Helvetica", 11, "bold"), foreground="#334155")
        style.configure("Info.TLabel", font=("Helvetica", 9), foreground="#64748b")
        style.configure("Success.TButton", background="#10b981", foreground="white")
        style.configure("Primary.TButton", background="#0ea5e9", foreground="white")
    
    # ========================================================================
    # TAB 1: JOB DESCRIPTION INPUT
    # ========================================================================
    
    def _create_job_input_tab(self):
        """Create job description input interface"""
        parent = self.tab_job_input
        
        # Header
        ttk.Label(parent, text="Job Description Input", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Input method selection
        input_frame = ttk.LabelFrame(parent, text="Input Method", padding=10)
        input_frame.pack(fill="x", pady=(0, 15))
        
        self.input_method = tk.StringVar(value="url")
        ttk.Radiobutton(input_frame, text="URL (recommended)", variable=self.input_method, value="url").pack(anchor="w")
        ttk.Radiobutton(input_frame, text="Text File", variable=self.input_method, value="file").pack(anchor="w")
        ttk.Radiobutton(input_frame, text="Paste Text", variable=self.input_method, value="text").pack(anchor="w")
        ttk.Radiobutton(input_frame, text="Load Existing Folder", variable=self.input_method, value="folder").pack(anchor="w")
        
        # URL input
        url_frame = ttk.Frame(parent)
        url_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(url_frame, text="Job Description URL:").pack(anchor="w")
        self.jd_url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.jd_url_var, width=70).pack(fill="x", pady=5)
        
        # File input
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(file_frame, text="Job Description File:").pack(anchor="w")
        file_input_frame = ttk.Frame(file_frame)
        file_input_frame.pack(fill="x", pady=5)
        self.jd_file_var = tk.StringVar()
        ttk.Entry(file_input_frame, textvariable=self.jd_file_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(file_input_frame, text="Browse...", command=self._browse_jd_file).pack(side="left", padx=(5, 0))
        
        # Text input
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ttk.Label(text_frame, text="Job Description Text:").pack(anchor="w")
        self.jd_text = scrolledtext.ScrolledText(text_frame, height=4, wrap="word")
        self.jd_text.pack(fill="both", expand=True, pady=5)
        
        # Folder input
        folder_frame = ttk.Frame(parent)
        folder_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(folder_frame, text="Existing Job Folder:").pack(anchor="w")
        folder_input_frame = ttk.Frame(folder_frame)
        folder_input_frame.pack(fill="x", pady=5)
        self.job_folder_var = tk.StringVar()
        ttk.Entry(folder_input_frame, textvariable=self.job_folder_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_input_frame, text="Browse...", command=self._browse_job_folder).pack(side="left", padx=(5, 0))
        
        # Company info
        company_frame = ttk.LabelFrame(parent, text="Optional Company Information", padding=10)
        company_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(company_frame, text="Company Name (optional - will auto-extract):").pack(anchor="w")
        self.company_name_var = tk.StringVar()
        ttk.Entry(company_frame, textvariable=self.company_name_var, width=50).pack(fill="x", pady=(2, 8))
        
        ttk.Label(company_frame, text="Job Title (optional - will auto-extract):").pack(anchor="w")
        self.job_title_var = tk.StringVar()
        ttk.Entry(company_frame, textvariable=self.job_title_var, width=50).pack(fill="x", pady=(2, 8))
        
        ttk.Label(company_frame, text="Company Website URL (for additional context):").pack(anchor="w")
        self.company_url_var = tk.StringVar()
        ttk.Entry(company_frame, textvariable=self.company_url_var, width=50).pack(fill="x", pady=(2, 8))
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Clear All", command=self._clear_job_input).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Next: Run Pipeline →", command=self._proceed_to_pipeline, style="Primary.TButton").pack(side="right", padx=5)
    
    def _browse_jd_file(self):
        """Browse for job description file"""
        filename = filedialog.askopenfilename(
            title="Select Job Description File",
            filetypes=[("Text files", "*.txt *.md"), ("All files", "*.*")]
        )
        if filename:
            self.jd_file_var.set(filename)
    
    def _browse_job_folder(self):
        """Browse for existing job folder"""
        folder = filedialog.askdirectory(title="Select Existing Job Folder")
        if folder:
            self.job_folder_var.set(folder)
            self.job_folder = folder
    
    def _clear_job_input(self):
        """Clear all job input fields"""
        self.jd_url_var.set("")
        self.jd_file_var.set("")
        self.jd_text.delete("1.0", tk.END)
        self.job_folder_var.set("")
        self.company_name_var.set("")
        self.job_title_var.set("")
        self.company_url_var.set("")
    
    def _proceed_to_pipeline(self):
        """Validate input and move to pipeline tab"""
        method = self.input_method.get()
        
        if method == "url" and not self.jd_url_var.get().strip():
            messagebox.showwarning("Missing Input", "Please enter a job description URL")
            return
        elif method == "file" and not self.jd_file_var.get().strip():
            messagebox.showwarning("Missing Input", "Please select a job description file")
            return
        elif method == "text" and not self.jd_text.get("1.0", tk.END).strip():
            messagebox.showwarning("Missing Input", "Please paste job description text")
            return
        elif method == "folder" and not self.job_folder_var.get().strip():
            messagebox.showwarning("Missing Input", "Please select an existing job folder")
            return
        
        self.notebook.select(self.tab_pipeline)
    
    # ========================================================================
    # TAB 2: PIPELINE EXECUTION
    # ========================================================================
    
    def _create_pipeline_tab(self):
        """Create pipeline execution interface"""
        parent = self.tab_pipeline
        
        # Header
        ttk.Label(parent, text="Multi-Agent Pipeline Execution", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
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
        ttk.Checkbutton(options_frame, text="Skip style editing (Agent 5) if draft is already good", variable=self.skip_style_editing).pack(anchor="w", pady=2)
        
        # Progress display
        progress_frame = ttk.LabelFrame(parent, text="Pipeline Progress", padding=10)
        progress_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=15, state="disabled", wrap="word")
        self.progress_text.pack(fill="both", expand=True)
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="← Back", command=lambda: self.notebook.select(self.tab_job_input)).pack(side="left", padx=5)
        self.run_button = ttk.Button(button_frame, text="Run Pipeline", command=self._run_pipeline, style="Success.TButton")
        self.run_button.pack(side="right", padx=5)
        ttk.Button(button_frame, text="Skip to Layout →", command=lambda: self.notebook.select(self.tab_layout)).pack(side="right", padx=5)
    
    def _run_pipeline(self):
        """Execute the multi-agent pipeline"""
        if not ORCHESTRATOR_AVAILABLE:
            messagebox.showerror("Not Available", "Orchestrator not found. Please deploy orchestrator_complete.py")
            return
        
        # Disable button during execution
        self.run_button.config(state="disabled", text="Running...")
        self.progress_text.config(state="normal")
        self.progress_text.delete("1.0", tk.END)
        
        # Run in thread to keep GUI responsive
        thread = threading.Thread(target=self._execute_pipeline_thread, daemon=True)
        thread.start()
    
    def _execute_pipeline_thread(self):
        """Execute pipeline in separate thread"""
        try:
            self._log_progress("Starting multi-agent pipeline...")
            
            # Get job input based on method
            method = self.input_method.get()
            jd_input = None
            
            if method == "url":
                jd_input = self.jd_url_var.get().strip()
                self._log_progress(f"Fetching from URL: {jd_input}")
            elif method == "file":
                with open(self.jd_file_var.get(), 'r', encoding='utf-8') as f:
                    jd_input = f.read()
                self._log_progress(f"Loaded from file: {self.jd_file_var.get()}")
            elif method == "text":
                jd_input = self.jd_text.get("1.0", tk.END).strip()
                self._log_progress("Using pasted text")
            elif method == "folder":
                # Load existing folder
                self.job_folder = self.job_folder_var.get()
                self._log_progress(f"Resuming from folder: {self.job_folder}")
            
            # Execute pipeline
            if method == "folder":
                # Resume from existing folder
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
                # Full pipeline
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
            
            # Load the generated resume JSON
            self._load_resume_json()
            
            self._log_progress("\n✓ Ready for layout customization")
            
            # Re-enable button
            self.after(100, lambda: self.run_button.config(state="normal", text="Run Pipeline"))
            self.after(100, lambda: messagebox.showinfo("Success", "Pipeline completed successfully!\n\nProceed to Layout tab to customize."))
            
        except Exception as e:
            self._log_progress(f"\n✗ Error: {str(e)}")
            self.after(100, lambda: self.run_button.config(state="normal", text="Run Pipeline"))
            self.after(100, lambda: messagebox.showerror("Pipeline Error", f"An error occurred:\n\n{str(e)}"))
    
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
        
        # Try to find resume JSON
        patterns = ["resume_final.json", "resume_validated.json", "resume.json"]
        for pattern in patterns:
            json_path = os.path.join(self.job_folder, pattern)
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.current_resume_json = json.load(f)
                self._log_progress(f"Loaded: {pattern}")
                return
    
    # ========================================================================
    # TAB 3: LAYOUT CUSTOMIZATION
    # ========================================================================
    
    def _create_layout_tab(self):
        """Create layout customization interface"""
        parent = self.tab_layout
        
        # Header
        ttk.Label(parent, text="PDF Layout Customization", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(parent, text="Customize how sections appear in your PDF", style="Info.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Main container with scrollbar
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Section order and visibility
        self._create_section_controls(scrollable_frame)
        
        # Advanced options
        self._create_advanced_layout_options(scrollable_frame)
        
        # Action buttons (outside scrollable area)
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0), side="bottom")
        
        ttk.Button(button_frame, text="← Back", command=lambda: self.notebook.select(self.tab_pipeline)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Load Config...", command=self._load_layout_config).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Config", command=self._save_layout_config).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self._reset_layout_config).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Next: Generate PDF →", command=lambda: self.notebook.select(self.tab_generate), style="Primary.TButton").pack(side="right", padx=5)
    
    def _create_section_controls(self, parent):
        """Create section ordering and visibility controls"""
        sections_frame = ttk.LabelFrame(parent, text="Section Order & Visibility", padding=10)
        sections_frame.pack(fill="x", pady=(0, 10))
        
        # Store section controls
        self.section_controls = {}
        
        sections = [
            ("professional_summary", "Professional Summary"),
            ("technical_expertise", "Technical Expertise"),
            ("experience", "Professional Experience"),
            ("projects", "Key Projects"),
            ("education", "Education"),
            ("publications", "Publications"),
            ("work_samples", "Work Samples")
        ]
        
        for i, (key, label) in enumerate(sections):
            section_frame = ttk.Frame(sections_frame)
            section_frame.pack(fill="x", pady=5)
            
            # Order
            order_var = tk.IntVar(value=i+1)
            ttk.Label(section_frame, text=f"Order:", width=8).pack(side="left")
            ttk.Spinbox(section_frame, from_=1, to=10, textvariable=order_var, width=5).pack(side="left", padx=5)
            
            # Enabled
            enabled_var = tk.BooleanVar(value=(key != "work_samples"))
            ttk.Checkbutton(section_frame, text=label, variable=enabled_var).pack(side="left", padx=10)
            
            # Keep Together
            keep_together_var = tk.BooleanVar(value=(key in ["professional_summary", "education", "publications"]))
            ttk.Checkbutton(section_frame, text="Keep Together", variable=keep_together_var).pack(side="left", padx=10)
            
            # Columns (for skills)
            if key == "technical_expertise":
                ttk.Label(section_frame, text="Columns:").pack(side="left", padx=(20, 5))
                columns_var = tk.IntVar(value=2)
                ttk.Spinbox(section_frame, from_=1, to=3, textvariable=columns_var, width=5).pack(side="left")
                self.section_controls[key] = (order_var, enabled_var, keep_together_var, columns_var)
            else:
                self.section_controls[key] = (order_var, enabled_var, keep_together_var)
    
    def _create_advanced_layout_options(self, parent):
        """Create advanced layout options"""
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Options", padding=10)
        advanced_frame.pack(fill="x", pady=(0, 10))
        
        # Page style
        style_frame = ttk.Frame(advanced_frame)
        style_frame.pack(fill="x", pady=5)
        ttk.Label(style_frame, text="Page Style:", width=15).pack(side="left")
        self.page_style_var = tk.StringVar(value="single_column")
        ttk.Combobox(style_frame, textvariable=self.page_style_var, values=["single_column", "two_column", "hybrid"], state="readonly", width=20).pack(side="left", padx=5)
        
        # Font
        font_frame = ttk.Frame(advanced_frame)
        font_frame.pack(fill="x", pady=5)
        ttk.Label(font_frame, text="Font Family:", width=15).pack(side="left")
        self.font_var = tk.StringVar(value="Inter")
        ttk.Combobox(font_frame, textvariable=self.font_var, values=["Inter", "Helvetica", "Arial", "Georgia", "Times"], state="readonly", width=20).pack(side="left", padx=5)
        
        # Font size
        size_frame = ttk.Frame(advanced_frame)
        size_frame.pack(fill="x", pady=5)
        ttk.Label(size_frame, text="Base Font Size:", width=15).pack(side="left")
        self.font_size_var = tk.StringVar(value="9.5pt")
        ttk.Combobox(size_frame, textvariable=self.font_size_var, values=["8.5pt", "9pt", "9.5pt", "10pt", "10.5pt"], state="readonly", width=20).pack(side="left", padx=5)
        
        # Colors
        color_frame = ttk.LabelFrame(advanced_frame, text="Colors", padding=5)
        color_frame.pack(fill="x", pady=(10, 0))
        
        color_options = [
            ("Accent Color:", "accent_color_var", "#0ea5e9"),
            ("Title Color:", "title_color_var", "#b45309"),
            ("Primary Color:", "primary_color_var", "#0f172a")
        ]
        
        for label, var_name, default in color_options:
            cf = ttk.Frame(color_frame)
            cf.pack(fill="x", pady=2)
            ttk.Label(cf, text=label, width=15).pack(side="left")
            var = tk.StringVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(cf, textvariable=var, width=15).pack(side="left", padx=5)
            ttk.Button(cf, text="Pick...", command=lambda v=var: self._pick_color(v)).pack(side="left")
    
    def _pick_color(self, color_var):
        """Open color picker"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(color_var.get())
        if color[1]:
            color_var.set(color[1])
    
    def _load_layout_config(self):
        """Load layout configuration from file"""
        filename = filedialog.askopenfilename(
            title="Load Layout Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                self._apply_layout_config(config)
                messagebox.showinfo("Success", "Layout configuration loaded")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration:\n{str(e)}")
    
    def _save_layout_config(self):
        """Save current layout configuration"""
        config = self._get_layout_config()
        
        # Determine save location
        if self.job_folder:
            default_path = os.path.join(self.job_folder, "resume_layout_config.json")
        else:
            default_path = "resume_layout_config.json"
        
        filename = filedialog.asksaveasfilename(
            title="Save Layout Configuration",
            initialfile=default_path,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("Success", f"Configuration saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")
    
    def _get_layout_config(self):
        """Get current layout configuration as dict"""
        config = {
            "layout": {
                "page_style": self.page_style_var.get(),
                "max_pages": 2
            },
            "sections": {},
            "typography": {
                "font_family": self.font_var.get(),
                "base_size": self.font_size_var.get()
            },
            "colors": {
                "accent": self.accent_color_var.get(),
                "title": self.title_color_var.get(),
                "primary": self.primary_color_var.get()
            }
        }
        
        # Add section configurations
        for key, controls in self.section_controls.items():
            if len(controls) == 4:  # technical_expertise with columns
                order, enabled, keep_together, columns = controls
                config["sections"][key] = {
                    "enabled": enabled.get(),
                    "order": order.get(),
                    "keep_together": keep_together.get(),
                    "columns": columns.get()
                }
            else:
                order, enabled, keep_together = controls
                config["sections"][key] = {
                    "enabled": enabled.get(),
                    "order": order.get(),
                    "keep_together": keep_together.get()
                }
        
        return config
    
    def _apply_layout_config(self, config):
        """Apply loaded configuration to UI"""
        # Apply basic settings
        if "layout" in config:
            self.page_style_var.set(config["layout"].get("page_style", "single_column"))
        
        if "typography" in config:
            self.font_var.set(config["typography"].get("font_family", "Inter"))
            self.font_size_var.set(config["typography"].get("base_size", "9.5pt"))
        
        if "colors" in config:
            self.accent_color_var.set(config["colors"].get("accent", "#0ea5e9"))
            self.title_color_var.set(config["colors"].get("title", "#b45309"))
            self.primary_color_var.set(config["colors"].get("primary", "#0f172a"))
        
        # Apply section settings
        if "sections" in config:
            for key, section_config in config["sections"].items():
                if key in self.section_controls:
                    controls = self.section_controls[key]
                    controls[0].set(section_config.get("order", 1))  # order
                    controls[1].set(section_config.get("enabled", True))  # enabled
                    controls[2].set(section_config.get("keep_together", False))  # keep_together
                    if len(controls) == 4:  # Has columns
                        controls[3].set(section_config.get("columns", 2))
    
    def _reset_layout_config(self):
        """Reset to default layout configuration"""
        if messagebox.askyesno("Reset", "Reset all layout settings to defaults?"):
            # Reset to defaults
            self.page_style_var.set("single_column")
            self.font_var.set("Inter")
            self.font_size_var.set("9.5pt")
            self.accent_color_var.set("#0ea5e9")
            self.title_color_var.set("#b45309")
            self.primary_color_var.set("#0f172a")
            
            # Reset section controls
            defaults = {
                "professional_summary": (1, True, True),
                "technical_expertise": (2, True, False, 2),
                "experience": (3, True, False),
                "projects": (4, True, False),
                "education": (5, True, True),
                "publications": (6, True, True),
                "work_samples": (7, False, False)
            }
            
            for key, values in defaults.items():
                if key in self.section_controls:
                    controls = self.section_controls[key]
                    for i, val in enumerate(values):
                        controls[i].set(val)
    
    # ========================================================================
    # TAB 4: PDF GENERATION
    # ========================================================================
    
    def _create_generate_tab(self):
        """Create PDF generation interface"""
        parent = self.tab_generate
        
        # Header
        ttk.Label(parent, text="Generate PDF Resume", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Options
        options_frame = ttk.LabelFrame(parent, text="Generation Options", padding=10)
        options_frame.pack(fill="x", pady=(0, 15))
        
        self.auto_open_pdf = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Automatically open PDF after generation", variable=self.auto_open_pdf).pack(anchor="w", pady=2)
        
        # Output location
        output_frame = ttk.Frame(options_frame)
        output_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(output_frame, text="Output location:").pack(anchor="w")
        self.output_path_var = tk.StringVar(value="(will be generated in job folder)")
        ttk.Entry(output_frame, textvariable=self.output_path_var, state="readonly").pack(fill="x", pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(parent, text="Resume Preview", padding=10)
        preview_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=20, state="disabled", wrap="word")
        self.preview_text.pack(fill="both", expand=True)
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="← Back to Layout", command=lambda: self.notebook.select(self.tab_layout)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Preview JSON", command=self._preview_json).pack(side="left", padx=5)
        self.generate_button = ttk.Button(button_frame, text="Generate PDF", command=self._generate_pdf, style="Success.TButton")
        self.generate_button.pack(side="right", padx=5)
    
    def _preview_json(self):
        """Preview the resume JSON that will be used"""
        if not self.current_resume_json:
            messagebox.showinfo("No Data", "No resume data loaded. Please run the pipeline first.")
            return
        
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", json.dumps(self.current_resume_json, indent=2))
        self.preview_text.config(state="disabled")
    
    def _generate_pdf(self):
        """Generate PDF with current configuration"""
        if not self.job_folder:
            messagebox.showwarning("No Job Folder", "Please run the pipeline first or load an existing folder")
            return
        
        try:
            # Save layout config to job folder
            import os
            config_path = os.path.join(self.job_folder, "resume_layout_config.json")
            config = self._get_layout_config()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            self.status_var.set("Generating PDF...")
            self.generate_button.config(state="disabled", text="Generating...")
            
            # Call PDF generator
            import subprocess
            result = subprocess.run(
                ["node", "generate-pdf-enhanced.js", self.job_folder],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "PDF generated successfully!")
                self.status_var.set("PDF generated successfully")
                
                # Find and open PDF if requested
                if self.auto_open_pdf.get():
                    pdf_files = list(Path(self.job_folder).glob("*.pdf"))
                    if pdf_files:
                        import platform
                        import os
                        pdf_path = str(pdf_files[-1])
                        if platform.system() == 'Windows':
                            os.startfile(pdf_path)
                        elif platform.system() == 'Darwin':
                            subprocess.run(['open', pdf_path])
                        else:
                            subprocess.run(['xdg-open', pdf_path])
            else:
                messagebox.showerror("PDF Generation Failed", f"Error:\n{result.stderr}")
                self.status_var.set("PDF generation failed")
            
            self.generate_button.config(state="normal", text="Generate PDF")
            
        except FileNotFoundError:
            messagebox.showerror("Node.js Not Found", "Node.js is required for PDF generation.\n\nPlease install Node.js from nodejs.org")
            self.generate_button.config(state="normal", text="Generate PDF")
            self.status_var.set("Node.js not found")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Timeout", "PDF generation timed out")
            self.generate_button.config(state="normal", text="Generate PDF")
            self.status_var.set("PDF generation timed out")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
            self.generate_button.config(state="normal", text="Generate PDF")
            self.status_var.set(f"Error: {str(e)}")


def main():
    """Launch the GUI application"""
    app = ResumeGeneratorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()