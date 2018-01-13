import battlecode as bc
import random
import sys
import traceback

import os

EARLY_GAME = 200

#-----------------------------------------------------------------------------------------------------------#
#                                                                                                           #
#                                           HELPER FUNCTIONS                                                #
#                                                                                                           #
#-----------------------------------------------------------------------------------------------------------#

def forwardish(targetDirection, robotId):
    for i in possibleDirections:
        directionToMove = directions[(targetDirection.value + i + 8) % 8]
        if gc.is_move_ready(robotId) and gc.can_move(robotId, directionToMove):
            gc.move_robot(robotId, directionToMove)
            return

def backwardish(directionToBack, robotId):
    for i in possibleDirections:
        directionToMove = directions[(targetDirection.opposite.value + i + 8) % 8]
        if gc.is_move_ready(robotId) and gc.can_move(robotId, directionToMove):
            gc.move_robot(robotId, directionToMove)
            return


#-----------------------------------------------------------------------------------------------------------#
#                                                                                                           #
#                                               ACTUAL CODE                                                 #
#                                                                                                           #
#-----------------------------------------------------------------------------------------------------------#

print(os.getcwd())

print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
directions = list(bc.Direction)
possibleDirections = [0, 1, -1, 2, -2, 3, -3, 4]
leMap = gc.starting_map(gc.planet())
initUnits = leMap.initial_units

print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)

my_team = gc.team()

while True:
    # We only support Python 3, which means brackets around print()
    #print('pyround:', gc.round())

    # frequent try/catches are a good idea
    try:
        # walk through our units:
        for unit in gc.my_units():

            # first, factory logic
            if unit.unit_type == bc.UnitType.Factory:
                garrison = unit.structure_garrison()
                if len(garrison) > 0:
                    for i in range(8):
                        d = directions[i]
                        if gc.can_unload(unit.id, d):
                            print('unloaded a %s!' %(unit.unit_type))
                            gc.unload(unit.id, d)
                            continue
                elif gc.can_produce_robot(unit.id, bc.UnitType.Knight):
                    gc.produce_robot(unit.id, bc.UnitType.Mage)
                    print('produced a ranger!')
                    continue

            # first, let's look for nearby blueprints to work on
            location = unit.location
            if location.is_on_map():
                nearby = gc.sense_nearby_units(location.map_location(), 30)
                for other in nearby:
                    if unit.unit_type == bc.UnitType.Worker and gc.can_build(unit.id, other.id):
                        gc.build(unit.id, other.id)
                        print('built a factory!')
                        # move onto the next unit
                        continue
                    if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
                        print('attacked a thing!')
                        gc.attack(unit.id, other.id)
                        continue

                    #basic ranger micro
                    if other.team != my_team and unit.unit_type == bc.UnitType.Ranger and not (gc.is_attack_ready(unit.id) or gc.can_attack(unit.id, other.id)):
                        print('backed up!')
                        backwardish(location.map_location().direction_to(other.location.map_location()), unit.id)
                        continue


            # okay, there weren't any dudes around
            # pick a random direction:
            d = random.choice(directions)

            # or, try to build a factory:
            if gc.karbonite() >= bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
                gc.blueprint(unit.id, bc.UnitType.Factory, d)
            # and if that fails, try to move

            if unit.unit_type == bc.UnitType.Mage and location.is_on_map():
                targetLoc = 0
                for i in initUnits:
                    if i.team != my_team and i.unit_type == bc.UnitType.Worker:
                        targetLoc = i.location

                d = location.map_location().direction_to(targetLoc.map_location())
                forwardish(d, unit.id)
            # elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
            #     gc.move_robot(unit.id, d)

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()

print(directions)

#WHAT TO DO NEXT:
#   Rangers can't shoot when they get too close. So Dont. 
#
#
#
#
