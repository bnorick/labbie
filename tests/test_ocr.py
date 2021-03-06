from os import read
from pathlib import Path

from PIL import Image
from labbie import enchants
from src.labbie.ocr import parse_image
import pytest

from PIL import ImageGrab, Image
import pytesseract
from labbie import utils
pytesseract.pytesseract.tesseract_cmd = str(utils.bin_dir() / 'tesseract' / 'tesseract.exe')

THREE_LINE_EXPECTED = [r'Trigger Commandment of Reflection when Hit', r"Adds 45 to 68 Fire Damage if you've Killed Recently", r"Enemies in Void Sphere's range take up to 10% increased Damage, based on distance from the Void Sphere", r'Raised Zombies deal 40% increased Damage', r'40% increased Dual Strike Damage']

@pytest.mark.parametrize(
    'input_path,expected_enchants',
    [(r'tests\test_data\three_line_enchant.png', THREE_LINE_EXPECTED),])
def test_ocr(input_path: Path, expected_enchants):
    image = Image.open(input_path)
    enchants = parse_image(image, None, None)
    assert enchants == expected_enchants


def test_playground():
    image_path = r'data\screenshots\2021-11-07_174755\full_processed.png'
    im_bw = Image.open(image_path)
    enchants = pytesseract.image_to_string(im_bw, config='--psm 5').replace('\x0c', '')
    pytest.set_trace()