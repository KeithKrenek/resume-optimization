"""
State Manager for Multi-Agent Resume Pipeline
Handles saving/loading intermediate outputs at each stage
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Dict
from rich.console import Console

from schemas import (
    PipelineState,
    JobAnalysis,
    ContentSelection,
    ResumeDraft,
    ValidationResult
)

console = Console()


class StateManager:
    """Manages pipeline state and intermediate outputs"""
    
    def __init__(self, job_folder: str):
        """
        Initialize state manager
        
        Args:
            job_folder: Path to job application folder
        """
        self.job_folder = job_folder
        self.state_file = os.path.join(job_folder, "pipeline_state.json")
        self.outputs_dir = os.path.join(job_folder, "agent_outputs")
        
        # Create outputs directory
        os.makedirs(self.outputs_dir, exist_ok=True)
        
        # Initialize or load state
        self.state = self._load_or_create_state()
    
    def _load_or_create_state(self) -> PipelineState:
        """Load existing state or create new one"""
        if os.path.exists(self.state_file):
            console.print(f"[cyan]Loading existing pipeline state...[/cyan]")
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return PipelineState(**data)
        else:
            console.print(f"[cyan]Creating new pipeline state...[/cyan]")
            # Extract company and job title from folder name
            folder_name = os.path.basename(self.job_folder)
            parts = folder_name.split('_')
            
            return PipelineState(
                job_folder=self.job_folder,
                company_name=parts[1] if len(parts) > 1 else "Unknown",
                job_title='_'.join(parts[2:]) if len(parts) > 2 else "Unknown",
                started_at=datetime.now().isoformat(),
                current_stage="initialized"
            )
    
    def save_state(self) -> None:
        """Persist current state to disk"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state.model_dump(), f, indent=2)
        
        console.print(f"[dim]State saved: {os.path.basename(self.state_file)}[/dim]")
    
    def save_agent_output(
        self,
        agent_name: str,
        output_data: Any,
        stage: str
    ) -> str:
        """
        Save agent output to dedicated file
        
        Args:
            agent_name: Name of agent (e.g., "job_analyzer")
            output_data: Agent's output (Pydantic model or dict)
            stage: Pipeline stage name
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{agent_name}.json"
        filepath = os.path.join(self.outputs_dir, filename)
        
        # Convert Pydantic models to dict
        if hasattr(output_data, 'model_dump'):
            data = output_data.model_dump()
        else:
            data = output_data
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        console.print(f"[green]✓[/green] Saved {agent_name} output: {filename}")
        
        # Update state
        self.state.current_stage = stage
        if stage not in self.state.completed_stages:
            self.state.completed_stages.append(stage)
        
        self.save_state()
        
        return filepath
    
    def load_agent_output(self, agent_name: str) -> Optional[Dict]:
        """Load most recent output from specific agent"""
        files = [f for f in os.listdir(self.outputs_dir) 
                 if f.endswith(f"{agent_name}.json")]
        
        if not files:
            return None
        
        # Get most recent
        files.sort(reverse=True)
        filepath = os.path.join(self.outputs_dir, files[0])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def set_job_analysis(self, analysis: JobAnalysis) -> None:
        """Store job analysis in state"""
        self.state.job_analysis = analysis
        self.save_agent_output("job_analyzer", analysis, "job_analysis_complete")
    
    def set_content_selection(self, selection: ContentSelection) -> None:
        """Store content selection in state"""
        self.state.content_selection = selection
        self.save_agent_output("content_selector", selection, "content_selection_complete")
    
    def set_resume_draft(self, draft: ResumeDraft) -> None:
        """Store resume draft in state (future)"""
        self.state.resume_draft = draft
        self.save_agent_output("resume_drafter", draft, "draft_complete")
    
    def set_validation_result(self, result: ValidationResult) -> None:
        """Store validation result in state"""
        self.state.validation_result = result
        self.save_agent_output("validator", result, "validation_complete")
    
    def set_edited_resume(self, draft: ResumeDraft) -> None:
        """Store edited resume in state (Agent 5 output)"""
        self.state.edited_resume = draft
        self.save_agent_output("voice_style_editor", draft, "style_editing_complete")
    
    def set_qa_report(self, report) -> None:
        """Store QA report in state (Agent 6 output)"""
        self.state.qa_report = report
        self.save_agent_output("final_qa", report, "qa_complete")
    
    def add_error(self, error: str) -> None:
        """Add error to state"""
        self.state.errors.append(error)
        self.save_state()
        console.print(f"[red]Error logged: {error}[/red]")
    
    def mark_completed(self) -> None:
        """Mark pipeline as completed"""
        self.state.current_stage = "completed"
        self.state.completed_at = datetime.now().isoformat()
        self.save_state()
    
    def get_summary(self) -> str:
        """Get human-readable state summary"""
        lines = [
            f"\n[bold cyan]Pipeline State Summary[/bold cyan]",
            f"Job: {self.state.company_name} - {self.state.job_title}",
            f"Current Stage: {self.state.current_stage}",
            f"Completed Stages: {', '.join(self.state.completed_stages)}",
        ]
        
        if self.state.errors:
            lines.append(f"[red]Errors: {len(self.state.errors)}[/red]")
        
        return "\n".join(lines)
    
    def can_skip_stage(self, stage: str) -> bool:
        """Check if stage can be skipped (already completed)"""
        return stage in self.state.completed_stages
    
    def get_outputs_directory(self) -> str:
        """Get path to outputs directory"""
        return self.outputs_dir
