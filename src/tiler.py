import pygame
from pygame import *

from src.coll_handler import CollHandler
from src.map_editor import load_json_file
from src.spritesheet_loader import load_spritesheet

PLACEMENT_MODES = ["draw", "fill", "autotile", "erase", "off-grid", "coll"]
FLOOD_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
AUTOTILE_DIRECTIONS = {
    'N': (0, -1), 'E': (1, 0),
    'S': (0, 1), 'W': (-1, 0),
    'NW': (-1, -1), 'NE': (1, -1),
    'SE': (1, 1), 'SW': (-1, 1)
}

MAX_LAYERS = 10


class Tiler:
    def __init__(self, path, tiler_config, tile_size, grid_size, world_size):
        self.config = tiler_config

        self.groups = load_json_file(path, {})
        for k, v in self.groups.items():
            self.groups[k] = load_spritesheet(v)

        self.group_types = list(self.groups.keys())
        self.num_groups = len(self.group_types)
        self.current_group_index = 0

        self.current_layer = 0
        self.current_variant = None
        self.mode_index = 0

        self.tile_size = tile_size
        self.grid_size = grid_size
        self.world_size = world_size

        original_surf = pygame.Surface(world_size, SRCALPHA)

        self.assets = {
            'grid_tiles': [],
            'off_grid_tiles': [],
            'off_grid_rects': [],

            'grid_surfs': [],
            'off_grid_surfs': [],
        }

        for i in range(MAX_LAYERS):
            self.assets['grid_tiles'].append({})
            self.assets['off_grid_tiles'].append({})
            self.assets['off_grid_rects'].append([])

            self.assets['grid_surfs'].append(original_surf.copy())
            self.assets['off_grid_surfs'].append(original_surf.copy())

        self.coll_handler = CollHandler(self, original_surf)

        self.undo_cache = self.grid_recache(0)
        self.copy_cache = {}

    @property
    def current_placement_mode(self):
        return PLACEMENT_MODES[self.mode_index]

    @property
    def current_group_name(self):
        return self.group_types[self.current_group_index]

    @property
    def current_group(self):
        return self.groups[self.current_group_name]

    @property
    def current_tile(self):
        return (None if self.current_variant is None else
                (self.current_group_name, self.current_variant, self.current_layer)
                )

    def get_tile_surf(self, tile):
        if tile is None: return None
        return self.groups[tile[0]]['assets'][tile[1]]

    def grid_recache(self, layer):
        return False, layer, {k: v for k, v in self.assets['grid_tiles'][layer].items()}

    @staticmethod
    def offgrid_recache(layer, value):
        return True, layer, value

    # UPDATE METYHODS
    def update_current_group(self, change):
        self.current_group_index += change

        if self.current_group_index >= self.num_groups:
            self.current_group_index = 0
        elif self.current_group_index < 0:
            self.current_group_index = self.num_groups - 1
        self.current_variant = None

    def update_current_layer(self, change):
        self.current_layer += change

        if self.current_layer >= MAX_LAYERS:
            self.current_layer = 0
        elif self.current_layer < 0:
            self.current_layer = MAX_LAYERS - 1

    # DRAW/ERASE
    def add_tiles(self, positions, allow_none):
        self.undo_cache = self.grid_recache(self.current_layer)

        if self.current_variant is None:
            if allow_none:
                self.remove_tiles(positions)
                return True
            else:
                return False

        for pos in positions:
            if tuple(pos) in self.assets['grid_tiles'][self.current_layer]:
                self.reset_tile(pos, self.current_layer)
            self.assets['grid_tiles'][self.current_layer][tuple(pos)] = self.current_tile
            self.draw_tile(pos, self.current_tile)
        return True

    def remove_tiles(self, positions):
        self.undo_cache = self.grid_recache(self.current_layer)

        if self.current_tile is None:
            for pos in positions:
                self.assets['grid_tiles'][self.current_layer].pop(tuple(pos), None)
                self.reset_tile(pos, self.current_layer)
        else:
            for pos in positions:
                tile = self.assets['grid_tiles'][self.current_layer].get(tuple(pos), None)
                if self.current_tile != tile and tile is not None:
                    del self.assets['grid_tiles'][self.current_layer][tuple(pos)]
                    self.reset_tile(pos, self.current_layer)

    # FILL
    def flood(self, pos, gr):
        temp = self.grid_recache(self.current_layer)
        if not gr.valid_tile(pos[0], pos[1]): return
        fill_tile = self.assets['grid_tiles'][self.current_layer].get(tuple(pos), None)
        if fill_tile == self.current_tile: return
        self.recurse_flood(pos, fill_tile, gr)
        self.undo_cache = temp

    def recurse_flood(self, start_pos, fill_tile, gr):
        if not gr.valid_tile(start_pos[0], start_pos[1]): return
        current_tile = self.assets['grid_tiles'][self.current_layer].get(tuple(start_pos), None)
        if current_tile != fill_tile and current_tile is not fill_tile: return

        self.add_tiles([start_pos], True)
        for direction in FLOOD_DIRECTIONS:
            test_pos = (start_pos[0] + direction[0], start_pos[1] + direction[1])
            self.recurse_flood(test_pos, fill_tile, gr)

    # AUTOTILE
    def autotile(self, positions):
        self.undo_cache = self.grid_recache(self.current_layer)

        for pos in positions:
            tile = self.assets['grid_tiles'][self.current_layer].get(tuple(pos), None)
            if tile is None or tile[0] not in self.config['autotile_groups']: continue

            i, bits = 1, {}
            for shift_key, shift in AUTOTILE_DIRECTIONS.items():
                test_pos = (pos[0] + shift[0], pos[1] + shift[1])
                test_tile = self.assets['grid_tiles'][self.current_layer].get(tuple(test_pos), None)
                bits[shift_key] = (test_tile is not None and test_tile[0] == tile[0]) << i
                i += 1

            # go through all possible diagonal neighbours
            bits['NW'] *= bits['N'] != 0 and bits['W'] != 0
            bits['NE'] *= bits['N'] != 0 and bits['E'] != 0
            bits['SW'] *= bits['S'] != 0 and bits['W'] != 0
            bits['SE'] *= bits['S'] != 0 and bits['E'] != 0

            new_tile_sheet_pos = tuple(
                self.groups[tile[0]]['config']['autotile_map'].get(
                    str(sum(bits.values())), self.groups[tile[0]]['config']['autotile_map']['default']
                ))

            self.assets['grid_tiles'][self.current_layer][tuple(pos)] = (tile[0], new_tile_sheet_pos, tile[2])
            self.redraw_tile(pos, self.current_layer)

    # OFFGRID
    def attempt_offgrid(self, pos):
        surf = self.get_tile_surf(self.current_tile)
        if surf is None: return

        test_rect = Rect(pos[0], pos[1], surf.get_width(), surf.get_height())
        col_ind = test_rect.collidelist(self.assets['off_grid_rects'][self.current_layer])

        if col_ind == -1:
            self.add_offgrid(self.current_tile, test_rect, self.current_layer)
        else:
            self.remove_offgrid(col_ind, self.current_layer)

    def add_offgrid(self, tile, tile_rect, layer):
        self.assets['off_grid_rects'][layer].append(tile_rect)
        self.assets['off_grid_tiles'][layer][tile_rect.topleft] = self.current_tile
        self.assets['off_grid_surfs'][layer].blit(
            self.get_tile_surf(tile), tile_rect.topleft
        )

        self.undo_cache = self.offgrid_recache(
            layer, len(self.assets['off_grid_rects'][layer]) - 1
        )

    def remove_offgrid(self, ind, layer):
        tile_rect = self.assets['off_grid_rects'][layer].pop(ind)
        tile = self.assets['off_grid_tiles'][layer].pop(tile_rect.topleft)
        self.assets['off_grid_surfs'][layer].fill(
            (0, 0, 0, 0), tile_rect
        )

        self.undo_cache = self.offgrid_recache(layer, (tile, tile_rect))

    # UNDO
    def undo(self):
        if self.undo_cache[0]:
            if isinstance(self.undo_cache[2], tuple):
                self.add_offgrid(self.undo_cache[2][0], self.undo_cache[2][1], self.undo_cache[1])
            else:
                self.remove_offgrid(self.undo_cache[2], self.undo_cache[1])
        else:
            temp = self.grid_recache(self.undo_cache[1])
            self.assets['grid_tiles'][self.undo_cache[1]] = self.undo_cache[2]
            self.redraw_layer(self.undo_cache[1])
            self.undo_cache = temp

    def copy(self, selections):
        self.copy_cache.clear()

        init_pos = selections[0]
        for pos in selections:
            copy_pos = (pos[0] - init_pos[0], pos[1] - init_pos[1])
            tile = self.assets['grid_tiles'][self.current_layer].get(tuple(pos), None)
            if tile is not None: self.copy_cache[copy_pos] = tile

    def paste(self, gr):
        init_pos = gr.selections[0]
        for pos, tile in self.copy_cache.items():
            paste_pos = (init_pos[0] + pos[0], init_pos[1] + pos[1])
            if gr.valid_tile(paste_pos[0], paste_pos[1]):
                if paste_pos in self.assets['grid_tiles'][self.current_layer]:
                    self.reset_tile(paste_pos, self.current_layer)
                self.assets['grid_tiles'][self.current_layer][paste_pos] = (tile[0], tile[1], self.current_layer)
                self.draw_tile(paste_pos, (tile[0], tile[1], self.current_layer))

    def cut(self, selections):
        self.copy(selections)
        self.remove_tiles(selections)

    # DRAWING METHODS
    def draw_tile(self, pos, tile):
        self.assets['grid_surfs'][tile[2]].blit(
            self.get_tile_surf(tile), (pos[0] * self.tile_size[0], pos[1] * self.tile_size[1])
        )

    def redraw_tile(self, pos, layer):
        self.reset_tile(pos, layer)

        tile = self.assets['grid_tiles'][layer].get(tuple(pos), None)
        self.draw_tile(pos, tile)

    def reset_tile(self, pos, layer):
        self.assets['grid_surfs'][layer].fill(
            (0, 0, 0, 0),
            (pos[0] * self.tile_size[0], pos[1] * self.tile_size[1], self.tile_size[0], self.tile_size[1])
        )

    def redraw_layer(self, layer):
        self.assets['grid_surfs'][layer].fill((0, 0, 0, 0))
        for pos, tile in self.assets['grid_tiles'][layer].items():
            self.draw_tile(pos, tile)

        self.assets['off_grid_surfs'][layer].fill((0, 0, 0, 0))
        for pos, tile in self.assets['off_grid_tiles'][layer].items():
            self.assets['off_grid_surfs'][layer].blit(self.get_tile_surf(tile), pos)

    def redraw(self):
        for i in range(MAX_LAYERS): self.redraw_layer(i)
