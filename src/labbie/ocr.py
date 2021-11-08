import pathlib
from typing import Optional

import loguru
from PIL import ImageGrab, Image
import pytesseract
import cv2 as cv
import numpy as np

from labbie import bounds
from labbie import utils

logger = loguru.logger
_Bounds = bounds.Bounds

pytesseract.pytesseract.tesseract_cmd = str(utils.bin_dir() / 'tesseract' / 'tesseract.exe')


def read_enchants(bounds: _Bounds, save_path: Optional[pathlib.Path], dilate: Optional[bool] = False):
    if save_path and not save_path.exists():
        save_path.mkdir(exist_ok=True, parents=True)
    image = ImageGrab.grab(bounds.as_tuple(), all_screens=True)
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
            Image.fromarray(im_bw).save(save_path / f'full_processed.png')      
    enchants = pytesseract.image_to_string(im_bw).replace('\x0c', '').split('\n\n')
    
    for index, enchant in enumerate(enchants):
        enchant = enchant.replace('’', "'").replace('\n', ' ')
        enchant = ' '.join(enchant.split())
        enchants[index] = enchant
    logger.info(f'found {enchants=}')
    return enchants