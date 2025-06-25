#!/usr/bin/env python3
"""
Simple test script to debug the get_config issue
"""

from jnpr.junos import Device
from jnpr.junos.utils.config import Config

def test_config_retrieval():
    """Test getting configuration in different formats"""
    
    # Replace with your actual device details
    hostname = "10.10.1.1"  # or whatever your R1 IP is
    username = "lab"
    password = "lab123"
    
    print(f"Connecting to {hostname}...")
    
    try:
        dev = Device(host=hostname, user=username, password=password)
        dev.open()
        print("✓ Connected successfully")
        
        # Test 1: Get current running config in set format
        print("\n--- Test 1: Running config in set format ---")
        try:
            running_set_rpc = dev.rpc.get_config(format='set')
            running_set = running_set_rpc.text if running_set_rpc.text else ""
            print(f"Running config set format length: {len(running_set)}")
            if running_set:
                print("Sample (first 200 chars):")
                print(running_set[:200])
        except Exception as e:
            print(f"Error getting running config: {e}")
        
        # Test 2: Get current running config in text format  
        print("\n--- Test 2: Running config in text format ---")
        try:
            running_text_rpc = dev.rpc.get_config(format='text')
            running_text = running_text_rpc.text if running_text_rpc.text else ""
            print(f"Running config text format length: {len(running_text)}")
            if running_text:
                print("Sample (first 200 chars):")
                print(running_text[:200])
        except Exception as e:
            print(f"Error getting running config in text: {e}")
            
        # Test 3: Load a candidate config and then get it
        print("\n--- Test 3: Candidate config test ---")
        try:
            config = Config(dev)
            config.lock()
            print("✓ Configuration locked")
            
            # Load a simple test config
            test_config = """
system {
    host-name TEST-HOST;
}
"""
            config.load(test_config, format='text')
            print("✓ Test configuration loaded")
            
            # Try to get candidate config in set format via RPC
            candidate_set_rpc = dev.rpc.get_config(format='set')
            candidate_set = candidate_set_rpc.text if candidate_set_rpc.text else ""
            print(f"Candidate config set format (RPC) length: {len(candidate_set)}")
            
            if candidate_set:
                print("Candidate config sample (first 300 chars):")
                print(candidate_set[:300])
            else:
                print("✗ RPC method returned empty candidate config")
                
                # Try CLI method instead
                print("\n--- Test 4: CLI method for set format ---")
                try:
                    cli_result = dev.cli("show configuration | display set", warning=False)
                    print(f"CLI method returned {len(cli_result)} characters")
                    if cli_result:
                        print("CLI set format sample (first 300 chars):")
                        print(cli_result[:300])
                        
                        if "TEST-HOST" in cli_result:
                            print("✓ Found our test configuration via CLI!")
                        else:
                            print("⚠ Test configuration not found in CLI output")
                    else:
                        print("✗ CLI method also returned empty")
                except Exception as cli_err:
                    print(f"CLI method error: {cli_err}")
                
            # Check diff
            diff = config.diff()
            if diff:
                print(f"\nConfiguration diff length: {len(diff)}")
                print("Diff sample:")
                print(diff[:200])
            else:
                print("No configuration differences found")
                
            # Rollback
            config.rollback()
            config.unlock()
            print("✓ Configuration rolled back and unlocked")
            
        except Exception as e:
            print(f"Error in candidate config test: {e}")
            try:
                config.rollback()
                config.unlock()
            except:
                pass
        
        # Test 4: Temporary commit method
        print("\n--- Test 4: Temporary commit method ---")
        try:
            config = Config(dev)
            config.lock()
            print("✓ Configuration locked for commit test")
            
            # Load a simple test config
            test_config = """
system {
    host-name TEST-HOST-COMMIT;
}
"""
            config.load(test_config, format='text')
            print("✓ Test configuration loaded for commit test")
            
            # Check diff first
            diff = config.diff()
            if diff:
                print(f"Configuration diff before commit: {len(diff)} chars")
                print("Diff sample:")
                print(diff[:200])
                
                # Commit the config temporarily
                print("Committing configuration...")
                config.commit()
                print("✓ Configuration committed")
                
                # Now get the set format
                cli_result = dev.cli("show configuration | display set")
                if cli_result:
                    print(f"Post-commit set config length: {len(cli_result)}")
                    
                    # Look for our test config
                    if "TEST-HOST-COMMIT" in cli_result:
                        print("✓ Found our test configuration in committed config!")
                        print("Sample of set commands containing our change:")
                        for line in cli_result.split('\n'):
                            if "TEST-HOST-COMMIT" in line:
                                print(f"  {line}")
                    else:
                        print("⚠ Test configuration not found in committed config")
                        
                    # Show a sample of the set config
                    print("Set config sample (first 300 chars):")
                    print(cli_result[:300])
                else:
                    print("✗ CLI command returned empty after commit")
                
                # Rollback to previous state
                print("Rolling back...")
                dev.cli("rollback 1")
                dev.cli("commit")
                print("✓ Rollback completed")
                
                # Verify rollback worked
                current_hostname = dev.cli("show configuration system host-name")
                print(f"Current hostname after rollback: {current_hostname.strip()}")
                
            else:
                print("No configuration differences found")
                config.rollback()
                config.unlock()
                
        except Exception as e:
            print(f"Error in temporary commit test: {e}")
            try:
                # Emergency rollback
                dev.cli("rollback 1")
                dev.cli("commit")
                print("Emergency rollback attempted")
            except:
                pass

        dev.close()
        print("\n✓ Connection closed")
        
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_config_retrieval()
