## Git and GitHub setup for this project

### 1) Initialize a local repository
```bash
git init -b main
```

- If your Git version does not support `-b`, run:
  ```bash
git init
git checkout -b main
  ```

Add a Python-friendly `.gitignore` (already included in the repo). Review and adjust if needed.

### 2) First commit
```bash
git add -A
git commit -m "chore: initial import of mcpconf with schema, CLI, examples, tests, docs"
```

### 3) Create a GitHub repository (manual method)
1. Go to `https://github.com/new` and create a new repository (name suggestion: `mcpconf`).
2. Do NOT initialize with a README, license, or .gitignore (we already have them locally).
3. Add the remote and push:
   ```bash
git remote add origin git@github.com:<your-user-or-org>/mcpconf.git
git push -u origin main
   ```
   - If you prefer HTTPS:
     ```bash
git remote add origin https://github.com/<your-user-or-org>/mcpconf.git
git push -u origin main
     ```

### 4) (Optional) Create via GitHub CLI
```bash
gh auth login
# public repo example
gh repo create mcpconf --public --source=. --remote=origin --push
```

### 5) Branching and PR workflow
```bash
git checkout -b feat/<short-topic>
# make changes
git add -A
git commit -m "feat: <summary>"
git push -u origin feat/<short-topic>

# open PR
gh pr create --title "feat: <title>" --body "<summary>"
```

### 6) Continuous Integration (GitHub Actions)
Create `.github/workflows/ci.yml`:
```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest
      - name: Run tests
        run: pytest -q
```

### 7) Releases and tags
```bash
# update version in pyproject.toml
git commit -am "chore: release v0.1.0"
git tag -a v0.1.0 -m "v0.1.0"
git push && git push --tags

# Create a GitHub Release (optional)
gh release create v0.1.0 --title "v0.1.0" --notes "Initial release"
```

### 8) Local verification before pushing
```bash
# install
yarn || true  # ignore if not present
pip install -e .
# run tests
pytest -q
# validate example against schema
python3 -m mcpconf.cli validate examples/mcp-servers.example.yaml --schema mcp-servers.schema.json
# generate outputs
python3 -m mcpconf.cli convert examples/mcp-servers.example.yaml --to mcpServers-json > examples/outputs/mcpServers.json
python3 -m mcpconf.cli convert examples/mcp-servers.example.yaml --to github-servers-json > examples/outputs/github-servers.json
python3 -m mcpconf.cli convert examples/mcp-servers.example.yaml --to claude-cli > examples/outputs/claude-cli.sh
```

### 9) Recommended protections (in repo settings)
- Require PR reviews before merging to `main`.
- Require passing CI checks on PRs.
- Restrict who can push directly to `main`.
