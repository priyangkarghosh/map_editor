import pygame
from pygame import Rect

RECT_UNION_DIRECTIONS = {
    'N': (0, -1), 'E': (1, 0),
    'S': (0, 1), 'W': (-1, 0),
    'NW': (-1, -1), 'NE': (1, -1),
    'SE': (1, 1), 'SW': (-1, 1)
}


class CollHandler:
    def __init__(self, tiler, surf):
        self.tiler = tiler
        self.ctype = None

        self.coll_surf = surf.copy()
        self.outline_surf = surf.copy()

        self.coll_tiles = {}
        self.coll_rects = {}

    def handle_selections(self, positions):
        if self.ctype is None: return

        for pos in positions:
            pos = tuple(pos)
            if pos in self.coll_tiles and self.coll_tiles[pos] == self.ctype:
                del self.coll_tiles[pos]
                self.reset_tile(pos)
            else:
                self.reset_tile(pos)
                self.coll_tiles[pos] = self.ctype
                self.draw_tile(pos)
        self.coll_rects = self.find_coll_rects()

    def draw_tile(self, pos):
        pygame.draw.rect(
            self.coll_surf, self.tiler.config['collision_types'][self.ctype],
            (pos[0] * self.tiler.tile_size[0], pos[1] * self.tiler.tile_size[1],
             self.tiler.tile_size[0], self.tiler.tile_size[1]),
        )

    def reset_tile(self, pos):
        self.coll_surf.fill(
            (0, 0, 0, 0),
            (pos[0] * self.tiler.tile_size[0], pos[1] * self.tiler.tile_size[1],
             self.tiler.tile_size[0], self.tiler.tile_size[1])
        )

    def find_coll_rects(self):
        if not self.coll_tiles: return {}

        coll_rects = {}
        tcopy = self.coll_tiles.copy()

        rows = self.tiler.grid_size[1]
        columns = self.tiler.grid_size[0]

        for ctype in self.tiler.config['collision_types'].keys():
            coll_rects[ctype] = []

            while True:
                left = [0] * columns
                right = [columns] * columns
                height = [0] * columns

                max_area = 0
                area_rect = [0, 0, 0]  # in form, left, right, bottom
                for y in range(rows):
                    cur_left = 0
                    cur_right = columns

                    for x in range(columns):
                        if (x, y) in tcopy and tcopy[(x, y)] == ctype:
                            left[x] = max(left[x], cur_left)
                            height[x] += 1
                        else:
                            cur_left = x + 1
                            height[x] = 0
                            left[x] = 0

                        right_x = columns - 1 - x
                        if (right_x, y) in tcopy and tcopy[(right_x, y)] == ctype:
                            right[right_x] = min(right[right_x], cur_right)
                        else:
                            right[right_x] = columns
                            cur_right = right_x

                    for x in range(columns):
                        area = (right[x] - left[x]) * height[x]
                        if area > max_area:
                            max_area = area

                            if left[x] == area_rect[0] and right[x] == area_rect[1]:
                                area_rect[2] = y
                            else:
                                area_rect[0] = left[x]
                                area_rect[1] = right[x]
                                area_rect[2] = y

                rect_size = [area_rect[1] - area_rect[0], 0]
                if rect_size[0] == 0: break
                rect_size[1] = max_area // rect_size[0]

                coll_rect = Rect(
                    area_rect[0],
                    area_rect[2] - rect_size[1] + 1,
                    rect_size[0], rect_size[1]
                )

                for x in range(coll_rect.left, coll_rect.right):
                    for y in range(coll_rect.top, coll_rect.bottom):
                        del tcopy[(x, y)]

                coll_rect.left *= self.tiler.tile_size[0]
                coll_rect.width *= self.tiler.tile_size[0]
                coll_rect.top *= self.tiler.tile_size[1]
                coll_rect.height *= self.tiler.tile_size[1]
                coll_rects[ctype].append(coll_rect)

        return coll_rects

    def is_same_ctype(self, ctype, pos):
        tile = self.coll_tiles.get(pos, None)
        return False if tile is None else (tile == ctype)

    def redraw(self):
        self.coll_surf.fill((0, 0, 0, 0))
        for pos, ctype in self.coll_tiles.items():
            pygame.draw.rect(
                self.coll_surf, self.tiler.config['collision_types'][ctype],
                (pos[0] * self.tiler.tile_size[0], pos[1] * self.tiler.tile_size[1],
                 self.tiler.tile_size[0], self.tiler.tile_size[1]),
            )
