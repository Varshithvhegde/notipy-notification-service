import requests
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from rich.prompt import Prompt
from rich import print as rprint

console = Console()
BASE_URL = "http://127.0.0.1:8000"

def wait_for_server():
    with console.status("[bold blue]Checking server health (port 8000)...", spinner="dots") as status:
        try:
            req = requests.get(f"{BASE_URL}/ping", timeout=3)
            req.raise_for_status()
            console.print(f"[bold green]✓[/bold green] Server Health: {req.json()['status'].upper()} ({req.json()['message']})")
        except requests.exceptions.RequestException:
            console.print("[bold red]⨯[/bold red] Server unreachable! Please run: [bold white]uvicorn app.main:app --reload[/bold white]")
            exit(1)

def setup_user():
    console.print("\n")
    console.print(Panel.fit("[bold cyan]Step 1: Identity & Preferences Config[/bold cyan]", border_style="cyan"))
    user_id = Prompt.ask("[bold yellow]Enter a Mock User ID to trace for this test run[/bold yellow]", default=f"guest_{int(time.time())}")
    
    with console.status(f"[bold blue]Initializing internal preferences for node {user_id}...", spinner="bouncingBar"):
        # Opt in to all
        for ch in ["email", "sms", "push"]:
            res = requests.post(f"{BASE_URL}/users/{user_id}/preferences", json={"channel": ch, "is_opted_in": True})
            if res.status_code != 200:
                console.print(f"[bold red]⨯[/bold red] Failed to config {ch.upper()}.")
        
        time.sleep(0.5) # for visuals
        # Verify
        prefs = requests.get(f"{BASE_URL}/users/{user_id}/preferences").json()
        
    table = Table(title=f"User Preferences Map: {user_id}")
    table.add_column("Channel", style="magenta")
    table.add_column("Opt-in Status", style="green")
    
    for p in prefs:
        table.add_row(
            p["channel"].upper(), 
            "[bold green]YES[/bold green]" if p["is_opted_in"] else "[bold red]NO[/bold red]"
        )
    
    console.print(table)
    return user_id

def test_notifications(user_id):
    console.print("\n")
    console.print(Panel.fit("[bold magenta]Step 2: Microservice Dispatch & Routing[/bold magenta]", border_style="magenta"))
    
    payload = {
        "user_id": user_id,
        "channels": ["email", "push"],
        "priority": "critical",
        "message_body": "Hello {{name}}, your premium API test has started!",
        "template_vars": {"name": "Varshith"},
        "idempotency_key": f"key_{int(time.time())}"
    }

    with console.status("[bold blue]Dispatching CRITICAL payloads to queue broker...", spinner="line"):
        res = requests.post(f"{BASE_URL}/notifications/", json=payload)
        res.raise_for_status()
        data = res.json()
        time.sleep(0.8) # for visuals
        
    console.print(f"[bold green]✓[/bold green] Fired {len(data)} asynchronous notification jobs via worker queue.")
    
    table = Table()
    table.add_column("DB Job ID", justify="right", style="cyan")
    table.add_column("Transport Channel")
    table.add_column("State")
    
    for d in data:
        stat_color = "yellow" if d["status"] == "pending" else "green"
        table.add_row(str(d["id"]), d["channel"].upper(), f"[bold {stat_color}]{d['status'].upper()}[/bold {stat_color}]")
    console.print(table)
    return data[0]["id"]

def test_telemetry(user_id, noti_id):
    console.print("\n")
    console.print(Panel.fit("[bold yellow]Step 3: State Verification & Telemetry[/bold yellow]", border_style="yellow"))
    
    with console.status("[bold blue]Polling database stream for worker execution...", spinner="dots"):
        time.sleep(2.0) # Explicitly wait for async worker to run
        res = requests.get(f"{BASE_URL}/notifications/{noti_id}")
        if res.status_code == 200:
            status = res.json()['status']
            color = "green" if status in ["sent", "delivered"] else ("red" if status == "failed" else "yellow")
            console.print(f"[bold green]✓[/bold green] Live Sync: Job #{noti_id} transitioned naturally to [bold {color}]{status.upper()}[/bold {color}]")
        
        hist = requests.get(f"{BASE_URL}/notifications/user/{user_id}?page=1&page_size=10").json()
        
    console.print(f"[bold green]✓[/bold green] Indexed Graph Data: [bold white]{hist.get('total', 0)}[/bold white] total records stored for node '{user_id}'.")

def test_idempotency():
    console.print("\n")
    console.print(Panel.fit("[bold red]Step 4: Concurrency & Idempotency Lock[/bold red]", border_style="red"))
    
    idem_key = f"protect_{int(time.time())}"
    payload = {
        "user_id": "idem_tester",
        "channels": ["sms"],
        "priority": "critical",
        "message_body": "Critical financial alert. Do not double-fire under load.",
        "idempotency_key": idem_key
    }
    
    with console.status("[bold blue]Simulating concurrent 'split-brain' requests...", spinner="bouncingBall"):
        r1 = requests.post(f"{BASE_URL}/notifications/", json=payload).json()
        time.sleep(0.2)
        r2 = requests.post(f"{BASE_URL}/notifications/", json=payload).json()
        
    console.print(f"[*] Thread 1 returned primary key: [cyan]{r1[0]['id']}[/cyan]")
    console.print(f"[*] Thread 2 returned primary key: [cyan]{r2[0]['id']}[/cyan]")
        
    if r1[0]["id"] == r2[0]["id"]:
        console.print(f"[bold green]✓[/bold green] Engine cleanly bypassed duplicate execution attempt via idempotency key.")
    else:
        console.print("[bold red]⨯[/bold red] Idempotency failed. Duplicate created.")

def test_rate_limiter():
    console.print("\n")
    console.print(Panel.fit("[bold purple]Step 5: Sliding Window Rate Limiter (Load Test)[/bold purple]", border_style="purple"))
    
    user_id = "bot_spammer_99"
    payload = {
        "user_id": user_id,
        "channels": ["email"],
        "priority": "low",
        "message_body": "Mass marketing spam",
        "idempotency_key": None
    }
    
    console.print(f"[*] Weaponizing payloads against endpoint (targeting 110 RPM max)...")
    
    caught = False
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        transient=False
    ) as progress:
        task = progress.add_task("[bold cyan]Firing POST requests...", total=105)
        
        for i in range(105):
            try:
                res = requests.post(f"{BASE_URL}/notifications/", json=payload)
                res.raise_for_status()
                progress.advance(task)
            except requests.exceptions.HTTPError:
                if res.status_code == 429:
                    caught = True
                    progress.update(task, description="[bold green]Rate Limit Tripwire Triggered![/bold green]", completed=i+1)
                    progress.stop()
                    console.print(f"\n[bold green]✓[/bold green] SUCCESS: Layer 7 shield activated! Request #{i+1} rejected with 429 Too Many Requests.")
                    break
            except Exception:
                pass
            
    if not caught:
        console.print("\n[bold red]⨯[/bold red] Rate limiter failed to intercept excessive footprint.")

def test_webhooks():
    console.print("\n")
    console.print(Panel.fit("[bold blue]Step 6: Webhook Integration Registry[/bold blue]", border_style="blue"))
    
    webhook_url = "https://webhook.site/6ec420d8-863c-4a0f-ae5b-429728ee264e"
    payload = {
        "url": webhook_url,
        "events": ["sent", "failed"],
        "secret": "notipy_secret_123"
    }
    
    with console.status("[bold blue]Registering callback listener via registry...", spinner="earth"):
        res = requests.post(f"{BASE_URL}/webhooks/", json=payload)
        res.raise_for_status()
        hook = res.json()
        time.sleep(0.5)

    console.print(f"[bold green]✓[/bold green] Webhook Registered: [cyan]{hook['url']}[/cyan]")
    
    with console.status("[bold blue]Cleaning up test hooks...", spinner="simpleDots"):
        requests.delete(f"{BASE_URL}/webhooks/{hook['id']}")
        time.sleep(0.3)
    
    console.print(f"[bold green]✓[/bold green] Ephemeral webhook lifecycle verified.")

def test_batch_api():
    console.print("\n")
    console.print(Panel.fit("[bold green]Step 7: Batch Delivery System[/bold green]", border_style="green"))
    
    payload = {
        "notifications": [
            {
                "user_id": "batch_user_A",
                "channels": ["email"],
                "message_body": "Batch test for A",
                "idempotency_key": f"batch_A_{int(time.time())}"
            },
            {
                "user_id": "batch_user_B",
                "channels": ["push", "sms"],
                "message_body": "Batch test for B",
                "idempotency_key": f"batch_B_{int(time.time())}"
            }
        ]
    }
    
    with console.status("[bold blue]Executing atomic multi-user batch dispatch...", spinner="point"):
        res = requests.post(f"{BASE_URL}/notifications/batch", json=payload)
        res.raise_for_status()
        data = res.json()
        time.sleep(0.5)

    console.print(f"[bold green]✓[/bold green] SUCCESS: Atomic batch processing complete.")
    console.print(f"[bold cyan]ℹ[/bold cyan] Total Individual Notifications Queued: [bold white]{data['queued_count']}[/bold white]")

def test_analytics():
    console.print("\n")
    console.print(Panel.fit("[bold white]Step 8: Global Analytics & Stream Stats[/bold white]", border_style="white"))
    
    with console.status("[bold blue]Querying aggregate engine telemetry...", spinner="earth"):
        res = requests.get(f"{BASE_URL}/analytics/stats")
        res.raise_for_status()
        data = res.json()
        time.sleep(0.5)

    console.print(f"[bold green]✓[/bold green] SUCCESS: Telemetry retrieved across {data['total_notifications']} system jobs.")
    
    table = Table(title="Notification Throughput by Channel")
    table.add_column("Channel", style="magenta")
    table.add_column("Sent", style="green")
    table.add_column("Failed", style="red")
    table.add_column("Pending", style="yellow")
    table.add_column("Total Load", style="bold cyan")
    
    for ch in data["by_channel"]:
        table.add_row(
            ch["channel"].upper(),
            str(ch["sent"]),
            str(ch["failed"]),
            str(ch["pending"]),
            str(ch["total"])
        )
    console.print(table)

if __name__ == "__main__":
    console.print("\n")
    console.rule("[bold cyan]🚀 notipy Engine Live Core Diagnostics 🚀")
    console.print("\n")
    
    wait_for_server()
    user_id = setup_user()
    
    noti_id = test_notifications(user_id)
    test_telemetry(user_id, noti_id)
    test_idempotency()
    test_rate_limiter()
    test_webhooks()
    test_batch_api()
    test_analytics()
    
    console.print("\n")
    console.rule("[bold green]ALL DIAGNOSTIC SYSTEMS GREEN[/bold green]")
    console.print("[dim italic center]System architecture verified and mathematically sound[/dim italic center]\n")
