import os
import pathlib
import toml
from PIL import Image
import pytest

from typing import List
from src.labbie import mods
from src.labbie import ocr

_MODS = mods.Mods
_OCR = ocr
_TEST_FILE_DIR = pathlib.Path('tests/test_data')
_TEST_FILE_EXPECTED_OUTPUT_NAME = 'expected.toml'
_TEST_FILE_INPUT_NAME = 'input.png'


def generate_test_samples():

    with os.scandir(_TEST_FILE_DIR) as it:
        for dir in it:
            # valid inputs are stored in directories
            if not dir.is_dir():
                continue
            dir_path = pathlib.Path(dir.path)
            with (dir_path / _TEST_FILE_EXPECTED_OUTPUT_NAME).open() as f:
                expected_output = toml.load(f)

            marks = [getattr(pytest.mark, mark) for mark in expected_output.get('marks', [])]
            yield pytest.param(dir_path / _TEST_FILE_INPUT_NAME,
                               expected_output['enchants'],
                               dir.name,
                               marks=marks)


@pytest.fixture()
def mods(injector):
    return injector.get(_MODS)


class TestOCR():

    @pytest.mark.parametrize(
        'image_path,expected_enchants,test_name',
        list(generate_test_samples())
    )
    def test_ocr(self, image_path: pathlib.Path, expected_enchants: List[str], test_name, mods):
        image = Image.open(image_path)
        partial_enchant_list = ocr.parse_image(image, None, None)
        ocr_output = mods.get_mod_list_from_ocr_results(partial_enchant_list)
        print(f'{ocr_output=}')
        assert ocr_output == expected_enchants
