#!/bin/bash

# Chrome OS Keyboard Tester - Automated Setup Script for Crostini
# This script automates Python and dependency installation in Crostini

echo "========================================"
echo "Chrome OS Keyboard Tester Setup"
echo "========================================"
echo ""

# Check if running in Crostini
if [ ! -d /opt/google/cros-containers ]; then
    echo "ERROR: This script must be run in Crostini (Linux on Chrome OS)"
    echo ""
    echo "To enable Crostini:"
    echo "1. Open Chrome OS Settings"
    echo "2. Go to 'Linux (Beta)' section"
    echo "3. Click 'Turn on' to set up Crostini"
    echo "4. Once setup is complete, open Terminal and run this script again"
    echo ""
    exit 1
fi

echo "Crostini detected. Proceeding with setup..."
echo ""

# Update package lists
echo "Updating package lists..."
sudo apt update

# Install Python 3 and pip if not already installed
echo "Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-tk

# Install pynput for keyboard capture
echo "Installing pynput library..."
pip3 install pynput --user

# Create a launcher script
echo "Creating launcher script..."
cat > ~/keyboard_tester.sh << 'EOF'
#!/bin/bash
cd ~/Downloads/  # Adjust this path to where you saved the files
python3 ChromeOS_Keyboard_Test.py
EOF

chmod +x ~/keyboard_tester.sh

# Create desktop shortcut
echo "Creating desktop shortcut..."
cat > ~/Desktop/KeyboardTester.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Keyboard Tester
Comment=Chrome OS Keyboard Tester
Exec=/home/$USER/keyboard_tester.sh
Icon=applications-utilities
Terminal=true
Categories=Utility;
EOF

chmod +x ~/Desktop/KeyboardTester.desktop

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "What was installed:"
echo "- Python 3"
echo "- pip (Python package manager)"
echo "- pynput library (for keyboard capture)"
echo ""
echo "To run the keyboard tester:"
echo "1. Copy ChromeOS_Keyboard_Test.py to your Downloads folder"
echo "2. Double-click 'Keyboard Tester' on your desktop"
echo "   OR run: ~/keyboard_tester.sh"
echo ""
echo "Note: You may need to adjust the path in ~/keyboard_tester.sh"
echo "if you saved the files in a different location."
echo ""
