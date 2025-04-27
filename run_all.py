"""
Run both the Streamlit app and Stripe webhook server
"""
import os
import subprocess
import sys
import time
from setup_env import setup_stripe_env

def run_services():
    """
    Run both the Streamlit app and the Stripe webhook server
    """
    # First, set up the environment variables
    setup_stripe_env()
    print("Environment variables set up successfully.")
    
    # Start the Stripe webhook server
    webhook_process = subprocess.Popen(
        [sys.executable, "webhook.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("Stripe webhook server started on port 5001.")
    
    # Start the Streamlit app
    streamlit_process = subprocess.Popen(
        ["streamlit", "run", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("Streamlit app started on port 8501.")
    
    try:
        while True:
            # Keep the script running
            time.sleep(1)
    except KeyboardInterrupt:
        # Terminate processes on Ctrl+C
        webhook_process.terminate()
        streamlit_process.terminate()
        print("\nAll services stopped.")

if __name__ == "__main__":
    run_services() 