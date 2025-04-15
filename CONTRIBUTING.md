# Contributing to Tenshi

Thank you for your interest in contributing to Tenshi! We welcome contributions, issues, and pull requests. Please review the following guidelines to help you get started.

---

## Table of Contents

- [Setting Up Your Environment](#setting-up-your-environment)
- [Reporting Issues](#reporting-issues)
- [Pull Request Process](#pull-request-process)
- [Code Style Guidelines](#code-style-guidelines)
- [Development Commands](#development-commands)
- [Code of Conduct](#code-of-conduct)

---

## Setting Up Your Environment

1. **Clone the Repository:**  
   Fork the repository and clone it locally:

   ```bash
   git clone https://github.com/NorkzYT/Tenshi.git
   ```

2. **Build Instructions:**
   Follow the installation instructions in the [Tenshi/README.md](Tenshi/README.md) to set up your local or Docker-based development environment.

3. **Dependencies:**
   Ensure you have all the necessary OS-level and Python dependencies as described in the `dockerfile` and the `requirements.txt`.

4. **Environment Variables:**
   Copy the provided `.env.example` to `.env` and populate it with the required values.

---

## Reporting Issues

- **Search First:**
  Before opening a new issue, please check the [existing issues](https://github.com/NorkzYT/Tenshi/issues) to see if the problem has already been reported.

- **Provide Details:**
  When reporting an issue, include a clear title, detailed description, steps to reproduce, and any logs or screenshots if possible.

---

## Pull Request Process

1. **Fork & Branch:**
   Fork the repository and create a new branch dedicated to your feature or bug fix.

2. **Commit Messages:**
   Write clear and concise commit messages explaining your changes.

3. **Testing:**
   Ensure your changes pass all tests and do not disrupt existing functionality.

4. **Submit:**
   Open a pull request against the main branch, describing your changes in detail and linking to any related issues.

---

## Code Style Guidelines

- **Coding Conventions:**
  Follow standard Go (if working on automation scripts) and Python coding best practices, along with appropriate commenting.

- **Comments & Documentation:**
  Maintain existing comments. Add additional comments where needed to explain new logic or modifications.

- **Error Handling:**
  Make sure that error handling and edge cases are appropriately addressed in your contributions.

- **Performance:**
  Optimize performance without sacrificing code readability or maintainability.

---

## Development Commands

For local development of Tenshi, use the provided Makefile. To build and run the development environment, execute:

```bash
make build-dev
```

This command builds and runs the development environment according to the configuration in `docker-compose.dev.yml`.

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](https://contributor-covenant.org/version/2/1/code_of_conduct/). By contributing, you agree to uphold this code. Please review it to ensure a welcoming and respectful community.

---

Thank you for contributing to Tenshi!
