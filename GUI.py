import time
import tkinter as tk
import math
import sys
import threading
import serial
import array
from tkinter import messagebox
from calculation_module import *
from COM import *
# Future time
FUTURE = 1  # seconds

# Distance sensitivity
DISTANCE_SENSITIVITY = 5
ERROR_DISTANCE = 999

# Tkinter canvas settings
RADAR_WIDTH = 800
RADAR_HEIGHT = 400
CENTER_X = RADAR_WIDTH/2
CENTER_Y = 400
LINE_LENGTH = 400

# Commands:
READ_DISTANCE = 1
FACE_TARGET = 2

# Serial settings
BAUD_RATE = 115200
FULL_SCAN_DEGREES = 180
DATA_SIZE = 5       # bytes we receive from the ESP


def send_data_to_esp32(cmd, angle):
    # Send the data to the ESP32
    cmd_byte = cmd.to_bytes(1, 'little')
    angle = int(angle)
    angle_byte = angle.to_bytes(1, 'little')
    bytes_list_esp32 = [cmd_byte, angle_byte]
    data_to_send_esp32 = b''.join(bytes_list_esp32)
    esp32_serial.flushOutput()
    esp32_serial.write(data_to_send_esp32)
    res = lambda arg: "FACE_TARGET" if cmd == FACE_TARGET else "READ_DISTANCE"
    print(f"Command {res(cmd)}, at {angle} was successfully sent to esp32")


def read_esp32_serial():
    try:
        incoming_data = esp32_serial.readline().decode()    # distance is a new-line terminated string
        incoming_data = incoming_data[:-1]          # pop the "\n"
        incoming_data = incoming_data.split('_')
        distance = int(incoming_data[0])
        angle = int(incoming_data[1])
        seconds = int(incoming_data[2])
        milliseconds = int(incoming_data[3])
        return distance, angle, seconds, milliseconds
    except ValueError as ee:
        print(ee)
        return read_esp32_serial()


class RadarControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control")
        self.blip_id = 0
        self.first_scan = True
        self.stop_scan_pressed = False
        self.p1 = None
        self.p2 = None
        self.got_p1 = False
        self.got_p2 = False
        self.max_angle = None
        self.min_angle = None
        self.max_distance = None
        self.min_distance = None
        self.speed = None
        self.total_reads = 0
        self.bad_reads = 0
        self.total_interceptions = 0
        self.room_scan_data = array.array('i', [0]*(FULL_SCAN_DEGREES+1))   # array for degrees 0 to 180.
        self.last_scan = array.array('i', [0]*(FULL_SCAN_DEGREES+1))   # array for degrees 0 to 180.
        # Create UI elements
        self.logo = tk.PhotoImage(file="../Assets/logo.png")
        self.resized_logo = self.logo.subsample(self.logo.width()//200, self.logo.height()//200)
        self.image_label = tk.Label(root, image=self.resized_logo)
        self.image_label.pack()
        self.label_font = ("Arial", 12, "normal")
        self.speed_label = tk.Label(root, text="Speed:", font=self.label_font)
        self.speed_scale = tk.Scale(root, from_=1, to=3, orient="horizontal")
        self.max_angle_label = tk.Label(root, text="Max Scan Angle:", font=self.label_font)
        self.max_angle_scale = tk.Scale(root, from_=0, to=180, orient="horizontal", resolution=1)
        self.max_angle_scale.set(180)
        self.min_angle_label = tk.Label(root, text="Min Scan Angle:", font=self.label_font)
        self.min_angle_scale = tk.Scale(root, from_=0, to=180, orient="horizontal", resolution=1)
        self.max_dist_label = tk.Label(root, text="Max Scan Distance [cm]:", font=self.label_font)
        self.max_dist_scale = tk.Scale(root, from_=30, to=800, orient="horizontal", resolution=1)
        self.max_dist_scale.set(800)
        self.min_dist_label = tk.Label(root, text="Min Scan Distance [cm]:", font=self.label_font)
        self.min_dist_scale = tk.Scale(root, from_=30, to=800, orient="horizontal", resolution=1)
        button_width = 20
        button_height = 2
        self.start_button = tk.Button(root, text="Start Scan", command=self.start_scan, bg="green", width=button_width, height=button_height, font=("Arial", 12, "italic"))
        self.stop_button = tk.Button(root, text="Stop Scan", command=self.stop_scan, bg="red", width=button_width, height=button_height, font=("Arial", 12, "italic"))
        self.reset_button = tk.Button(root, text="Reset", command=self.reset_scan, bg="blue", width=button_width, height=button_height, font=("Arial", 12, "italic"))
        self.statistics_button = tk.Button(root, text="Statistics", command=self.print_statistics, bg="cyan", width=button_width, height=button_height, font=("Arial", 12, "italic"))
        # Create a canvas for radar display
        self.radar_canvas = tk.Canvas(root, width=RADAR_WIDTH, height=RADAR_HEIGHT, bg="black")
        # Place UI elements on the grid
        pad_x = 1
        pad_y = 1
        self.image_label.grid(row=0, column=2, padx=pad_x, pady=pad_y, rowspan=5, columnspan=2)
        self.speed_label.grid(row=0, column=0, padx=pad_x, pady=pad_y)
        self.speed_scale.grid(row=0, column=1, padx=pad_x, pady=pad_y)
        self.max_angle_label.grid(row=1, column=0, padx=pad_x, pady=pad_y)
        self.max_angle_scale.grid(row=1, column=1, padx=pad_x, pady=pad_y)
        self.min_angle_label.grid(row=2, column=0, padx=pad_x, pady=pad_y)
        self.min_angle_scale.grid(row=2, column=1, padx=pad_x, pady=pad_y)
        self.max_dist_label.grid(row=3, column=0, padx=pad_x, pady=pad_y)
        self.max_dist_scale.grid(row=3, column=1, padx=pad_x, pady=pad_y)
        self.min_dist_label.grid(row=4, column=0, padx=pad_x, pady=pad_y)
        self.min_dist_scale.grid(row=4, column=1, padx=pad_x, pady=pad_y)
        self.reset_button.grid(row=5, column=0, columnspan=1, padx=pad_x, pady=pad_y)
        self.start_button.grid(row=5, column=1, columnspan=1, padx=pad_x, pady=pad_y)
        self.stop_button.grid(row=5, column=2, columnspan=1, padx=pad_x, pady=pad_y)
        self.statistics_button.grid(row=5, column=3, columnspan=1, padx=pad_x, pady=pad_y)
        self.radar_canvas.grid(row=7, column=0, columnspan=4, padx=pad_x, pady=pad_y)
        self.radar_canvas.create_text(40, 20, text="Standby", fill="green", font=("Arial", 10, "bold"), tags="standby")
        # Initialize radar scanning state
        self.scanning = False
        self.angle = 90
        _x = CENTER_X + LINE_LENGTH * math.cos(math.radians(self.angle))
        _y = CENTER_Y - LINE_LENGTH * math.sin(math.radians(self.angle))  # Adjusted for upper side
        self.radar_canvas.create_line(CENTER_X, CENTER_Y, _x, _y, fill="green1", width=1, tags="line")
        # Create arcs for distance measuring.
        radius = 50
        delta = 50
        for i in range(8):
            self.radar_canvas.create_arc(CENTER_X - radius, CENTER_Y - radius, CENTER_X + radius, CENTER_Y + radius, start=0, extent=180, outline="green", width=1, style=tk.ARC, tags=f"{i}m")
            radius = radius + delta
            # write distance to the arcs
            self.radar_canvas.create_text(CENTER_X, 500-radius-5, text=f"{i}m", fill="green", font=("Arial", 8, "bold"))

    def print_statistics(self):
        if self.total_reads == 0:
            tk.messagebox.showinfo("Info",f"total reads = {self.total_reads}\nbad reads = {self.bad_reads}\nLiDAR health = 0.0%\ntotal interceptions: {self.total_interceptions}")
        else:
            tk.messagebox.showinfo("Info", f"total reads = {self.total_reads}\nbad reads = {self.bad_reads}\nLiDAR health = {float(self.bad_reads/self.total_reads)}%\ntotal interceptions: {self.total_interceptions}")

    def draw_new_line(self, angle, color="green1"):
        x_line = CENTER_X + LINE_LENGTH * math.cos(math.radians(angle))
        y_line = CENTER_Y - LINE_LENGTH * math.sin(math.radians(angle))  # Adjusted for upper side
        self.radar_canvas.delete("line")  # Clear previous line
        self.radar_canvas.create_line(CENTER_X, CENTER_Y, x_line, y_line, fill=color, width=1, tags="line")
        self.root.update()  # Update the display

    def check_scales_input(self):
        if self.min_angle_scale.get() > self.max_angle_scale.get():
            tk.messagebox.showwarning("Warning", "Minimum Angle cannot be larger than Maximum Angle")
            return 1
        if self.min_dist_scale.get() > self.max_dist_scale.get():
            tk.messagebox.showwarning("Warning", "Minimum Scan Distance cannot be larger than Maximum Scan "
                                                 "Distance")
            return 1    # 1 is error
        return 0  # 0 is success

    def disable_scales(self):
        self.max_dist_scale.configure(state='disabled')
        self.min_dist_scale.configure(state='disabled')
        self.max_angle_scale.configure(state='disabled')
        self.min_angle_scale.configure(state='disabled')
        self.speed_scale.configure(state='disabled')

    def enable_scales(self):
        self.max_dist_scale.configure(state='active')
        self.min_dist_scale.configure(state='active')
        self.max_angle_scale.configure(state='active')
        self.min_angle_scale.configure(state='active')
        self.speed_scale.configure(state='active')

    def draw_surroundings(self):
        for i in range(FULL_SCAN_DEGREES):
            if self.room_scan_data[i] == 0 or self.room_scan_data[i+1] == 0:
                continue  # skip.
            x0 = CENTER_X + self.room_scan_data[i] * math.cos(math.radians(i))/2
            y0 = CENTER_Y - self.room_scan_data[i] * math.sin(math.radians(i))/2
            x1 = CENTER_X + self.room_scan_data[i+1] * math.cos(math.radians(i+1))/2
            y1 = CENTER_Y - self.room_scan_data[i+1] * math.sin(math.radians(i+1))/2
            self.radar_canvas.create_line(x0, y0, x1, y1, fill="yellow", width=2, tags="surroundings")
            self.radar_canvas.update()

    def check_if_object(self, distance, angle):
        if self.max_distance >= distance >= self.min_distance:
            # This is the tweaking
            if self.last_scan[angle] - DISTANCE_SENSITIVITY > distance:
                return True
        else:
            return False

    def qualify_p1(self, distance, angle, last_scan_index, secs, millisecond):
        if self.check_if_object(distance, angle):
            self.p1 = Point(distance, angle, secs, millisecond)
            self.got_p1 = True

    def qualify_p2(self, distance, angle, last_scan_index, secs, millisecond):
        if self.check_if_object(distance, angle):
            self.p2 = Point(distance, angle, secs, millisecond)
            self.got_p2 = True

    def draw_target(self, distance):
        x_target = CENTER_X + distance * math.cos(math.radians(self.angle)) / 2
        y_target = CENTER_Y - distance * math.sin(math.radians(self.angle)) / 2
        # Animate a fading effect of the blip
        for i in range(4):
            self.radar_canvas.create_oval(x_target - 4, y_target - 4, x_target + 4, y_target + 4, width=2,
                                          fill=f"red{4 - i}", tags=f"blip_{self.blip_id}_{i + 1}")
            self.root.after(5000 - 1000 * (i + 1), self.radar_canvas.delete, f"blip_{self.blip_id}_{i + 1}")
            self.blip_id += 1

    def disable_buttons(self):
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.DISABLED)
        self.reset_button.configure(state=tk.DISABLED)

    def enable_buttons(self):
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.NORMAL)
        self.reset_button.configure(state=tk.NORMAL)

    def reset_scan(self):
        if self.scanning:
            tk.messagebox.showwarning("Warning", "Can't reset while system is running")
        else:
            self.stop_scan()
            self.first_scan = True
            for i in range(FULL_SCAN_DEGREES+1):
                self.room_scan_data[i] = 0
            self.radar_canvas.delete("surroundings")

    def start_scan(self):
        if self.check_scales_input() == 1:
            return
        if not self.scanning:
            self.disable_scales()
            self.max_angle = int(self.max_angle_scale.get())
            self.min_angle = int(self.min_angle_scale.get())
            self.max_distance = int(self.max_dist_scale.get())
            self.min_distance = int(self.min_dist_scale.get())
            self.speed = int(self.speed_scale.get())
            self.scanning = True
            self.radar_canvas.delete("standby")
            self.radar_canvas.create_text(40, 20, text="Scanning", fill="green", font=("Arial", 10, "bold"), tags="scanning")
            self.radar_canvas.update()
            if self.first_scan:
                self.disable_buttons()
                print("Initial room scan started.")
                self.radar_canvas.create_text(400, 200, text="Initial Room Scan", fill="wheat", font=("Arial", 50, "bold"), tags="initial_scanning")
                self.radar_canvas.update()
                for i in range(self.min_angle, self.max_angle+1, 1):
                    # Always read_data after requesting it
                    send_data_to_esp32(cmd=READ_DISTANCE, angle=i)
                    self.draw_new_line(angle=self.angle)
                    # Don't care about seconds and milliseconds here
                    tmp_dist, tmp_angle, tmp_sec, tmp_ms = read_esp32_serial()
                    if tmp_dist == ERROR_DISTANCE:
                        tk.messagebox.showwarning("Warning", "ERROR: LiDAR unable to read due to poor object reflectivity")
                        self.radar_canvas.delete("initial_scanning")
                        self.radar_canvas.delete("standby")
                        self.enable_scales()
                        self.scanning = False
                        self.radar_canvas.create_text(40, 20, text="Standby", fill="green", font=("Arial", 10, "bold"), tags="standby")
                        self.radar_canvas.update()
                        return      # return to user
                    self.angle = tmp_angle
                    self.room_scan_data[self.angle] = tmp_dist
                    self.last_scan[self.angle] = tmp_dist
                    print('at angle:', self.angle, 'distance:', self.room_scan_data[i])
                self.first_scan = False
                self.radar_canvas.delete("initial_scanning")
                self.draw_surroundings()
                self.radar_canvas.update()
                self.enable_buttons()
                print("Initial room scan done.")
            # Start radar scanning logic here
            print("Radar scanning started.")
            self.update_radar_display()

    def stop_scan(self):
        if self.scanning:
            # Stop radar scanning logic here
            print("Radar scanning stopped.")
            self.enable_scales()
            self.scanning = False
            self.radar_canvas.delete("scanning")
            self.stop_scan_pressed = True
            self.radar_canvas.create_text(40, 20, text="Standby", fill="green", font=("Arial", 10, "bold"), tags="standby")
            self.radar_canvas.update()


    def update_radar_display(self):
        if self.scanning:
            # Sweep Left Movement
            for k in range(self.min_angle, self.max_angle+1, 1):
                time.sleep((3-self.speed)*0.1)
                if self.stop_scan_pressed:
                    break
                # always request data before reading it! This is how it works.
                send_data_to_esp32(cmd=READ_DISTANCE, angle=k)
                distance, self.angle, seconds, milliseconds = read_esp32_serial()
                bad_read = False
                if distance == ERROR_DISTANCE:
                    self.bad_reads += 1
                    distance = self.max_distance + 1
                    bad_read = True
                    print('WARNING: LiDAR unable to read due to poor object reflectivity')
                    print('Assuming Maximum distance read')
                    time.sleep(1)
                self.total_reads += 1
                print(f"Found object in dist:{distance}, and angle:{self.angle}")
                if self.max_distance >= distance >= self.min_distance:
                    self.draw_target(distance)
                self.draw_new_line(angle=self.angle)
                if self.got_p1 == False:
                    self.qualify_p1(distance=distance, last_scan_index=k, angle=self.angle, secs=seconds, millisecond=milliseconds)
                if not bad_read:        # bad_read == false, take the new read distance. Else: keeps the old reading.
                    self.last_scan[self.angle] = distance

            # Sweep Right Movement
            for k in range(self.max_angle, self.min_angle - 1, -1):
                time.sleep((4 - self.speed) * 0.1)
                if self.stop_scan_pressed:
                    self.stop_scan_pressed = False
                    break
                # always request data before reading it!
                send_data_to_esp32(cmd=READ_DISTANCE, angle=k)
                distance, self.angle, seconds, milliseconds = read_esp32_serial()
                bad_read = False
                if distance == ERROR_DISTANCE:
                    self.bad_reads += 1
                    distance = self.max_distance + 1
                    bad_read = True
                    print('WARNING: LiDAR unable to read due to poor object reflectivity')
                    print('Assuming Maximum distance read')
                    time.sleep(1)
                self.total_reads += 1
                print(f"Found object in dist:{distance}, and angle:{self.angle}")
                self.draw_target(distance)
                self.draw_new_line(angle=self.angle)
                if self.got_p2 == False:
                    self.qualify_p2(distance=distance, last_scan_index=k, angle=self.angle, secs=seconds, millisecond=milliseconds)
                if not bad_read:        # bad_read == false, take the new read distance. Else: keep the old reading.
                    self.last_scan[self.angle] = distance
            # Check if got 2 points, of an object in the frame
            if self.got_p1 and self.got_p2:
                print('GOT TWO POINTS!')
                print(f'P1.x = {self.p1.x}, P1.y = {self.p1.y}, P1.r = {self.p1.r}, P1.theta = {self.p1.theta}'
                      f'P1.time = {self.p1.t_sec*1000+self.p1.t_ms} ms')
                print(f'P2.x = {self.p2.x}, P2.y = {self.p2.y}, P2.r = {self.p2.r}, P2.theta = {self.p2.theta}'
                      f'P2.time = {self.p2.t_sec * 1000 + self.p2.t_ms} ms')
                time.sleep(1)
                vel_x, vel_y = calculate_velocity(self.p1, self.p2)
                print(f'vel_x = {vel_x}, vel_y = {vel_y}')
                intercept_angle = calculate_interception_angle(vx=vel_x, vy=vel_y, last_point=self.p2, future=FUTURE)
                print(f'interception angle {intercept_angle}')
                self.intercept_target(intercept_angle)
                print('intercepting target!')
            # Didn't find 2 point in the sweep right, sweep left.
            # OR, finished interception!
            self.got_p1 = False
            self.got_p2 = False
            self.root.after(1, self.update_radar_display)  # Recursive call for animation

    def intercept_target(self, angle):
        self.draw_new_line(color="blue", angle=angle)
        self.radar_canvas.delete("scanning")
        self.radar_canvas.create_text(400, 200, text="INTERCEPTING", fill="blue", font=("Arial", 50, "bold"), tags="intercepting")
        self.radar_canvas.update()
        threading.Thread(target=send_data_to_esp32, args=(FACE_TARGET, angle)).start()
        # PC Will sleep for 1.5 second while the ESP will "sleep" with flashlight on for 1 second!
        # This is because the serial takes time to send via serial. The 1 seconds sleep for the ESP is our choice,
        # the 1.5 is the estimation, where 0.5 seconds is the amount of time travel for the
        time.sleep(1.5)
        self.radar_canvas.delete("intercepting")
        self.radar_canvas.create_text(40, 20, text="Scanning", fill="green", font=("Arial", 10, "bold"), tags="scanning")
        self.radar_canvas.update()


if __name__ == "__main__":
    esp32_serial = serial.Serial(COM_PORT, BAUD_RATE)  # ESP32's UART port
    esp32_serial.flushInput()
    esp32_serial.flushOutput()
    _root = tk.Tk()
    app = RadarControlApp(_root)
    _root.mainloop()
