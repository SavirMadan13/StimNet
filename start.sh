#!/bin/bash

# Simple wrapper script for backward compatibility
# Just calls the main launch script

echo "🚀 Starting Distributed Framework..."
echo "   (Using launch.sh - run './launch.sh --help' for more options)"
echo ""

exec ./launch.sh "$@"