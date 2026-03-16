#!/bin/bash
set -e

echo "🏛️  Setting up Council — Agent Governance"
echo ""

# ── Python backend ──
echo "📦 Installing Python dependencies..."
pip install -e . 2>/dev/null || pip3 install -e .
echo "  ✓ Python dependencies installed"

# ── Frontend ──
echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
pnpm install
cd ..
echo "  ✓ Frontend dependencies installed"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run in development:"
echo "  Terminal 1:  python -m council.main"
echo "  Terminal 2:  cd frontend && pnpm dev"
echo ""
echo "Then open http://localhost:5174"
