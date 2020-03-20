import numpy as np
import random
import math

# 地图规模
MapWidth = 10
MapHeight = 10

# 地价 10的倍数
LandPrice = 200

# 加载建筑物地图
BuildingMap = np.load("Buildings.npy")

# 病毒的种类数
PollutionComponentNum = 3

# 最大回合数 要求一定是偶数
MaxRound = 120

# 覆盖范围的种类数
MaxRangeNum = 3

# 覆盖范围与形状
DeltaPos = [
    [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (0, 2), (0, -2), (2, 0), (-2, 0)],
    [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)],
    [(0, 0), (1, 1), (1, -1), (-1, 1), (-1, -1),
     (2, 2), (2, -2), (-2, 2), (-2, -2)],
]

# rangeType = 0
# _ _ * _ _
# _ _ * _ _
# * * * * *
# _ _ * _ _
# _ _ * _ _

# rangeType = 1
# _ _ _ _ _
# _ * * * _
# _ * * * _
# _ * * * _
# _ _ _ _ _

# rangeType = 2
# * _ _ _ *
# _ * _ * _
# _ _ * _ _
# _ * _ * _
# * _ _ _ *

ProcessorRangeCost = [500, 600, 500]
ProcessorTypeCost = [150, 100, 150]
DetectorRangeCost = [200, 250, 200]

# 情报贩子的价格
TipsterCost = 400

# 解决病毒的价格
PollutionProfit = [700, 800, 750]

# 每个非高大建筑的格子是疫区的概率
PollutionProbability = 0.35

NotPolluted = (np.random.rand(MapWidth, MapHeight) > PollutionProbability)
NotPolluted[BuildingMap] = True

# 疫情分布地图

PollutionMap = np.random.randint(
    1, 2**PollutionComponentNum, size=(MapWidth, MapHeight), dtype=np.int)
PollutionMap[NotPolluted] = 0

# 玩家0与玩家1分别的初始可见地图
# 玩家0执先手，玩家1执后手

PollutionMap0 = np.zeros_like(PollutionMap)
PollutionMap1 = np.zeros_like(PollutionMap)
PollutionProfitMap = np.zeros_like(PollutionMap)

PollutionPoss = []
for i in range(MapWidth):
    for j in range(MapHeight):
        if not NotPolluted[i][j]:
            PollutionPoss.append((i, j))

random.shuffle(PollutionPoss)

PollutionNum = len(PollutionPoss)

for i, j in PollutionPoss[:int(PollutionNum/3)]:
    PollutionMap0[i][j] = PollutionMap[i][j]

for i, j in PollutionPoss[PollutionNum-int(PollutionNum/3):PollutionNum]:
    PollutionMap1[i][j] = PollutionMap[i][j]

for i in range(MapWidth):
    for j in range(MapHeight):
        for k in range(PollutionComponentNum):
            PollutionProfitMap[i][j] += ((PollutionMap[i]
                                          [j] >> k) & 1)*PollutionProfit[k]

# 初始得分
Scores = [0, 0]

# 初始金钱数量
Moneys = [4000, 4000]

# 所有地皮的竞价与使用情况
from Units import *
Lands = [[] for i in range(MapWidth)]

for i in range(MapWidth):
    for j in range(MapHeight):
        if BuildingMap[i][j]:
            Lands[i].append(
                Land((i, j), owner=2, occupied=True, filled=True, bidOnly=2))
        else:
            Lands[i].append(Land((i, j)))
if __name__ == '__main__':
    def PrintMap(m):
        if m.dtype == np.bool:
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    if m[i][j]:
                        print('o', sep='', end='')
                    else:
                        print('*', sep='', end='')
                print('')
        else:
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    print(m[i][j], sep='', end='')
                print('')

    print('Buildings Map')
    PrintMap(BuildingMap)
    print()

    print('Pollution Map')
    PrintMap(PollutionMap)
    print()

    print('Pollution Map 0')
    PrintMap(PollutionMap0)
    print()

    print('Pollution Map 1')
    PrintMap(PollutionMap1)
    print()

