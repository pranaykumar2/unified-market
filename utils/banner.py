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
    
    # Detect terminal width for responsive design
    terminal_width = shutil.get_terminal_size().columns
    
    # 1. Generate Graffiti Text (responsive to screen size)
    # For small screens (mobile/Termux): use compact fonts
    # For large screens (PC): use bold fonts
    # Fonts to try: 'slant', 'graffiti', 'starwars', 'doom', 'ansi_shadow'
    if terminal_width < 80:
        # Small screen (Android/Termux) - use compact font
        title_text = pyfiglet.figlet_format("UNIFIED BOT", font="small")
    elif terminal_width < 120:
        # Medium screen - use standard font
        title_text = pyfiglet.figlet_format("UNIFIED BOT", font="standard")
    else:
        # Large screen (PC) - use dramatic font
        title_text = pyfiglet.figlet_format("UNIFIED BOT", font="doom")
    
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
    desc = Text("The Market News Scraper System", style="italic white")
    content.append(desc)
    content.append("\n")
    content.append("─" * 30, style="dim gray")
    content.append("\n")
    content.append("v2.0 • Unified • Capital Market + Money Control + Trendlyne", style="bold green")
    
    # 3. Create the Panel
    # Calculate width to center it nicely (using already detected terminal_width)
    panel_width = min(terminal_width - 4, 100) # Max 100 chars wide
    
    panel = Panel(
        Align.center(content),
        box=box.DOUBLE_EDGE,
        border_style="bright_magenta",
        title="[bold green] Balaji Equities Ltd [/bold green]",
        subtitle="[bold blue] 🚀 LAUNCHING [/bold blue]",
        width=panel_width,
        padding=(1, 2)
    )
    
    print("\n")
    console.print(panel)
    print("\n")

if __name__ == "__main__":
    print_banner()
