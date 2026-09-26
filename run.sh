#!/bin/bash
echo "=========================================="
echo "  Chama App Kenya - Starting..."
echo "=========================================="
echo ""

# Install dependencies if needed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting server on http://0.0.0.0:5000"
echo "Open on your phone: http://YOUR-IP:5000"
echo ""
echo "Demo Login:"
echo "  Phone: 0712345678"
echo "  Password: password123"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

python3 app.py
