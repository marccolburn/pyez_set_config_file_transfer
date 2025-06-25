#!/usr/bin/env python3
"""
Test script for diff-to-set conversion
"""

def convert_diff_to_set_commands(diff_output):
    """
    Convert Junos configuration diff output to set commands.
    """
    if not diff_output:
        return ""
    
    set_commands = []
    current_path = []
    
    for line in diff_output.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Handle [edit ...] lines to track hierarchy
        if line.startswith('[edit'):
            # Extract the path from [edit path]
            path_match = line[5:-1]  # Remove [edit and ]
            if path_match:
                current_path = path_match.split()
            else:
                current_path = []
        
        # Handle additions (+ lines)
        elif line.startswith('+'):
            config_line = line[1:].strip()
            if config_line and not config_line.startswith('['):
                # Parse the configuration line
                set_cmd = build_set_command(current_path, config_line)
                if set_cmd:
                    set_commands.append(set_cmd)
    
    return '\n'.join(set_commands)

def build_set_command(path, config_line):
    """
    Build a set command from a hierarchical path and config line.
    """
    # Remove trailing semicolon and clean up
    config_line = config_line.rstrip(';').strip()
    
    if not config_line:
        return None
    
    # Handle different types of configuration lines
    if '{' in config_line:
        # This is a hierarchy opening, extract the key
        key = config_line.split('{')[0].strip()
        full_path = path + [key]
        return f"set {' '.join(full_path)}"
    
    elif '=' in config_line:
        # This might be an assignment (rare in Junos)
        parts = config_line.split('=', 1)
        key = parts[0].strip()
        value = parts[1].strip().strip('"')
        full_path = path + [key]
        return f"set {' '.join(full_path)} {value}"
        
    else:
        # Regular configuration line
        parts = config_line.split()
        if parts:
            # Check if this is a leaf with a value
            if len(parts) > 1:
                # Multi-word configuration
                key = parts[0]
                value = ' '.join(parts[1:])
                full_path = path + [key]
                return f"set {' '.join(full_path)} {value}"
            else:
                # Single word configuration
                full_path = path + parts
                return f"set {' '.join(full_path)}"
    
    return None

def test_diff_conversion():
    """Test the diff to set conversion with sample data"""
    
    # Sample diff output from your debug
    test_diff = """
[edit system]
-  host-name R1;
+  host-name TEST-HOST;
"""
    
    print("Testing diff-to-set conversion:")
    print("Input diff:")
    print(test_diff)
    print("\nConverted set commands:")
    
    set_commands = convert_diff_to_set_commands(test_diff)
    print(set_commands)
    
    # Test with more complex diff
    complex_diff = """
[edit interfaces ge-0/0/0 unit 0 family inet]
+   address 192.168.1.1/24;
[edit protocols ospf area 0.0.0.0]
+   interface ge-0/0/0.0;
[edit system]
+   ntp {
+       server 192.168.1.100;
+   }
"""
    
    print("\n" + "="*50)
    print("Testing complex diff:")
    print("Input diff:")
    print(complex_diff)
    print("\nConverted set commands:")
    
    set_commands = convert_diff_to_set_commands(complex_diff)
    print(set_commands)

if __name__ == "__main__":
    test_diff_conversion()
