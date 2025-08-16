# Streamlit Cloud entry point
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main dashboard
from dashboard import main

# Streamlit Cloudでは直接実行
main()