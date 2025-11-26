#!/bin/bash

# LLM Council - Start script

echo "Starting LLM Council..."
echo ""

# Start backend
echo "Starting backend on http://localhost:8001..."
uv run python -m backend.main &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend
echo "Starting frontend on http://localhost:5173..."
cd frontend || exit 1
if [ ! -d node_modules ]; then
  echo "Installing frontend dependencies..."
  npm install || exit 1
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✓ LLM Council is running!"
echo "  Backend:  http://localhost:8001"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Waiting for frontend to become available..."
for i in {1..30}; do
  if command -v curl >/dev/null 2>&1 && curl -s http://localhost:5173 >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Opening the web dashboard..."
if command -v open >/dev/null 2>&1; then
  open "http://localhost:5173" >/dev/null 2>&1 &
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://localhost:5173" >/dev/null 2>&1 &
fi
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
