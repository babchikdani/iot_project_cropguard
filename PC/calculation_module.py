import math
import time
from Point import *
EPSILON = 0.1


# calculate the delta between P2-P1 times! Assume that p2 is the latter point
def __calculate_delta_t(p1_sec, p1_ms, p2_sec, p2_ms):
    p1_total_ms = p1_sec*1000 + p1_ms       # tops at 59,999 ms
    p2_total_ms = p2_sec*1000 + p2_ms       # tops at 59,999 ms
    if p2_total_ms > p1_total_ms:
        return p2_total_ms-p1_total_ms
    else:   # A new minute started and then p2 is lower in seconds than p1
        return 60000-p1_total_ms+p2_total_ms


# Given two Points (with timestamps inside), calculate the velocities on X, Y axis.
# Returns the velocities in [cm/secs]!
def calculate_velocity(point1: Point, point2: Point):
    delta_x = point2.x - point1.x   # in cm
    delta_y = point2.y - point1.y   # in cm
    print('delta_x = ', delta_x)
    print('delta_y = ', delta_y)
    delta_t_ms = __calculate_delta_t(point1.t_sec, point1.t_ms, point2.t_sec, point2.t_ms)
    print('delta_t_ms = ', delta_t_ms)
    delta_t_secs = delta_t_ms/1000.0    # converts 59800 ms -> 59.800 seconds
    print('delta_t_secs = ', delta_t_secs)
    if delta_t_ms == 0:
        raise ValueError("Time difference (delta_t) cannot be zero")
    velocity_x_axis = delta_x/delta_t_secs      # [cm/sec]!
    velocity_y_axis = delta_y/delta_t_secs      # [cm/sec]!
    return velocity_x_axis, velocity_y_axis


# calculates the interception point from a given point, velocity and future time
# future measured in SECONDS!
# Vx, Vy measured in [cm/sec]!
# calculates the interception angle at which the target is supposed to be in @future time.
# return the interception angle and th
def calculate_interception_angle(vx, vy, last_point: Point, future):
    # future is the seconds into the future where we want hte object to be intercepted.
    predicted_x = last_point.x + vx * future
    predicted_y = last_point.y + vy * future
    if vy == 0 and vx == 0:
        theta_rad = math.atan2(last_point.y, last_point.x)
        if theta_rad < 0:
            theta_rad += math.pi
        return abs(math.degrees(theta_rad))
    if vy == 0:  # horizontal velocity
        if abs(predicted_y) < EPSILON:  # Very close to zero
            if predicted_x > 0:
                return 0
            elif predicted_x < 0:
                return 180
            else:   # predicted_x == 0
                if last_point.x > 0:
                    return 0
                else:
                    return 180
    if vx == 0:
        if abs(predicted_x) < EPSILON:  # Very close to zero
            return 90

    if predicted_y < 0:
        return 90  # when the object is outside the scan scope -> look straight
    theta_rad = math.atan2(predicted_y, predicted_x)
    if theta_rad < 0:
        theta_rad += math.pi
    intercept_angle = abs(math.degrees(theta_rad))
    return intercept_angle


