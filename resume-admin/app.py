import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import shutil
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import webbrowser
import pyperclip
import subprocess
import json

# --- USER CONFIGURATION: SET YOUR DEFAULTS HERE ---
# Use forward slashes for paths (e.g., "C:/Users/YourName/Documents")
APP_DEFAULTS = {
    "save_path": r"C:\Users\keith\Dropbox\Resume",
    "instructions_file": r"C:\Users\keith\OneDrive\Desktop\CODE\resume-optimization\assistant-instructions\tech-resume-tailor.md",
    "resume_db_file": r"C:\Users\keith\OneDrive\Desktop\CODE\keith_resume_database.json",
    "html_template": "resume-template-3.html"
}
# ----------------------------------------------------

class JobAppOrganizer(tk.Tk):
    """
    A two-step desktop application to organize job application assets and
    prepare a prompt for an AI assistant.
    """
    def __init__(self):
        super().__init__()
        self.title("Job Application Assistant")
        self.geometry("750x650")

        # --- Instance variables ---
        self.jd_file_path_from_step1 = None 

        # --- Style Configuration ---
        style = ttk.Style(self)
        style.configure("TLabel", padding=5, font=("Helvetica", 10))
        style.configure("TButton", padding=5, font=("Helvetica", 10, "bold"))
        style.configure("TEntry", padding=5)
        style.configure("TFrame", padding=10)
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))

        # --- Main UI: Tabbed Notebook ---
        self.notebook = ttk.Notebook(self)
        self.step1_frame = ttk.Frame(self.notebook, padding=10)
        self.step2_frame = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.step1_frame, text="Step 1: Organize Files")
        self.notebook.add(self.step2_frame, text="Step 2: Prepare AI Prompt")
        self.notebook.pack(expand=True, fill="both")
        
        self._create_step1_widgets(self.step1_frame)
        self._create_step2_widgets(self.step2_frame)

    # --- Widget Creation for Step 1 ---
    def _create_step1_widgets(self, parent):
        ttk.Label(parent, text="Step 1: Organize Job Application Files", style="Header.TLabel").grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Label(parent, text="1. Job Description (Paste URL or Text):").grid(row=1, column=0, sticky="w")
        self.jd_input = tk.Text(parent, height=10, width=80, wrap="word", relief="solid", borderwidth=1)
        self.jd_input.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        ttk.Label(parent, text="2. Company URL:").grid(row=3, column=0, sticky="w")
        self.company_url_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.company_url_var, width=80).grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        ttk.Label(parent, text="3. Save Location:").grid(row=5, column=0, sticky="w")
        self.save_path_var = tk.StringVar(value=APP_DEFAULTS["save_path"])
        ttk.Entry(parent, textvariable=self.save_path_var, width=70).grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(parent, text="Browse...", command=lambda: self._select_directory(self.save_path_var)).grid(row=6, column=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(parent, text="4. Select HTML Template File:").grid(row=7, column=0, sticky="w")
        self.html_file_var = tk.StringVar()
        self.html_dropdown = ttk.Combobox(parent, textvariable=self.html_file_var, state="readonly", width=40)
        self.html_dropdown.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self._populate_template_files()
        
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=9, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Reset Fields", command=self._reset_step1).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Organize and Proceed to Step 2 ->", command=self._process_step1).pack(side=tk.LEFT, padx=10)

        self.status1_var = tk.StringVar(value="Ready.")
        ttk.Label(parent, textvariable=self.status1_var, relief=tk.SUNKEN, anchor="w").grid(row=10, column=0, columnspan=3, sticky="ew", pady=(10,0))
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

    # --- Widget Creation for Step 2 ---
    def _create_step2_widgets(self, parent):
        ttk.Label(parent, text="Step 2: Generate Resume Prompt for AI", style="Header.TLabel").grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Label(parent, text="1. Select AI Assistant:").grid(row=1, column=0, sticky="w")
        self.ai_var = tk.StringVar()
        ai_dropdown = ttk.Combobox(parent, textvariable=self.ai_var, state="readonly", values=["ChatGPT", "Claude", "Gemini"], width=40)
        ai_dropdown.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        ai_dropdown.current(0)

        ttk.Label(parent, text="2. Select System Instructions File:").grid(row=3, column=0, sticky="w")
        self.instructions_path_var = tk.StringVar(value=APP_DEFAULTS["instructions_file"])
        ttk.Entry(parent, textvariable=self.instructions_path_var, width=70).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(parent, text="Browse...", command=lambda: self._select_file(self.instructions_path_var, "Select Instructions File")).grid(row=4, column=2, sticky="w")
        
        ttk.Label(parent, text="3. Select Resume Database File:").grid(row=5, column=0, sticky="w")
        self.resume_db_path_var = tk.StringVar(value=APP_DEFAULTS["resume_db_file"])
        ttk.Entry(parent, textvariable=self.resume_db_path_var, width=70).grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(parent, text="Browse...", command=lambda: self._select_file(self.resume_db_path_var, "Select Resume DB File")).grid(row=6, column=2, sticky="w")

        ttk.Label(parent, text="4. Job Description File (auto-filled from Step 1 or select manually):").grid(row=7, column=0, sticky="w")
        self.jd_path_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.jd_path_var, width=70).grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(parent, text="Browse...", command=lambda: self._select_file(self.jd_path_var, "Select Job Description File")).grid(row=8, column=2, sticky="w")

        button_frame = ttk.Frame(parent)
        button_frame.grid(row=9, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Reset Fields", command=self._reset_step2).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Prepare Prompt & Open AI", command=self._process_step2).pack(side=tk.LEFT, padx=10)
        
        self.status2_var = tk.StringVar(value="Ready.")
        ttk.Label(parent, textvariable=self.status2_var, relief=tk.SUNKEN, anchor="w").grid(row=10, column=0, columnspan=3, sticky="ew", pady=(10,0))
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

    # --- Helper and Logic Functions ---
    def _reset_step1(self):
        self.jd_input.delete("1.0", tk.END)
        self.company_url_var.set("")
        self.save_path_var.set(APP_DEFAULTS["save_path"])
        self._populate_template_files() # Resets dropdowns to defaults
        self.status1_var.set("Fields reset.")

    def _reset_step2(self):
        self.ai_var.set("ChatGPT")
        self.instructions_path_var.set(APP_DEFAULTS["instructions_file"])
        self.resume_db_path_var.set(APP_DEFAULTS["resume_db_file"])
        # If step 1 was completed, retain its output, otherwise clear
        self.jd_path_var.set(self.jd_file_path_from_step1 or "")
        self.status2_var.set("Fields reset.")

    def _select_directory(self, string_var):
        folder = filedialog.askdirectory(initialdir=os.path.dirname(string_var.get()))
        if folder: string_var.set(folder)

    def _select_file(self, string_var, title):
        file = filedialog.askopenfilename(title=title, initialdir=os.path.dirname(string_var.get()), filetypes=(("Markdown Files", "*.md"), ("Text Files", "*.txt"), ("All files", "*.*")))
        if file: string_var.set(file)

    def _populate_template_files(self):
        base_path = "templates"
        html_path = os.path.join(base_path, "html")
        try:
            os.makedirs(html_path, exist_ok=True)
            html_files = [f for f in os.listdir(html_path) if f.endswith(".html")]
            
            self.html_dropdown['values'] = html_files
            if APP_DEFAULTS["html_template"] in html_files:
                self.html_dropdown.set(APP_DEFAULTS["html_template"])
            elif html_files: self.html_dropdown.current(0)

        except Exception as e:
            messagebox.showerror("Template Error", f"Could not read from './{base_path}': {e}")
            
    def _get_jd_text(self, source):
        if source.strip().startswith(('http://', 'https://')):
            self.status1_var.set("Fetching job description from URL...")
            self.update_idletasks()
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                response = requests.get(source.strip(), headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                main_content = soup.find('main') or soup.find('body')
                return main_content.get_text(separator='\n', strip=True) if main_content else "Could not parse text."
            except requests.RequestException as e:
                messagebox.showerror("URL Error", f"Failed to fetch content from URL: {e}")
                return None
        return source

    def _sanitize_company_name(self, url):
        if not url: return "company"
        try:
            domain = url.split('/')[2]
            name = domain.replace('www.', '').split('.')[0]
            return re.sub(r'[^\w\-_]', '', name)
        except IndexError:
            return "company"

    def _process_step1(self):
        jd_source = self.jd_input.get("1.0", tk.END).strip()
        company_url, save_path = self.company_url_var.get().strip(), self.save_path_var.get().strip()
        html_file = self.html_file_var.get()

        if not all([jd_source, company_url, save_path, html_file]):
            messagebox.showwarning("Missing Information", "Please fill out all fields in Step 1.")
            return

        jd_text = self._get_jd_text(jd_source)
        if jd_text is None:
            self.status1_var.set("Error fetching URL. Please try again.")
            return

        folder_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._sanitize_company_name(company_url)}"
        
        try:
            new_dir_path = os.path.join(save_path, folder_name)
            os.makedirs(new_dir_path, exist_ok=True)
            self.jd_file_path_from_step1 = os.path.join(new_dir_path, "job_description.md")
            
            with open(self.jd_file_path_from_step1, 'w', encoding='utf-8') as f: f.write(jd_text)
            # shutil.copy2(os.path.join("templates/html", html_file), new_dir_path)
            
            self.status1_var.set(f"Success! Files saved. Proceeding to Step 2.")
            self.jd_path_var.set(self.jd_file_path_from_step1)
            self.notebook.select(self.step2_frame)

        except Exception as e:
            self.status1_var.set(f"An error occurred: {e}")
            messagebox.showerror("File Error", f"An error occurred while creating files: {e}")

    def _process_step2(self):
        ai_assistant = self.ai_var.get()
        instructions_file = self.instructions_path_var.get().strip()
        resume_db_file = self.resume_db_path_var.get().strip()
        jd_file = self.jd_path_var.get().strip()

        if not all([ai_assistant, instructions_file, resume_db_file, jd_file]):
            messagebox.showwarning("Missing Information", "Please select an AI and all three required files.")
            return

        try:
            save_folder = os.path.dirname(jd_file)
            if not os.path.isdir(save_folder):
                 messagebox.showerror("Invalid Path", "The directory for the Job Description file does not exist.")
                 return
            
            with open(instructions_file, 'r', encoding='utf-8') as f: instructions_text = f.read()
            with open(resume_db_file, 'r', encoding='utf-8') as f: resume_db_text = f.read()
            with open(jd_file, 'r', encoding='utf-8') as f: jd_text = f.read()

            final_prompt = (
                "--- TASK ---\n"
                "As described in the following system message, please review the job description, research the company, and create an optimized resume from the attached database file that is expertly tailored to the job description.\n"
                f"--- SYSTEM INSTRUCTIONS ---\n{instructions_text}\n --- END INSTRUCTIONS ---\n\n"
                f"--- JOB DESCRIPTION ---\n{jd_text}\n --- END JOB DESCRIPTION ---\n\n"
                f"--- COMPANY URL ---\n{self.company_url_var.get().strip()}\n\n"
                f"--- RESUME DATABASE ---\n{resume_db_text}\n --- END RESUME DATABASE ---\n\n"
            )
            
            pyperclip.copy(final_prompt)
            self.status2_var.set("Prompt copied to clipboard!")

            # --- Create the blank JSON file ---
            # json_filename = f"resume_{ai_assistant.lower()}.json"
            json_filename = "resume.json"
            json_filepath = os.path.join(save_folder, json_filename)
            if not os.path.exists(json_filepath):
                with open(json_filepath, 'w', encoding='utf-8') as f:
                    f.write('{}')

            # --- Create blank TXT files for cover letter and other questions ---
            cover_letter_filename = "cover_letter.txt"
            cover_letter_filepath = os.path.join(save_folder, cover_letter_filename)
            if not os.path.exists(cover_letter_filepath):
                with open(cover_letter_filepath, 'w', encoding='utf-8') as f:
                    f.write('No cover letter requested.')

            other_questions_filename = "other_questions.txt"
            other_questions_filepath = os.path.join(save_folder, other_questions_filename)
            if not os.path.exists(other_questions_filepath):
                with open(other_questions_filepath, 'w', encoding='utf-8') as f:
                    f.write('No other questions requested.')

            removed_from_json_filename = "removed_from_json.txt"
            removed_from_json_filename = os.path.join(save_folder, removed_from_json_filename)
            if not os.path.exists(removed_from_json_filename):
                with open(removed_from_json_filename, 'w', encoding='utf-8') as f:
                    f.write('CONTENT REMOVED FROM JSON DUE TO LENGTH LIMITS:\n\n')
            
            # --- Open AI website ---
            ai_urls = {"ChatGPT": "https://chat.openai.com/", "Claude": "https://claude.ai/", "Gemini": "https://gemini.google.com/"}
            target_url = ai_urls.get(ai_assistant, "https://www.google.com")            
            webbrowser.open_new_tab(target_url)

            # --- Create and open a VS Code workspace for an efficient workflow ---
            try:
                js_project_folder = os.path.abspath("templates/js")
                
                # Ensure the templates/js folder exists to avoid errors
                if not os.path.isdir(js_project_folder):
                    os.makedirs(js_project_folder)

                # Workspace configuration
                workspace_config = {
                    "folders": [
                        {"path": save_folder.replace("\\", "/")}, # Use forward slashes for JSON
                        {"path": js_project_folder.replace("\\", "/")}
                    ],
                    "settings": {
                        "terminal.integrated.cwd": js_project_folder.replace("\\", "/")
                    }
                }
                
                # Write the .code-workspace file
                company_name_for_file = os.path.basename(save_folder)
                workspace_filename = f"{company_name_for_file}.code-workspace"
                workspace_filepath = os.path.join(save_folder, workspace_filename)
                
                with open(workspace_filepath, 'w', encoding='utf-8') as f:
                    json.dump(workspace_config, f, indent=4)
                    
                # Open the workspace file in VS Code
                # Use shell=True for Windows compatibility to find 'code.cmd'
                subprocess.run(['code', workspace_filepath], check=True, shell=True if os.name == 'nt' else False)
                self.status2_var.set("Prompt copied! VS Code workspace opened.")

            except (FileNotFoundError, subprocess.CalledProcessError):
                # Fallback if VS Code is not found or fails to run
                self.status2_var.set("Prompt copied! VS Code not found, opening folder.")
                webbrowser.open(save_folder)

            # messagebox.showinfo(
            #     "Action Required",
            #     f"The full prompt has been copied to your clipboard!\n\n"
            #     f"{ai_assistant} has been opened in a new tab in your default browser.\n\n"
            #     "Please click inside the chat input box and paste (Ctrl+V or Cmd+V)."
            # )

        except FileNotFoundError as e:
            messagebox.showerror("File Not Found", f"Could not find a required file: {e.filename}")
            self.status2_var.set("Error: File not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status2_var.set(f"An error occurred: {e}")

if __name__ == "__main__":
    app = JobAppOrganizer()
    app.mainloop()

