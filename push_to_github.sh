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

# Add all changes in solutions directory
echo -e "\n${GREEN}Adding changes...${NC}"
# Detect if we're in solutions directory or project root
CURRENT_DIR=$(basename "$PWD")
if [ "$CURRENT_DIR" = "solutions" ]; then
    git add .
else
    git add solutions/
fi

# Check if there are other changes to add
read -p "Add all other changes too? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
fi

# Get commit message
echo -e "\n${GREEN}Enter commit message (or press Enter for default):${NC}"
read -r COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Update solutions - $(date '+%Y-%m-%d %H:%M:%S')"
fi

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
