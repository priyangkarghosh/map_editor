import time as t

import pygame
import pygame.freetype

from pygame import *

from src import map_loader
from src.spritesheet_loader import *
from src.extras import ceil, clamp

pygame.init()

LEFT_UI_RECT = Rect(8, 8, 320, 704)
LEFT_ICONS_RECT = Rect(310, 36, 56, 203)

LEFT_TOP_UI_LINE = [(24, 68), (309, 68)]
LEFT_BOT_UI_LINE = [(24, 600), (309, 600)]

SHEET_SELECT_FONT = pygame.font.Font("assets/internal/DisposableDroidBB.ttf", 48)
SHEET_SELECT_RECT = Rect(24, 14, 286, 56)

GENERAL_UI_FONT = pygame.font.Font("assets/internal/DisposableDroidBB.ttf", 24)
UI_RECTS = [
    Rect(334, 6, 50, 24),
    Rect(1172, 6, 100, 24),
    Rect(1172, 714, 100, 24),
    Rect(334, 714, 100, 24),
]

TEXT_FIELD_FONT = pygame.font.Font("assets/internal/DisposableDroidBB.ttf", 24)
TEXT_FIELD_RECT = Rect(23, 608, 287, 28)


def draw_ui(surf, config, user_input, tiler, gr, ui_buttons, sl_buttons):
    draw_left_bg(surf, config)
    draw_text_field(surf, config, user_input)

    # render the buttons
    button_rect = Rect(333, 46, 24, 24)
    for i, button in enumerate(ui_buttons['assets'].values()):
        if button_rect.collidepoint(user_input['mouse_pos']) or i == tiler.mode_index:
            surf.blit(pygame.transform.scale(button, (30, 30)), (button_rect.left - 3, button_rect.top - 3))

            if user_input['mouse_pressed'] and i != tiler.mode_index:
                tiler.current_variant = None
                tiler.mode_index = i
        else:
            surf.blit(button, button_rect)
        button_rect.top += 32

    # render the buttons
    button_rect = Rect(240, 640, 32, 32)
    for i, button in enumerate(sl_buttons['assets'].values()):
        if button_rect.collidepoint(user_input['mouse_pos']):
            surf.blit(pygame.transform.scale(button, (34, 34)), (button_rect.left - 1, button_rect.top - 1))
            if user_input['mouse_pressed']:
                if not i: user_input['try_save'] = True
                else: user_input['try_load'] = True
        else:
            surf.blit(button, button_rect)
        button_rect.left += 36

    # draw the tiles in the current spritesheet
    last_placed_pos = list(LEFT_TOP_UI_LINE[0])
    last_placed_pos[1] += 3

    # display the currently usable tiles
    if tiler.current_placement_mode == "coll":
        for ctype, colour in tiler.config['collision_types'].items():
            size = [
                tiler.tile_size[0] * config['tile_scale'],
                tiler.tile_size[1] * config['tile_scale']
            ]

            tile_rect = Rect(last_placed_pos[0], last_placed_pos[1], size[0] * 1.2, size[1] * 1.2)
            if tile_rect.collidepoint(user_input['mouse_pos']) or tiler.coll_handler.ctype == ctype:
                size = [ceil(size[0] * 1.2), ceil(size[1] * 1.2)]

                if user_input['mouse_pressed']: tiler.coll_handler.ctype = ctype
                rendered_text = GENERAL_UI_FONT.render(ctype, False, config['ui_text_colour'])
                surf.blit(rendered_text, rendered_text.get_rect(top=tile_rect.top + 4, left=tile_rect.right + 8))

            border_size = [
                size[0] + config["tile_border_width"] * 2,
                size[1] + config["tile_border_width"] * 2
            ]

            last_placed_pos[1] += config['tile_display_padding']

            pygame.draw.rect(
                surf, config['tile_border_colour'],
                (last_placed_pos[0], last_placed_pos[1], border_size[0], border_size[1]),
                width=config["tile_border_width"]
            )

            pygame.draw.rect(
                surf, colour,
                (last_placed_pos[0] + config["tile_border_width"],
                 last_placed_pos[1] + config["tile_border_width"],
                 size[0], size[1])
            )

            last_placed_pos[1] += border_size[1]

    else:
        for tile_pos, tile in tiler.current_group['assets'].items():
            size = [tile.get_width(), tile.get_height()]
            match tiler.current_placement_mode:
                case "draw" | "fill":
                    if size[0] != gr.tile_size[0]: continue
                    if size[1] != gr.tile_size[1]: continue
                case "autotile":
                    if tiler.current_group_name not in tiler.config['autotile_groups']:
                        break
                case _:
                    pass

            size[0] *= config['tile_scale']
            size[1] *= config['tile_scale']

            if last_placed_pos[1] > 500:
                last_placed_pos[0] += size[0] + config['tile_display_padding'] * 3
                last_placed_pos[1] = LEFT_TOP_UI_LINE[0][1] + 3
            last_placed_pos[1] += config['tile_display_padding']

            tile_rect = Rect(last_placed_pos[0], last_placed_pos[1], size[0] * 1.2, size[1] * 1.2)
            if tile_rect.collidepoint(user_input['mouse_pos']) or tiler.current_variant == tile_pos:
                size = [ceil(size[0] * 1.2), ceil(size[1] * 1.2)]

                if user_input['mouse_pressed']: tiler.current_variant = tile_pos

            border_size = [
                size[0] + config["tile_border_width"] * 2,
                size[1] + config["tile_border_width"] * 2
            ]
            tile_surf = pygame.transform.scale(tile, size)

            pygame.draw.rect(
                surf, config['tile_border_colour'],
                (last_placed_pos[0], last_placed_pos[1], border_size[0], border_size[1]),
                width=config["tile_border_width"]
            )

            surf.blit(
                tile_surf,
                (last_placed_pos[0] + config["tile_border_width"],
                 last_placed_pos[1] + config["tile_border_width"])
            )

            last_placed_pos[1] += border_size[1]

    # render text
    draw_text(surf, user_input, tiler, config, gr)


def draw_left_bg(surf, config):
    pygame.draw.rect(surf, config['ui_icons_fill_colour'], LEFT_ICONS_RECT, border_radius=5)
    pygame.draw.rect(surf, config['ui_icons_border_colour'], LEFT_ICONS_RECT, width=4, border_radius=5)

    pygame.draw.rect(surf, config['ui_fill_colour'], LEFT_UI_RECT, border_radius=10)
    pygame.draw.rect(surf, config['ui_border_colour'], LEFT_UI_RECT, width=4, border_radius=10)

    pygame.draw.rect(surf, config['ui_fill_colour'], LEFT_UI_RECT, border_radius=10)
    pygame.draw.rect(surf, config['ui_border_colour'], LEFT_UI_RECT, width=4, border_radius=10)

    pygame.draw.line(surf, config['ui_border_colour'], LEFT_TOP_UI_LINE[0], LEFT_TOP_UI_LINE[1], width=4)
    pygame.draw.line(surf, config['ui_border_colour'], LEFT_BOT_UI_LINE[0], LEFT_BOT_UI_LINE[1], width=4)


def draw_selection(surf, config, select_start, mouse_pos):
    sel_rect = Rect(select_start[0], select_start[1], mouse_pos[0] - select_start[0], mouse_pos[1] - select_start[1])
    pygame.draw.rect(surf, config['ui_select_fill_colour'], sel_rect, border_radius=5)
    pygame.draw.rect(surf, config['ui_select_border_colour'], sel_rect, width=1, border_radius=5)


def draw_text_field(surf, config, user_input):
    colour = (0, 0, 0, 0)
    if TEXT_FIELD_RECT.collidepoint(user_input['mouse_pos']):
        colour = config['text_field_selected_colour']
        if user_input['mouse_pressed']:
            user_input['text_field_selected'] = True
    else:
        colour = config['text_field_colour']
        if user_input['mouse_pressed']:
            user_input['text_field_selected'] = False

    pygame.draw.rect(surf, colour, TEXT_FIELD_RECT, border_radius=4)
    pygame.draw.rect(surf, config['text_field_outline_colour'], TEXT_FIELD_RECT, width=2, border_radius=4)

    rendered_text = TEXT_FIELD_FONT.render(
        user_input["text"][-24:] +
        ("|" if user_input['text_field_selected'] and user_input['caret_timer'] > 0 else ""),
        False, (0, 0, 0)
    )

    surf.blit(
        rendered_text, rendered_text.get_rect(centery=TEXT_FIELD_RECT.centery, left=TEXT_FIELD_RECT.left + 5)
    )

    if int(t.time() * 2 % 2) == 0: user_input['caret_timer'] = 0.8
    user_input['caret_timer'] = clamp(user_input['caret_timer'] - 0.166, 0, 1)


def draw_text(surf, user_input, tiler, config, gr):
    if tiler.current_placement_mode == "coll":
        render_text = "collisions"
    else:
        render_text = tiler.group_types[tiler.current_group_index]
    if len(render_text) > 10: render_text = render_text[0:8] + ".."

    rendered_text = SHEET_SELECT_FONT.render(render_text, False, config['ui_text_colour'])
    surf.blit(rendered_text, rendered_text.get_rect(center=SHEET_SELECT_RECT.center))

    rendered_text = GENERAL_UI_FONT.render(
        "placement mode: " + str(tiler.current_placement_mode), False, config['floating_text_colour']
    )
    surf.blit(rendered_text, rendered_text.get_rect(topleft=UI_RECTS[0].topleft))

    # display the current layer
    # TOP RIGHT UI
    # display the selected tile
    rendered_text = GENERAL_UI_FONT.render(
        "layer: " + str(tiler.current_layer), False, config['floating_text_colour']
    )

    prev_placement = rendered_text.get_rect(topright=UI_RECTS[1].topright)
    surf.blit(rendered_text, prev_placement)

    # display the type of tile selected
    if tiler.current_placement_mode == "coll":
        render_text = "type: " + str(tiler.coll_handler.ctype)
    else:
        render_text = "tile: " + str(tiler.current_variant)
    rendered_text = GENERAL_UI_FONT.render(render_text, False, config['floating_text_colour'])

    prev_placement = rendered_text.get_rect(topright=prev_placement.bottomright)
    surf.blit(rendered_text, prev_placement)

    # display the render mode
    if user_input['preview_enabled']:
        rendered_text = GENERAL_UI_FONT.render(
            "render mode: preview", False, config['floating_text_colour']
        )
    elif not user_input['grid_enabled']:
        rendered_text = GENERAL_UI_FONT.render(
            "render mode: no grid", False, config['floating_text_colour']
        )
    else:
        rendered_text = GENERAL_UI_FONT.render(
            "render mode: default", False, config['floating_text_colour']
        )

    prev_placement = rendered_text.get_rect(topright=prev_placement.bottomright)
    surf.blit(rendered_text, prev_placement)

    # BOTTOM RIGHT UI
    # display the mouse pos
    rendered_text = GENERAL_UI_FONT.render(
        "mouse pos: " + str(user_input['mouse_pos']), False, config['floating_text_colour']
    )

    prev_placement = rendered_text.get_rect(bottomright=UI_RECTS[2].topright)
    surf.blit(rendered_text, prev_placement)

    # display the grid pos
    rendered_text = GENERAL_UI_FONT.render(
        "grid pos: " + str(user_input['grid_pos']), False, config['floating_text_colour']
    )

    prev_placement = rendered_text.get_rect(bottomright=prev_placement.topright)
    surf.blit(rendered_text, prev_placement)

    # display the panning offset
    rendered_text = GENERAL_UI_FONT.render(
        "pan: " + str(gr.panning_offset), False, config['floating_text_colour']
    )

    prev_placement = rendered_text.get_rect(bottomright=prev_placement.topright)
    surf.blit(rendered_text, prev_placement)

    # display the zoom scale
    rendered_text = GENERAL_UI_FONT.render(
        "zoom: " + str(round(gr.zoom_scale, 2)), False, config['floating_text_colour']
    )

    prev_placement = rendered_text.get_rect(bottomright=prev_placement.topright)
    surf.blit(rendered_text, prev_placement)

    # BOTTOM LEFT UI
    # display the world size
    rendered_text = GENERAL_UI_FONT.render(
        "world size: " + str(gr.world_size), False, config['floating_text_colour']
    )

    prev_placement = rendered_text.get_rect(bottomleft=UI_RECTS[3].topleft)
    surf.blit(rendered_text, prev_placement)

    # display the tile size
    rendered_text = GENERAL_UI_FONT.render(
        "tile size: " + str(gr.tile_size), False, config['floating_text_colour']
    )

    prev_placement = rendered_text.get_rect(bottomleft=prev_placement.topleft)
    surf.blit(rendered_text, prev_placement)
