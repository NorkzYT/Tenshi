<p align="center">
  <img src="https://raw.githubusercontent.com/NorkzYT/Tenshi/refs/heads/main/docs/content/assets/img/tenshi-cover-rl.png" width="490" alt="Tenshi">
</p>

<p align="center">
  Bypasses Cloudflare Turnstile using OpenCV and browser automation.
</p>

<div align="center">
  <!-- Contributions Welcome -->
  <a href="CODE_OF_CONDUCT.md" target="_blank">
    <img src="https://img.shields.io/badge/contributions-welcome-brightgreen?logo=github" alt="Contributions Welcome">
  </a>
  <!-- Commits per Month -->
  <a href="https://github.com/NorkzYT/Tenshi/pulse" target="_blank">
    <img src="https://img.shields.io/github/commit-activity/m/NorkzYT/Tenshi" alt="Commits per Month">
  </a>
  <!-- License -->
  <a href="LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/license-MIT-purple" alt="License">
  </a>
  <!-- Contributor Covenant -->
  <a href="https://contributor-covenant.org/version/2/1/code_of_conduct/" target="_blank">
    <img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-purple" alt="Contributor Covenant 2.1">
  </a>
  <!-- GitHub Stars -->
  <a href="https://github.com/NorkzYT/Tenshi/stargazers" target="_blank">
    <img src="https://img.shields.io/github/stars/NorkzYT/Tenshi" alt="GitHub Stars">
  </a>
</div>

<details>
<summary><strong>Expand Table of Contents</strong></summary>

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development](#development)
- [Usage](#usage)
  - [FastAPI Endpoints](#fastapi-endpoints)
  - [Docker Compose / CLI](#docker-compose--cli)
- [Configuration](#configuration)
- [Directory Layout](#directory-layout)
- [Contributing](#contributing)
- [License](#license)

</details>

## Overview

Tenshi automates Cloudflare Turnstile challenges by combining:

- **Computer vision** with OpenCV templates
- **Browser control** via Brave Browser remote debugging
- **Scripted workflows** driven by FastAPI endpoints

You can integrate Tenshi into any scraping or automation pipeline to solve Turnstile barriers before driving further interactions.

## Features

- Detects and clicks “Reload” or challenge buttons when Turnstile appears
- Offers `/trigger`, `/save_chapter`, `/save_image`, `/get_image` HTTP endpoints
- Ships in a fully configured Docker image for Linux, macOS, and Windows hosts
- Exposes a remote‑debuggable Brave instance (Chromium via CDP)
- Supports lazy‑loaded image scraping via Playwright and Python scripts

## Prerequisites

- [Docker Engine](https://docs.docker.com/engine/) ≥ 28.0.2
- [Docker Compose](https://docs.docker.com/compose/) ≥ v2.34.0
- A machine with at least 2 GB RAM and 4 CPU Cores
- Network access to target URLs

## Installation

1. **Clone repository**

   ```bash
   git clone https://github.com/NorkzYT/Tenshi.git
   cd Tenshi
   ```

2. **Copy and configure environment**

   ```bash
   cp .env.example .env
   # Then set:
   # TENSHI_VNC_PASSWORD  – password for VNC/noVNC access
   ```

3. **Build and start (production)**

   ```bash
   make prod
   ```

4. **Verify services**
   - FastAPI at `http://localhost:6081`
   - noVNC at `http://localhost:6080`
   - VNC on port 5900 (password = TENSHI_VNC_PASSWORD)

## Development

Use the development compose file to bind‑mount scripts and data:

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Maps `./docker/data` → `/tenshi/data` for persisted output
- Forwards Brave CDP port `9222` to host `6082`
- Enables optional OpenCV debug logging via `DEBUG_OPENCV=1`

## Usage

### FastAPI Endpoints

All endpoints live under `http://<host>:6081`.

| Endpoint        | Method | Description                                                                                |
| --------------- | ------ | ------------------------------------------------------------------------------------------ |
| `/trigger`      | GET    | Load URL in browser and run Turnstile bypass.                                              |
| `/save_chapter` | GET    | Fetch all images from a chapter page, download them into `/tenshi/data/<slug>/<chapter>/`. |
| `/save_image`   | GET    | Download a single image URL into `/tenshi/data/<chapter>/`.                                |
| `/get_image`    | GET    | List or retrieve saved images from a chapter folder.                                       |

#### Examples

```bash
# 1. Bypass Turnstile on example.com
curl "http://localhost:6081/trigger?url=https://example.com&sleep=5000"

# 2. Save entire chapter
curl "http://localhost:6081/save_chapter?chapter_url=https://site.com/chapter-1&slug=my-series"

# 3. Save single image
curl "http://localhost:6081/save_image?chapter_url=https://site.com/ch1&image_url=https://cdn.site.com/img1.jpg"

# 4. List saved images
curl "http://localhost:6081/get_image?slug=my-series&chapter=chapter-1"
```

### Docker Compose / CLI

You can drive Tenshi from your host via Docker Compose:

```bash
# Run once
docker compose exec tenshi curl "http://127.0.0.1:8000/trigger?url=https://example.com"
```

## Configuration

| Variable              | Description                                             | Default       |
| --------------------- | ------------------------------------------------------- | ------------- |
| `TENSHI_PASSWORD`     | System password for user `tenshi`                       | _required_    |
| `TENSHI_VNC_PASSWORD` | Password for VNC/noVNC access                           | _required_    |
| `DEBUG_OPENCV`        | Enable debug screenshots and logs for template matching | `0`           |
| `TARGET_URL`          | Initial URL Brave opens on container start              | `about:blank` |

| Port | Service                      |
| ---- | ---------------------------- |
| 6081 | FastAPI (trigger API)        |
| 6080 | noVNC HTML5 VNC client       |
| 5900 | Raw VNC (x11vnc)             |
| 6082 | Brave remote debugging (CDP) |

## 🤝 Contribution

Contributions, issues, and pull requests are welcome! Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for development and contribution guidelines.

## License

This project is licensed under MIT. See [LICENSE](./LICENSE) for details.

## 📈 Star History

<a href="https://star-history.com/#NorkzYT/Tenshi">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=NorkzYT/Tenshi&type=Date&theme=dark">
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=NorkzYT/Tenshi&type=Date">
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=NorkzYT/Tenshi&type=Date">
  </picture>
</a>
