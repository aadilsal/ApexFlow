import sys
import os

# Add the src folder to the path so that absolute imports like 'apex_flow.api...' work
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from apex_flow.api.main import app
