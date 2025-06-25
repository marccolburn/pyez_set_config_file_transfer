#!/bin/bash

# Setup script for Python 3.6 compatibility on CentOS 7

echo "Setting up PyEZ environment for Python 3.6 on CentOS 7..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip to avoid issues
echo "Upgrading pip..."
pip install --upgrade pip

# Install compatible versions of dependencies
echo "Installing Python 3.6 compatible packages..."

# Install specific versions that work with Python 3.6
pip install "cryptography==3.4.8"
pip install "paramiko==2.11.0"
pip install "lxml==4.6.5"
pip install "ncclient==0.6.13"
pip install "pyserial==3.5"
pip install "scp==0.13.6"

# Install junos-eznc last after dependencies are set
pip install "junos-eznc==2.6.3"

echo "Installation complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "source venv/bin/activate"
echo ""
echo "To test the installation, you can run:"
echo "python -c 'from jnpr.junos import Device; print(\"PyEZ imported successfully!\")'"
