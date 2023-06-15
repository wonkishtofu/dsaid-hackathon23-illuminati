import h5pyd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.spatial import cKDTree

YEAR = '2020'
f = h5pyd.File(f"/nrel/nsrdb/v3/nsrdb_{YEAR}.h5", 'r')
print(f)
