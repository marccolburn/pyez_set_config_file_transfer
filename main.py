import csv
import os
import tempfile
import glob
import logging
import argparse
import paramiko
import time
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.utils.scp import SCP
from jnpr.junos.exception import ConnectError
from jnpr.junos.exception import LockError
from jnpr.junos.exception import UnlockError
from jnpr.junos.exception import ConfigLoadError
from jnpr.junos.exception import CommitError


def enable_netconf_ssh(hostname, mgmt_ip, username, password, timeout=30):
    """
    Enable NETCONF over SSH on a Juniper device using direct SSH connection.
    This is needed before PyEZ can connect to devices that don't have NETCONF enabled.
    
    Args:
        hostname (str): Device hostname for logging
        mgmt_ip (str): Management IP address
        username (str): SSH username
        password (str): SSH password
        timeout (int): Connection timeout in seconds
        
    Returns:
        bool: True if NETCONF was enabled successfully, False otherwise
    """
    try:
        print(f"Enabling NETCONF on {hostname} ({mgmt_ip}) via SSH...")
        logging.info(f"Attempting to enable NETCONF on {hostname} via SSH")
        
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect via SSH
        ssh.connect(
            hostname=mgmt_ip,
            username=username,
            password=password,
            timeout=timeout,
            look_for_keys=False,
            allow_agent=False
        )
        
        logging.info(f"SSH connection established to {hostname}")
        
        # Create interactive shell
        shell = ssh.invoke_shell()
        time.sleep(2)  # Wait for shell to be ready
        
        # Send commands to enable NETCONF
        commands = [
            "configure",
            "set system services netconf ssh",
            "commit",
            "exit"
        ]
        
        for cmd in commands:
            logging.debug(f"Sending command to {hostname}: {cmd}")
            shell.send(cmd + '\n')
            time.sleep(2)  # Wait for command to execute
            
            # Read output
            if shell.recv_ready():
                output = shell.recv(4096).decode('utf-8')
                logging.debug(f"Command output: {output}")
                
                # Check for errors
                if 'error' in output.lower() or 'invalid' in output.lower():
                    logging.warning(f"Possible error in command output: {output}")
        
        # Final read to get any remaining output
        time.sleep(3)
        if shell.recv_ready():
            final_output = shell.recv(4096).decode('utf-8')
            logging.debug(f"Final output: {final_output}")
        
        shell.close()
        ssh.close()
        
        print(f"✓ NETCONF configuration applied to {hostname}")
        logging.info(f"NETCONF enablement completed for {hostname}")
        
        # Wait a bit for NETCONF service to start
        print(f"Waiting for NETCONF service to start on {hostname}...")
        time.sleep(5)
        
        return True
        
    except paramiko.AuthenticationException:
        print(f"✗ Authentication failed for {hostname}")
        logging.error(f"SSH authentication failed for {hostname}")
        return False
        
    except paramiko.SSHException as ssh_err:
        print(f"✗ SSH connection failed for {hostname}: {ssh_err}")
        logging.error(f"SSH connection error for {hostname}: {ssh_err}")
        return False
        
    except Exception as err:
        print(f"✗ Error enabling NETCONF on {hostname}: {err}")
        logging.error(f"Error enabling NETCONF on {hostname}: {err}")
        return False


def check_netconf_connectivity(hostname, mgmt_ip, username, password, timeout=10):
    """
    Check if NETCONF is available on a device by attempting a PyEZ connection.
    
    Args:
        hostname (str): Device hostname for logging
        mgmt_ip (str): Management IP address
        username (str): Username for authentication
        password (str): Password for authentication
        timeout (int): Connection timeout in seconds
        
    Returns:
        bool: True if NETCONF is available, False otherwise
    """
    try:
        logging.info(f"Testing NETCONF connectivity to {hostname}")
        dev = Device(host=mgmt_ip, user=username, password=password, timeout=timeout)
        dev.open()
        dev.close()
        logging.info(f"NETCONF connectivity confirmed for {hostname}")
        return True
    except ConnectError:
        logging.info(f"NETCONF not available on {hostname}")
        return False
    except Exception as err:
        logging.warning(f"Error testing NETCONF on {hostname}: {err}")
        return False


def convert_junos_text_to_set(config_text):
    """
    Convert Junos text configuration to set commands.
    Handles hierarchical structure properly.
    """
    set_commands = []
    lines = config_text.strip().split('\n')
    path_stack = []
    
    for line in lines:
        line = line.rstrip()
        
        # Skip empty lines and comments
        if not line or line.strip().startswith('#'):
            continue
        
        # Calculate indentation level (assuming 4 spaces per level)
        indent = len(line) - len(line.lstrip())
        level = indent // 4
        
        # Adjust path stack to current level
        while len(path_stack) > level:
            path_stack.pop()
        
        content = line.strip()
        
        if content.endswith('{'):
            # Start of a configuration block
            block_name = content[:-1].strip()
            path_stack.append(block_name)
        elif content == '}':
            # End of block - already handled by indentation
            continue
        elif content.endswith(';'):
            # Configuration statement
            statement = content[:-1].strip()
            full_path = ' '.join(path_stack + [statement])
            set_commands.append(f"set {full_path}")
        elif content and not content.startswith('#'):
            # Handle any other content
            full_path = ' '.join(path_stack + [content])
            if not full_path.endswith('{') and not full_path.endswith('}'):
                set_commands.append(f"set {full_path}")
    
    return set_commands


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
    host_config_dir = os.path.join(config_dir, hostname)
    if not os.path.exists(host_config_dir):
        print(f"Warning: Config directory {host_config_dir} does not exist")
        return []
    
    config_files = glob.glob(os.path.join(host_config_dir, "*.config"))
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
        config_file_path (str): Path to configuration file to load
        hostname (str): Device hostname for logging
        
    Returns:
        str: Path to the set format file on device, or None if failed
    """
    config_filename = os.path.basename(config_file_path)
    set_filename = config_filename.replace('.config', '.set.config')
    remote_set_path = f'/tmp/{set_filename}'
    
    try:
        print(f"Processing {config_filename} on {hostname}...")
        logging.info(f"Starting to process {config_filename} on {hostname}")
        
        # Check if config file exists and is readable
        if not os.path.exists(config_file_path):
            logging.error(f"Config file does not exist: {config_file_path}")
            return None
            
        with open(config_file_path, 'r') as f:
            config_content = f.read()
            logging.info(f"Config file size: {len(config_content)} characters")
            logging.debug(f"Config content preview: {config_content[:200]}...")
        
        # Initialize config utility
        config = Config(dev)
        logging.info(f"Attempting to lock configuration on {hostname}")
        config.lock()
        logging.info(f"Configuration locked successfully on {hostname}")
        
        # Load configuration from file
        print(f"Loading configuration from {config_file_path}")
        logging.info(f"Loading configuration from {config_file_path}")
        config.load(path=str(config_file_path), format='text')
        logging.info(f"Configuration loaded successfully from {config_file_path}")
        
        # Check if there are any pending changes
        logging.info("Checking for configuration differences...")
        try:
            diff_output = config.diff()
            if diff_output:
                logging.info(f"Configuration diff found: {len(diff_output)} characters")
                logging.debug(f"Diff preview: {diff_output[:300]}...")
            else:
                logging.warning("No configuration differences found after loading")
        except Exception as diff_err:
            logging.warning(f"Could not get diff: {diff_err}")
        
        # Convert the configuration file directly to set format
        print(f"Converting {config_filename} to set format")
        logging.info("Converting configuration file directly to set commands")
        
        # Use our reliable text-to-set converter
        try:
            set_commands = convert_junos_text_to_set(config_content)
            
            if set_commands:
                set_config = '\n'.join(set_commands)
                logging.info(f"Successfully converted config to {len(set_commands)} set commands")
                logging.debug(f"Set commands preview: {set_config[:300]}...")
            else:
                logging.warning("Config conversion resulted in no set commands")
                config.rollback()
                config.unlock()
                return None
                
        except Exception as convert_err:
            logging.error(f"Error converting config to set format: {convert_err}")
            config.rollback()
            config.unlock()
            return None
        
        if set_config.strip():
            logging.info("Set configuration found, creating temporary file")
            # Create a temporary local file with set format config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.set', delete=False) as temp_file:
                temp_file.write(set_config)
                temp_local_path = temp_file.name
            
            logging.info(f"Temporary file created: {temp_local_path}")
            
            # Copy to device using SCP
            logging.info(f"Copying set config to device at {remote_set_path}")
            with SCP(dev) as scp:
                scp.put(temp_local_path, remote_set_path)
            
            # Clean up local temp file
            os.remove(temp_local_path)
            logging.info("Temporary local file cleaned up")
        else:
            print(f"No configuration found or empty configuration for {config_filename}")
            logging.warning(f"Empty set configuration for {config_filename}")
            config.rollback()
            config.unlock()
            return None
        
        # Rollback the pending changes
        print(f"Rolling back changes on {hostname}")
        logging.info(f"Rolling back configuration changes on {hostname}")
        config.rollback()
        config.unlock()
        logging.info(f"Configuration unlocked on {hostname}")
        
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
        host_output_dir = os.path.join(local_dir, hostname)
        if not os.path.exists(host_output_dir):
            os.makedirs(host_output_dir)
        
        # Extract filename from remote path
        filename = os.path.basename(remote_path)
        local_path = os.path.join(host_output_dir, filename)
        
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


def process_device(device_info, config_dir, output_dir, username, password, enable_netconf=False):
    """
    Process all configuration files for a single device.
    
    Args:
        device_info (dict): Dictionary with hostname and mgmt_ip
        config_dir (str): Directory containing configuration files
        output_dir (str): Directory to save output files
        username (str): Username for device authentication
        password (str): Password for device authentication
        enable_netconf (bool): Whether to enable NETCONF if not available
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
    
    # Check if NETCONF enablement is requested
    if enable_netconf:
        print(f"Checking NETCONF connectivity for {hostname}...")
        if not check_netconf_connectivity(hostname, mgmt_ip, username, password):
            print(f"NETCONF not available on {hostname}, attempting to enable...")
            if not enable_netconf_ssh(hostname, mgmt_ip, username, password):
                print(f"Failed to enable NETCONF on {hostname}, skipping device...")
                return
            
            # Test connectivity again after enabling
            print(f"Testing NETCONF connectivity after enablement...")
            if not check_netconf_connectivity(hostname, mgmt_ip, username, password):
                print(f"NETCONF still not available on {hostname} after enablement, skipping...")
                return
            else:
                print(f"✓ NETCONF is now available on {hostname}")
        else:
            print(f"✓ NETCONF already available on {hostname}")
    
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Juniper Configuration Set Format Converter')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--enable-netconf', action='store_true', help='Enable NETCONF on devices if not available')
    parser.add_argument('--username', default='lab', help='Device username (default: lab)')
    parser.add_argument('--password', default='lab123', help='Device password (default: lab123)')
    parser.add_argument('--csv-file', default='devices.csv', help='CSV file with device info (default: devices.csv)')
    parser.add_argument('--config-dir', default='configs', help='Config directory (default: configs)')
    parser.add_argument('--output-dir', default='output', help='Output directory (default: output)')
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    log_level = logging.DEBUG if args.debug else logging.INFO
    
    # Reconfigure logging
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pyez_debug.log'),
            logging.StreamHandler()
        ]
    )
    
    # Configuration parameters
    CSV_FILE = args.csv_file
    CONFIG_DIR = args.config_dir
    OUTPUT_DIR = args.output_dir
    USERNAME = args.username
    PASSWORD = args.password
    
    print("Starting Juniper Configuration Processing Script")
    print(f"CSV File: {CSV_FILE}")
    print(f"Config Directory: {CONFIG_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Debug Mode: {'Enabled' if args.debug else 'Disabled'}")
    print(f"NETCONF Enablement: {'Enabled' if args.enable_netconf else 'Disabled'}")
    
    if args.enable_netconf:
        print("\n⚠️  NETCONF Enablement Warning:")
        print("This will attempt to enable NETCONF on devices that don't have it.")
        print("This requires SSH access and will modify device configurations.")
        print("Press Ctrl+C within 5 seconds to cancel...")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return
    
    logging.info("Script started with the following parameters:")
    logging.info(f"CSV File: {CSV_FILE}, Config Dir: {CONFIG_DIR}, Output Dir: {OUTPUT_DIR}")
    logging.info(f"Username: {USERNAME}, Debug: {args.debug}, Enable NETCONF: {args.enable_netconf}")
    
    # Read device information from CSV
    devices = read_device_csv(CSV_FILE)
    if not devices:
        print("No devices found. Exiting.")
        return
    
    # Create output directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Process each device
    for device_info in devices:
        try:
            process_device(device_info, CONFIG_DIR, OUTPUT_DIR, USERNAME, PASSWORD, args.enable_netconf)
        except KeyboardInterrupt:
            print("\nScript interrupted by user")
            break
        except Exception as err:
            print(f"Unexpected error processing device {device_info.get('hostname', 'unknown')}: {err}")
            continue
    
    print("\nScript completed!")


if __name__ == "__main__":
    main()