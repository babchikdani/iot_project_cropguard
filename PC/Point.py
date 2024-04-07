import math
class Point:
    def __init__(self, r=0, theta=0, sec=0, ms=0):
        self.r = r
        self.theta = theta  # angle, in degrees!
        ###
        self.x = None   # in cm
        self.y = None   # in cm
        self.t_sec = None   # time detected, in seconds!
        self.t_ms = None    # time detected, in milliseconds!
        self.x = math.cos(math.radians(theta)) * self.r
        self.y = math.sin(math.radians(theta)) * self.r
        self.t_sec = sec
        self.t_ms = ms

