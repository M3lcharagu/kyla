#!/usr/bin/env python3
"""Local-only simulated KYLA HUD server. Python 3.9+, standard library only."""

import json
import os
import platform
import random
import secrets
import subprocess
import time
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


TOKEN = secrets.token_urlsafe(32)
HTML_FILE = Path(__file__).resolve().with_name("index.html")

CORE_AGENTS = [
    "Intake", "Report", "Ops", "Proposal", "Automation Engineer",
    "RAG Architect", "RAG Engineer", "Web Dev", "QA", "Brief",
    "Writer", "Editor", "Signal", "Risk", "Support",
]

SANDBOX_AGENTS = [
    {"name": "claude", "codename": "Oracle of the Veil", "role": "Reasoning, research synthesis, and careful drafts."},
    {"name": "codex", "codename": "Scribe of Iron", "role": "Code generation, implementation, and repair."},
    {"name": "copilot", "codename": "Twin Lantern", "role": "Pair-programming support and in-editor suggestions."},
    {"name": "cursor", "codename": "Needle of Daedalus", "role": "Repository navigation and focused refactoring."},
    {"name": "docker-agent", "codename": "Golem of Clay", "role": "Isolated sandbox jobs and repeatable build tasks."},
    {"name": "droid", "codename": "Mercury's Courier", "role": "Small delegated tasks and task dispatch."},
    {"name": "shell", "codename": "The Black Key", "role": "Local shell operations and system-level glue."},
]

WORKFLOWS = [
    {"id": "pride", "vice": "Pride", "virtue": "Humility", "name": "Studio Mirror", "vice_job": "Shape a bold website or post.", "virtue_job": "Check quality and delivery evidence."},
    {"id": "greed", "vice": "Greed", "virtue": "Generosity", "name": "Quant Discipline", "vice_job": "Follow the take-profit plan; do not chase.", "virtue_job": "Protect capital and avoid forcing trades."},
    {"id": "lust", "vice": "Lust", "virtue": "Chastity", "name": "Moji Moji", "vice_job": "Turn 3 references into tiered video concepts.", "virtue_job": "Focus the production pipeline on a 20-video batch."},
    {"id": "envy", "vice": "Envy", "virtue": "Kindness", "name": "Signal Garden", "vice_job": "Scan TikTok, Discord, web, and GitHub for patterns.", "virtue_job": "Turn useful findings into original work."},
    {"id": "gluttony", "vice": "Gluttony", "virtue": "Temperance", "name": "CSC Study", "vice_job": "Gather course material and questions.", "virtue_job": "Narrow the pile into a focused study plan."},
    {"id": "wrath", "vice": "Wrath", "virtue": "Patience", "name": "R13 Release Gate", "vice_job": "Identify delivery, security, and compliance risks.", "virtue_job": "Run the reviews before SOPHIA and Mel approve."},
    {"id": "sloth", "vice": "Sloth", "virtue": "Diligence", "name": "Weekly Loophole Sweep", "vice_job": "Surface neglected risks and unfinished checks.", "virtue_job": "Review docs/LOOPHOLES.md every week."},
]

SIGNALS = [
    "BTC/USD | WATCH | DEMO ticker; verify risk, no live price",
    "ETH/USD | WAIT | DEMO ticker; protect the downside first",
    "BTC/USD | NO TRADE | DEMO ticker; discipline over action",
    "XAU/USD | WATCH | DEMO ticker; not a trading recommendation",
]


def read_ram_gb():
    """Read physical memory on macOS using its built-in sysctl command."""
    if platform.system() != "Darwin":
        return None
    try:
        result = subprocess.run(
            ["/usr/sbin/sysctl", "-n", "hw.memsize"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1,
            check=True,
        )
        return round(int(result.stdout.strip()) / (1024 ** 3), 1)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def hardware_state():
    try:
        load_1m = round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        load_1m = None
    mac_version = platform.mac_ver()[0]
    os_name = "macOS " + mac_version if mac_version else platform.system()
    return {
        "target": "2012 MacBook Pro / 13-inch / i5",
        "detected_os": os_name,
        "cpu": platform.processor() or platform.machine() or "unknown",
        "logical_cores": os.cpu_count(),
        "load_1m": load_1m,
        "ram_gb": read_ram_gb(),
        "agent_note": "Docker sandbox agents are CPU-throttled by design.",
    }


def build_state():
    """Return simulated activity and local host readings; no agents are queried."""
    tick = int(time.monotonic() // 5)
    rng = random.Random(tick)
    all_agents = (
        [(name, "ROSTER") for name in CORE_AGENTS]
        + [(item["name"], "SANDBOX") for item in SANDBOX_AGENTS]
    )
    order = list(range(len(all_agents)))
    rng.shuffle(order)
    reporting = set(order[:2])
    active = set(order[2:7])
    agents = []
    for index, (name, group) in enumerate(all_agents):
        if index in reporting:
            status, detail = "REPORT", "just reported"
        elif index in active:
            status, detail = "ACTIVE", "working"
        else:
            status, detail = "IDLE", "standby"
        agents.append({"name": name, "group": group, "status": status, "detail": detail})
    workflows = []
    active_workflows = set(rng.sample(range(len(WORKFLOWS)), 3))
    for index, item in enumerate(WORKFLOWS):
        workflows.append(dict(item, active=index in active_workflows))
    progress = 35 + ((tick * 7) % 60)
    done = (progress * 20) // 100
    return {
        "demo": True,
        "agents": agents,
        "sandbox": [
            dict(item, status=next(
                (agent["status"] for agent in agents if agent["name"] == item["name"]),
                "IDLE",
            ))
            for item in SANDBOX_AGENTS
        ],
        "workflows": workflows,
        "loopholes": [
            {"priority": "P0", "text": "DEMO: no live sweep performed; verify critical risks."},
            {"priority": "P1", "text": "Review docs/LOOPHOLES.md in the weekly sweep."},
            {"priority": "P2", "text": "Check alt text and mobile layout on the next site."},
        ],
        "farm": {
            "name": "Moji Moji video farm", "done": done, "total": 20,
            "progress": progress, "status": "SIMULATED RUN",
            "input": "3 refs -> tiered concepts -> 20 videos",
        },
        "signal": SIGNALS[tick % len(SIGNALS)],
        "hardware": hardware_state(),
        "quant": {
            "strategy_target": 50,
            "positive_backtest_goal": 150,
            "sequence_setups": ["SSS", "BBB", "BBS", "SSB"],
            "risk_cycle": "2:1 risk-tiered cycle",
            "scalp_limit": "45 minutes maximum",
            "timeframes": ["30s", "1m", "5m", "15m", "30m", "1h"],
            "mt5_scope": "Previous-day and weekly highs/lows; Asian session; valley gaps.",
            "notice": "Targets and simulated ticker only; no live prices or results.",
        },
        "gate": {
            "name": "R13", "checks": ["QA", "Security", "Legal", "License"],
            "passed": [], "status": "LOCKED - demo checks incomplete",
            "next": ["SOPHIA review", "Mel approval", "Publish"],
        },
        "router": [
            {"name": "Tier 1", "title": "Instant rules", "detail": "Local rules and simple deterministic tasks"},
            {"name": "Tier 2", "title": "Fast model", "detail": "Quick classification, drafting, and response"},
            {"name": "Tier 3", "title": "Deeper agent work", "detail": "Crew, tools, and long-running tasks"},
        ],
        "frameworks": [
            "CrewAI / MetaGPT-style crews",
            "AutoGPT-style long-running agents",
            "AgentGPT-style one-off agents",
            "SuperAGI-style shared tooling",
            "n8n automation glue",
        ],
        "sources": [
            "TikTok", "Discord", "Web browser brain",
            "GitHub: M3lcharagu/kyla-quant", "GitHub: kyla",
        ],
        "publishing": ["Gumroad", "Shopify"],
        "life_goals": [
            "Jan 3: Mazda CX-3 + Embu crib + 50k KSH",
            "3 websites per week at 9k KSH each",
            "Trading discipline and CSC course progress",
            "Celine",
        ],
    }


class KylaHandler(BaseHTTPRequestHandler):
    server_version = "KYLA-HUD/2.0"

    def log_message(self, format_string, *args):
        print("[KYLA] local request")

    def is_authorized(self):
        parsed = urlparse(self.path)
        query_token = parse_qs(parsed.query).get("token", [""])[0]
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            cookie = SimpleCookie()
        morsel = cookie.get("kyla_token")
        cookie_token = morsel.value if morsel else ""
        header_token = self.headers.get("X-Kyla-Token", "")
        return any(
            candidate and secrets.compare_digest(candidate, TOKEN)
            for candidate in (query_token, cookie_token, header_token)
        )

    def send_bytes(self, status, body, content_type, set_cookie=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; connect-src 'self'; "
            "img-src 'self' data:; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'",
        )
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(body)

    def send_error_text(self, status, message):
        self.send_bytes(status, message.encode("ascii"), "text/plain; charset=utf-8")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            if not self.is_authorized():
                self.send_error_text(403, "Access denied. Restart server.py and use its printed URL.")
                return
            try:
                page = HTML_FILE.read_bytes()
            except OSError:
                self.send_error_text(500, "Could not read index.html. Keep it beside server.py.")
                return
            query_token = parse_qs(parsed.query).get("token", [""])[0]
            cookie_header = None
            if query_token and secrets.compare_digest(query_token, TOKEN):
                cookie_header = (
                    "kyla_token={}; HttpOnly; SameSite=Strict; "
                    "Path=/; Max-Age=28800"
                ).format(TOKEN)
            self.send_bytes(200, page, "text/html; charset=utf-8", set_cookie=cookie_header)
            return
        if parsed.path == "/api/state":
            if not self.is_authorized():
                self.send_error_text(401, "Unauthorized")
                return
            payload = json.dumps(build_state()).encode("utf-8")
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        self.send_error_text(404, "Not found")

    def do_HEAD(self):
        self.send_error_text(405, "Method not allowed")


def main():
    if not HTML_FILE.is_file():
        raise SystemExit("Missing index.html. Put it beside server.py.")
    server = ThreadingHTTPServer(("127.0.0.1", 0), KylaHandler)
    port = server.server_address[1]
    url = "http://127.0.0.1:{}/?token={}".format(port, TOKEN)
    print("KYLA HUD is local-only and uses simulated agent and market data.")
    print("Open this fresh URL in your browser:")
    print(url)
    print("Keep the URL private. Press Ctrl-C here to stop the HUD.")
    try:
        webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKYLA HUD stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
