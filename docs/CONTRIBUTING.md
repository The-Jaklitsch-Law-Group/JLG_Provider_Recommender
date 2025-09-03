# Contributing to JLG Provider Recommender

Thank you for your interest in contributing to the JLG Provider Recommender! This document provides guidelines for contributing to this project.

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/The-Jaklitsch-Law-Group/JLG_Provider_Recommender.git
   cd JLG_Provider_Recommender
   ```

2. **Set up development environment**
   ```bash
   # Using UV (recommended)
   ./setup.sh  # Linux/macOS
   setup.bat   # Windows

   # Or manually with UV
   uv venv --python 3.11
   uv sync
   ```

3. **Run the application**
   ```bash
   uv run streamlit run app.py
   ```

4. **Run tests**
   ```bash
   uv run pytest tests/ -v --cov=. --cov-report=html
   ```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 for Python code style
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose

### Testing
- Write unit tests for all new features
- Maintain test coverage above 80%
- Include integration tests for critical workflows
- Test with the provided sample data

### Documentation
- Update README.md for new features
- Add docstrings to all functions
- Update DEPLOYMENT.md for deployment changes
- Include examples in code comments

## 📝 Contribution Process

### 1. Issue Creation
- Check existing issues before creating new ones
- Use the issue templates when available
- Provide clear reproduction steps for bugs
- Include mockups or examples for feature requests

### 2. Pull Request Process
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes with tests
4. Update documentation as needed
5. Ensure all tests pass
6. Submit a pull request with a clear description

### 3. Pull Request Requirements
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New features include tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive

### 4. Review Process
- All PRs require review before merging
- Address reviewer feedback promptly
- Keep PRs focused and reasonably sized
- Squash commits before merging when appropriate

## 🎯 Areas for Contribution

### High Priority
- Performance optimizations for large datasets
- Enhanced error handling and user feedback
- Additional geocoding service integrations
- Mobile-responsive UI improvements

### Medium Priority
- Additional export formats (PDF, CSV)
- Provider filtering and search enhancements
- Advanced analytics and reporting
- Accessibility improvements

### Documentation
- Tutorial videos or guides
- API documentation
- Deployment guides for other platforms
- Translation to other languages

## 🐛 Bug Reports

When reporting bugs, please include:
- Description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable
- Sample data (if relevant and non-sensitive)

## 💡 Feature Requests

For feature requests, please provide:
- Clear description of the desired functionality
- Use case and business justification
- Mockups or examples if applicable
- Implementation suggestions (optional)

## 📊 Data Contributions

### Sample Data
- Ensure all data is anonymized and non-sensitive
- Follow the existing data structure and naming conventions
- Include validation scripts for new data formats
- Document data sources and processing steps

### Data Privacy
- Never include real patient or sensitive information
- Use synthetic or anonymized data for examples
- Follow HIPAA and other applicable privacy regulations
- Remove any personally identifiable information

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professionalism in all interactions

### Communication
- Use GitHub issues for project-related discussions
- Be clear and concise in communications
- Provide context for questions and requests
- Respond to feedback in a timely manner

## 🛡️ Security

- Do not commit secrets, API keys, or sensitive data
- Report security vulnerabilities privately via email
- Follow the security guidelines in SECURITY.md
- Use environment variables for configuration

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers this project.

## 🙋 Getting Help

If you need help with contributing:
- Check the README.md for basic setup instructions
- Review existing issues and pull requests
- Open a discussion or issue for questions
- Contact the maintainers at [info@jaklitschlawgroup.com](mailto:info@jaklitschlawgroup.com)

Thank you for contributing to making legal technology more accessible and effective!
