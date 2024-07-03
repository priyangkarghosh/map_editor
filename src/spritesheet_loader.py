import pygame.image

from src.map_editor import configure_sheet

TOP_LEFT_SHIFT = 1 + (1 << 1) + (1 << 2)
TOP_RIGHT_SHIFT = 1 + (1 << 1) + (1 << 3)

def load_spritesheet(path, split_colour=(255, 0, 255)):
    config = configure_sheet(path + ".json")
    tile_surf = pygame.image.load(path + ".png").convert()
    tile_surf.set_colorkey(config['colourkey'])

    tiles = {}
    sheet_pos = [0, 0]
    tile_in_progress = False

    width = tile_surf.get_width()
    height = tile_surf.get_height()
    for y in range(height - 1):
        # reset the x sheet_pos
        sheet_pos[0] = 0
        tile_start = None
        for x in range(width - 1):
            # use bit shifting instead of making a list
            bshift = (tile_surf.get_at((x, y)) == split_colour)
            if not bshift: continue

            bshift += (tile_surf.get_at((x + 1, y)) == split_colour) << 1
            bshift += (tile_surf.get_at((x, y + 1)) == split_colour) << 2
            bshift += (tile_surf.get_at((x + 1, y + 1)) == split_colour) << 3

            # this is the start of a tile (topleft corner)
            if bshift == TOP_LEFT_SHIFT:
                tile_in_progress = True
                tile_start = (x + 1, y + 1)

            # this is the top right corner of a tile
            elif bshift == TOP_RIGHT_SHIFT:
                if tile_start is None: continue

                # find the bottom right corner
                y2 = y + 1
                while y2 < height and tile_surf.get_at((x, y2)) != split_colour:
                    y2 += 1

                # get the subsurface which corresponds to the tile
                tile = tile_surf.subsurface(tile_start[0], tile_start[1], x + 1 - tile_start[0], y2 - tile_start[1])
                tiles[tuple(sheet_pos)] = tile
                tile_in_progress = False

                # increment the x sheet_pos
                sheet_pos[0] += 1

        # check if a new row was found
        if tile_start is not None and not tile_in_progress:
            sheet_pos[1] += 1

    return {
        'assets': tiles,
        'config': config,
    }
