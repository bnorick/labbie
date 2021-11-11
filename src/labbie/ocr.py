import pathlib
from typing import List, Optional

import cv2 as cv
import loguru
import numpy as np
from PIL import ImageGrab, Image
import pytesseract

from labbie import bounds
from labbie import utils

logger = loguru.logger
_KRANGLES = [
    ('Sammon', 'Summon'),
]

pytesseract.pytesseract.tesseract_cmd = str(utils.bin_dir() / 'tesseract' / 'tesseract.exe')


def read_enchants(bounds_: bounds.Bounds, save_path: Optional[pathlib.Path], dilate: Optional[bool] = False):
    if save_path and not save_path.exists():
        save_path.mkdir(exist_ok=True, parents=True)
    image = ImageGrab.grab(bounds_.as_tuple(), all_screens=True)
    if save_path:
        image.save(save_path / 'full.png')
    enchants = parse_image(image, save_path, dilate)
    return enchants


def parse_image(image, save_path, dilate):
    grayscale = cv.cvtColor(np.array(image), cv.COLOR_RGB2GRAY)
    (thresh, im_bw) = cv.threshold(grayscale, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
    if dilate:
        kernel = np.ones((2,2),np.uint8)
        # errosion is equivalent to dilation for white back ground black text.
        im_bw = cv.erode(im_bw, kernel, iterations=1)
    if save_path:
        Image.fromarray(im_bw).save(save_path / 'full_processed.png')
    enchants = pytesseract.image_to_string(im_bw, config='--psm 12').replace('\x0c', '').replace('’', "'")
    enchants = [e.strip() for e in enchants.split('\n') if e]
    return _fix_krangled_ocr(enchants)


def _fix_krangled_ocr(enchants: List[str]):
    unkrangled_enchants = []
    for enchant in enchants:
        for krangle in _KRANGLES:
            enchant = enchant.replace(*krangle)
        unkrangled_enchants.append(enchant)
    return unkrangled_enchants
