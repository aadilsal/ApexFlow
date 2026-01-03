#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting VPS Setup..."

# 1. Update System
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# 2. Install Essentials
echo "🛠 Installing Git, Curl, Unzip..."
apt-get install -y git curl unzip htop

# 3. Install Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed."
else
    echo "✅ Docker already installed."
fi

# 4. Install Docker Compose (V2 is included in modern docker, checking just in case)
echo "🐳 Checking Docker Compose..."
docker compose version

echo "✨ Setup Complete! You can now clone your repo."
echo "   Run: git clone https://github.com/YOUR_GITHUB_USER/ApexFlow.git"
