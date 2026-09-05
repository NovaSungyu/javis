import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table
from rich import box

from config import GEMINI_API_KEY, DEFAULT_MODEL
from core.llm import JarvisLLM
from core.termux import TermuxBridge

console = Console()

def render_banner():
    banner_text = """
   ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
   ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
   ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
       [ Mobile Termux Operating Core ]
    """
    console.print(Panel(Text(banner_text, style="bold cyan"), box=box.ROUNDED, border_style="cyan"))

def show_system_status():
    table = Table(title="J.A.R.V.I.S. System Diagnostics", box=box.SIMPLE_HEAD, header_style="bold yellow")
    table.add_column("Subsystem", style="cyan")
    table.add_column("Status", style="green")

    # Termux API Check
    api_avail = TermuxBridge.is_termux_api_available()
    table.add_row("Termux Hardware API", "ONLINE" if api_avail else "OFFLINE (Mock Mode)")

    # Battery
    battery = TermuxBridge.get_battery_status()
    batt_str = f"{battery.get('percentage')}% ({battery.get('status')})"
    table.add_row("Device Battery", batt_str)

    # Wi-Fi
    wifi = TermuxBridge.get_wifi_info()
    wifi_str = f"{wifi.get('ssid')} ({wifi.get('ip')})"
    table.add_row("Network (Wi-Fi)", wifi_str)

    # LLM API
    has_key = bool(GEMINI_API_KEY or os.getenv("GEMINI_API_KEY"))
    table.add_row("LLM Engine", f"Gemini ({DEFAULT_MODEL})" if has_key else "API Key Missing")

    console.print(table)

def handsfree_voice_loop(jarvis: JarvisLLM):
    """Continuous hands-free voice loop mode: listens, acts, and responds aloud in a continuous cycle."""
    console.print(Panel("[bold green]🎙️ Hands-Free Voice Mode Activated![/bold green]\nSay 'exit', 'quit', or '종료' to return to terminal.", border_style="green"))
    if TermuxBridge.is_termux_api_available():
        TermuxBridge.speak("Hands free voice mode activated, Sir. I am listening.")

    while True:
        try:
            console.print("\n[bold green]🎤 Listening... (Speak your command)[/bold green]")
            spoken_text = TermuxBridge.speech_to_text()

            if not spoken_text:
                console.print("[dim yellow]No speech detected. Listening again...[/dim yellow]")
                time.sleep(1)
                continue

            console.print(f"[bold cyan]You (Voice):[/bold cyan] {spoken_text}")
            cmd = spoken_text.strip().lower()

            if cmd in ["exit", "quit", "stop", "종료", "그만", "꺼줘"]:
                farewell = "Exiting hands-free voice mode, Sir."
                console.print(f"[bold yellow]{farewell}[/bold yellow]")
                if TermuxBridge.is_termux_api_available():
                    TermuxBridge.speak(farewell)
                break

            with console.status("[bold bright_blue]J.A.R.V.I.S. processing...[/bold bright_blue]", spinner="dots"):
                response = jarvis.send_message(spoken_text)

            console.print(Panel(response, title="J.A.R.V.I.S.", title_align="left", border_style="bright_blue"))
            TermuxBridge.speak(response)

        except KeyboardInterrupt:
            console.print("\n[bold red]Hands-free mode stopped by user.[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]Voice Mode Error:[/bold red] {e}")
            break

def main():
    os.system("clear" if os.name != "nt" else "cls")
    render_banner()
    
    jarvis = JarvisLLM()
    auto_speak = False
    
    show_system_status()
    
    console.print("\n[bold yellow]System Initialized.[/bold yellow] Type [bold green]/help[/bold green] for command list.")
    console.print("[dim]Commands: /handsfree (continuous voice), /voice (one-shot voice), /speak (toggle TTS), /status, /exit[/dim]\n")

    if not jarvis.is_configured():
        console.print(
            "[bold red]![/bold red] [yellow]Notice:[/yellow] GEMINI_API_KEY environment variable is not set.\n"
            "Please add your key to [bold].env[/bold] file or set it using:\n"
            "[bold cyan]export GEMINI_API_KEY='your_api_key_here'[/bold cyan]\n"
        )

    # Check command-line argument for instant hands-free start (python main.py --voice)
    if len(sys.argv) > 1 and sys.argv[1] in ["--voice", "-v", "--handsfree"]:
        handsfree_voice_loop(jarvis)
        return

    # Startup Greeting
    greeting = "Good day, Sir. J.A.R.V.I.S. is online and ready for your command."
    console.print(Panel(greeting, title="J.A.R.V.I.S.", title_align="left", border_style="bright_blue"))
    if TermuxBridge.is_termux_api_available():
        TermuxBridge.speak("Good day Sir. JARVIS is online.")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            if not user_input.strip():
                continue

            cmd = user_input.strip().lower()

            if cmd in ["exit", "quit", "/exit", "/quit", "/q"]:
                farewell = "Shutting down J.A.R.V.I.S. core systems. Have a pleasant day, Sir."
                console.print(Panel(farewell, title="J.A.R.V.I.S.", border_style="red"))
                if auto_speak and TermuxBridge.is_termux_api_available():
                    TermuxBridge.speak(farewell)
                break

            elif cmd == "/help":
                console.print(
                    "[bold yellow]JARVIS Command Menu:[/bold yellow]\n"
                    " - [cyan]/handsfree[/cyan] : Continuous Hands-Free Voice Mode (Full automatic voice conversation loop)\n"
                    " - [cyan]/voice[/cyan]     : Record a single voice command\n"
                    " - [cyan]/speak[/cyan]     : Toggle automatically speaking responses via TTS\n"
                    " - [cyan]/status[/cyan]    : Display system diagnostics & battery status\n"
                    " - [cyan]/clear[/cyan]     : Clear terminal screen\n"
                    " - [cyan]/exit[/cyan]      : Power down JARVIS\n"
                )
                continue

            elif cmd in ["/handsfree", "/hf", "/hands-free"]:
                handsfree_voice_loop(jarvis)
                continue

            elif cmd == "/speak":
                auto_speak = not auto_speak
                status = "ENABLED" if auto_speak else "DISABLED"
                console.print(f"[bold yellow]TTS Speech Output:[/bold yellow] [bold green]{status}[/bold green]")
                continue

            elif cmd == "/status":
                show_system_status()
                continue

            elif cmd == "/clear":
                os.system("clear" if os.name != "nt" else "cls")
                render_banner()
                continue

            elif cmd == "/voice":
                console.print("[bold green]Listening... Please speak into your phone microphone.[/bold green]")
                spoken_text = TermuxBridge.speech_to_text()
                if spoken_text:
                    console.print(f"[bold cyan]You (Voice):[/bold cyan] {spoken_text}")
                    user_input = spoken_text
                else:
                    console.print("[bold red]Could not recognize speech or speech input cancelled.[/bold red]")
                    continue

            # Process with LLM
            with console.status("[bold bright_blue]J.A.R.V.I.S. processing...[/bold bright_blue]", spinner="dots"):
                response = jarvis.send_message(user_input)

            console.print(Panel(response, title="J.A.R.V.I.S.", title_align="left", border_style="bright_blue"))

            if auto_speak:
                TermuxBridge.speak(response)

        except KeyboardInterrupt:
            console.print("\n[bold red]Interrupted. Type /exit to terminate.[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
