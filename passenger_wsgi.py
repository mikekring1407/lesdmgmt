import sys
import os

# This interp line is only needed if your Python installation is in a
# non-standard location (e.g., inside a virtual environment)
# Uncomment and adjust the path if needed
# INTERP = os.path.expanduser("/path/to/your/venv/bin/python")
# if sys.executable != INTERP:
#     os.execl(INTERP, INTERP, *sys.argv)

# Import your Flask application
from main import app as application