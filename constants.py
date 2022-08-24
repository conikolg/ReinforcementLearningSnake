from enum import Enum


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, obj):
        if not isinstance(obj, Point):
            return False
        return self.x == obj.x and self.y == obj.y


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    DARK_RED = (139, 0, 0)
    LIME_GREEN = (50, 205, 50)
    FOREST_GREEN = (34, 139, 34)
