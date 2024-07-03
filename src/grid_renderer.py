import pygame

from pygame import *

from src.extras import clamp

TILEMAP_RENDER_RECT = Rect(370, 0, 910, 720)


class GridRenderer:
    def __init__(self, config, tile_size, grid_size):
        self.config = config

        # initialize camera variables
        self.zoom_scale = 1

        self.panning = False
        self.panning_offset = [0, 0]

        # initialize selecting multiple tiles
        self.selections = []
        self.updated_tiles = []
        self.multiselect_start = [0, 0]

        # init old stuff
        self.prev_selections = []
        self.prev_grid_pos = [0, 0]

        # initialize the grid map vars
        self.tile_size = tile_size
        self.grid_size = grid_size
        self.world_size = (
            grid_size[0] * tile_size[0],
            grid_size[1] * tile_size[1]
        )

        # calculate the min and max panning offsets
        self.min_panning = [
            -self.world_size[0] // 2 - self.config['pan_padding'][0],
            -self.world_size[1] // 2 - self.config['pan_padding'][1],
        ]

        self.max_panning = [
            self.world_size[0] // 2 + self.config['pan_padding'][0],
            self.world_size[1] // 2 + self.config['pan_padding'][1],
        ]

        # render the entire grid
        self.surf = Surface(self.world_size, SRCALPHA)
        self.render_grid()

    def update_gr(self, grid_pos, user_input, tiler):
        delta = pygame.mouse.get_rel()

        # calculate the panning
        if self.panning:
            self.panning_offset[0] = self.panning_offset[0] + delta[0]
            self.panning_offset[1] = self.panning_offset[1] + delta[1]

        self.panning_offset[0] = clamp(
            self.panning_offset[0],
            int(self.min_panning[0]),
            int(self.max_panning[0])
        )

        self.panning_offset[1] = clamp(
            self.panning_offset[1],
            int(self.min_panning[1]),
            int(self.max_panning[1])
        )

        # render the current highlight
        if grid_pos[0] != self.prev_grid_pos[0] or grid_pos[1] != self.prev_grid_pos[1]:
            self.draw_empty_tile(self.prev_grid_pos[0], self.prev_grid_pos[1])
            self.draw_custom_tile(
                grid_pos[0], grid_pos[1], self.config['grid_highlight_colour'], self.config['grid_highlight_width']
            )
        self.prev_grid_pos = grid_pos

        # check if the mouse button is being held down
        if user_input['mouse_pressed']:
            if user_input['multi_enabled']:
                pass
            else:
                if grid_pos not in self.updated_tiles and self.valid_tile(grid_pos[0], grid_pos[1]):
                    self.updated_tiles.append(grid_pos)
                    if grid_pos in self.selections:
                        self.selections.remove(grid_pos)
                    else:
                        self.selections.append(grid_pos)
        else:
            self.updated_tiles.clear()

        # render the selections:
        # reset the old selections
        for s in self.prev_selections: self.draw_empty_tile(s[0], s[1])

        # render the current selections
        render_sel = self.calc_multi_select(grid_pos) if user_input['multi_enabled'] and user_input['mouse_pressed'] else self.selections
        for s in render_sel:
            if s[0] == grid_pos[0] and s[1] == grid_pos[1]:
                self.draw_custom_tile(s[0], s[1], self.config['grid_selected_highlight_colour'], 0)
            else:
                self.draw_custom_tile(s[0], s[1], self.config['grid_select_colour'], 0)
        self.prev_selections = render_sel

    def update_zoom(self, amount):
        self.zoom_scale = clamp(
            self.zoom_scale + self.config['zoom_speed'] * amount, self.config['min_zoom'], self.config['max_zoom']
        )

    def update_select(self, grid_pos, user_input):
        if user_input['mouse_pressed']:
            if grid_pos not in self.selections:
                self.clear_selections()

            if user_input['multi_enabled']:
                self.multiselect_start = grid_pos
        else:
            if user_input['multi_enabled']:
                self.selections = self.calc_multi_select(grid_pos)

    def clear_selections(self):
        for s in self.selections:
            self.draw_empty_tile(s[0], s[1])
        self.selections.clear()

    def calc_multi_select(self, grid_pos):
        sel_list = []

        # calculate the position ranges
        x_range = y_range = []
        if self.multiselect_start[0] < grid_pos[0]:
            x_range = [self.multiselect_start[0], grid_pos[0]]
        else:
            x_range = [grid_pos[0], self.multiselect_start[0]]

        if self.multiselect_start[1] < grid_pos[1]:
            y_range = [self.multiselect_start[1], grid_pos[1]]
        else:
            y_range = [grid_pos[1], self.multiselect_start[1]]

        # clamp the x and y ranges
        x_range = [
            clamp(x_range[0], 0, self.grid_size[0]),
            clamp(x_range[1], 0, self.grid_size[0])
        ]

        y_range = [
            clamp(y_range[0], 0, self.grid_size[1]),
            clamp(y_range[1], 0, self.grid_size[1])
        ]

        # add to the selection list
        for x in range(x_range[0], x_range[1]):
            for y in range(y_range[0], y_range[1]):
                sel_list.append([x, y])

        return sel_list

    def update_pan(self, is_panning):
        self.panning = is_panning

    def draw_custom_tile(self, grid_x, grid_y, colour, width):
        if grid_x >= self.grid_size[0] or grid_x < 0: return
        if grid_y >= self.grid_size[1] or grid_y < 0: return

        self.reset_tile(grid_x, grid_y)
        self.draw_generic_tile(grid_x, grid_y, colour, width)

    def draw_empty_tile(self, grid_x, grid_y):
        self.reset_tile(grid_x, grid_y)
        self.draw_generic_tile(
            grid_x, grid_y, self.config['grid_outline_colour'], self.config['grid_outline_width']
        )

    def reset_tile(self, grid_x, grid_y):
        self.surf.fill(
            (0, 0, 0, 0),
            (grid_x * self.tile_size[0], grid_y * self.tile_size[1], self.tile_size[0], self.tile_size[1])
        )

    def draw_generic_tile(self, grid_x, grid_y, colour, width):
        pygame.draw.rect(
            self.surf, colour,
            (grid_x * self.tile_size[0], grid_y * self.tile_size[1], self.tile_size[0], self.tile_size[1]),
            width=width, border_radius=self.config['grid_border_radius']
        )

    # re-renders the entire grid
    def render_grid(self):
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                self.draw_empty_tile(x, y)

    def valid_tile(self, x, y):
        return 0 <= x < self.grid_size[0] and 0 <= y < self.grid_size[1]
