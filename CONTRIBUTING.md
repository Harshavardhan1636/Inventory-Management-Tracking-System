# Contributing to Inventory-Management-Tracking-System

Thank you for your interest in contributing to Inventory-Management-Tracking-System!

This document provides guidelines for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior
- Be respectful and considerate
- Welcome newcomers and help them get started
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other contributors

### Unacceptable Behavior
- Harassment or discrimination of any kind
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

---

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic understanding of computer vision (helpful but not required)
- Familiarity with Flask and SQLAlchemy (for backend contributions)

### Setting Up Development Environment

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Inventory-Management-Tracking-System.git
   cd Inventory-Management-Tracking-System
   ```

3. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install development dependencies:**
   ```bash
   pip install black pytest pytest-cov flake8 mypy
   ```

6. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## How to Contribute

### Types of Contributions

**Code Contributions:**
- Bug fixes
- New features
- Performance improvements
- Refactoring

**Documentation:**
- Improving existing docs
- Adding examples
- Fixing typos
- Translating documentation

**Testing:**
- Writing new tests
- Improving test coverage
- Reporting bugs

**Design:**
- UI/UX improvements
- Icon design
- Visual assets

---

## Development Workflow

### 1. Choose an Issue

- Check existing [issues](../../issues)
- Look for `good first issue` or `help wanted` labels
- Comment on the issue to claim it

### 2. Write Code

- Follow coding standards (see below)
- Write tests for new features
- Update documentation
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run tests
pytest tests/

# Check code formatting
black --check .

# Run linting
flake8 .

# Type checking
mypy .
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat(detection): improve YOLOv8 confidence threshold handling

- Add configurable confidence thresholds per class
- Update documentation
- Add tests for new functionality

Closes #123
```

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Go to the original repository
- Click "New Pull Request"
- Select your branch
- Fill out the PR template
- Submit

---

## Coding Standards

### Python Code Style

**Follow PEP 8 with modifications:**
- Line length: 100 characters
- Use double quotes for strings
- Use Black for formatting

**Example:**
```python
def process_detection(
    frame: np.ndarray,
    confidence: float = 0.5
) -> List[Dict[str, Any]]:
    """Process detection on a single frame.
    
    Args:
        frame: Input image frame
        confidence: Minimum confidence threshold
        
    Returns:
        List of detection dictionaries
    """
    # Implementation here
    pass
```

### Code Quality

**Do:**
- ✅ Write clear, self-documenting code
- ✅ Add docstrings to all public functions/classes
- ✅ Use type hints
- ✅ Handle errors gracefully
- ✅ Log important events
- ✅ Write tests for new features

**Don't:**
- ❌ Hard-code values (use configuration)
- ❌ Leave commented-out code
- ❌ Use print() for debugging (use logging)
- ❌ Ignore linting warnings
- ❌ Skip documentation

### File Organization

```
module_name/
├── __init__.py       # Module exports
├── core.py           # Core functionality
├── helpers.py        # Helper functions
└── exceptions.py     # Custom exceptions
```

---

## Testing Guidelines

### Writing Tests

**Test Structure:**
```python
# tests/test_module.py
import pytest
from module import function_to_test

class TestFunctionName:
    """Test suite for function_to_test."""
    
    def test_basic_functionality(self):
        """Test basic use case."""
        result = function_to_test(input_data)
        assert result == expected_output
        
    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

### Test Coverage

- Aim for 80%+ coverage for new code
- Test happy paths and edge cases
- Test error handling
- Mock external dependencies

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_reasoning.py

# Run specific test
pytest tests/test_reasoning.py::TestSlotState::test_creation
```

---

## Documentation

### Documentation Requirements

**Code Documentation:**
- Docstrings for all public functions/classes
- Inline comments for complex logic
- Type hints

**User Documentation:**
- Update relevant docs in `docs/` folder
- Add examples for new features
- Update README if needed

**API Documentation:**
- Document new endpoints
- Include request/response examples
- Update API_REFERENCE.md

### Writing Documentation

**Good Documentation:**
```python
def calculate_confidence(detections: List[Dict]) -> float:
    """Calculate aggregated confidence from multiple detections.
    
    Computes weighted average confidence across temporal buffer.
    More recent detections have higher weight.
    
    Args:
        detections: List of detection dicts with 'confidence' key
        
    Returns:
        Weighted confidence score (0.0-1.0)
        
    Raises:
        ValueError: If detections list is empty
        
    Example:
        >>> dets = [{'confidence': 0.8}, {'confidence': 0.9}]
        >>> calculate_confidence(dets)
        0.85
    """
    pass
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages are clear
- [ ] PR description explains changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] Tests pass
```

### Review Process

1. **Automated Checks:** CI/CD runs tests and linting
2. **Code Review:** Maintainers review your code
3. **Feedback:** Address review comments
4. **Approval:** Once approved, PR is merged
5. **Cleanup:** Delete your branch after merge

### After Merge

- Pull latest changes from main
- Delete your feature branch
- Start on next issue!

---

## Questions?

- **Issues:** [GitHub Issues](../../issues)
- **Discussions:** [GitHub Discussions](../../discussions)
- **Documentation:** [docs/](docs/)

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Inventory-Management-Tracking-System! 🎉
