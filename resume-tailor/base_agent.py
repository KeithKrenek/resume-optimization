"""
Base Agent Class
Abstract base for all specialized agents in the pipeline
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str,
        agent_name: str,
        agent_description: str
    ):
        """
        Initialize base agent
        
        Args:
            client: Anthropic API client
            model: Model name to use
            agent_name: Name of this agent
            agent_description: What this agent does
        """
        self.client = client
        self.model = model
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.console = console
    
    @abstractmethod
    def build_prompt(self, **kwargs) -> str:
        """
        Build the prompt for this agent
        Must be implemented by each agent
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: str) -> Any:
        """
        Parse the agent's response into structured output
        Must be implemented by each agent
        """
        pass
    
    def execute(self, **kwargs) -> Any:
        """
        Execute the agent's task
        
        Args:
            **kwargs: Agent-specific inputs
            
        Returns:
            Parsed structured output
        """
        # Show agent header
        self.console.print(f"\n[bold cyan]{'='*70}[/bold cyan]")
        self.console.print(Panel.fit(
            f"[bold white]{self.agent_name}[/bold white]\n"
            f"[dim]{self.agent_description}[/dim]",
            border_style="cyan"
        ))
        
        # Build prompt
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Building prompt...", total=None)
            prompt = self.build_prompt(**kwargs)
            progress.update(task, completed=True)
            
            # Show prompt stats
            prompt_chars = len(prompt)
            prompt_tokens_est = prompt_chars // 4  # Rough estimate
            self.console.print(f"[dim]Prompt: {prompt_chars:,} chars (~{prompt_tokens_est:,} tokens)[/dim]")
            
            # Call API
            progress.add_task("[cyan]Calling Claude API...", total=None)
            response = self._call_api(prompt)
            progress.update(task, completed=True)
            
            # Parse response
            progress.add_task("[cyan]Parsing response...", total=None)
            result = self.parse_response(response)
            progress.update(task, completed=True)
        
        self.console.print(f"[green]✓ {self.agent_name} completed successfully[/green]")
        
        return result
    
    def _call_api(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Anthropic API with retries
        
        Args:
            prompt: Prompt to send
            max_retries: Number of retries on failure
            
        Returns:
            Response text
        """
        for attempt in range(max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=16000,
                    temperature=0.2,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                # Extract text from response
                response_text = ""
                for block in message.content:
                    if hasattr(block, 'text'):
                        response_text += block.text
                
                # Show response stats
                response_chars = len(response_text)
                response_tokens_est = response_chars // 4
                self.console.print(f"[dim]Response: {response_chars:,} chars (~{response_tokens_est:,} tokens)[/dim]")
                
                return response_text
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.console.print(f"[yellow]Retry {attempt + 1}/{max_retries} after error: {e}[/yellow]")
                else:
                    self.console.print(f"[red]API call failed after {max_retries} attempts[/red]")
                    raise
        
        return ""
    
    def extract_json_from_response(self, text: str) -> Optional[str]:
        """Extract JSON from Claude's response (handles markdown code blocks)"""
        import re
        
        # Try markdown code blocks first
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            return match.group(1)
        
        # Try raw JSON
        json_pattern2 = r'(\{.*\})'
        match2 = re.search(json_pattern2, text, re.DOTALL)
        
        if match2:
            return match2.group(1)
        
        return None
    
    def show_summary(self, summary_data: Dict[str, Any]) -> None:
        """Display agent output summary"""
        self.console.print(f"\n[bold cyan]{self.agent_name} Summary:[/bold cyan]")
        for key, value in summary_data.items():
            if isinstance(value, list):
                self.console.print(f"  {key}: {len(value)} items")
            elif isinstance(value, dict):
                self.console.print(f"  {key}: {len(value)} entries")
            else:
                self.console.print(f"  {key}: {value}")
