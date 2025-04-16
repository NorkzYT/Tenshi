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
    <img src="https://img.shields.io/badge/license-GNUv3-purple" alt="License">
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

## 🔍 Overview

Tenshi is a modular automation tool designed to bypass Cloudflare Turnstile anti-bot measures. It leverages computer vision (via OpenCV) and browser automation to navigate through Cloudflare Turnstile challenge seamlessly.

## 🌐 Supported Environments

- **Operating Systems**: Linux, macOS, and Windows (via Docker installation)
- **Browser**: Brave Browser (with remote debugging enabled)
- **Automation**: Combines xdotool, OpenCV, and FastAPI to control browser behavior
- **Containerization**: Fully configured Docker environment for both development and production

## 🚀 Installation

### 🐳 Docker

1. Ensure Docker is installed.
2. Copy `.env.example` to `.env` and set your environment variables.
3. Build and run the container:
   ```bash
   docker compose -f docker-compose.yml up -d --force-recreate
   ```

## 💻 Usage

### FastAPI Endpoints

Tenshi exposes a FastAPI server with several endpoints:

- **Trigger Automation**  
  **Endpoint:** `/trigger`  
  **Description:** Loads the target URL in the browser, executes optional JavaScript, and initiates the Cloudflare bypass workflow.  
  **Example (using curl):**

  ```bash
  curl "http://localhost:6081/trigger?url=https://example.com&js=&wait=&sleep=5000"
  ```

- **Save Image**  
  **Endpoint:** `/save_image`  
  **Description:** Navigates to the chapter URL, processes the provided image URL, and invokes the browser save automation.  
  **Example:**

  ```bash
  curl "http://localhost:6081/save_image?chapter_url=https://example.com/chapter1&image_url=https://cdn.example.com/image1.jpg"
  ```

- **Get Saved Image**  
  **Endpoint:** `/get_image`  
  **Description:** Returns a list of saved image filenames for a specified chapter folder or a specific image if a filename is provided.  
  **Example:**
  ```bash
  curl "http://localhost:6081/get_image?chapter=chapter_1"
  ```

### Remote Debugging Integration

Tenshi is built to work with a remote debugging–enabled Brave browser. In Docker, Brave is launched with remote debugging (internally on port 9223, forwarded to 6082). This enables you to connect your preferred browser automation tools (for example, Chromedp, Puppeteer, or Playwright) to control browser actions programmatically. The included [`toongod_scrape_demo.go`](./example/toongod_scrape_demo.go) demonstrates how to:

- Connect to the remote debugging endpoint (e.g. `http://<your-ip>:6082`)
- Navigate pages and extract content
- Trigger Cloudflare bypass actions via the FastAPI endpoints
-

### Automation Capabilities

After bypassing the Cloudflare Turnstile challenge, Tenshi allows you to further automate your browser. By connecting to the remote debugging port, you can integrate with powerful automation libraries such as Chromedp, Puppeteer, Playwright, and others. This flexibility enables you to build customized scrapers or automation workflows that can interact with the browser directly once the initial bypass is complete.

## 🤝 Contribution

Contributions, issues, and pull requests are welcome! Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for development and contribution guidelines.

## 📈 Star History

<a href="https://star-history.com/#NorkzYT/Tenshi">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=NorkzYT/Tenshi&type=Date&theme=dark">
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=NorkzYT/Tenshi&type=Date">
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=NorkzYT/Tenshi&type=Date">
  </picture>
</a>
