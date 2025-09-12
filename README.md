# QA Project Debugging & CI/CD Setup (Dinnova → zytrack.ch)

Automated end-to-end login tests for the **Dinnova** time-tracking tool (**zytrack.ch**), running locally, in **Docker**, and on **GitHub Actions** with **Chrome**.
Focus: a clean **Dockerfile** and a reproducible **CI workflow**.

---

## What this repo does

* Runs Selenium login tests (success + failure paths) against `https://app.zytrack.ch/login`.
* Uses **Chrome** (headed locally for debugging, headless in CI/Docker).
* Ships a **Docker image** you can run anywhere (x64).
* Includes a **GitHub Actions** workflow that installs Chrome and runs the test suite on every push/PR.

---

## Project structure (minimal)

```
.
├── tests/
│   └── test_login.py          # Selenium tests (Chrome)
├── requirements.txt           # selenium / pytest / webdriver-manager / dotenv (if used)
├── Dockerfile                 # builds a runnable image for CI parity
└── .github/
    └── workflows/
        └── ci.yml             # GitHub Actions workflow (Chrome)
```

---

## Environment variables

These control the test target and credentials:

* `DINNOVA_QA_LOGIN_URL` – e.g., `https://app.zytrack.ch/login`
* `DINNOVA_QA_USERNAME` – test user
* `DINNOVA_QA_PASSWORD` – test password
* `HEADLESS` – `1` for headless (CI/Docker), `0` for headed (local debugging)

> For CI: store real values as **Repository → Settings → Secrets and variables → Actions → New repository secret**.

---

## 🧪 Local runs (recommended for debugging)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create a .env (optional if your tests load dotenv)
cat > .env <<'ENV'
DINNOVA_QA_LOGIN_URL=https://app.zytrack.ch/login
DINNOVA_QA_USERNAME=you@example.com
DINNOVA_QA_PASSWORD=your_password
HEADLESS=0
ENV

pytest -q          # headed Chrome (easier to inspect selectors)
```

Tips:

* Use **explicit waits** (`WebDriverWait(...).until(...)`) before interacting with elements like `#email`, `#password`.
* If a cookie/consent banner appears, dismiss it first.
* Capture artifacts (screenshot + HTML) on failure to see what Chrome rendered.

---

## 🐳 Docker (x64)

The image contains Python + Chrome and runs tests headless by default.
Build for **x64** and run with your env:

```bash
# Build (x64)
docker buildx build --platform linux/amd64 -t dinnova-qa:latest .

# Run (x64)
docker run --rm --platform linux/amd64 \
  -e DINNOVA_QA_LOGIN_URL="https://app.zytrack.ch/login" \
  -e DINNOVA_QA_USERNAME="user@example.com" \
  -e DINNOVA_QA_PASSWORD="supersecret" \
  -e HEADLESS=1 \
  dinnova-qa:latest

# Or load envs from a file
# docker run --rm --platform linux/amd64 --env-file .env dinnova-qa:latest
```

### Dockerfile

```dockerfile
# Dockerfile (x64-focused, Chrome)
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Base libs needed by Chrome in headless environments
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl wget gnupg unzip fonts-liberation xdg-utils \
      libasound2 libatk-bridge2.0-0 libatk1.0-0 libx11-6 libxcomposite1 libxdamage1 libxext6 \
      libxfixes3 libxrandr2 libxkbcommon0 libgbm1 libgtk-3-0 libcups2 libnspr4 libnss3 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome (stable) for amd64
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-linux.gpg \
  && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
     > /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
  && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy tests
COPY tests ./tests

# Default to running tests headless
ENV HEADLESS=1

# Run
CMD ["pytest", "-q"]
```

> Chromedriver is resolved automatically at runtime via **webdriver-manager** (see `test_login.py`/driver factory). This keeps Chrome/driver in sync.

---

## 🚦 GitHub Actions (CI) — Chrome on Ubuntu

**Workflow name**: *CI*.
Triggered on every `push` and `pull_request`.
Installs Python + **Chrome** via `browser-actions/setup-chrome@v2`, then runs pytest.

How it works:

1. Checks out the repo.
2. Installs Python 3.12.
3. Installs **Chrome** (and optionally Chromedriver).
4. Installs Python deps.
5. Runs the tests in **headless Chrome**.

---

## Test notes (selectors & stability)

* Use **explicit waits** for dynamic elements:

  ```python
  email = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "email")))
  pwd   = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "password")))
  ```
* Submit with: `form button[type='submit']`.
* Failure message selector (tailored to zytrack UI):

  ```python
  WebDriverWait(driver, 15).until(
      EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-red-600"))
  )
  ```
* Add a cookie/consent dismiss step if needed before interacting.

---

## Job name & status

* **GitHub Actions job title**: `QA Login Tests (Chrome + Docker)`
* CI should be **green** on push/PR; Docker image runs the same suite (headless) for parity.

---

## Troubleshooting

* **Element not found (`NoSuchElementException`)**
  Usually timing. Add/adjust `WebDriverWait` and confirm you’re on the expected URL.
* **Headless vs headed differences**
  Keep `--window-size=1920,1080` for headless runs to avoid responsive layout shifts.
* **Credentials**
  Use **Secrets** in CI; never commit real passwords.

---

## License / Ownership

© Dinnova — QA automation for zytrack.ch.
Internal test accounts only; do not use production credentials outside approved pipelines.
