class EnchantDataNotFound(Exception):
    def __init__(self, error=None):
        if error is None:
            error = 'No enchant data found.'
        super().__init__(error)


class EnchantDataInvalid(Exception):
    def __init__(self, error=None):
        if error is None:
            error = 'Invalid enchant data.'
        super().__init__(error)


class EnchantsNotLoaded(Exception):
    def __init__(self, error=None):
        if error is None:
            error = 'Enchants are not loaded.'
        super().__init__(error)


class NoSuchEnchant(Exception):
    def __init__(self, error=None):
        if error is None:
            error = 'No matching enchant.'
        super().__init__(error)


class NoSuchBase(Exception):
    def __init__(self, error=None):
        if error is None:
            error = 'No matching base.'
        super().__init__(error)


class FailedToDownloadResource(Exception):
    def __init__(self, remote_resource: str):
        error = 'Failed to download resource {}.'
        super().__init__(error)


