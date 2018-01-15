import battlecode as bc
import random
import sys
import traceback
import heapq
import os
import numpy as np

EARLY_EARLY_GAME = 150
EARLY_GAME = 400

#TIMOTHY HAN PYBOT 2
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
        directionToMove = directions[(directionToBack.opposite().value + i + 8) % 8]
        if gc.is_move_ready(robotId) and gc.can_move(robotId, directionToMove):
            gc.move_robot(robotId, directionToMove)
            return

#numpy array (accessed with array[x, y]) for initial karbonite values, -1 for impassable terrain
def getInitMap():
    if gc.planet() == bc.Planet.Earth:
        width = leMap.width
        height = leMap.height
        actualMap = np.zeros((width, height))
        for i in range(width):
            for j in range(height):
                mL = bc.MapLocation(bc.Planet.Earth, i, j)
                if leMap.is_passable_terrain_at(mL):
                    actualMap[i, j] = leMap.initial_karbonite_at(mL)
                else: 
                    actualMap[i, j] = -1
        return actualMap

def workerGatherHeur(karboniteDepoLoc, karboniteDepoSize, location, range2, workerHarvest): #takes in distance squared
    inRange=[]
    mLocation=location.map_location()
    for loc in gc.all_locations_within(mLocation,range2):
        if loc in karboniteDepoLoc:
            ind=karboniteDepoLoc.index(loc)
            heur=karboniteDepoSize[ind]//workerHarvest/(mLocation.distance_squared_to(loc)+0.001)
            heapq.heappush(inRange,(-heur,ind))
    if inRange:
        x=heapq.heappop(inRange)
        return (x[0],karboniteDepoLoc[x[1]],x[1])
    return ""
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
leActualMap = getInitMap()

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

        #Global info------------------------------

        productionCount = 0
        blueprintLoc = None
        blueprintWaiting = False

        #----------------------------------------------------------------
        for unit in gc.my_units():
            location = unit.location

            if not location.is_on_map():
                continue

            # first, factory logic
            if unit.unit_type == bc.UnitType.Factory:   #FACTORY
                garrison = unit.structure_garrison()
                if len(garrison) > 0:
                    for i in range(8):
                        d = directions[i]
                        if gc.can_unload(unit.id, d):
                            print('unloaded a %s!' %(unit.unit_type))
                            gc.unload(unit.id, d)
                            continue

                if not unit.structure_is_built():
                    blueprintLoc = unit.location.map_location()
                    blueprintWaiting = True

                if gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                    # if random.randint(0, 10) < 4:
                    #     gc.produce_robot(unit.id, bc.UnitType.Knight)
                    # else:
                    gc.produce_robot(unit.id, bc.UnitType.Ranger)
                    print('produced a ranger!')
                    productionCount+=1
                    continue

            # first, let's look for nearby blueprints to work o
            #WORKER    
            elif unit.unit_type == bc.UnitType.Worker:
                nearby = gc.sense_nearby_units(location.map_location(), 2)
                for other in nearby:
                    if other.team == my_team and gc.can_build(unit.id, other.id):
                        gc.build(unit.id, other.id)
                        print('built a factory!')
                        continue
                for i in directions:
                    if gc.karbonite() >= bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, i):
                            gc.blueprint(unit.id, bc.UnitType.Factory, i)
                            continue
                if blueprintWaiting:
                    mLoc = location.map_location()
                    distToBlue = mLoc.distance_squared_to(blueprintLoc)
                    if distToBlue > 2:
                        forwardish(mLoc.direction_to(blueprintLoc), unit.id)
                        continue

            #RANGER
            if unit.unit_type == bc.UnitType.Ranger:
                nearby = gc.sense_nearby_units(location.map_location(), unit.vision_range)
                nearby = sorted(nearby, key=lambda x: x.health)
                for other in nearby:
                    if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
                        print('attacked a thing!')
                        gc.attack(unit.id, other.id)
                        continue
                    #basic ranger micro
                    if other.team != my_team and not (gc.is_attack_ready(unit.id) or gc.can_attack(unit.id, other.id)):
                        print('backed up!')
                        backwardish(location.map_location().direction_to(other.location.map_location()), unit.id)
                        continue

            #GENERIC MOVEMENT
            if unit.unit_type != bc.UnitType.Worker and unit.unit_type != bc.UnitType.Rocket and unit.unit_type != bc.UnitType.Factory and location.is_on_map():
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