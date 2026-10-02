# Web agent smoke tests

These are the two smoke tests for the optional browser agent. They use only local markup and dummy test data; neither test visits a website, reads real credentials, or performs a login. Run them from the repository root with the virtual environment activated. Test 2 requires the Playwright package and installed Chromium; it runs headlessly only to verify local rendering.

## Smoke test 1: syntax, imports, and credential redaction

```sh
python -m compileall -q agents
python -c "from agents.web import BrowserAgent; from agents.login_helpers import Credentials; c = Credentials('smoke-user', 'dummy-not-a-real-password'); assert '[REDACTED]' in repr(c) and 'dummy-not-a-real-password' not in repr(c); assert BrowserAgent(headless=True).headless; print('PASS: imports and secret redaction')"
```

Expected result: `PASS: imports and secret redaction` (compileall is silent on success). This test does not start a browser.

## Smoke test 2: launch Chromium and inspect local HTML

Install Chromium first using the instructions in [web-agent.md](web-agent.md), then run:

```sh
python -c "from agents.web import BrowserAgent; agent = BrowserAgent(headless=True).start(); agent.set_content('<title>Kyla local smoke</title><main>local-smoke-ok</main>'); assert agent.title() == 'Kyla local smoke'; assert 'local-smoke-ok' in agent.text('main'); agent.close(); print('PASS: local Chromium render')"
```

Expected result: `PASS: local Chromium render`. The smoke-test page is supplied from a string; there is no external network request. If a prior assertion fails, the process exits and the browser process is cleaned up by process termination. Do not replace the local HTML with a login page or real credentials when running smoke tests.

These tests were documented but not executed as part of the GitHub-only implementation; run them in the target machine's environment to verify its Python, Playwright, OS libraries, and browser installation.
