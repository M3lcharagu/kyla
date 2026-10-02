"""Interactive, headed browser REPL for deliberate user-directed browsing."""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import List

from agents.login_helpers import (
    fill_login_fields,
    prompt_credentials,
    wait_for_visible_2fa,
)
from agents.web import BrowserAgent


HELP = """Commands:
  open <http(s)-url>                 Navigate to a page
  url                                Show the current page URL
  title                              Show the current page title
  text [css-selector]                Read visible text (default: body)
  click <css-selector>               Click one element
  fill <css-selector> <value>        Fill a non-secret field
  credentials-fill <user> <password> Prompt locally, then fill selected login fields only
  manual-2fa                         Pause while you complete 2FA in the visible browser
  screenshot [path]                  Save a screenshot (default: web-agent.png)
  back                               Go back
  reload                             Reload the page
  help                               Show this help
  quit                               Close the browser and exit

Selectors are CSS selectors. Credentials are prompted (not command-line args),
never submitted automatically, and are not printed. Complete sign-in and 2FA
in the visible browser yourself. Only visit sites you trust.
"""


def _dispatch(agent: BrowserAgent, words: List[str]) -> bool:
    if not words:
        return True
    command, args = words[0].lower(), words[1:]

    if command in ("quit", "exit"):
        return False
    if command == "help":
        print(HELP)
    elif command == "open" and len(args) == 1:
        agent.goto(args[0])
        print("Page loaded.")
    elif command == "url" and not args:
        print(agent.current_url())
    elif command == "title" and not args:
        print(agent.title())
    elif command == "text" and len(args) <= 1:
        print(agent.text(args[0] if args else "body"))
    elif command == "click" and len(args) == 1:
        agent.click(args[0])
        print("Clicked.")
    elif command == "fill" and len(args) >= 2:
        agent.fill(args[0], " ".join(args[1:]))
        print("Filled.")
    elif command == "credentials-fill" and len(args) == 2:
        credentials = prompt_credentials()
        try:
            fill_login_fields(agent.page, args[0], args[1], credentials)
        except Exception:
            print("Could not fill the requested fields; credential values were withheld.", file=sys.stderr)
        else:
            print("Filled selected fields only. Review the page and submit manually if appropriate.")
        finally:
            del credentials
    elif command == "manual-2fa" and not args:
        wait_for_visible_2fa(agent.page)
        print("2FA checkpoint acknowledged.")
    elif command == "screenshot" and len(args) <= 1:
        path = args[0] if args else "web-agent.png"
        saved = agent.screenshot(path)
        print(f"Screenshot saved to {saved}.")
    elif command == "back" and not args:
        agent.back()
        print("Navigated back.")
    elif command == "reload" and not args:
        agent.reload()
        print("Page reloaded.")
    else:
        print("Invalid command or arguments. Type 'help'.", file=sys.stderr)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Visible, interactive Kyla browser agent")
    parser.add_argument(
        "--browser",
        choices=BrowserAgent._BROWSER_NAMES,
        default="chromium",
        help="Playwright browser engine (default: chromium)",
    )
    args = parser.parse_args()

    agent = BrowserAgent(browser=args.browser, headless=False)
    try:
        agent.start()
    except Exception as exc:
        print(f"Could not start browser: {exc}", file=sys.stderr)
        return 1

    print("Kyla web agent (visible browser). Type 'help' for commands; 'quit' to exit.")
    try:
        while True:
            try:
                line = input("web> ")
            except EOFError:
                break
            try:
                words = shlex.split(line)
                if not _dispatch(agent, words):
                    break
            except KeyboardInterrupt:
                print()
                break
            except Exception as exc:
                # CLI operations do not echo page content or any credential values.
                print(f"Command failed: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print()
    finally:
        agent.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
