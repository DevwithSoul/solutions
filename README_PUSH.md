# GitHub Push Scripts

Two scripts are provided to automate pushing new content to GitHub:

## 1. Bash Script (Recommended)

**File:** `push_to_github.sh`

### Usage:
```bash
cd solutions
./push_to_github.sh
```

Or from project root:
```bash
./solutions/push_to_github.sh
```

## 2. Python Script

**File:** `push_to_github.py`

### Usage:
```bash
cd solutions
./push_to_github.py
```

Or from project root:
```bash
python3 solutions/push_to_github.py
```

## Features

Both scripts provide:
- ✓ Automatic detection of changes
- ✓ Interactive commit message input
- ✓ Default timestamped commit messages
- ✓ Option to add all changes or just solutions/
- ✓ Automatic branch detection
- ✓ Color-coded output
- ✓ Error handling

## Workflow

1. Script checks if you're in a git repository
2. Shows current git status
3. Adds changes in `solutions/` directory
4. Asks if you want to add other changes
5. Prompts for commit message (or uses default)
6. Commits changes
7. Pushes to current branch on GitHub

## Default Commit Message

If no message is provided, uses:
```
Update solutions - YYYY-MM-DD HH:MM:SS
```

## Requirements

- Git installed and configured
- GitHub repository set up with remote origin
- Proper authentication (SSH key or credentials)
