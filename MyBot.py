#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction, Position

# This library allows you to generate random numbers.
import random

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging

from hlt.game_map import GameMap
from hlt.player import Player
from hlt.entity import Ship


def get_closest_drop_point(me: Player, ship: Ship, game_map: GameMap):
    positions = [me.shipyard.position]
    for dropoff in me.get_dropoffs():
        positions.append(dropoff.position)
    
    closest = positions[0]
    closest_distance = game_map.calculate_distance(ship.position, closest)
    for pos in positions:
        dist = game_map.calculate_distance(ship.position, pos)
        if dist < closest_distance:
            closest = pos
            closest_distance = dist
    return closest


def get_safe_random_direction(ship: Ship, game_map: GameMap):
    safe_choices = []
    for direction in Direction.get_all_cardinals():
        if not game_map[ship.position.directional_offset(direction)].is_occupied:
            safe_choices.append(direction)
    if safe_choices:
        chosen_direction = random.choice(safe_choices)
        game_map[ship.position.directional_offset(chosen_direction)].mark_unsafe(ship)
        return chosen_direction
    return None


def make_moves(me: Player, game_map: GameMap):
    for ship in me.get_ships():
        #If full, return to closest drop
        if ship.has_halite():
            target_position = get_closest_drop_point(me, ship, game_map)
            command_queue.append(
                ship.move(
                    game_map.naive_navigate(ship, target_position)
                )
            )
        elif game_map[ship.position].halite_amount < constants.MAX_HALITE / 20:
            safe_direction = get_safe_random_direction(ship=ship, game_map=game_map)
            if safe_direction:
                command_queue.append(
                    ship.move(safe_direction)
                )
            else:
                command_queue.append(ship.stay_still())
        else:
            command_queue.append(ship.stay_still())

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("CassiusBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    make_moves(me=me, game_map=game_map)

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
