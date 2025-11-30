#!/usr/bin/env python3

"""
GitHub Push Script for Solutions
Automatically commits and pushes new content to GitHub
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'


def run_command(cmd, check=True):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error: {e.stderr}{Colors.NC}")
        if check:
            sys.exit(1)
        return None


def main():
    print(f"{Colors.GREEN}=== GitHub Push Script ==={Colors.NC}")
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        print(f"{Colors.RED}Error: Not a git repository{Colors.NC}")
        sys.exit(1)
    
    # Check for uncommitted changes
    status = run_command("git status --porcelain", check=False)
    if not status:
        print(f"{Colors.YELLOW}No changes to commit{Colors.NC}")
        sys.exit(0)
    
    # Show status
    print(f"\n{Colors.GREEN}Current status:{Colors.NC}")
    print(run_command("git status --short"))
    
    # Add only solution directories (exclude push scripts)
    print(f"\n{Colors.GREEN}Adding solution directories...{Colors.NC}")
    
    # Get all directories in solutions/
    solutions_dir = Path('solutions') if Path('solutions').exists() else Path('.')
    for item in solutions_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            run_command(f"git add {item}")
    
    # Generate commit message
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"Update solutions - {timestamp}"
    
    # Commit changes
    print(f"\n{Colors.GREEN}Committing changes...{Colors.NC}")
    run_command(f'git commit -m "{commit_msg}"')
    
    # Get current branch
    branch = run_command("git rev-parse --abbrev-ref HEAD")
    
    # Push to GitHub
    print(f"\n{Colors.GREEN}Pushing to GitHub...{Colors.NC}")
    run_command(f"git push origin {branch}")
    
    print(f"\n{Colors.GREEN}✓ Successfully pushed to GitHub!{Colors.NC}")
    print(f"Branch: {Colors.YELLOW}{branch}{Colors.NC}")
    print(f"Commit: {Colors.YELLOW}{commit_msg}{Colors.NC}")


if __name__ == "__main__":
    main()
