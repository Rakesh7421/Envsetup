#!/bin/bash

echo "--- Applying Final Output Suppression Fix ---"

# --- 1. Find the Python Interpreter ---
PYTHON_CMD=$(command -v python3 || command -v python)
if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: Could not find 'python' or 'python3' command. Cannot proceed."
    exit 1
fi

# --- 2. Determine the Installation Path ---
SITE_PACKAGES_PATH=$($PYTHON_CMD -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
if [ -z "$SITE_PACKAGES_PATH" ]; then
    echo "ERROR: Could not determine Python site-packages path."
    exit 1
fi

# --- 3. Create the stealth 'pyb' module files ---
PYB_INIT_FILE="$SITE_PACKAGES_PATH/pyb/__init__.py"
PYB_DIR="$SITE_PACKAGES_PATH/pyb"

mkdir -p "$PYB_DIR"

echo "Re-creating __init__.py to hide all command execution details..."

# The 'pyb' function is stripped of all internal print statements (except errors).
cat > "$PYB_INIT_FILE" << EOF
import subprocess
import os
import sys

def pyb(command):
    """
    Executes a shell command silently. Only prints the command's stdout.
    Internally converts newlines to ' & ' on Windows for sequential execution.
    Returns the command's exit code.
    """
    cleaned_command = command.strip()

    if not cleaned_command:
        # Keep this print for explicit user errors
        print("Error: Empty command string provided.")
        return 1
        
    # --- INTERNAL EXECUTION FIX FOR WINDOWS ---
    # Replace newlines with the command separator '&' for sequential execution.
    if sys.platform.startswith('win') or 'MINGW' in os.environ.get('MSYSTEM', ''):
        final_command = cleaned_command.replace('\n', ' & ').replace('\r', '')
    else:
        final_command = cleaned_command

    # NOTE: The print statements for "Executing shell command: ---START---" are intentionally removed here.

    try:
        # Execute the command
        result = subprocess.run(final_command, shell=True, check=True, capture_output=True, text=True)

        if result.stdout:
            # Only print the actual command output
            print(result.stdout.strip())
        
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Stderr: {e.stderr.strip()}")
        return e.returncode
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1
EOF

echo "SUCCESS: 'pyb' module is now clean. Only command output will be shown."

# --- 4. Auto Test with Provided File (Expected Clean Output) ---
echo "--- Running Auto Test for Clean Output ---"

# This re-runs your problem file with the FIXED pyb function now in place.
# It uses 'cd /tmp' but since the previous test worked, this should be clean.
$PYTHON_CMD -c "from pyb import pyb; \
pyb('''\
cd /tmp\n\
ls -a\n\
echo \"Script finished!\"\
''')"

echo "--- Automated Fix and Test Complete ---"
