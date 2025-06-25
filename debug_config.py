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
            
            # Try to get candidate config in set format
            candidate_set_rpc = dev.rpc.get_config(format='set')
            candidate_set = candidate_set_rpc.text if candidate_set_rpc.text else ""
            print(f"Candidate config set format length: {len(candidate_set)}")
            
            if candidate_set:
                print("Candidate config sample (first 300 chars):")
                print(candidate_set[:300])
                
                # Look for our test config
                if "TEST-HOST" in candidate_set:
                    print("✓ Found our test configuration in candidate!")
                else:
                    print("⚠ Test configuration not found in candidate")
            else:
                print("✗ Candidate config is empty!")
                
            # Check diff
            diff = config.diff()
            if diff:
                print(f"Configuration diff length: {len(diff)}")
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
        
        dev.close()
        print("\n✓ Connection closed")
        
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_config_retrieval()
