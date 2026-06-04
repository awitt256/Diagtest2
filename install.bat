@echo off
python - <<EOF
import sys
if sys.version_info >= (3,13):
    print("ERROR: Python 3.13+ detected.")
    print("pygame does not support this version.")
    print("Install Python 3.12.x instead.")
    sys.exit(1)
print("Python version OK")
EOF

python -m pip install --upgrade pip
python -m pip install customtkinter Pillow pygame opencv-python
pause