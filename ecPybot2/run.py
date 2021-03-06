import battlecode as bc
import random
import sys
import traceback
import queue
import os
import heapq

EARLY_EARLY_GAME = 150
EARLY_GAME = 400

#PYBOT 2
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
        return (-x[0],karboniteDepoLoc[x[1]],x[1])
    return ""
def workerBuildHeur():

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

        #Global info------------------------------
        #karbonite depos
        karboniteDepoLoc = []
        karboniteDepoSize = []
        for r in range(leMap.height):
            for c in range(leMap.width):
                loc=bc.MapLocation(gc.planet(),c,r)
                karb = leMap.initial_karbonite_at(loc)
                if karb>0:
                    # print("karb: "+str(karb))
                    karboniteDepoLoc.append(loc)
                    karboniteDepoSize.append(karb)
        scavenger = set() #workers that look for karbonite
        productionCount=1
        workerUnload=0
        gameTurn=bc.game_turns()

        #----------------------------------------------------------------
        for unit in gc.my_units():
            location = unit.location
            mapLocation = location.map_location()
            if not location.is_on_map():
                continue
            nearby = gc.sense_nearby_units(location.map_location(), unit.vision_range)
            # first, factory logic
            if unit.unit_type == bc.UnitType.Factory:   #FACTORY
                garrison = unit.structure_garrison()
                if len(garrison) > 0:
                    for i in range(8):
                        d = directions[i]
                        if gc.can_unload(unit.id, d):
                            print('unloaded a %s!' %(unit.unit_type))
                            gc.unload(unit.id, d)
                            if gameTurn<50 or workerUnload%3!=0:
                                scavenger.add(sense_unit_at_location(mapLocation.add(d)).id)
                            continue
                print("its a factory")
                print("karbonite I have: "+str(gc.karbonite()))
                if gc.can_produce_robot(unit.id, bc.UnitType.Worker):
                    print("prodCount: "+str(productionCount))
                    if productionCount<4 or productionCount%2==0 and productionCount<60:
                        gc.produce_robot(unit.id, bc.UnitType.Worker)
                        print('produced worker')
                    # if random.randint(0, 10) < 4:
                    #     gc.produce_robot(unit.id, bc.UnitType.Knight)
                    # else:
                    elif gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                        gc.produce_robot(unit.id, bc.UnitType.Ranger)
                        print('produced a ranger!')
                    productionCount+=1
                    

            # first, let's look for nearby blueprints to work on

            #RANGER
            elif unit.unit_type == bc.UnitType.Ranger:
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

            #WORKER    
            elif unit.unit_type == bc.UnitType.Worker:
                adjacent=gc.sense_nearby_units(location.map_location(),2)
                d = random.choice(directions)

                if unit.id in scavenger: #-------------------scavengers--------------------------------------------------------------------------------
                    workerHarvest=unit.worker_harvest_amount()
                    karboLoc=workerGatherHeur(karboniteDepoLoc, karboniteDepoSize,location,65,workerHarvest)
                    if not karboLoc:
                        continue
                    if karboLoc[0]!=0:
                        d=location.map_location().direction_to(karboLoc[1])
                        if karboLoc[0]>999:
                            gc.harvest(unit.id, d)
                            karboniteDepoSize[karboLoc[2]]-=workerHarvest
                            if karboniteDepoSize[karboLoc[2]]<1:
                                   karboniteDepoSize.remove(karboLoc[2])
                                   karboniteDepoLoc.remove(karboLoc[2])
                    else:
                        karboLoc=workerGatherHeur(karboniteDepo,location,9,workerHarvest)
                        if karboLoc[0]!=0:
                            d=location.map_location().direction_to(karboLoc[1])
                    forwardish(d,unit.id)
                else:#---------------------------------------builders------------------------------------------------------------------------
                    for other in nearby:
                        if other.team == my_team:
                            if gc.can_build(unit.id, other.id) and other in adjacent:
                                gc.build(unit.id, other.id)
                                print('built a factory!')
                            elif gc.karbonite() >= bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
                                gc.blueprint(unit.id, bc.UnitType.Factory, d)
                            elif other.unit_type==bc.UnitType.Factory:
                                    backwardish(location.map_location().direction_to(other.location.map_location()), unit.id)
                    # else:
                    #     noFactory=True

                # move onto the next unit
            # okay, there weren't any dudes around
            # pick a random direction:
            # d = random.choice(directions)

            # or, try to build a factory:
            # and if that fails, try to move

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
