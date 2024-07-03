import json

DEFAULT_EDITOR_CONFIG = {
    "zoom_speed": 0.1,
    "max_tile_size": [32, 32],
    "max_grid_size": [64, 64],
    "grid_colour": [255, 255, 255, 200],
}

DEFAULT_TILER_CONFIG = {
    "autotile_types": [],
    "physics_tiles": [],
}

DEFAULT_SHEET_CONFIG = {
    "colourkey": (0, 0, 0),
}


def load_json_file(path, default):
    try:
        with open(path, 'r') as file:
            data = json.load(file)
        file.close()

    except FileNotFoundError:
        data = default
        with open(path, 'w') as file:
            file.write(json.dumps(data))
        file.close()
    return data


def configure_editor(path):
    return load_json_file(path, DEFAULT_EDITOR_CONFIG)


def configure_tiler(path):
    return load_json_file(path, DEFAULT_TILER_CONFIG)


def configure_sheet(path):
    return load_json_file(path, DEFAULT_SHEET_CONFIG)
