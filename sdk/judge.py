import bot_judge_py as bot
import subprocess
import shlex
import time
import io
import sys
import numpy as np
import random
import math
import json

# 地图规模
MapWidth = 10
MapHeight = 10

# 地价 10的倍数
LandPrice = 200

# 加载建筑物地图
BuildingMap = np.load("/var/botany/Buildings.npy")

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
# processingType
# 1 << processingType


class Processor(object):
    def __init__(self, pos, rangeType, processingType, owner):
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
        x, y = self.pos
        for dx, dy in DeltaPos[self.rangeType]:
            if x+dx == targetPos[0] and y+dy == targetPos[1]:
                if max(abs(dx), abs(dy)) == 2 and BuildingMap[x+(dx >> 1)][y+(dy >> 1)]:
                    return False
                return True
        return False


class Detector(object):
    def __init__(self, pos, rangeType, owner):
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
        x, y = self.pos
        for dx, dy in DeltaPos[self.rangeType]:
            if x+dx == targetPos[0] and y+dy == targetPos[1]:
                if max(abs(dx), abs(dy)) == 2 and BuildingMap[x+(dx >> 1)][y+(dy >> 1)]:
                    return False
                return True
        return False


class Land(object):
    def __init__(self, pos, owner=-1, occupied=False, filled=False, bid=LandPrice-1, bidder=-1, round=-1, bidOnly=-1):
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
                        #print('o', sep='', end='')
                        pass
                    else:
                        pass
                        #print('*', sep='', end='')
                        # print('')
        else:
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    pass
                    #print(m[i][j], sep='', end='')
                    # print('')

                    #print('Buildings Map')
                    # PrintMap(BuildingMap)
                    # print()

                    #print('Pollution Map')
                    # PrintMap(PollutionMap)
                    # print()

                    #print('Pollution Map 0')
                    # PrintMap(PollutionMap0)
                    # print()

                    #print('Pollution Map 1')
                    # PrintMap(PollutionMap1)
                    # print()


detectors = []
processors = []

# subpro = []

errMsg = ['', '']

log = {}
logPerRound = []

msgObj = {}
logForSDK = [[], []]

# DEBUG


def convertByte(jsonStr):
    msgLen = len(jsonStr)
    msg = msgLen.to_bytes(4, byteorder='big', signed=True)
    msg += bytes(jsonStr, encoding="utf8")
    return msg


def sendMsg(jsonStr, goal):
    #jsonObj = json.loads(jsonStr)
    #print("======== Send To %d ========" % jsonObj['AI'])
    #print(json.dumps(jsonObj, sort_keys=True, indent=4, separators=(',', ': ')))
    # print("============================")
    #print("goal = %d" % goal)
    # subpro[goal].stdin.buffer.write(convertByte(jsonStr))
    # subpro[goal].stdin.buffer.flush()
    bot.send(goal, jsonStr)


def receiveMsg(AI):
    #readBuffer = subpro[AI].stdout.buffer
    #dataLen = int.from_bytes(readBuffer.read(4), byteorder='big', signed=True)
    # print(dataLen)
    #data = readBuffer.read(dataLen)
    # return data
    s, _ = bot.recv(AI, 1000)
    return s


def logInitState():
    initState = {
        'mapWidth': MapWidth,
        'mapHeight': MapHeight,
        'landPrice': LandPrice,
        'buildings': [],  # [(x0,y0),(x1,y1),...]
        'pollutionComponentNum': PollutionComponentNum,
        'maxRoundNum': MaxRound,
        'maxRangeNum': MaxRangeNum,
        'processorRangeCost': ProcessorRangeCost,
        'processorTypeCost': ProcessorTypeCost,
        'detectorRangeCost': DetectorRangeCost,
        'tipsterCost': TipsterCost,
        'pollutionProfit': PollutionProfit,
        'pollutionMap': PollutionMap.tolist(),
        'pollutionMap0': PollutionMap0.tolist(),
        'pollutionMap1': PollutionMap1.tolist(),
        'scores': Scores,
        'moneys': Moneys,
    }
    errMsg = ['', '']
    for i in range(MapWidth):
        for j in range(MapHeight):
            if BuildingMap[i][j]:
                initState['buildings'].append((i, j))

    log[-1] = initState


def sendInitState(AI):
    initState = {
        'mapWidth': MapWidth,
        'mapHeight': MapHeight,
        'landPrice': LandPrice,
        'buildings': [],  # [(x0,y0),(x1,y1),...]
        'pollutionComponentNum': PollutionComponentNum,
        'maxRoundNum': MaxRound,
        'maxRangeNum': MaxRangeNum,
        'processorRangeCost': ProcessorRangeCost,
        'processorTypeCost': ProcessorTypeCost,
        'detectorRangeCost': DetectorRangeCost,
        'tipsterCost': TipsterCost,
        'pollutionProfit': PollutionProfit,
        'AI': AI,
        'errMsg': errMsg[AI],
    }
    errMsg[AI] = ''
    for i in range(MapWidth):
        for j in range(MapHeight):
            if BuildingMap[i][j]:
                initState['buildings'].append((i, j))
    sendMsg(json.dumps(initState), AI)


def sendRoundState(AI, round):
    pollutionM = PollutionMap0 if AI == 0 else PollutionMap1
    state = {
        'AI': AI,
        'pollution': pollutionM.tolist(),
        'lands': [],  # 所有的地皮的详细信息
        'moneys': Moneys,
        'scores': Scores,
        'detectors': [],  # 所有场内的检测设备
        'processors': [],  # 所有场内的处理设备
        'log': logForSDK[AI],
        'errMsg': errMsg[AI],
    }
    errMsg[AI] = ''
    for i in range(MapWidth):
        state['lands'].append([])
        for j in range(MapHeight):
            state['lands'][i].append(Lands[i][j].toJsonObj())

    for detector in detectors:
        state['detectors'].append(detector.toJsonObj())

    for processor in processors:
        state['processors'].append(processor.toJsonObj())
    sendMsg(json.dumps(state), AI)


def validate(msg, AI):
    # msg = {
    #     'detector':{
    #         'pos':(x,y),
    #         'rangeType':0/1/2,
    #     },
    #     'tipster':{
    #         'pos':(x,y),
    #     },
    #     'bid':{
    #         'pos':(x,y),
    #         'bidPrice': money,
    #     },
    #     'processor':{
    #         'pos':(x,y),
    #         'rangeType':0/1/2,
    #         'processingType':0/1/2..,
    #     },
    # }
    global msgObj
    try:
        msgObj = json.loads(msg)
    except:
        errMsg[AI] = "json can't decode msg str"
        return False

    try:
        assert 'detector' in msgObj, "detector operation not found"
        assert (msgObj['detector'] is None) or ('pos' in msgObj['detector']
                                                and 'rangeType' in msgObj['detector']), 'detector operation invalid'
        assert 'tipster' in msgObj, "tipster operation not found"
        assert (msgObj['tipster'] is None) or (
            'pos' in msgObj['tipster']), 'tipster operation invalid'
        assert 'bid' in msgObj, "bid operation not found"
        assert (msgObj['bid'] is None) or ('pos' in msgObj['bid']
                                           and 'bidPrice' in msgObj['bid']), 'bid operation invalid'
        assert 'processor' in msgObj, "processor operation not found"
        assert (msgObj['processor'] is None) or ('pos' in msgObj['processor'] and 'rangeType' in msgObj['processor']
                                                 and 'processingType' in msgObj['processor']), 'processing operation invalid'
    except AssertionError as Argument:
        errMsg[AI] = Argument
        return False

    try:
        if not msgObj['detector'] is None:
            assert type(msgObj['detector']['pos']) == type(
                []), 'detector pos invalid'
            assert len(msgObj['detector']['pos']) == 2, 'detector pos invalid'
            assert type(msgObj['detector']['pos'][0]) == type(
                0), "detector pos invalid"
            assert type(msgObj['detector']['pos'][1]) == type(
                0), "detector pos invalid"
            assert type(msgObj['detector']['rangeType']) == type(
                0), 'detector rangeType invalid'
        if not msgObj['tipster'] is None:
            assert type(msgObj['tipster']['pos']) == type(
                []), 'tipster pos invalid'
            assert len(msgObj['tipster']['pos']) == 2, 'tipster pos invalid'
            assert type(msgObj['tipster']['pos'][0]) == type(
                0), "tipster pos invalid"
            assert type(msgObj['tipster']['pos'][1]) == type(
                0), "tipster pos invalid"

        if not msgObj['bid'] is None:
            assert type(msgObj['bid']['pos']) == type([]), 'bid pos invalid'
            assert len(msgObj['bid']['pos']) == 2, 'bid pos invalid'
            assert type(msgObj['bid']['pos'][0]) == type(0), "bid pos invalid"
            assert type(msgObj['bid']['pos'][1]) == type(0), "bid pos invalid"
            assert type(msgObj['bid']['bidPrice']) == type(
                0), 'bid bidPrice invalid'
        if not msgObj['processor'] is None:
            assert type(msgObj['processor']['pos']) == type(
                []), 'processor pos invalid'
            assert len(msgObj['processor']['pos']
                       ) == 2, 'processor pos invalid'
            assert type(msgObj['processor']['pos'][0]) == type(
                0), "processor pos invalid"
            assert type(msgObj['processor']['pos'][1]) == type(
                0), "processor pos invalid"
            assert type(msgObj['processor']['rangeType']) == type(
                0), 'processor rangeType invalid'
            assert type(msgObj['processor']['processingType']) == type(
                0), 'processor processingType invalid'
    except AssertionError as Argument:
        errMsg[AI] = Argument
        return False
    return True


def treatPollution(pro, AI):
    pM = PollutionMap0 if AI == 0 else PollutionMap1
    for i in range(MapWidth):
        for j in range(MapHeight):
            if pro.cover((i, j)) and pM[i][j]:
                if ((pM[i][j] >> pro.processingType) & 1):
                    pM[i][j] -= (1 << pro.processingType)
                    if pM[i][j] == 0:
                        Moneys[AI] += int(PollutionProfitMap[i][j])
                        Scores[AI] += int(PollutionProfitMap[i][j])
                        PollutionMap0[i][j] = 0
                        PollutionMap1[i][j] = 0
                        PollutionMap[i][j] = 0
                        logPerRound.append(
                            (10, AI, (i, j), (int)(PollutionProfitMap[i][j])))
                        logForSDK[AI].append((5, (i, j)))


def construct(operation, AI):
    if operation['processor'] is not None:
        pos = operation['processor']['pos']
        rangeType = operation['processor']['rangeType']
        processingType = operation['processor']['processingType']
        if 0 <= pos[0] and pos[0] <= MapWidth-1 and 0 <= pos[1] and pos[1] <= MapHeight-1:
            land = Lands[pos[0]][pos[1]]
            if land.owner == AI and not land.occupied:
                if 0 <= rangeType and rangeType < MaxRangeNum and 0 <= processingType and processingType < PollutionComponentNum:
                    cost = ProcessorRangeCost[rangeType] + \
                        ProcessorTypeCost[processingType]
                    if Moneys[AI] >= cost:
                        Moneys[AI] -= cost
                        land.occupied = True
                        processors.append(
                            Processor(tuple(pos), rangeType, processingType, AI))
                        logPerRound.append(
                            (1, AI, tuple(pos), rangeType, processingType))
                        logForSDK[AI].append(
                            (4, tuple(pos), rangeType, processingType))
                        logForSDK[1-AI].append((9, tuple(pos),
                                                rangeType, processingType))
                        treatPollution(processors[-1], AI)


def checkPollution(det, AI):
    pM = PollutionMap0 if AI == 0 else PollutionMap1
    for i in range(MapWidth):
        for j in range(MapHeight):
            if det.cover((i, j)):
                if PollutionMap[i][j] and pM[i][j] == 0:
                    pM[i][j] = PollutionMap[i][j]
                    logPerRound.append((6, AI, (i, j)))
                    logForSDK[AI].append((3, (i, j), (int)(pM[i][j])))


def launch(operation, AI):
    if operation['detector'] is not None:
        pos = operation['detector']['pos']
        rangeType = operation['detector']['rangeType']
        if 0 <= pos[0] and pos[0] <= MapWidth-1 and 0 <= pos[1] and pos[1] <= MapHeight-1:
            land = Lands[pos[0]][pos[1]]
            if not land.filled:
                if 0 <= rangeType and rangeType < MaxRangeNum:
                    cost = DetectorRangeCost[rangeType]
                    if Moneys[AI] >= cost:
                        Moneys[AI] -= cost
                        land.filled = True
                        detectors.append(Detector(pos, rangeType, AI))
                        logPerRound.append((5, AI, tuple(pos), rangeType))
                        logForSDK[AI].append((2, tuple(pos), rangeType))
                        logForSDK[1-AI].append((8, tuple(pos), rangeType))
                        checkPollution(detectors[-1], AI)


def bid(operation, AI):
    if operation['bid'] is not None:
        pos = operation['bid']['pos']
        bidPrice = operation['bid']['bidPrice']
        if 0 <= pos[0] and pos[0] <= MapWidth-1 and 0 <= pos[1] and pos[1] <= MapHeight-1:
            land = Lands[pos[0]][pos[1]]
            if land.owner == -1 and (land.bidOnly == AI or land.bidOnly == -1) and land.bidder != AI and bidPrice > land.bid and bidPrice % int(0.1*LandPrice) == 0:
                land.bid = bidPrice
                land.bidder = AI
                land.round = 6
                logForSDK[AI].append((6, tuple(pos), bidPrice))
                logForSDK[1-AI].append((7, tuple(pos), bidPrice))
                logPerRound.append((2, AI, tuple(pos), bidPrice))


def tipster(operation, AI):
    if operation['tipster'] is not None:
        pos = operation['tipster']['pos']
        pM = PollutionMap0 if AI == 0 else PollutionMap1
        if Moneys[AI] >= TipsterCost:
            Moneys[AI] -= TipsterCost
            logPerRound.append((3, AI, tuple(pos)))
        else:
            return
        deltaM = np.zeros_like(PollutionMap)
        for i in range(MapWidth):
            for j in range(MapHeight):
                if PollutionMap[i][j] and pM[i][j] == 0:
                    deltaM[i][j] = PollutionMap[i][j]
        if np.sum(deltaM) == 0:
            return

        tmp = []
        for i in range(MapWidth):
            for j in range(MapHeight):
                if deltaM[i][j] > 0:
                    tmp.append((i, j))
        tmp.sort(key=lambda x: abs(x[0]-pos[0])+abs(x[1]-pos[1]))
        pM[tmp[0][0]][tmp[0][1]] = PollutionMap[tmp[0][0]][tmp[0][1]]
        logForSDK[AI].append((0, tuple(pos)))
        logPerRound.append((4, AI, tuple(tmp[0])))
        logForSDK[AI].append(
            (1, tuple(tmp[0]), (int)(pM[tmp[0][0]][tmp[0][1]])))


def bidUpdate():
    for i in range(MapWidth):
        for j in range(MapHeight):
            land = Lands[i][j]
            if land.owner == -1 and (land.bidder == 0 or land.bidder == 1):
                land.round -= 1
                logPerRound.append((7, (i, j), land.round))
                if land.round == 0:
                    if Moneys[land.bidder] >= land.bid:
                        Moneys[land.bidder] -= land.bid
                        land.owner = land.bidder
                        logPerRound.append((8, (i, j), land.owner, land.bid))
                    else:
                        logPerRound.append((9, (i, j), land.bidder))
                        land.bidOnly = 1-land.bidder
                        land.bidder = -1
                        land.bid = LandPrice-1


def endGame():
    if np.sum(PollutionMap) == 0:
        return True
    money = max(Moneys)
    tmp = [TipsterCost, min(DetectorRangeCost), min(
        ProcessorRangeCost) + min(ProcessorTypeCost)]
    if money < min(tmp):
        return True
    return False


def main():
    global log, logPerRound, subpro, logForSDK
    if bot.init(sys.argv) != 2:
        print('Incorrect number of players!')
        sys.exit()

    # 启动进程
    # try:
    #    subpro.append(subprocess.Popen(shlex.split(sys.argv[1]), stdout=subprocess.PIPE,\
    #            stdin=subprocess.PIPE, universal_newlines=True))
    #    subpro.append(subprocess.Popen(shlex.split(sys.argv[2]), stdout=subprocess.PIPE,\
    #            stdin=subprocess.PIPE, universal_newlines=True))
    # except Exception as e:
    #    for pro in subpro:
    #        try:
    #            pro.terminate()
    #        except:
    #            pass
    #    print(e)
    #    sys.exit()
    # 初始化，给出地图信息

    sendInitState(0)
    sendInitState(1)

    logInitState()

    for round in range(MaxRound):
        AI = round % 2
        # 向AI发送当前的局面信息
        sendRoundState(AI, round)
        # 等待并接收AI的操作信息
        # time.sleep(1)
        # 执行AI的操作消息
        msg = receiveMsg(AI)

        # Fail
        if msg == None:
            Scores[AI] = -1
            Scores[1-AI] = 0
            break

        logForSDK[AI] = []

        if validate(msg, AI):
            # 为了降低AI难度，结算顺序如下：
            # 治理设备建造操作结算
            construct(msgObj, AI)

            # 地皮标记操作结算
            bid(msgObj, AI)

            # 设置新的检测设备
            launch(msgObj, AI)

            # 使用技能操作结算
            tipster(msgObj, AI)

        # 地皮竞拍结果结算
        bidUpdate()

        log[round] = logPerRound
        logPerRound = []

        # 判断游戏是否结束
        if endGame():
            break

    # 保存录像文件
    print('{ "player0": %d, "player1": %d, "replay": "%s" }' %
          (Scores[0], Scores[1], json.dumps(log)))
    # fo = open("replay.json", "w")
    # fo.write(json.dumps(log))
    # fo.close()
    bot.finish()


if __name__ == '__main__':
    # 配置环境等等初始化放在这里
    main()
