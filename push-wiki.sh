#!/bin/bash
# Script to push wiki to GitHub using SSH

set -e

WIKI_DIR="/tmp/MooAId.wiki"
WIKI_REPO="git@github.com:CertifiedSlop/MooAId.wiki.git"

echo "📚 Pushing Wiki to GitHub..."

# Remove existing wiki clone if exists
if [ -d "$WIKI_DIR" ]; then
    rm -rf "$WIKI_DIR"
fi

# Clone wiki repository
echo "Cloning wiki repository..."
git clone "$WIKI_REPO" "$WIKI_DIR"

# Copy wiki files
echo "Copying wiki files..."
cp wiki/*.md "$WIKI_DIR/"

# Commit and push
cd "$WIKI_DIR"
git add .
git commit -m "Add initial wiki documentation

Pages:
- Home
- Installation Guide
- Profile Builder
- CLI Usage
- REST API Documentation
- Configuration
- Docker Deployment
- FAQ"

echo "Pushing to GitHub..."
git push origin main

echo "✅ Wiki pushed successfully!"
echo "View at: https://github.com/CertifiedSlop/MooAId/wiki"
