import sys

from src import map_loader, map_editor
from src.ui_renderer import *

from src.grid_renderer import *
from src.tiler import *

# initialize pygame
pygame.init()
pygame.display.set_caption('lvl editor')
pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEWHEEL, DROPFILE])

# get the config for the editor
editor_config = map_editor.configure_editor("config_files/editor_config.json")
tiler_config = map_editor.configure_tiler("config_files/tiler_config.json")

# initialize the proper surfaces
screen = pygame.display.set_mode(editor_config['window_size'], DOUBLEBUF)

display = pygame.Surface(editor_config['window_size'], SRCALPHA)
ui_surf = display.copy()

# init the clock
clock = pygame.time.Clock()

# init the grid renderer
grid_rect = Rect(0, 0, 0, 0)

gr = GridRenderer(editor_config, (16, 16), (32, 32))
render_surf = Surface(gr.world_size, SRCALPHA)

# init the tiler
tiler = Tiler(editor_config['assets_path'], tiler_config, gr.tile_size, gr.grid_size, gr.world_size)
ui_buttons = load_spritesheet("assets/internal/uisprites")
sl_buttons = load_spritesheet("assets/internal/saveload")

# input
user_input = {
    "mouse_pressed": False,
    "selecting": False,

    "grid_enabled": True,
    "preview_enabled": False,

    "multi_enabled": False,
    "lctrl_pressed": False,

    "select_start": [0, 0],
    "mouse_pos": [0, 0],
    "rel_mouse_pos": [0, 0],
    "grid_pos": [0, 0],

    "text_field_selected": False,
    "caret_timer": 0,
    "text": "",

    "try_save": False,
    "try_load": False
}

while True:
    # reset the screen
    display.fill(editor_config['window_fill_colour'])
    render_surf.fill((0, 0, 0, 0))
    ui_surf.fill((0, 0, 0, 0))

    # get the current mouse position
    user_input["mouse_pos"] = pygame.mouse.get_pos()

    # calculate the tile_maps render position
    grid_rect.topleft = [
        TILEMAP_RENDER_RECT.left + gr.panning_offset[0],
        TILEMAP_RENDER_RECT.top + gr.panning_offset[1],
    ]

    grid_rect.left += (TILEMAP_RENDER_RECT.width - (gr.world_size[0] * gr.zoom_scale)) // 2
    grid_rect.top += (TILEMAP_RENDER_RECT.height - (gr.world_size[1] * gr.zoom_scale)) // 2

    # find the current grid pos and rel mouse pos (position of mouse on the grid)
    user_input['grid_pos'] = [
        int(((user_input["mouse_pos"][0] - grid_rect.left) / gr.zoom_scale) // gr.tile_size[0]),
        int(((user_input["mouse_pos"][1] - grid_rect.top) / gr.zoom_scale) // gr.tile_size[1]),
    ]

    user_input['rel_mouse_pos'] = [
        int((user_input["mouse_pos"][0] - grid_rect.left) / gr.zoom_scale),
        int((user_input["mouse_pos"][1] - grid_rect.top) / gr.zoom_scale)
    ]

    # update everything
    gr.update_gr(user_input['grid_pos'], user_input, tiler)

    # render all the layers of the tile map
    for i in range(MAX_LAYERS):
        grid_layer = tiler.assets['grid_surfs'][i]
        off_grid_layer = tiler.assets['off_grid_surfs'][i]

        alpha_set = editor_config['layer_opacity'] if not user_input[
            'preview_enabled'] and tiler.current_placement_mode != "coll" and i != tiler.current_layer else 255

        grid_layer.set_alpha(alpha_set)
        off_grid_layer.set_alpha(alpha_set)

        render_surf.blit(grid_layer, (0, 0))
        render_surf.blit(off_grid_layer, (0, 0))

    # render the collision layer
    if tiler.current_placement_mode == "coll":
        render_surf.blit(tiler.coll_handler.coll_surf, (0, 0))

        for ctype, rects in tiler.coll_handler.coll_rects.items():
            for rect in rects:
                pygame.draw.rect(
                    render_surf, tiler_config['rect_outlines'][ctype], rect,
                    width=tiler_config['rect_width']
                )

    # render everything else
    if not user_input['preview_enabled']:
        pygame.draw.rect(
            render_surf, editor_config['surf_outline_colour'],
            (0, 0, gr.world_size[0], gr.world_size[1]),
            width=editor_config['surf_outline_width'], border_radius=editor_config['surf_border_radius']
        )

        if user_input['grid_enabled'] and tiler.current_placement_mode != "off-grid":
            render_surf.blit(gr.surf, (0, 0))
        else:
            if tiler.current_variant is not None:
                tsurf = tiler.current_group['assets'][tiler.current_variant]
                tsurf.set_alpha(editor_config['preview_place_opacity'])

                if tiler.current_placement_mode == "off-grid":
                    render_surf.blit(
                        tsurf, (user_input['rel_mouse_pos'][0], user_input['rel_mouse_pos'][1])
                    )
                else:
                    render_surf.blit(
                        tsurf,
                        (user_input['grid_pos'][0] * tiler.tile_size[0], user_input['grid_pos'][1] * tiler.tile_size[1])
                    )

                    for pos in gr.calc_multi_select(user_input['grid_pos']) if not (
                            not user_input['multi_enabled'] or not user_input['mouse_pressed']) else gr.selections:
                        render_surf.blit(
                            tsurf, (pos[0] * tiler.tile_size[0], pos[1] * tiler.tile_size[1])
                        )

                tsurf.set_alpha(255)
            elif user_input['mouse_pressed']:
                gr.clear_selections()

    # render the surf to the display
    grid_rect.size = (int(gr.world_size[0] * gr.zoom_scale), int(gr.world_size[1] * gr.zoom_scale))
    display.blit(pygame.transform.scale(render_surf, grid_rect.size), grid_rect.topleft)

    # render the selection
    if user_input['selecting']:
        draw_selection(ui_surf, editor_config, user_input['select_start'], user_input['mouse_pos'])

    # render the ui
    draw_ui(ui_surf, editor_config, user_input, tiler, gr, ui_buttons, sl_buttons)

    # re-render the window
    screen.fill((0, 0, 0, 0))
    screen.blits((
        (pygame.transform.scale(display, editor_config['window_size']), (0, 0)),
        (pygame.transform.scale(ui_surf, editor_config['window_size']), (0, 0))
    ))

    # misc ui
    user_input["text_changed"] = False

    if user_input['try_save']:
        map_loader.save_map(user_input['text'] + ".tmap", gr, tiler)
        user_input['try_save'] = False

    if user_input['try_load']:
        new_map = map_loader.load_map(user_input['text'] + ".tmap", editor_config, gr, tiler)
        if new_map is not None: gr, tiler = new_map
        user_input['try_load'] = False

    # loop through pygame events and get user input
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

            if user_input["text_field_selected"]:
                user_input["text_changed"] = True
                if event.key == pygame.K_RETURN:
                    user_input["text_field_selected"] = False
                elif event.key == pygame.K_BACKSPACE:
                    user_input["text"] = user_input["text"][:-1]
                    user_input['caret_timer'] = 0.8
                else:
                    user_input["text"] += event.unicode
                    user_input['caret_timer'] = 0.8
            elif user_input['lctrl_pressed']:
                if event.key == editor_config['key_mappings']['undo']:
                    tiler.undo()
                if event.key == editor_config['key_mappings']['copy']:
                    tiler.copy(gr.selections)
                    gr.clear_selections()
                if event.key == editor_config['key_mappings']['paste']:
                    tiler.paste(gr)
                    gr.clear_selections()
                if event.key == editor_config['key_mappings']['cut']:
                    tiler.cut(gr.selections)
                    gr.clear_selections()
                if event.key == editor_config['key_mappings']['save_map']:
                    map_loader.save_map(user_input['text'] + ".tmap", gr, tiler)
                if event.key == editor_config['key_mappings']['load_map']:
                    new_map = map_loader.load_map(user_input['text'] + ".tmap", editor_config, gr, tiler)
                    if new_map is not None: gr, tiler = new_map
            else:
                if event.key == editor_config['key_mappings']['enable_grid']:
                    user_input['grid_enabled'] = not user_input['grid_enabled']
                if event.key == editor_config['key_mappings']['enable_preview']:
                    user_input['preview_enabled'] = not user_input['preview_enabled']
                if event.key == editor_config['key_mappings']['change_sheet_right']:
                    tiler.update_current_group(+1)
                if event.key == editor_config['key_mappings']['change_sheet_left']:
                    tiler.update_current_group(-1)
                if event.key == editor_config['key_mappings']['change_layer_up']:
                    tiler.update_current_layer(+1)
                if event.key == editor_config['key_mappings']['change_layer_down']:
                    tiler.update_current_layer(-1)
                if event.key == editor_config['key_mappings']['multiselect']:
                    user_input['multi_enabled'] = True
                if event.key == editor_config['key_mappings']['lctrl']:
                    user_input['lctrl_pressed'] = True

        if event.type == KEYUP:
            if event.key == editor_config['key_mappings']['multiselect']:
                user_input['multi_enabled'] = False
            if event.key == editor_config['key_mappings']['lctrl']:
                user_input['lctrl_pressed'] = False

        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                user_input['mouse_pressed'] = True
                if TILEMAP_RENDER_RECT.collidepoint(user_input["mouse_pos"][0], user_input["mouse_pos"][1]):
                    gr.update_select(user_input['grid_pos'], user_input)

                    if not (grid_rect.collidepoint(user_input["mouse_pos"][0], user_input["mouse_pos"][1])):
                        gr.clear_selections()
                        tiler.current_variant = None

                        if user_input["multi_enabled"]:
                            user_input["select_start"] = user_input["mouse_pos"]
                            user_input['selecting'] = True

                    elif (user_input["preview_enabled"] or tiler.current_placement_mode == "off-grid" or not user_input['grid_enabled']) and user_input["multi_enabled"]:
                        user_input["select_start"] = user_input["mouse_pos"]
                        user_input['selecting'] = True

            if event.button == 2:
                tiler.current_variant = None
                tiler.coll_handler.ctype = None

            if event.button == 3:
                if TILEMAP_RENDER_RECT.collidepoint(user_input["mouse_pos"][0], user_input["mouse_pos"][1]):
                    gr.update_pan(True)

        if event.type == MOUSEBUTTONUP:
            if event.button == 1:
                user_input['mouse_pressed'] = False
                gr.update_select(user_input['grid_pos'], user_input)

                if not user_input['preview_enabled']:
                    match tiler.current_placement_mode:
                        case "draw":
                            if tiler.add_tiles(gr.selections, False):
                                gr.clear_selections()
                        case "erase":
                            tiler.remove_tiles(gr.selections)
                            gr.clear_selections()
                        case "fill":
                            tiler.flood(user_input['grid_pos'], gr)
                            gr.clear_selections()
                        case "autotile":
                            tiler.autotile(gr.selections)
                            gr.clear_selections()
                        case "off-grid":
                            if not user_input['selecting']:
                                tiler.attempt_offgrid(user_input['rel_mouse_pos'])
                        case "coll":
                            tiler.coll_handler.handle_selections(gr.selections)
                            gr.clear_selections()
                user_input['selecting'] = False

            if event.button == 3:
                gr.update_pan(False)

        if event.type == pygame.MOUSEWHEEL:
            if TILEMAP_RENDER_RECT.collidepoint(user_input["mouse_pos"][0], user_input["mouse_pos"][1]):
                gr.update_zoom(event.y)

        if event.type == DROPFILE:
            new_map = map_loader.load_map(event.file, editor_config, gr, tiler)
            if new_map is not None:
                gr, tiler = new_map
                user_input['text'] = event.file.split('.tmap')[0]

    # update the screen
    pygame.display.flip()
    clock.tick(65)
