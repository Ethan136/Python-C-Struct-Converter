import unittest
import sys
import os
import xml.etree.ElementTree as ET

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.struct_model import StructModel
from model.input_field_processor import InputFieldProcessor

class TestStructParsingCore(unittest.TestCase):
    """Test cases for core struct parsing functionality without GUI"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = StructModel()
        self.input_processor = InputFieldProcessor()
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.config_file = os.path.join(self.test_data_dir, 'struct_parsing_test_config.xml')
        
        # Load test configurations
        self.test_configs = self._load_test_configs()

    def _load_test_configs(self):
        """Load test configurations from XML file"""
        if not os.path.exists(self.config_file):
            return {}
        
        tree = ET.parse(self.config_file)
        root = tree.getroot()
        configs = {}
        
        for test_case in root.findall('test_case'):
            name = test_case.get('name')
            struct_file = test_case.get('struct_file')
            description = test_case.get('description')
            
            # Parse input data
            input_data = []
            for input_elem in test_case.find('input_data').findall('input'):
                input_data.append({
                    'index': int(input_elem.get('index')),
                    'value': input_elem.get('value'),
                    'unit_size': int(input_elem.get('unit_size')),
                    'description': input_elem.get('description')
                })
            
            # Parse expected results
            expected_results = {}
            for endianness in test_case.find('expected_results').findall('endianness'):
                endian_name = endianness.get('name')
                expected_results[endian_name] = {}
                
                for member in endianness.findall('member'):
                    member_name = member.get('name')
                    expected_results[endian_name][member_name] = {
                        'expected_value': member.get('expected_value'),
                        'expected_hex': member.get('expected_hex'),
                        'description': member.get('description')
                    }
            
            configs[name] = {
                'struct_file': struct_file,
                'description': description,
                'input_data': input_data,
                'expected_results': expected_results
            }
        
        return configs

    def _process_input_data(self, input_data, endianness, layout, total_size):
        """Process input data using InputFieldProcessor and struct layout"""
        struct_bytes = bytearray(total_size)
        input_idx = 0
        for item in layout:
            if item['type'] == 'padding':
                continue
            input_item = input_data[input_idx]
            value = input_item['value']
            unit_size = input_item['unit_size']
            raw_bytes = self.input_processor.process_input_field(value, unit_size, endianness)
            struct_bytes[item['offset']:item['offset']+item['size']] = raw_bytes
            input_idx += 1
        return struct_bytes.hex()

    def test_struct_a_parsing(self):
        """Test struct A parsing with various inputs"""
        if 'struct_a_test' not in self.test_configs:
            self.skipTest("struct_a_test configuration not found")
        
        config = self.test_configs['struct_a_test']
        struct_file_path = os.path.join(self.test_data_dir, config['struct_file'])
        
        # Load struct definition
        struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(struct_file_path)
        self.assertIsNotNone(struct_name, "Failed to load struct definition")
        
        # Test both endianness
        for endianness in ['little', 'big']:
            with self.subTest(endianness=endianness):
                # Process input data
                hex_data = self._process_input_data(config['input_data'], endianness, layout, total_size)
                
                # Parse with model
                parsed_values = self.model.parse_hex_data(hex_data, endianness)
                
                # Verify results
                expected = config['expected_results'][endianness]
                for member_name, expected_data in expected.items():
                    # Find the parsed member
                    parsed_member = None
                    for item in parsed_values:
                        if item['name'] == member_name:
                            parsed_member = item
                            break
                    
                    self.assertIsNotNone(parsed_member, f"Member '{member_name}' not found in parsed results")
                    
                    # Check value
                    expected_value = expected_data['expected_value']
                    actual_value = parsed_member['value']
                    self.assertEqual(actual_value, expected_value, 
                                   f"Value mismatch for {member_name} in {endianness} endian: "
                                   f"expected {expected_value}, got {actual_value}")
                    
                    # Check hex representation
                    expected_hex = expected_data['expected_hex']
                    actual_hex = parsed_member['hex_raw']
                    self.assertEqual(actual_hex, expected_hex,
                                   f"Hex mismatch for {member_name} in {endianness} endian: "
                                   f"expected {expected_hex}, got {actual_hex}")

    def test_struct_with_padding_parsing(self):
        """Test struct with padding parsing"""
        if 'struct_with_padding_test' not in self.test_configs:
            self.skipTest("struct_with_padding_test configuration not found")
        
        config = self.test_configs['struct_with_padding_test']
        struct_file_path = os.path.join(self.test_data_dir, config['struct_file'])
        
        # Load struct definition
        struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(struct_file_path)
        self.assertIsNotNone(struct_name, "Failed to load struct definition")
        
        # Test both endianness
        for endianness in ['little', 'big']:
            with self.subTest(endianness=endianness):
                # Process input data
                hex_data = self._process_input_data(config['input_data'], endianness, layout, total_size)
                
                # Parse with model
                parsed_values = self.model.parse_hex_data(hex_data, endianness)
                
                # Verify results
                expected = config['expected_results'][endianness]
                for member_name, expected_data in expected.items():
                    # Find the parsed member
                    parsed_member = None
                    for item in parsed_values:
                        if item['name'] == member_name:
                            parsed_member = item
                            break
                    
                    self.assertIsNotNone(parsed_member, f"Member '{member_name}' not found in parsed results")
                    
                    # Check value
                    expected_value = expected_data['expected_value']
                    actual_value = parsed_member['value']
                    self.assertEqual(actual_value, expected_value, 
                                   f"Value mismatch for {member_name} in {endianness} endian: "
                                   f"expected {expected_value}, got {actual_value}")

    def test_empty_input_handling(self):
        """Test empty input handling"""
        if 'empty_input_test' not in self.test_configs:
            self.skipTest("empty_input_test configuration not found")
        
        config = self.test_configs['empty_input_test']
        struct_file_path = os.path.join(self.test_data_dir, config['struct_file'])
        
        # Load struct definition
        struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(struct_file_path)
        self.assertIsNotNone(struct_name, "Failed to load struct definition")
        
        # Test both endianness
        for endianness in ['little', 'big']:
            with self.subTest(endianness=endianness):
                # Process input data
                hex_data = self._process_input_data(config['input_data'], endianness, layout, total_size)
                
                # Parse with model
                parsed_values = self.model.parse_hex_data(hex_data, endianness)
                
                # Verify results
                expected = config['expected_results'][endianness]
                for member_name, expected_data in expected.items():
                    # Find the parsed member
                    parsed_member = None
                    for item in parsed_values:
                        if item['name'] == member_name:
                            parsed_member = item
                            break
                    
                    self.assertIsNotNone(parsed_member, f"Member '{member_name}' not found in parsed results")
                    
                    # Check value
                    expected_value = expected_data['expected_value']
                    actual_value = parsed_member['value']
                    self.assertEqual(actual_value, expected_value, 
                                   f"Value mismatch for {member_name} in {endianness} endian: "
                                   f"expected {expected_value}, got {actual_value}")

    def test_mixed_sizes_parsing(self):
        """Test struct with mixed field sizes"""
        if 'mixed_sizes_test' not in self.test_configs:
            self.skipTest("mixed_sizes_test configuration not found")
        
        config = self.test_configs['mixed_sizes_test']
        struct_file_path = os.path.join(self.test_data_dir, config['struct_file'])
        
        # Load struct definition
        struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(struct_file_path)
        self.assertIsNotNone(struct_name, "Failed to load struct definition")
        
        # Test both endianness
        for endianness in ['little', 'big']:
            with self.subTest(endianness=endianness):
                # Process input data
                hex_data = self._process_input_data(config['input_data'], endianness, layout, total_size)
                
                # Parse with model
                parsed_values = self.model.parse_hex_data(hex_data, endianness)
                
                # Verify results
                expected = config['expected_results'][endianness]
                for member_name, expected_data in expected.items():
                    # Find the parsed member
                    parsed_member = None
                    for item in parsed_values:
                        if item['name'] == member_name:
                            parsed_member = item
                            break
                    
                    self.assertIsNotNone(parsed_member, f"Member '{member_name}' not found in parsed results")
                    
                    # Check value
                    expected_value = expected_data['expected_value']
                    actual_value = parsed_member['value']
                    self.assertEqual(actual_value, expected_value, 
                                   f"Value mismatch for {member_name} in {endianness} endian: "
                                   f"expected {expected_value}, got {actual_value}")

    def test_all_configurations(self):
        """Test all configurations in the XML file"""
        for test_name, config in self.test_configs.items():
            with self.subTest(test_name=test_name):
                struct_file_path = os.path.join(self.test_data_dir, config['struct_file'])
                
                # Check if struct file exists
                if not os.path.exists(struct_file_path):
                    self.skipTest(f"Struct file {config['struct_file']} not found")
                
                # Load struct definition
                struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(struct_file_path)
                self.assertIsNotNone(struct_name, f"Failed to load struct definition for {test_name}")
                
                # Test both endianness
                for endianness in ['little', 'big']:
                    with self.subTest(endianness=endianness):
                        # Process input data
                        hex_data = self._process_input_data(config['input_data'], endianness, layout, total_size)
                        
                        # Parse with model
                        parsed_values = self.model.parse_hex_data(hex_data, endianness)
                        
                        # Verify results
                        expected = config['expected_results'][endianness]
                        for member_name, expected_data in expected.items():
                            # Find the parsed member
                            parsed_member = None
                            for item in parsed_values:
                                if item['name'] == member_name:
                                    parsed_member = item
                                    break
                            
                            self.assertIsNotNone(parsed_member, 
                                               f"Member '{member_name}' not found in parsed results for {test_name}")
                            
                            # Check value
                            expected_value = expected_data['expected_value']
                            actual_value = parsed_member['value']
                            self.assertEqual(actual_value, expected_value, 
                                           f"Value mismatch for {member_name} in {test_name} ({endianness} endian): "
                                           f"expected {expected_value}, got {actual_value}")

if __name__ == '__main__':
    unittest.main() 