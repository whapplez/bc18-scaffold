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
# NEED TO DO: 
#   pathfinding
#   go to mars lol
#   get defense till mars
#   get workers to harvest
#-----------------------------------------------------------------------------------------------------------#
#                                                                                                           #
#                                           HELPER FUNCTIONS                                                #
#                                                                                                           #
#-----------------------------------------------------------------------------------------------------------#

def onEarth(loc):
    if (loc.x<0) or (loc.y<0) or (loc.x>=gc.starting_map(bc.Planet.Earth).width) or (loc.y>=gc.starting_map(bc.Planet.Earth).height): return False
    return True

class mmap():
    def __init__(self,width,height):
        self.width=width
        self.height=height
        self.arr=[[0]*self.height for i in range(self.width)]

    def onMap(self,loc):
        if (loc.x<0) or (loc.y<0) or (loc.x>=self.width) or (loc.y>=self.height): 
            return False
        return True

    def clear(self):
        self.arr=[[0]*self.height for i in range(self.width)]

    def get(self,mapLocation): #get karbo value
        if not self.onMap(mapLocation):
            return -1
        return self.arr[mapLocation.x][mapLocation.y]

    def set(self,mapLocation,val): #set karbo value
        self.arr[mapLocation.x][mapLocation.y] = val

    def printout(self):
        print('printing map:')
        for y in range(self.height):
            buildstr=''
            for x in range(self.width):
                buildstr+=format(self.arr[x][self.height-1-y],'2d')
            print(buildstr)

    def addDisk(self,mapLocation,r2,val):
        locs = gc.all_locations_within(mapLocation,r2)
        for loc in locs:
            if self.onMap(loc):
                self.set(loc,self.get(loc)+val)

    def multiply(self,mmap2):
        for x in range(self.width):
            for y in range(self.height):
                ml = bc.MapLocation(bc.Planet.Earth,x,y);
                self.set(ml,self.get(ml)*mmap2.get(ml))

    def findBest(self,mapLocation,r2):
        locs = gc.all_locations_within(mapLocation,r2)
        bestAmt = 0
        bestLoc = None
        for loc in locs:
            amt = self.get(loc)
            if amt>bestAmt:
                bestAmt=amt
                bestLoc=loc
        return bestAmt, bestLoc

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

def genMoveRanger(unit, location):
    if unit.unit_type != bc.UnitType.Worker and unit.unit_type != bc.UnitType.Rocket and unit.unit_type != bc.UnitType.Factory and location.is_on_map():
        targetLoc = 0
        for i in initUnits:
            if i.team != my_team and i.unit_type == bc.UnitType.Worker:
                if distanceBetweenUnits(unit, i) <= 6:
                    finishedInit.append(i.location.map_location())
                if not i.location.map_location() in finishedInit:
                    targetLoc = i.location
                    break

        if isinstance(targetLoc, int):
            if len(enemy) > 0:
                targetLoc = enemy[0].location
        if isinstance(targetLoc, int):
            d = random.choice(directions)
        else:
            d = location.map_location().direction_to(targetLoc.map_location())
        forwardish(d, unit.id)

def distanceBetweenUnits(unit, other):
    return unit.location.map_location().distance_squared_to(other.location.map_location())

def nextKarboDirection(unit):
    mostKarbo = 0
    mostKarboDir = None
    location = unit.location.map_location()
    for d in directions:
        amountOfKarbo = checkKarbo(location.add(d))
        if mostKarbo < amountOfKarbo:
            mostKarbo = amountOfKarbo
            mostKarboDir = d
    return mostKarbo, mostKarboDir

def checkKarbo(mapLocation):
    if onEarth(mapLocation):
        return gc.karbonite_at(mapLocation)
    return 0

def findKarbo(unit): #THIS SHIT TIMES OUT
    currentLocs = []
    currentLocs.append(unit.location.map_location())
    while len(currentLocs) > 0:
        nextLocs = []
        for locs in currentLocs:
            for d in directions:
                nextLoc = locs.add(d)
                if kMap.get(nextLoc)==0:
                    dMap.set(nextLoc,1)
                    nextLocs.append(nextLoc)
                if dMap.get(nextLoc) < 1 and kMap.get(nextLoc)>0:
                    dMap.clear()
                    return nextLoc
        currentLocs = nextLocs
    return None


# def pathFinder(unit, mapLocation):
    

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
finishedInit = []
enemy = []
planet = gc.planet()

karboLocs = []
dMap = mmap(leMap.width, leMap.height) #make dummy map
kMap = mmap(leMap.width, leMap.height) #make a karbo map
for x in range(leMap.width):
    for y in range(leMap.height):
        loc = bc.MapLocation(planet, x, y)
        initKarbo = leMap.initial_karbonite_at(loc)
        if initKarbo > 0:
            karboLocs.append(loc)
        kMap.set(loc, initKarbo)

print("pystarted")

random.seed(6137)

gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)

my_team = gc.team()

while True:
    try:
        # walk through our units:
        #Global info where i count things------------------------------
        workerCount = 0
        factoryCount = 0
        for unit in gc.my_units():
            if unit.unit_type == bc.UnitType.Worker:
                workerCount += 1
            if unit.unit_type == bc.UnitType.Factory:
                factoryCount += 1

        blueprintLoc = None
        blueprintWaiting = False
        #------------------------------------------

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
                    continue

                # if gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                #     gc.produce_robot(unit.id, bc.UnitType.Ranger)
                #     print('produced a ranger!')
                #     productionCount+=1
                #     continue

            #WORKER    
            if unit.unit_type == bc.UnitType.Worker:
                if workerCount < 10: #replicates workers
                    for d in directions:
                        if gc.can_replicate(unit.id, d):
                            gc.replicate(unit.id, d)
                            workerCount += 1
                            print("I replicated!")
                            continue

                nearby = gc.sense_nearby_units(location.map_location(), 2)
                for other in nearby: #builds adjacent factories
                    if gc.can_build(unit.id, other.id):
                        gc.build(unit.id, other.id)
                        print("I built Shit!")
                        continue

                if blueprintWaiting: #goes to nearest factories
                    mLoc = location.map_location()
                    distToBlue = mLoc.distance_squared_to(blueprintLoc)
                    if distToBlue > 2:
                        forwardish(mLoc.direction_to(blueprintLoc), unit.id)
                        print("I went to the unfinished blueprint!", gc.round())
                        continue

                for i in directions: #blueprints factories
                    if gc.karbonite() >= bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, i):
                        if factoryCount < 200:
                            gc.blueprint(unit.id, bc.UnitType.Factory, i)
                            print("Blueprinted!")
                            continue

                bestAmount, bestDirection = nextKarboDirection(unit)
                #Harvests the closest and best deposit of karbonite if nearby
                if bestAmount > 0:
                    if gc.can_harvest(unit.id, bestDirection):
                        gc.harvest(unit.id, bestDirection)
                        arbLoc = unit.location.map_location().add(bestDirection)
                        kMap.set(arbLoc, gc.karbonite_at(arbLoc))
                        continue

                #goes looking for karbonite
                karboLocs = sorted(karboLocs, key=lambda x: x.distance_squared_to(unit.location.map_location()))
                if gc.round() < 10:
                    print(len(karboLocs), gc.round())
                if len(karboLocs) > 0:
                    while len(karboLocs) > 0:
                        if gc.can_sense_location(karboLocs[0]):
                            if gc.karbonite_at(karboLocs[0]) == 0:
                                print(unit.location.map_location())
                                print(gc.karbonite_at(karboLocs[0]))
                                print(karboLocs[0])
                                xd = karboLocs.remove(karboLocs[0])
                                print(xd)
                                continue

                        forwardish(unit.location.map_location().direction_to(karboLocs[0]), unit.id)
                        break
                    continue

            #RANGER
            if unit.unit_type == bc.UnitType.Ranger:
                nearby = gc.sense_nearby_units(location.map_location(), unit.vision_range)
                nearby = sorted(nearby, key=lambda x: x.health)
                for other in nearby:
                    if other.team != my_team:
                        if not other in enemy:
                            enemy.append(other)

                        if gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
                            print('attacked a thing!')
                            gc.attack(unit.id, other.id)
                            if other.health == 0:
                                enemy.remove(other)
                            continue
                    #basic ranger micro
                        if not (gc.is_attack_ready(unit.id) or gc.can_attack(unit.id, other.id)):
                            print('backed up!')
                            backwardish(location.map_location().direction_to(other.location.map_location()), unit.id)
                            continue
            genMoveRanger(unit, location)

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
