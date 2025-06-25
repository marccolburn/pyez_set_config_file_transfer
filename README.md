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

1. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure you have network connectivity to your Juniper devices
3. Have valid credentials for device access

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

## Notes

- The script uses SCP for file transfers, ensure SCP is enabled on your devices
- Temporary files are created in `/tmp/` on the remote devices
- The script automatically creates output directories as needed
- All configuration changes are rolled back - no changes are committed to devices
