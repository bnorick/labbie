import pathlib
from typing import Optional

import loguru
from PIL import ImageGrab
import pytesseract

from labbie import bounds
from labbie import utils

logger = loguru.logger
_Bounds = bounds.Bounds

pytesseract.pytesseract.tesseract_cmd = str(utils.bin_dir() / 'tesseract' / 'tesseract.exe')


def read_enchants(bounds: _Bounds, save_path: Optional[pathlib.Path]):
    if save_path and not save_path.exists():
        save_path.mkdir(exist_ok=True, parents=True)

    enchant_count = 5
    divider_height = 5
    height = bounds.bottom - bounds.top - divider_height * (enchant_count - 1)
    height_per_enchant = height // 5
    width = bounds.right - bounds.left
    image = ImageGrab.grab(bounds.as_tuple())
    if save_path:
        image.save(save_path / 'full.png')
    enchants = []
    top = 0
    for i in range(enchant_count):
        piece = image.crop((0, top, width, top + height_per_enchant))
        processed = piece.convert('L').point(lambda p: 0 if p > 125 else 255, mode='1')
        top += height_per_enchant + divider_height
        if save_path:
            piece.save(save_path / f'{i}.png')
            processed.save(save_path / f'{i}_processed.png')
        enchant = pytesseract.image_to_string(processed).replace('\n', ' ').replace('\x0c', '')
        enchant = enchant.replace('’', "'")
        enchant = ' '.join(enchant.split())
        enchants.append(enchant)
    logger.info(f'found {enchants=}')
    return enchants
