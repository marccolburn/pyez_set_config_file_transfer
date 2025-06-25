#!/usr/bin/env python3
"""
Alternative script that checks Python version and provides appropriate error messages.
This can help diagnose version-specific issues.
"""

import sys
import subprocess

def check_python_version():
    """Check if we're running a compatible Python version."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3:
        print("ERROR: Python 3 is required")
        return False
    
    if version.major == 3 and version.minor < 6:
        print("ERROR: Python 3.6 or later is required")
        return False
    
    if version.major == 3 and version.minor == 6:
        print("WARNING: Python 3.6 detected - using compatibility mode")
        return "compat"
    
    print("Python version is compatible")
    return True

def install_compatible_packages():
    """Install packages compatible with the current Python version."""
    version = sys.version_info
    
    if version.major == 3 and version.minor == 6:
        print("Installing Python 3.6 compatible packages...")
        packages = [
            "cryptography==3.4.8",
            "paramiko==2.11.0", 
            "lxml==4.6.5",
            "ncclient==0.6.13",
            "pyserial==3.5",
            "scp==0.13.6",
            "junos-eznc==2.6.3"
        ]
    else:
        print("Installing latest compatible packages...")
        packages = [
            "junos-eznc",
            "pandas"
        ]
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("PyEZ Compatibility Checker and Installer")
    print("=" * 40)
    
    # Check Python version
    version_check = check_python_version()
    
    if version_check is False:
        print("Please upgrade Python and try again.")
        sys.exit(1)
    
    # Test if we can import required modules
    try:
        print("Testing imports...")
        from jnpr.junos import Device
        print("✓ junos-eznc is working")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        
        response = input("Would you like to install compatible packages? (y/n): ")
        if response.lower() == 'y':
            if install_compatible_packages():
                print("Installation completed. Please run the script again.")
            else:
                print("Installation failed. Please check the errors above.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Other error: {e}")
        sys.exit(1)
    
    print("✓ All imports successful - PyEZ is ready to use!")
