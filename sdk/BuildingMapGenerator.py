import numpy as np

BuildingProbability = 0.1
IsBuilding = (np.random.rand(10,10) < BuildingProbability)

np.save("Buildings.npy",IsBuilding)
