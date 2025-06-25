#!/bin/bash

# Enhanced setup script for Python 3.6 compatibility on CentOS 7
# This script handles all the dependency conflicts

echo "Enhanced PyEZ setup for Python 3.6 on CentOS 7..."
echo "This will clean any existing installation and install compatible versions"

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create fresh virtual environment
echo "Creating new virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip to latest compatible version for Python 3.6
echo "Upgrading pip..."
pip install --upgrade "pip<21.0"

# Install dependencies in specific order to avoid conflicts
echo "Installing base dependencies..."

# Install lowest level dependencies first
pip install "setuptools==59.6.0"
pip install "wheel==0.37.1"

# Install cryptographic dependencies in order
echo "Installing cryptographic stack..."
pip install "pycparser==2.21"
pip install "cffi==1.14.6"
pip install "six==1.16.0"
pip install "cryptography==3.4.8"

# Install PyNaCl before paramiko (critical for Python 3.6)
echo "Installing PyNaCl..."
pip install "PyNaCl==1.4.0"

# Install bcrypt
echo "Installing bcrypt..."
pip install "bcrypt==3.2.2"

# Install paramiko
echo "Installing paramiko..."
pip install "paramiko==2.11.0"

# Install other dependencies
echo "Installing other dependencies..."
pip install "pyserial==3.5"
pip install "scp==0.13.6"

# Install XML processing
echo "Installing XML processing..."
pip install "lxml==4.6.5"

# Install NETCONF client
echo "Installing NETCONF client..."
pip install "ncclient==0.6.13"

# Finally install junos-eznc
echo "Installing junos-eznc..."
pip install "junos-eznc==2.6.3"

echo ""
echo "Installation complete!"
echo ""

# Test the installation
echo "Testing installation..."
python -c "
try:
    from jnpr.junos import Device
    print('✓ junos-eznc imported successfully')
    
    import paramiko
    print('✓ paramiko imported successfully')
    
    from jnpr.junos.utils.config import Config
    print('✓ Config utility imported successfully')
    
    from jnpr.junos.utils.scp import SCP
    print('✓ SCP utility imported successfully')
    
    print('')
    print('All imports successful! PyEZ is ready to use.')
    
except ImportError as e:
    print(f'✗ Import failed: {e}')
    exit(1)
except Exception as e:
    print(f'✗ Other error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "Setup completed successfully!"
    echo ""
    echo "To activate the environment in the future, run:"
    echo "source venv/bin/activate"
    echo ""
    echo "You can now run your PyEZ script with:"
    echo "python main.py"
else
    echo ""
    echo "Setup failed. Please check the error messages above."
    exit 1
fi
