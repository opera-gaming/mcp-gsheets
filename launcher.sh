#!/bin/bash
set -e

echo "🚀 MCP Google Sheets Launcher"
echo "=============================="

if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL not set, using default"
    export DATABASE_URL="postgresql://mcpuser:mcppassword@localhost:5432/mcp_gsheets"
fi

echo "📦 Installing dependencies..."
uv pip install -e .

echo "🗄️  Running database migrations..."
alembic upgrade head

if [ "$1" == "web" ]; then
    echo "🌐 Starting web service..."
    python -m mcp_gsheets.webapp
elif [ "$1" == "mcp" ]; then
    echo "🔧 Starting MCP server..."
    python -m mcp_gsheets.http_server
elif [ "$1" == "migrate" ]; then
    echo "✅ Migrations complete!"
else
    echo ""
    echo "Usage: ./launcher.sh [web|mcp|migrate]"
    echo ""
    echo "Commands:"
    echo "  web     - Run database migrations and start web service"
    echo "  mcp     - Run database migrations and start MCP HTTP server"
    echo "  migrate - Run database migrations only"
    echo ""
fi
