"""
Startup Banner Module
Generates a stunning graffiti-style banner using Rich and Pyfiglet.
"""
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich import box
import pyfiglet
import shutil

def print_banner():
    """Prints a 'shocking' startup banner."""
    console = Console()
    
    # 1. Generate Graffiti Text
    # Fonts to try: 'slant', 'graffiti', 'starwars', 'doom', 'ansi_shadow'
    # 'ansi_shadow' looks very professional and graffiti-like
    title_text = pyfiglet.figlet_format("UNIFIED BOT", font="ansi_shadow")
    
    # 2. visual breakdown
    # Create a gradient effect manually or use rich's style
    # We'll use a Panel to contain everything
    
    content = Text()
    
    # Title (Cyan/Magenta Gradient feel)
    content.append(title_text, style="bold cyan")
    content.append("\n")
    
    # Developer Credit (High contrast)
    dev_text = Text("⚡ DEVELOPED BY: PRANAY KUMAR ⚡", style="bold yellow on red blink")
    content.append(dev_text)
    content.append("\n\n")
    
    # Description
    desc = Text("The Ultimate Market Intelligence System", style="italic white")
    content.append(desc)
    content.append("\n")
    content.append("─" * 40, style="dim gray")
    content.append("\n")
    content.append("v2.0 • Production Hardened • 100x Efficient", style="bold green")
    
    # 3. Create the Panel
    # Calculate width to center it nicely
    width = shutil.get_terminal_size().columns
    panel_width = min(width - 4, 100) # Max 100 chars wide
    
    panel = Panel(
        Align.center(content),
        box=box.DOUBLE_EDGE,
        border_style="bright_magenta",
        title="[bold green] system_startup_sequence() [/bold green]",
        subtitle="[bold blue] 🚀 LAUNCHING [/bold blue]",
        width=panel_width,
        padding=(1, 2)
    )
    
    print("\n")
    console.print(panel)
    print("\n")

if __name__ == "__main__":
    print_banner()
