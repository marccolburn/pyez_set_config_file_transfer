#!/usr/bin/env python3
"""
Test script for converting Junos text configuration to set commands.
This uses a much simpler and more reliable approach.
"""

def convert_junos_text_to_set(config_text):
    """
    Convert Junos text configuration to set commands.
    Handles hierarchical structure properly.
    """
    set_commands = []
    lines = config_text.strip().split('\n')
    path_stack = []
    
    for line in lines:
        original_line = line
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

def test_conversion():
    """Test the conversion with sample configs"""
    
    # Test 1: Simple config
    simple_config = """
system {
    host-name TEST-ROUTER;
    domain-name example.com;
}
"""
    
    print("=== Test 1: Simple Configuration ===")
    print("Input:")
    print(simple_config)
    print("\nSet commands:")
    commands = convert_junos_text_to_set(simple_config)
    for cmd in commands:
        print(cmd)
    
    # Test 2: Complex nested config  
    complex_config = """
interfaces {
    ge-0/0/0 {
        unit 0 {
            description "WAN interface";
            family inet {
                address 192.168.1.1/24;
            }
        }
    }
    lo0 {
        unit 0 {
            family inet {
                address 10.0.0.1/32;
            }
        }
    }
}

protocols {
    ospf {
        area 0.0.0.0 {
            interface ge-0/0/0.0;
            interface lo0.0 {
                passive;
            }
        }
    }
    bgp {
        group external {
            type external;
            peer-as 65001;
            neighbor 192.168.1.2;
        }
    }
}

system {
    ntp {
        server 192.168.1.100;
        server 192.168.1.101;
    }
}
"""
    
    print("\n=== Test 2: Complex Configuration ===")
    print("Input:")
    print(complex_config)
    print("\nSet commands:")
    commands = convert_junos_text_to_set(complex_config)
    for cmd in commands:
        print(cmd)
    
    print(f"\nTotal set commands generated: {len(commands)}")

if __name__ == "__main__":
    test_conversion()
