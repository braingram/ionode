#!/bin/bash

echo "Starting server..."
python start_ionode.py &
SERVER_PID="$!"
echo "Server running in pid: $SERVER_PID"

echo "Starting ui..."
python start_ui.py

kill $SERVER_PID
