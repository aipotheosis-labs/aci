# Contributing to ACI.dev

Thank you for your interest in contributing to ACI.dev! We welcome contributions from everyone, whether it's submitting bug reports, suggesting new features, improving documentation, or contributing code.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to foster an open and welcoming community.

## Getting Started

Before you begin contributing, please set up your local development environment by following the instructions in the [README.md](README.md).

## Repository Structure

Our monorepo contains two main components:

- **`/backend`**: Python FastAPI server, CLI, Database etc.
- **`/frontend`**: Next.js application for the developer portal

## How to Contribute

### Reporting Bugs

If you've found a bug:

1. Check if the bug has already been reported in the GitHub Issues
2. If not, create a new issue with a clear title and description
3. Include steps to reproduce, expected behavior, and actual behavior
4. Add any relevant screenshots or error logs

### Suggesting Features

We welcome feature suggestions:

1. Describe the feature and its use case
2. Explain how it would benefit ACI.dev users
3. Provide any examples or references if available

### Code Contributions

1. **Fork the repository** to your GitHub account
2. **Clone your fork** to your local machine
3. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following our coding standards (see below)
5. **Commit your changes** with clear, descriptive commit messages
6. **Push your branch** to your fork
7. **Create a pull request** to the main repository

#### Pull Request Process

1. Ensure your code follows our coding standards
2. Update documentation if necessary
3. Make sure all tests pass
4. Reference any related issues in your pull request description
5. Wait for review from maintainers

## Coding Standards

### Backend (Python)

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Ensure code passes Ruff linting and MyPy type checking
- Include tests for new functionality

### Frontend (TypeScript/React)

- Follow the project's ESLint and Prettier configuration
- Use TypeScript types appropriately
- Follow React best practices and existing component patterns
- Write tests for new components and functionality
- Maintain responsive design principles

## Testing

- Backend: Run tests with pytest
- Frontend: Run tests with Vitest

## License

By contributing to ACI.dev, you agree that your contributions will be licensed under the project's [Apache 2.0 License](LICENSE).
