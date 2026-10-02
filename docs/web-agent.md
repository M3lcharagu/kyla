# Kyla web agent

The web agent is an optional, local Playwright utility for deliberate browsing. It opens a **visible** browser by default and exposes a small set of explicit page actions. It does not run arbitrary page scripts, submit a login form automatically, defeat CAPTCHA/security challenges, or automate 2FA. Use it only on sites you are authorized to access; a browser page can still communicate with the site and any resources that site loads.

## Requirements and compatibility

- Python **3.9 or newer** is the intended baseline, consistent with the existing local HUD. The implementation uses only standard-library modules plus Playwright.
- Playwright is an optional dependency, not pinned in this repository. The commands below install the current release available to `pip`; Playwright's supported Python/platform matrix can change. This implementation has not been run against every OS/browser combination, so treat the compatibility list below as intended, not a CI-tested guarantee.
- Playwright supports Chromium, Firefox, and WebKit on its supported Windows, macOS, and Linux environments. Chromium is the default. Browser binaries are separate from the Python package and must be installed. Linux may also need OS libraries; see below.
- The REPL is headed and requires a desktop/display session. The API accepts `headless=True` for local non-interactive smoke tests only; that does not make manual login or 2FA suitable for headless use.

## Install

From the repository root, create and activate a virtual environment, then install Playwright and Chromium.

### macOS / Linux (bash or zsh)

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install playwright
python -m playwright install chromium
```

On Linux, if the browser reports missing system libraries, install the required OS packages (the command may need administrator privileges), then install the browser binary:

```sh
python -m playwright install --with-deps chromium
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install playwright
python -m playwright install chromium
```

If PowerShell blocks virtual-environment activation, follow your organization's policy for script execution or invoke `.venv\Scripts\python.exe` directly for the remaining commands. On macOS, allow the browser to launch if the OS prompts. Firefox/WebKit are optional; install their binaries with `python -m playwright install firefox webkit` before selecting them.

## Start the REPL

With the virtual environment active:

```sh
python -m agents.web_cli
```

The browser starts visibly. Type `help` in the `web>` prompt. For example, `open https://example.org`, `title`, `text`, `click "a"`, and `screenshot page.png`. Quote CSS selectors and values with spaces using shell-style quotes. The `fill` command is for non-secret form values; do not put passwords into command history or command arguments.

### User-directed sign-in and secrets

For a site where you are authorized to sign in, navigate there and inspect the page first. Use `credentials-fill "#username" "#password"`; the REPL asks for the username and masks password entry with Python's `getpass` where the terminal supports it. The helper only fills those two explicit fields. It does not click submit; inspect the visible page and submit yourself if appropriate. Passwords are not written to the repository, command history, or helper logs, though they necessarily exist temporarily in process memory and are sent to the page when you choose to fill them.

Alternatively, `agents.login_helpers.load_local_credentials()` can read a JSON file stored on your machine. Its default path is `~/.config/kyla/web-agent/credentials.json`; provide an explicit path to use another file. On POSIX, the helper rejects files with group/other permission bits; create a private file with mode `0600` (for example, `chmod 600 ~/.config/kyla/web-agent/credentials.json`). On Windows, review and restrict the file's ACL yourself. Do not put this file in the repository or sync it to a shared location. Prefer the interactive prompt when possible. The CLI intentionally does not accept credentials as flags or environment variables.

After you submit the form yourself, use `manual-2fa`. It pauses in the terminal while you complete the site's challenge in the visible browser and press Enter to acknowledge. Do not paste one-time codes into the REPL. No challenge is bypassed, automated, or hidden.

## API sketch

```python
from agents.web import BrowserAgent

with BrowserAgent() as browser:  # headed Chromium by default
    browser.goto("https://example.org")
    print(browser.title())
    print(browser.text("body"))
    browser.screenshot("page.png")
```

`BrowserAgent` also provides `click`, `fill`, `back`, `reload`, `current_url`, and `set_content` (useful for network-free tests). Navigation allows absolute HTTP/HTTPS URLs and `about:blank`; URLs containing embedded username/password are rejected. Calls are synchronous and use a 30-second default timeout.
