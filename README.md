# Juniper Configuration Set Format Converter

This script connects to Juniper devices, loads configuration files, saves them in set format, and transfers the set format files back to the local machine.

## Features

- Reads device information from a CSV file
- Processes multiple configuration files per device
- Loads configurations without committing changes
- Saves candidate configurations in set format
- Transfers set format files to local machine
- Automatically rolls back changes after processing
- Organizes output files by hostname

## Prerequisites

### Python 3.6 Compatibility (CentOS 7)

If you're running Python 3.6 on CentOS 7, you'll need to use specific package versions to avoid compatibility issues:

#### Option 1: Automatic Setup (Recommended)
```bash
chmod +x setup_python36.sh
./setup_python36.sh
```

#### Option 2: Manual Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python 3.6 compatible versions
pip install -r requirements.txt
```

#### Option 3: Check Compatibility
```bash
python3 check_compatibility.py
```

### General Requirements
1. Network connectivity to your Juniper devices
2. Valid credentials for device access
3. SCP enabled on Juniper devices

## Directory Structure

```
project/
├── main.py                    # Main script
├── requirements.txt           # Python dependencies
├── devices.csv               # Device information (hostname, mgmt_ip)
├── configs/                  # Configuration files directory
│   ├── router1/             # Directory for router1 configs
│   │   ├── chapter1-start.config
│   │   └── chapter1-end.config
│   ├── router2/             # Directory for router2 configs
│   │   ├── chapter1-start.config
│   │   └── chapter1-end.config
│   └── ...
└── output/                   # Output directory for set format files
    ├── router1/             # Set format files from router1
    │   ├── chapter1-start.set.config
    │   └── chapter1-end.set.config
    └── ...
```

## Configuration

Edit the configuration parameters in the `main()` function:

```python
CSV_FILE = 'devices.csv'     # CSV file with device information
CONFIG_DIR = 'configs'       # Directory containing config files
OUTPUT_DIR = 'output'        # Directory to save set format files
USERNAME = 'admin'           # Device username
PASSWORD = 'password'        # Device password
```

## CSV File Format

The `devices.csv` file should contain two columns:
- `hostname`: Device hostname (used for directory organization)
- `mgmt_ip`: Management IP address for device connection

Example:
```csv
hostname,mgmt_ip
router1,192.168.1.10
router2,192.168.1.11
router3,192.168.1.12
```

## Usage

1. Update the `devices.csv` file with your router information
2. Create directories under `configs/` for each hostname
3. Place your Juniper configuration files (*.config) in the respective hostname directories
4. Update the credentials in the script
5. Run the script:
   ```bash
   python main.py
   ```

## Output

The script will:
1. Connect to each device listed in the CSV
2. Load each .config file found in the device's directory
3. Save the candidate configuration in set format
4. Transfer the set format file to the local `output/hostname/` directory
5. Rollback the changes on the device
6. The output files will have ".set" added before ".config" in the filename

For example:
- Input: `configs/router1/chapter1-start.config`
- Output: `output/router1/chapter1-start.set.config`

## Functions Overview

- `read_device_csv()`: Reads device information from CSV
- `get_config_files()`: Gets list of config files for a hostname
- `connect_to_device()`: Establishes connection to Juniper device
- `process_config_file()`: Loads config, saves in set format, rolls back
- `transfer_file_from_device()`: Transfers file from device to local machine
- `cleanup_remote_file()`: Removes temporary files from device
- `process_device()`: Orchestrates processing for a single device
- `main()`: Main workflow coordination

## Error Handling

The script includes comprehensive error handling for:
- Network connectivity issues
- Authentication failures
- File system errors
- Configuration loading errors
- File transfer failures

## Troubleshooting

### Python 3.6 Issues

If you encounter errors like:
```
AttributeError: module 'typing' has no attribute 'NoReturn'
```

This indicates that newer versions of cryptography/PyEZ are being installed that require Python 3.7+. Use the provided `setup_python36.sh` script or manually install the pinned versions in `requirements.txt`.

### Common Solutions:

1. **Clean installation:**
   ```bash
   rm -rf venv/
   ./setup_python36.sh
   ```

2. **Check your Python version:**
   ```bash
   python3 --version
   python3 check_compatibility.py
   ```

3. **Verify package versions:**
   ```bash
   source venv/bin/activate
   pip list | grep -E "(cryptography|junos-eznc|paramiko)"
   ```

### Expected Compatible Versions for Python 3.6:
- cryptography==3.4.8
- junos-eznc==2.6.3
- paramiko==2.11.0
- lxml==4.6.5
- ncclient==0.6.13

## Notes

- The script uses SCP for file transfers, ensure SCP is enabled on your devices
- Temporary files are created in `/tmp/` on the remote devices
- The script automatically creates output directories as needed
- All configuration changes are rolled back - no changes are committed to devices
