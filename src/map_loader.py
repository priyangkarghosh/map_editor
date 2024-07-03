import json

from src.extras import *
from src.grid_renderer import GridRenderer
from src.tiler import Tiler


def save_map(path, gr, tiler):
    if not path and path.split('.')[-1] != "tmap": return

    data = {
        'tile_size': stringify(tuple(gr.tile_size)),
        'grid_size': stringify(tuple(gr.grid_size)),
        'num_layers': 0, 'grid_tiles': {}, 'off_grid_tiles': {},
        'collision_rects': [], 'collision_tiles': {}
    }

    # add the grid tiles
    grid_layer_index = 0
    for layer in tiler.assets['grid_tiles']:
        if not layer: continue

        data['grid_tiles'][grid_layer_index] = []
        for grid_pos, tile in layer.items():
            data['grid_tiles'][grid_layer_index].append({
                'grid_position': stringify(grid_pos), 'group': tile[0], 'variant': stringify(tuple(tile[1])),
                'layer': grid_layer_index, 'editor_layer': tile[2],
                'world_position': stringify((grid_pos[0] * gr.tile_size[0], grid_pos[1] * gr.tile_size[1]))
            })
        grid_layer_index += 1

    # add the off-grid tiles
    offgrid_layer_index = 0
    for layer in tiler.assets['off_grid_tiles']:
        if not layer: continue

        data['off_grid_tiles'][offgrid_layer_index] = []
        for pos, tile in layer.items():
            data['off_grid_tiles'][offgrid_layer_index].append({
                'group': tile[0], 'variant': stringify(tuple(tile[1])), 'layer': offgrid_layer_index,
                'editor_layer': tile[2], 'world_position': stringify(tuple(pos))
            })
        offgrid_layer_index += 1

    # save the number of layers the map has
    data['num_layers'] = max(grid_layer_index, offgrid_layer_index)

    # collision rects
    rect_index = 0
    for ctype, arr in tiler.coll_handler.find_coll_rects().items():
        for rect in arr:
            data['collision_rects'].append({
                'topleft': stringify(rect.topleft),
                'size': stringify(rect.size), 'type': 0
            })

            for x in range(rect.left // gr.tile_size[0], rect.right // gr.tile_size[0]):
                for y in range(rect.top // gr.tile_size[1], rect.bottom // gr.tile_size[1]):
                    data['collision_tiles'][stringify((x, y))] = stringify((rect_index, ctype, 0))
            rect_index += 1

    # add the data to the correct file
    with open(path, 'w') as file:
        file.write(json.dumps(data))
    file.close()


def load_map(path, config, gr, tiler):
    if not path and path.split('.')[-1] != "tmap": return

    data = {}
    try:
        with open(path, 'r') as file:
            data = json.load(file)
        file.close()
    except FileNotFoundError:
        return

    tile_size = tuplify(data['tile_size'])
    grid_size = tuplify(data['grid_size'])

    new_gr = GridRenderer(gr.config, tile_size, grid_size)
    new_tiler = Tiler(config['assets_path'], tiler.config, new_gr.tile_size, new_gr.grid_size, new_gr.world_size)

    for layer in data['grid_tiles'].values():
        for tile in layer:
            new_tiler.assets['grid_tiles'][tile['editor_layer']][tuplify(tile['grid_position'])] = \
                (tile['group'], tuplify(tile['variant']), tile['editor_layer'])

    for layer in data['off_grid_tiles'].values():
        for tile in layer:
            new_tiler.assets['off_grid_tiles'][tile['editor_layer']][tuplify(tile['world_position'])] = \
                (tile['group'], tuplify(tile['variant']), tile['editor_layer'])

    for pos, rect_info in data['collision_tiles'].items():
        new_tiler.coll_handler.coll_tiles[tuplify(pos)] = tuplify(rect_info)[1]
    new_tiler.coll_handler.coll_rects = new_tiler.coll_handler.find_coll_rects()

    new_tiler.redraw()
    new_tiler.coll_handler.redraw()

    return new_gr, new_tiler
