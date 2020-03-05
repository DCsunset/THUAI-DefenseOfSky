import json
from Parameters import *
import math
# processingType 
# 1 << processingType
class Processor(object):
    def __init__(self,pos,rangeType,processingType,owner):
        super().__init__()
        self.pos = pos
        self.rangeType = rangeType
        self.processingType = processingType
        self.owner = owner
    def toJsonObj(self):
        data = {
            'pos': self.pos,
            'rangeType': self.rangeType,
            'processingType': self.processingType,
            'owner': self.owner,
        }
        return data
    def cover(self, targetPos):
        if BuildingMap[targetPos[0]][targetPos[1]]:
            return False
        x,y = self.pos
        for dx,dy in DeltaPos[self.rangeType]:
            if x+dx == targetPos[0] and y+dy == targetPos[1]:
                if max(abs(dx),abs(dy)) == 2 and BuildingMap[x+(dx>>1)][y+(dy>>1)]:
                    return False
                return True
        return False

                
        

class Detector(object):
    def __init__(self,pos,rangeType,owner):
        super().__init__()
        self.pos = pos
        self.rangeType = rangeType
        self.owner = owner
    def toJsonObj(self):
        data = {
            'pos': self.pos,
            'rangeType': self.rangeType,
            'owner': self.owner,
        }
        return data
    def cover(self, targetPos):
        if BuildingMap[targetPos[0]][targetPos[1]]:
            return False
        x,y = self.pos
        for dx,dy in DeltaPos[self.rangeType]:
            if x+dx == targetPos[0] and y+dy == targetPos[1]:
                if max(abs(dx),abs(dy)) == 2 and BuildingMap[x+(dx>>1)][y+(dy>>1)]:
                    return False
                return True
        return False

class Land(object):
    def __init__(self,pos,owner=-1,occupied=False,filled=False,bid=LandPrice-1,bidder=-1,round=-1,bidOnly=-1):
        super().__init__()
        self.pos = pos
        self.owner = owner
        self.filled = filled
        self.occupied = occupied
        self.bid = bid
        self.bidder = bidder
        self.round = round
        self.bidOnly = bidOnly
    def toJsonObj(self):
        data = {
            'pos': self.pos,
            'owner': self.owner,
            'occupied': self.occupied,
            'filled': self.filled,
            'bid': self.bid,
            'bidder': self.bidder,
            'round': self.round,
            'bidOnly': self.bidOnly
        }
        return data