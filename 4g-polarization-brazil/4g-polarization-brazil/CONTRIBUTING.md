# Contributing to 4G Polarization Research

Thank you for your interest in contributing to this research project! This document provides guidelines for contributing code, documentation, or suggestions.

## Getting Started

### Prerequisites

1. **Python 3.8+** with packages in `requirements.txt`
2. **R 4.0+** with required packages (see R script headers)
3. **Git** for version control
4. **LaTeX** (optional, for paper compilation)

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/[username]/4g-polarization-brazil.git
cd 4g-polarization-brazil

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install R packages
Rscript -e "install.packages(c('did', 'fixest', 'ggplot2', 'dplyr', 'tidyr', 'knitr', 'kableExtra'))"
```

## Types of Contributions

### 1. Code Contributions

**Data Cleaning Scripts:**
- Follow existing structure in `code/cleaning/`
- Document all data transformations
- Include error handling and logging
- Test with sample data before committing

**Analysis Scripts:**
- Use clear variable names
- Comment complex operations
- Include summary statistics and diagnostics
- Save outputs to appropriate directories

**Style Guidelines:**
- Python: Follow PEP 8
- R: Follow tidyverse style guide
- Comment non-obvious operations
- Use meaningful function/variable names

### 2. Documentation Contributions

We welcome improvements to:
- README clarity
- Data documentation
- Methodology explanations
- Code comments
- Error messages

### 3. Bug Reports

When reporting bugs, please include:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python/R versions)
- Relevant error messages

Use GitHub Issues with the "bug" label.

### 4. Feature Requests

For new features or enhancements:
- Describe the proposed feature
- Explain the use case
- Consider implementation complexity
- Discuss with maintainers before coding

Use GitHub Issues with the "enhancement" label.

## Contribution Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/[your-username]/4g-polarization-brazil.git
cd 4g-polarization-brazil

# Add upstream remote
git remote add upstream https://github.com/[original-username]/4g-polarization-brazil.git
```

### 2. Create a Branch

```bash
# Create a descriptive branch name
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 3. Make Changes

- Write clear, documented code
- Follow existing project structure
- Test your changes thoroughly
- Update documentation if needed

### 4. Commit Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "Add: brief description of changes

- Detailed point 1
- Detailed point 2"
```

**Commit Message Guidelines:**
- Use imperative mood ("Add" not "Added")
- First line: brief summary (<50 chars)
- Blank line
- Detailed description if needed
- Reference issues: "Fixes #123"

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Describe changes, reference issues, explain testing
```

## Testing Guidelines

### Data Processing Tests

Before committing data cleaning scripts:
1. Test with sample data (100-1000 rows)
2. Verify output format matches expectations
3. Check for memory issues with large files
4. Ensure reproducibility

### Analysis Tests

Before committing analysis scripts:
1. Verify results match expected patterns
2. Check for convergence issues
3. Test with different parameters
4. Document any anomalies

## Code Review Process

1. **Automated Checks**: Scripts must run without errors
2. **Documentation**: Code must be well-documented
3. **Testing**: Changes must be tested
4. **Review**: At least one maintainer must approve
5. **Discussion**: Be open to feedback and suggestions

## Research Ethics

This project involves electoral and personal data. Please:

- Respect data privacy and regulations
- Do not commit raw data with personal information
- Follow ethical research practices
- Cite sources appropriately
- Acknowledge contributors

## Data Handling

### Never Commit:
- Raw data files (use .gitignore)
- Personal identifiable information
- API keys or credentials
- Large binary files (>10MB)

### Do Commit:
- Code and scripts
- Documentation
- Small sample/example data
- Configuration templates
- Analysis results (tables, figures)

## Questions?

- **General Questions**: Open a GitHub Discussion
- **Bug Reports**: Open a GitHub Issue with "bug" label
- **Feature Requests**: Open a GitHub Issue with "enhancement" label
- **Security Issues**: Email maintainers directly (see README)

## Recognition

Contributors will be acknowledged in:
- GitHub contributors page
- Paper acknowledgments section
- CONTRIBUTORS.md file (if created)

Significant contributions may warrant co-authorship (to be discussed with lead authors).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to understanding the relationship between digital technology and political polarization!
