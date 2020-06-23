from collections import namedtuple
import random

__all__ = [ 'Tetromino' ] 

Cell = namedtuple('Cell', 'x y')

#PALETTES = (
#    ('blue', 'red', 'yellow', 'orange', 'purple', 'green', 'cyan'),
#    ('#54c7fc', '#ffcd00', '#ff9600', '#ff2851', '#0076ff', '#44db5e', '#ff3824'),
#    ('#00b3ca', '#7dd0b6', '#1d4e89', '#d2b29b', '#e38690', '#f69256', '#eaf98b'),
#    ('#02a68d', '#016295', '#c8cd7d', '#44225e', '#bb1e39', '#e4633b', '#ba1a62'),
#    ('#6db875', '#dd7983', '#0f5959', '#17a697', '#638ca6', '#b569b3', '#d93240')
#)
#
#def get_color(s):
#    r = int(s[1:3], base=16)
#    g = int(s[3:5], base=16)
#    b = int(s[5:], base=16)
#    return r, g, b
#
#PALETTE = dict(zip('LJSZTOI', getcolor(c) for c in PALETTES[-1]))

SHAPES = {
'L': (
"""
xxx
x..
""",
"""
xx
.x
.x
""",
"""
..x
xxx
""",
"""
x.
x.
xx
"""
),
'J': (
"""
xxx
..x
""",
"""
.x
.x
xx
""",
"""
x..
xxx
""",
"""
xx
x.
x.
"""
),
'S': (
"""
.xx
xx.
""",
"""
x.
xx
.x
"""
),
'Z': (
"""
xx.
.xx
""",
"""
.x
xx
x.
"""
),
'T': (
"""
xxx
.x.
""",
"""
.x
xx
.x
""",
"""
.x.
xxx
""",
"""
x.
xx
x.
"""
),
'O': (
"""
xx
xx
""",
),
'I': (
"""
xxxx
""",
"""
.x
.x
.x
.x
"""
)
}

class Tetromino:
    TYPES = list(SHAPES)

    def __init__(self):
        self.state = 0
        self.x = 0
        self.y = 0
        self.type = random.choice(self.TYPES)

    def get_width(self):
        shape = SHAPES[self.type][self.state]
        return max(len(line) for line in shape.split())

    def get_height(self):
        shape = SHAPES[self.type][self.state]
        return len(shape.split())

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def rotate(self, n=1):
        self.state = (self.state + n) % len(SHAPES[self.type])

    def __iter__(self):
        shape = SHAPES[self.type][self.state]
        for y, line in enumerate(shape.split()):
            for x, c in enumerate(line):
                if c != '.':
                    yield Cell(x + self.x, y + self.y)

