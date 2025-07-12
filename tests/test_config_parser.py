#!/usr/bin/env python3
"""
Test Configuration Parser
=========================

This module parses XML test configuration files for input conversion testing.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional

class TestConfig:
    """Represents a single test configuration"""
    
    def __init__(self, name: str, unit_size: int, description: str):
        self.name = name
        self.unit_size = unit_size
        self.description = description
        self.input_values: Dict[int, str] = {}
        self.expected_results: Dict[int, Dict[str, str]] = {}
    
    def add_input_value(self, index: int, value: str):
        """Add an input value for a specific index"""
        self.input_values[index] = value
    
    def add_expected_result(self, index: int, big_endian: str, little_endian: str, original_value: str):
        """Add expected result for a specific index"""
        self.expected_results[index] = {
            'big_endian': big_endian,
            'little_endian': little_endian,
            'original_value': original_value
        }
    
    def get_input_values_list(self) -> List[str]:
        """Get input values as a list in index order"""
        max_index = max(self.input_values.keys()) if self.input_values else -1
        return [self.input_values.get(i, "") for i in range(max_index + 1)]
    
    def get_expected_results_list(self) -> List[Dict[str, str]]:
        """Get expected results as a list in index order"""
        max_index = max(self.expected_results.keys()) if self.expected_results else -1
        return [self.expected_results.get(i, {}) for i in range(max_index + 1)]

class TestConfigParser:
    """Parser for XML test configuration files"""
    
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        self.test_configs: Dict[str, TestConfig] = {}
    
    def parse(self) -> Dict[str, TestConfig]:
        """Parse the XML configuration file and return test configurations"""
        try:
            tree = ET.parse(self.config_file_path)
            root = tree.getroot()
            
            for test_config_elem in root.findall('test_config'):
                # Parse basic attributes
                name = test_config_elem.get('name', 'unnamed_test')
                unit_size = int(test_config_elem.get('unit_size', 1))
                description = test_config_elem.get('description', 'No description')
                
                # Create test config object
                test_config = TestConfig(name, unit_size, description)
                
                # Parse input values
                input_values_elem = test_config_elem.find('input_values')
                if input_values_elem is not None:
                    # New: support <array> for simplified input
                    array_elem = input_values_elem.find('array')
                    if array_elem is not None and array_elem.text:
                        # Split by comma, whitespace, or newlines
                        raw = array_elem.text.strip()
                        # Support comma, whitespace, or newline separated
                        import re
                        values = [v.strip() for v in re.split(r'[\s,]+', raw) if v.strip()]
                        for idx, value in enumerate(values):
                            test_config.add_input_value(idx, value)
                    # Also support legacy <value index=...>
                    for value_elem in input_values_elem.findall('value'):
                        index = int(value_elem.get('index', 0))
                        value = value_elem.text or ""
                        test_config.add_input_value(index, value)
                
                # Parse expected results
                expected_results_elem = test_config_elem.find('expected_results')
                if expected_results_elem is not None:
                    for result_elem in expected_results_elem.findall('result'):
                        index = int(result_elem.get('index', 0))
                        big_endian = result_elem.get('big_endian', '')
                        little_endian = result_elem.get('little_endian', '')
                        original_value = result_elem.text or ""
                        test_config.add_expected_result(index, big_endian, little_endian, original_value)
                
                self.test_configs[name] = test_config
            
            return self.test_configs
            
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error reading configuration file: {e}")
    
    def get_test_config(self, name: str) -> Optional[TestConfig]:
        """Get a specific test configuration by name"""
        return self.test_configs.get(name)
    
    def get_all_test_names(self) -> List[str]:
        """Get all test configuration names"""
        return list(self.test_configs.keys())
    
    def validate_config(self) -> List[str]:
        """Validate the configuration and return list of errors"""
        errors = []
        
        for name, config in self.test_configs.items():
            # Check if input values and expected results have matching indices
            input_indices = set(config.input_values.keys())
            result_indices = set(config.expected_results.keys())
            
            if input_indices != result_indices:
                errors.append(f"Test '{name}': Input indices {input_indices} don't match result indices {result_indices}")
            
            # Check if unit size is valid
            if config.unit_size not in [1, 4, 8]:
                errors.append(f"Test '{name}': Invalid unit size {config.unit_size}, must be 1, 4, or 8")
            
            # Check if expected results have required attributes
            for index, result in config.expected_results.items():
                if 'big_endian' not in result:
                    errors.append(f"Test '{name}', index {index}: Missing big_endian attribute")
                if 'little_endian' not in result:
                    errors.append(f"Test '{name}', index {index}: Missing little_endian attribute")
        
        return errors

def create_sample_config() -> str:
    """Create a sample XML configuration for testing"""
    sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<test_configs>
    <test_config name="sample_4byte_test" unit_size="4" description="Sample 4-byte test">
        <input_values>
            <value index="0">123</value>
            <value index="1">456</value>
        </input_values>
        <expected_results>
            <result index="0" big_endian="0000007b" little_endian="7b000000">123</result>
            <result index="1" big_endian="000001c8" little_endian="c8010000">456</result>
        </expected_results>
    </test_config>
</test_configs>'''
    return sample_xml

if __name__ == "__main__":
    # Test the parser
    import tempfile
    import os
    
    # Create a temporary file with sample config
    sample_xml = create_sample_config()
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as f:
        f.write(sample_xml)
        temp_file = f.name
    
    try:
        # Test parsing
        parser = TestConfigParser(temp_file)
        configs = parser.parse()
        
        print("Parsed test configurations:")
        for name, config in configs.items():
            print(f"  {name}: {config.description}")
            print(f"    Unit size: {config.unit_size}")
            print(f"    Input values: {config.get_input_values_list()}")
            print(f"    Expected results: {len(config.expected_results)} items")
        
        # Test validation
        errors = parser.validate_config()
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  {error}")
        else:
            print("Configuration is valid!")
            
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file) 