#!/bin/bash

# GitHub Push Script for Solutions
# Automatically commits and pushes new content to GitHub

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GitHub Push Script ===${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
if git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}No changes to commit${NC}"
    exit 0
fi

# Show status
echo -e "${GREEN}Current status:${NC}"
git status --short

# Add only solution directories (exclude push scripts)
echo -e "\n${GREEN}Adding solution directories...${NC}"

# Find and add all directories in solutions/ (excluding hidden dirs)
if [ -d "solutions" ]; then
    for dir in solutions/*/; do
        if [ -d "$dir" ]; then
            git add "$dir"
        fi
    done
else
    # We're already in solutions/
    for dir in */; do
        if [ -d "$dir" ]; then
            git add "$dir"
        fi
    done
fi

# Generate commit message
COMMIT_MSG="Update solutions - $(date '+%Y-%m-%d %H:%M:%S')"

# Commit changes
echo -e "\n${GREEN}Committing changes...${NC}"
git commit -m "$COMMIT_MSG"

# Push to GitHub
echo -e "\n${GREEN}Pushing to GitHub...${NC}"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push origin "$BRANCH"

echo -e "\n${GREEN}✓ Successfully pushed to GitHub!${NC}"
echo -e "Branch: ${YELLOW}$BRANCH${NC}"
echo -e "Commit: ${YELLOW}$COMMIT_MSG${NC}"
