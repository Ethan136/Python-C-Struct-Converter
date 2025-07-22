import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.presenter.struct_presenter import StructPresenter
from src.model.struct_model import StructModel
from tests.data_driven.xml_presenter_refactor_loader import load_presenter_refactor_tests


class TestPresenterRefactor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = StructModel()
        cls.view = MagicMock()
        cls.presenter = StructPresenter(cls.model, cls.view)
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_presenter_refactor_config.xml')
        cls.cases = load_presenter_refactor_tests(xml_path)

    def test_presenter_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                members = case['members']
                if case['type'] == 'compute_layout':
                    layout = self.presenter.compute_member_layout(members, 8)
                    names = [item.get('name', '') for item in layout]
                    types = [item.get('type', '') for item in layout]
                    self.assertEqual(len(layout), len(case['expected_layout']))
                    for exp in case['expected_layout']:
                        self.assertIn(exp['name'], names)
                        if 'type' in exp:
                            idx = names.index(exp['name'])
                            self.assertEqual(types[idx], exp['type'])
                        if 'size' in exp:
                            idx = names.index(exp['name'])
                            self.assertEqual(layout[idx]['size'], exp['size'])
                elif case['type'] == 'remaining_space':
                    bits, bytes_ = self.presenter.calculate_remaining_space(members, 8)
                    expected = case['expected_remaining']
                    self.assertEqual(bits, expected[0])
                    self.assertEqual(bytes_, expected[1])


if __name__ == '__main__':
    unittest.main()
