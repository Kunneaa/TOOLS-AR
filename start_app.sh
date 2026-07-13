#!/bin/bash
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Ensure requirements are installed
echo "Checking requirements..."
pip3 install -r requirements.txt > /dev/null 2>&1

echo "Starting Streamlit App..."
streamlit run app.py
