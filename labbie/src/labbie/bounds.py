import dataclasses

from labbie import mixins


@dataclasses.dataclass
class Bounds(mixins.SerializableMixin):
    left: int
    top: int
    right: int
    bottom: int

    def as_tuple(self):
        return (self.left, self.top, self.right, self.bottom)
