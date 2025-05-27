# Development Guidelines

## Dependency Management Best Practices

### 🎯 Core Principle
**Never import development-only packages in production code**

### 📁 File Structure Rules

#### `requirements.txt` - Production Dependencies Only
- Contains packages needed to **run** the application
- Used in production deployments, Docker containers
- Keep this minimal and lean

#### `requirements-dev.txt` - Development Dependencies  
- Includes production dependencies via `-r requirements.txt`
- Adds development tools (testing, linting, etc.)
- Used by developers and CI/CD

### 🚫 Common Mistakes to Avoid

#### ❌ Don't Do This:
```python
# In src/quickquiz/api/main.py (production code)
import pytest  # pytest is dev-only!
import mypy    # mypy is dev-only!
from ruff import check  # ruff is dev-only!

@app.get("/debug")
def debug_endpoint():
    # Never use dev tools in production endpoints
    pytest.main(["-v"])  # Will break in production!
```

#### ✅ Do This Instead:
```python
# In src/quickquiz/api/main.py (production code)
from fastapi import FastAPI  # fastapi is in requirements.txt
from sqlalchemy import create_engine  # sqlalchemy is in requirements.txt

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### 📦 Package Categories

#### Production Packages (requirements.txt):
- **Web Framework**: `fastapi`, `uvicorn`
- **Database**: `sqlalchemy`, `psycopg2-binary`, `alembic`
- **AI/ML**: `openai`, `langchain`
- **Document Processing**: `pdfplumber`, `trafilatura`
- **Validation**: `pydantic`
- **Caching**: `redis`

#### Development Packages (requirements-dev.txt only):
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`
- **Linting**: `ruff`, `mypy`, `pre-commit`
- **Type Stubs**: `types-*`
- **Documentation**: `sphinx`, `mkdocs`

### 🧪 Testing Strategy

#### 1. Run Production Dependency Test Locally
```bash
# Before committing, always run:
python scripts/test_prod_deps.py
```

#### 2. Separate Test Files from Production Code
```
tests/                    # Test files (can import dev packages)
├── test_api/
├── test_services/
└── conftest.py

src/quickquiz/           # Production code (NO dev imports!)
├── api/
├── services/
└── models/
```

#### 3. Use Environment Variables for Debug Features
```python
# In production code - use env vars for debug features
import os
from fastapi import FastAPI

app = FastAPI()

if os.getenv("DEBUG", "false").lower() == "true":
    # Only enable debug routes in development
    @app.get("/debug")
    def debug_info():
        return {"debug": "enabled"}
```

### 🔄 Development Workflow

#### 1. Daily Development
```bash
# Use dev dependencies for development
source .venv/bin/activate
# Already installed: pip install -r requirements-dev.txt
```

#### 2. Before Committing
```bash
# Test with production dependencies
python scripts/test_prod_deps.py

# Run pre-commit hooks
pre-commit run --all-files
```

#### 3. CI/CD Will Test Both
- Production dependencies test
- Full test suite with dev dependencies

### 🛠️ Tools and Automation

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# They will automatically:
# - Check for dev-only imports
# - Run linting
# - Run type checking
# - Test production dependencies
```

#### IDE Configuration
Add to your IDE's import organization rules:
- Group standard library imports first
- Group third-party imports second
- Group local imports last
- Flag imports of packages not in requirements.txt

### 📋 Code Review Checklist

#### For All Pull Requests:
- [ ] No development packages imported in `src/` directory
- [ ] All new dependencies added to correct requirements file
- [ ] Production dependency test passes
- [ ] No debug code left in production paths
- [ ] Environment variables used for optional features

#### Red Flags During Review:
- `import pytest` in non-test files
- `import mypy` in production code  
- `import ruff` in production code
- Hard-coded debug flags
- Development-only environment variables in production code

### 🚀 Deployment Safety

#### Docker Multi-stage Builds
```dockerfile
# Development stage
FROM python:3.12-slim as development
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Production stage  
FROM python:3.12-slim as production
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
# This will fail if dev-only imports exist!
```

#### Environment-specific Testing
```bash
# Test in production-like environment
docker build --target production -t quickquiz:prod .
docker run quickquiz:prod python -c "from src.quickquiz.api.main import app"
```

### 💡 Pro Tips

1. **Use Type Hints**: They help catch import issues early
2. **Modular Design**: Keep business logic separate from framework code
3. **Environment Variables**: Use them for all configuration
4. **Logging**: Use proper logging instead of print statements
5. **Error Handling**: Don't rely on dev tools for error handling

### 🆘 Emergency Fixes

If you accidentally deploy with dev dependencies:

1. **Immediate**: Rollback to previous version
2. **Fix**: Remove dev-only imports from production code  
3. **Test**: Run `python scripts/test_prod_deps.py`
4. **Deploy**: Re-deploy with fixed code

### 📖 Additional Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [Docker Multi-stage Builds](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Remember**: When in doubt, test with production dependencies only!