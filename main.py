import csv
import os
import tempfile
from pathlib import Path
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.utils.scp import SCP
from jnpr.junos.exception import ConnectError
from jnpr.junos.exception import LockError
from jnpr.junos.exception import UnlockError
from jnpr.junos.exception import ConfigLoadError
from jnpr.junos.exception import CommitError


def read_device_csv(csv_file):
    """
    Read CSV file containing hostname and management IP addresses.
    
    Args:
        csv_file (str): Path to CSV file with columns: hostname, mgmt_ip
        
    Returns:
        list: List of dictionaries with hostname and mgmt_ip keys
    """
    devices = []
    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                devices.append({
                    'hostname': row['hostname'].strip(),
                    'mgmt_ip': row['mgmt_ip'].strip()
                })
        print(f"Loaded {len(devices)} devices from {csv_file}")
        return devices
    except FileNotFoundError:
        print(f"Error: CSV file {csv_file} not found")
        return []
    except Exception as err:
        print(f"Error reading CSV file: {err}")
        return []


def get_config_files(hostname, config_dir):
    """
    Get list of configuration files for a specific hostname.
    
    Args:
        hostname (str): Device hostname
        config_dir (str): Base directory containing config files
        
    Returns:
        list: List of configuration file paths for the hostname
    """
    host_config_dir = Path(config_dir) / hostname
    if not host_config_dir.exists():
        print(f"Warning: Config directory {host_config_dir} does not exist")
        return []
    
    config_files = list(host_config_dir.glob("*.config"))
    print(f"Found {len(config_files)} config files for {hostname}")
    return config_files


def connect_to_device(hostname, mgmt_ip, username, password):
    """
    Establish connection to Juniper device.
    
    Args:
        hostname (str): Device hostname
        mgmt_ip (str): Management IP address
        username (str): Username for authentication
        password (str): Password for authentication
        
    Returns:
        Device: Connected Junos device object or None if failed
    """
    dev = Device(host=mgmt_ip, user=username, password=password)
    try:
        print(f"Connecting to {hostname} ({mgmt_ip})...")
        dev.open()
        print(f"Successfully connected to {hostname}")
        return dev
    except ConnectError as err:
        print(f"Cannot connect to {hostname} ({mgmt_ip}): {err}")
        return None


def process_config_file(dev, config_file_path, hostname):
    """
    Load configuration, save in set format, and rollback changes.
    
    Args:
        dev (Device): Connected Junos device
        config_file_path (Path): Path to configuration file to load
        hostname (str): Device hostname for logging
        
    Returns:
        str: Path to the set format file on device, or None if failed
    """
    config_filename = config_file_path.name
    set_filename = config_filename.replace('.config', '.set.config')
    remote_set_path = f'/tmp/{set_filename}'
    
    try:
        print(f"Processing {config_filename} on {hostname}...")
        
        # Initialize config utility
        config = Config(dev)
        config.lock()
        
        # Load configuration from file
        print(f"Loading configuration from {config_file_path}")
        config.load(path=str(config_file_path), format='text')
        
        # Save candidate configuration in set format
        print(f"Saving candidate config in set format to {remote_set_path}")
        
        # Execute "show configuration | display set" to get candidate config in set format
        set_config_rpc = dev.rpc.get_config(format='set')
        set_config = set_config_rpc.text
        
        if set_config and set_config.strip():
            # Create a temporary local file with set format config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.set', delete=False) as temp_file:
                temp_file.write(set_config)
                temp_local_path = temp_file.name
            
            # Copy to device using SCP
            with SCP(dev) as scp:
                scp.put(temp_local_path, remote_set_path)
            
            # Clean up local temp file
            os.remove(temp_local_path)
        else:
            print(f"No configuration found for {config_filename}")
            config.rollback()
            config.unlock()
            return None
        
        # Rollback the pending changes
        print(f"Rolling back changes on {hostname}")
        config.rollback()
        config.unlock()
        
        return remote_set_path
        
    except (LockError, ConfigLoadError, CommitError) as err:
        print(f"Error processing config {config_filename} on {hostname}: {err}")
        try:
            config.rollback()
            config.unlock()
        except:
            pass
        return None
    except Exception as err:
        print(f"Unexpected error processing {config_filename} on {hostname}: {err}")
        try:
            config.rollback()
            config.unlock()
        except:
            pass
        return None


def transfer_file_from_device(dev, remote_path, local_dir, hostname):
    """
    Transfer file from device to local directory.
    
    Args:
        dev (Device): Connected Junos device
        remote_path (str): Path to file on remote device
        local_dir (str): Local directory to save file
        hostname (str): Device hostname for directory structure
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create hostname directory if it doesn't exist
        host_output_dir = Path(local_dir) / hostname
        host_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract filename from remote path
        filename = Path(remote_path).name
        local_path = host_output_dir / filename
        
        print(f"Transferring {remote_path} from {hostname} to {local_path}")
        
        with SCP(dev) as scp:
            scp.get(remote_path, str(local_path))
        
        print(f"Successfully transferred {filename} from {hostname}")
        return True
        
    except Exception as err:
        print(f"Error transferring file from {hostname}: {err}")
        return False


def cleanup_remote_file(dev, remote_path, hostname):
    """
    Remove temporary file from remote device.
    
    Args:
        dev (Device): Connected Junos device
        remote_path (str): Path to file on remote device
        hostname (str): Device hostname for logging
    """
    try:
        print(f"Cleaning up {remote_path} on {hostname}")
        dev.rpc.file_delete(path=remote_path)
    except Exception as err:
        print(f"Warning: Could not cleanup {remote_path} on {hostname}: {err}")


def process_device(device_info, config_dir, output_dir, username, password):
    """
    Process all configuration files for a single device.
    
    Args:
        device_info (dict): Dictionary with hostname and mgmt_ip
        config_dir (str): Directory containing configuration files
        output_dir (str): Directory to save output files
        username (str): Username for device authentication
        password (str): Password for device authentication
    """
    hostname = device_info['hostname']
    mgmt_ip = device_info['mgmt_ip']
    
    print(f"\n{'='*50}")
    print(f"Processing device: {hostname}")
    print(f"{'='*50}")
    
    # Get configuration files for this hostname
    config_files = get_config_files(hostname, config_dir)
    if not config_files:
        print(f"No configuration files found for {hostname}, skipping...")
        return
    
    # Connect to device
    dev = connect_to_device(hostname, mgmt_ip, username, password)
    if not dev:
        return
    
    try:
        # Process each configuration file
        for config_file in config_files:
            # Process the config file
            remote_set_path = process_config_file(dev, config_file, hostname)
            
            if remote_set_path:
                # Transfer the set format file back
                transfer_success = transfer_file_from_device(
                    dev, remote_set_path, output_dir, hostname
                )
                
                # Cleanup remote file
                if transfer_success:
                    cleanup_remote_file(dev, remote_set_path, hostname)
    
    finally:
        # Close connection
        print(f"Closing connection to {hostname}")
        dev.close()


def main():
    """
    Main function to orchestrate the configuration processing workflow.
    """
    # Configuration parameters
    CSV_FILE = 'devices.csv'  # CSV file with hostname, mgmt_ip columns
    CONFIG_DIR = 'configs'    # Directory containing subdirectories for each hostname
    OUTPUT_DIR = 'output'     # Directory to save set format files
    USERNAME = 'lab'        # Device username
    PASSWORD = 'lab123'     # Device password
    
    print("Starting Juniper Configuration Processing Script")
    print(f"CSV File: {CSV_FILE}")
    print(f"Config Directory: {CONFIG_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    
    # Read device information from CSV
    devices = read_device_csv(CSV_FILE)
    if not devices:
        print("No devices found. Exiting.")
        return
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Process each device
    for device_info in devices:
        try:
            process_device(device_info, CONFIG_DIR, OUTPUT_DIR, USERNAME, PASSWORD)
        except KeyboardInterrupt:
            print("\nScript interrupted by user")
            break
        except Exception as err:
            print(f"Unexpected error processing device {device_info.get('hostname', 'unknown')}: {err}")
            continue
    
    print("\nScript completed!")


if __name__ == "__main__":
    main()