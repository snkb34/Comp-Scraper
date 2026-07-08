"""Convenience launcher for the local Streamlit app."""
import subprocess
import sys

subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
