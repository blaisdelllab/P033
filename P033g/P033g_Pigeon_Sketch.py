#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example: Refactored PigeonSketch
Implements:
 - Single click handler that checks a "phase state" (sample vs. sketch).
 - Dot class now distinguishes a visual stimulus (visible dot) from its receptive field.
 - A dictionary of PHASE_CONFIG to unify repeated logic.
 - A single setup_phase() function that reads PHASE_CONFIG and 
   draws the sample side or sets up matching/distractor if needed.
 - FR4 logic, time-outs, repeated attempts, etc.
 - During ITI, reinforcement, and time-out (in test mode) a text is shown.
 - For incorrect attempts, the same trial arrangement is repeated but with the right side cleared.
 - For phases 1.d and later that require line drawing, the right side now replicates 
   the sample side dots (plus distractors in phases 2 and 3) and supports dashed and final lines.
"""

import sys
import csv
from random import sample, choice, randint
from time import time, sleep
from datetime import datetime, date
from tkinter import Tk, Canvas, BOTH, TclError, Label, Button, StringVar, OptionMenu, IntVar, Radiobutton

try:
    from PIL import Image, ImageTk
except ImportError:
    pass

import os as os_mod
from os import path, mkdir, getcwd, popen  # popen imported from os

############################
#  OPERANT BOX DETECTION   #
############################
if os_mod.path.expanduser('~').split("/")[2] == "blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")

# Additional hardware-specific setup
try:
    if operant_box_version:
        import pigpio  # import pi, OUTPUT

        # Setup GPIO numbers (NOT PINS; use GPIO num)
        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        house_light_GPIO_num = 21

        # Setup use of pi()
        rpi_board = pigpio.pi()

        # Set each pin to output 
        rpi_board.set_mode(servo_GPIO_num, pigpio.OUTPUT)          # Servo motor...
        rpi_board.set_mode(hopper_light_GPIO_num, pigpio.OUTPUT)       # Hopper light LED...
        rpi_board.set_mode(house_light_GPIO_num, pigpio.OUTPUT)        # House light LED...

        # Setup the servo motor (Default frequency is 50 MHz)
        rpi_board.set_PWM_frequency(servo_GPIO_num, 50)

        # Grab UP/DOWN values from CSV file
        hopper_vals_csv_path = str(path.expanduser('~') + "/Desktop/Box_Info/Hopper_vals.csv")
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        hopper_up_val = up_down_table[1][0]
        hopper_down_val = up_down_table[1][1]

        # Run the shell script that maps the touchscreen to operant box monitor
        popen("sh /home/blaisdelllab/Desktop/Hardware_Code/map_touchscreen.sh")
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")

#############################
# PHASE CONFIG
#############################
"""
We store each phase’s logic in a dictionary.
A new phase "1.c2: Complex Discrimination" is added.
In that phase, after the sample dot is selected, the canvas shows the target dot (same grid as sample) 
plus either 2 or 3 distractor dots. Only the target dot is correct.
"""
PHASE_CONFIG = {
    "1a": {
        "phase_name": "1.a: Single Dot",
        "sample_selection": "single",
        "lines": False,
        "matching_dot": False,
        "distractor": False
    },
    "1b": {
        "phase_name": "1.b: Sample->Sketch",
        "sample_selection": "single",
        "matching_dot": True,
        "distractor": False,
        "lines": False
    },
    "1c": {
        "phase_name": "1.c: Discrimination",
        "sample_selection": "single",
        "matching_dot": True,
        "distractor": True,
        "lines": False
    },
    "1c2": {
        "phase_name": "1.c2: Complex Discrimination",
        "sample_selection": "single",
        "matching_dot": True,
        "distractor": True,
        "num_distractors": True,  # Use multiple distractors (2 or 3)
        "lines": False
    },
    "1d": {
        "phase_name": "1.d: 2-dot line",
        "sample_selection": "two_random",
        "lines": True,
        "matching_dot": False,
        "distractor": False
    },
    "2a_standard": {
        "phase_name": "2.a: 3-dot standard triangle",
        "sample_selection": "standard_triangle_3",
        "lines": True,
        "matching_dot": False,
        "distractor": False,
        "sketch_total": 3
    },
    "2b_random": {
        "phase_name": "2.b: 3-dot random (skip collinear)",
        "sample_selection": "three_random_noncollinear",
        "lines": True,
        "matching_dot": False,
        "distractor": False,
        "sketch_total": 3
    },
    "3a_standard": {
        "phase_name": "3.a: 4-dot standard rectangle",
        "sample_selection": "rectangle_4",
        "lines": True,
        "matching_dot": False,
        "distractor": False,
        "sketch_total": 4
    },
    "3b_random": {
        "phase_name": "3.b: 4-dot random",
        "sample_selection": "four_random_noncollinear",
        "lines": True,
        "matching_dot": False,
        "distractor": False,
        "sketch_total": 4
    }
}

# Global mapping of internal phase keys to log phase labels
PHASE_LABELS = {
    "1a": "1.a",
    "1b": "1.b",
    "1c": "1.c",
    "1c2": "1.d",
    "1d": "2.a",
    "2a_standard": "2.b",
    "2b_random": "2.c",
    "3a_standard": "2.d",
    "3b_random": "2.e"
}

#############################
# DOT CLASS
#############################
class Dot:
    def __init__(self, row, col, x, y, receptive_size, visible_size, color="#3b3b3b"):
        self.row = row
        self.col = col
        self.x0 = x
        self.y0 = y
        self.x1 = x + receptive_size
        self.y1 = y + receptive_size
        offset = (receptive_size - visible_size) / 2
        self.vx0 = x + offset
        self.vy0 = y + offset
        self.vx1 = self.vx0 + visible_size
        self.vy1 = self.vy0 + visible_size
        self.color = color
        self.visible = False
        self.selected = False
        self.peck_count = 0

    def is_clicked(self, x, y):
        if not self.visible:
            return False
        return (self.x0 <= x <= self.x1) and (self.y0 <= y <= self.y1)

    def center(self):
        return ((self.vx0 + self.vx1) / 2, (self.vy0 + self.vy1) / 2)

    def draw(self, canvas, highlight=False):
        fill_color = self.color
        canvas.create_oval(self.vx0, self.vy0, self.vx1, self.vy1,
                           fill=fill_color, outline=fill_color, tags="dots")
        if highlight or self.selected:
            border_id = canvas.create_oval(self.vx0, self.vy0, self.vx1, self.vy1,
                                           outline="black", width=3, tags="dots")
            canvas.tag_raise(border_id)

##############################################
# EXPERIMENTER CONTROL PANEL
##############################################
class ExperimenterControlPanel:
    def __init__(self):
        self.control_window = Tk()
        self.control_window.title("PigeonSketch Control Panel")

        # Updated subject list: Itzamna and Sting replaced with Hendrix and Joplin.
        self.pigeon_name_list = ["Hendrix", "Joplin", "Waluigi", "Evaristo", "Mario", "Hawthorne"]
        self.pigeon_name_list.sort()
        self.pigeon_name_list.insert(0, "TEST")

        Label(self.control_window, text="Subject Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        OptionMenu(self.control_window, self.subject_ID_variable,
                   *self.pigeon_name_list).pack()

        self.experimental_phase_titles = [
            "GridDisplay",
            "1.a: Single Dot",
            "1.b: Sample->Sketch",
            "1.c: Discrimination",
            "1.c2: Complex Discrimination",
            "1.d: 2-dot line",
            "2a: 3-dot standard triangle",
            "2b: 3-dot random",
            "3a: 4-dot standard rectangle",
            "3b: 4-dot random"
        ]
        Label(self.control_window, text="Experimental Phase:").pack()
        self.exp_phase_variable = StringVar(self.control_window)
        self.exp_phase_variable.set("Select")
        OptionMenu(self.control_window, self.exp_phase_variable,
                   *self.experimental_phase_titles).pack()

        Label(self.control_window, text="Record data?").pack()
        self.record_data_variable = IntVar()
        Radiobutton(self.control_window, variable=self.record_data_variable,
                    text="Yes", value=1).pack()
        Radiobutton(self.control_window, variable=self.record_data_variable,
                    text="No", value=0).pack()
        self.record_data_variable.set(1)

        Button(self.control_window, text='Start program', bg="green2",
               command=self.build_chamber_screen).pack()

        self.control_window.mainloop()

    def build_chamber_screen(self):
        if self.subject_ID_variable.get() in self.pigeon_name_list and self.exp_phase_variable.get() != "Select":
            MainScreen(subject_ID=self.subject_ID_variable.get(),
                       exp_phase=self.exp_phase_variable.get(),
                       record_data=bool(self.record_data_variable.get()))
        else:
            print("ERROR: Please select subject name & phase properly.")

##############################################
# MAIN SCREEN
##############################################
class MainScreen:
    def __init__(self, subject_ID, exp_phase, record_data):
        self.subject_ID = subject_ID
        self.exp_phase_title = exp_phase
        self.record_data = record_data
        self.experiment_name = "PigeonSketch"

        self.phase_key = self.parse_phase_key(exp_phase)
        self.phase_config = PHASE_CONFIG.get(self.phase_key, None)

        if operant_box_version:
            self.box_number = "BOX_1"
        else:
            self.box_number = "NA"

        self.max_trials = 90
        self.trial_counter = 0
        self.attempt_counter = 0
        self.FR_requirement = 4

        if operant_box_version:
            self.ITI_duration = 10000
            self.reinforcement_duration = 6000
        else:
            self.ITI_duration = 1000
            self.reinforcement_duration = 1000

        # Set start_time later after 30-sec delay if needed.
        self.start_time = None  
        self.previous_peck_time = time()

        self.root = Tk()
        self.root.title(f"{self.experiment_name} - {exp_phase}")
        self.screen_width = 1024
        self.screen_height = 768
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        self.root.bind("<Escape>", self.exit_program)

        # -------------------------------------------
        # Hardware display integration:
        # If running in operant box mode, then we
        # key-bind the "c" key to toggle the cursor,
        # set fullscreen with specified geometry,
        # and use a master canvas.
        self.mainscreen_width = self.screen_width
        self.mainscreen_height = self.screen_height
        if operant_box_version:
            self.cursor_visible = True
            self.change_cursor_state()  # turn off cursor immediately
            self.root.bind("<c>", lambda event: self.change_cursor_state())
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
            self.root.attributes('-fullscreen', True)
            self.mastercanvas = Canvas(self.root, bg="black")
            self.mastercanvas.pack(fill=BOTH, expand=True)
            self.canvas = self.mastercanvas
        else:
            self.mastercanvas = Canvas(self.root, bg="black",
                                       height=self.mainscreen_height,
                                       width=self.mainscreen_width)
            self.mastercanvas.pack()
            self.canvas = self.mastercanvas
        # -------------------------------------------

        # Bind the space bar for manual reinforcement.
        self.root.bind("<space>", self.manual_reinforcement_handler)

        # Updated header: added "Line Distance" after "Phase"
        header = [
            "TrialNum", "Attempt", "SessionTime", "Xcord", "Ycord", "PrevX", "PrevY",
            "EventType", "CurrentDotCoord", "PrevDotCoord", "IRI", "StartTime",
            "Phase", "Line Distance", "Correct Dot", "Distractor Dot", "Region",
            "Experiment", "BoxNumber", "Subject", "Date"
        ]
        self.session_data = [header]

        self.house_light_on = False
        self.dot_grid_left = []
        self.dot_grid_right = []
        self.last_peck_x = None
        self.last_peck_y = None
        self.last_dot_coord = None

        self.right_first_dot = None
        self.dashed_line_ids = []

        self.generate_dots()

        self.current_phase_side = "sample"
        self.current_trial_config = {}

        # Data storage directories
        if path.expanduser('~').split("/")[2] == "blaisdelllab":
            print("*** Running operant box version ***")
            self.data_folder_directory = str(path.expanduser('~')) + "/Desktop/Data/P033_data/P033g_PigeonSketch_Data"
        else:
            print("*** Running test version (no hardware) ***")
            self.data_folder_directory = getcwd() + "/P033g_PigeonSketch_Data"

        try:
            if not path.isdir(self.data_folder_directory):
                mkdir(self.data_folder_directory)
                print("NEW DATA FOLDER CREATED")
        except FileExistsError:
            print("Data folder exists.")
        try:
            subject_folder = path.join(self.data_folder_directory, self.subject_ID)
            if not path.isdir(subject_folder):
                mkdir(subject_folder)
                print(f"NEW DATA FOLDER FOR {self.subject_ID.upper()} CREATED")
        except FileExistsError:
            pass

        # Delay start by 30 seconds if operant box version and subject is not "TEST"
        if operant_box_version and self.subject_ID != "TEST":
            print("Delay 30 seconds before starting experiment...")
            self.canvas.delete("all")
            self.root.after(30000, self.start_experiment)
        else:
            self.start_experiment()

        self.root.mainloop()

    def start_experiment(self):
        self.start_time = datetime.now()
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True)
        if self.phase_key == "GridDisplay":
            self.show_grid_display()
        else:
            self.next_trial(new_trial=True)

    def change_cursor_state(self):
        if self.cursor_visible:
            self.root.config(cursor="none")
            print("### Cursor turned off ###")
            self.cursor_visible = False
        else:
            self.root.config(cursor="")
            print("### Cursor turned on ###")
            self.cursor_visible = True

    # --- NEW: Manual reinforcement handler triggered by space bar ---
    def manual_reinforcement_handler(self, event):
        # Write a manual reinforcement event into the data log.
        self.write_data("NA", "NA", "manual_reinforcement", "NA", 0)
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num, True)     # Turn on hopper light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_up_val)  # Raise hopper
            # After the reinforcement duration, lower the hopper and turn off the hopper light.
            self.root.after(self.reinforcement_duration, self.end_manual_reinforcement)

    def end_manual_reinforcement(self):
        if operant_box_version:
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_down_val)  # Lower hopper
            rpi_board.write(hopper_light_GPIO_num, False)    # Turn off hopper light

    ########## PHASE PARSER
    def parse_phase_key(self, title):
        if "GridDisplay" in title:
            return "GridDisplay"
        elif "1.a" in title:
            return "1a"
        elif "1.b" in title:
            return "1b"
        elif "1.c2" in title:
            return "1c2"
        elif "1.c" in title:
            return "1c"
        elif "1.d" in title:
            return "1d"
        elif "2a" in title:
            return "2a_standard"
        elif "2b" in title:
            return "2b_random"
        elif "3a" in title:
            return "3a_standard"
        elif "3b" in title:
            return "3b_random"
        else:
            return None

    ########## DOT GENERATION
    def generate_dots(self):
        # New sizes: visible dot size increased from 40 to 45,
        # receptive field increased from 60 to 68 (approximately 125% scaling of original values)
        filled_circle_size = 50
        non_filled_circle_size = 78
        circle_spacing = 38
        left_x_start = circle_spacing
        # Introduce vertical offset variable:
        grid_vertical_offset = 35
        left_y_start = circle_spacing + grid_vertical_offset
        left_width = self.screen_width // 2

        right_x_start = self.screen_width // 2 + circle_spacing
        right_y_start = circle_spacing + grid_vertical_offset
        right_width = self.screen_width - (self.screen_width // 2)

        # Introduce a grid horizontal offset variable (adjust as needed).
        grid_offset = 3

        num_cols_left = (left_width - circle_spacing) // (non_filled_circle_size + circle_spacing)
        num_rows_left = (self.screen_height - circle_spacing) // (non_filled_circle_size + circle_spacing)
        num_cols_right = (right_width - circle_spacing) // (non_filled_circle_size + circle_spacing)
        num_rows_right = (self.screen_height - circle_spacing) // (non_filled_circle_size + circle_spacing)

        # Determine additional row skip for subjects Waluigi, Hawthorne, or Mario.
        if self.subject_ID in {"Waluigi", "Mario", "Hawthorne"}:
            extra_row_skip = 2  # Skip two rows (row indices 0 and 1)
        else:
            extra_row_skip = 1  # Skip one row (row index 0)

        # --- Remove top row(s): start at row index extra_row_skip instead of 0 ---
        for row in range(extra_row_skip, num_rows_left):
            for col in range(num_cols_left):
                x = left_x_start + grid_offset + col * (non_filled_circle_size + circle_spacing)
                y = left_y_start + row * (non_filled_circle_size + circle_spacing)
                dot = Dot(row=row, col=col, x=x, y=y,
                          receptive_size=non_filled_circle_size,
                          visible_size=filled_circle_size,
                          color="#3b3b3b")
                self.dot_grid_left.append(dot)

        for row in range(extra_row_skip, num_rows_right):
            for col in range(num_cols_right):
                x = right_x_start + grid_offset + col * (non_filled_circle_size + circle_spacing)
                y = right_y_start + row * (non_filled_circle_size + circle_spacing)
                dot = Dot(row=row, col=col, x=x, y=y,
                          receptive_size=non_filled_circle_size,
                          visible_size=filled_circle_size,
                          color="#3b3b3b")
                self.dot_grid_right.append(dot)
        # -----------------------------------------------------------

    def draw_grid_dot(self, dot):
        # Draw the receptive field with a distinct color (e.g., light gray)
        self.canvas.create_oval(dot.x0, dot.y0, dot.x1, dot.y1,
                                fill="#cccccc", outline="#cccccc", tags="dots_rf")
        # Then draw the visible dot using the standard dot.draw() method.
        dot.draw(self.canvas)

    def show_grid_display(self):
        self.canvas.delete("all")
        self.draw_background(False)
        # Make all dots in both grids visible.
        for d in self.dot_grid_left:
            d.visible = True
        for d in self.dot_grid_right:
            d.visible = True
        # Instead of using draw_all_dots(), loop through all dots and use draw_grid_dot()
        # so that we draw both the receptive field and the visible dot.
        for d in self.dot_grid_left + self.dot_grid_right:
            self.draw_grid_dot(d)

    ########## DRAW BACKGROUND
    def draw_background(self, active_right=False):
        self.canvas.delete("bg")
        left_bg = "#279dd2"
        right_bg = "#ffd09e" if active_right else "#279dd2"
        self.canvas.create_rectangle(0, 0, self.screen_width//2, self.screen_height,
                                     fill=left_bg, outline=left_bg, tags="bg")
        self.canvas.create_rectangle(self.screen_width//2, 0, self.screen_width, self.screen_height,
                                     fill=right_bg, outline=right_bg, tags="bg")
        self.canvas.create_line(self.screen_width//2, 0, self.screen_width//2, self.screen_height,
                                fill="#ff69c3", width=2, tags="bg")

    ########## DRAW ALL DOTS AND LINES
    def draw_all_dots(self):
        self.canvas.delete("dots")
        for d in self.dot_grid_left:
            if d.visible:
                d.draw(self.canvas)
        for d in self.dot_grid_right:
            if d.visible:
                d.draw(self.canvas)
        if self.current_trial_config.get("sample_line"):
            for (r1, c1), (r2, c2) in self.current_trial_config["sample_line"]:
                dot1 = self.find_left_dot(r1, c1)
                dot2 = self.find_left_dot(r2, c2)
                if dot1 and dot2:
                    cx1, cy1 = dot1.center()
                    cx2, cy2 = dot2.center()
                    self.canvas.create_line(cx1, cy1, cx2, cy2, fill="black", width=3, tags="dots")

    ########## FIND DOT
    def find_left_dot(self, row, col):
        for d in self.dot_grid_left:
            if d.row == row and d.col == col:
                return d
        return None

    def find_right_dot(self, row, col):
        for d in self.dot_grid_right:
            if d.row == row and d.col == col:
                return d
        return None

    ########## TRIAL FLOW
    def next_trial(self, new_trial=True):
        if new_trial:
            if self.trial_counter >= self.max_trials:
                print("Max trials => end session.")
                self.exit_program()
                return
            self.trial_counter += 1
            self.attempt_counter = 1
            self.setup_phase(retry=False)
        else:
            self.attempt_counter += 1
            self.setup_phase(retry=True)
        print(f"Starting Trial {self.trial_counter}, Attempt {self.attempt_counter}")

    def setup_phase(self, retry=False):
        self.canvas.delete("all")
        if not self.phase_config or self.phase_key == "GridDisplay":
            return
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True)
        self.current_phase_side = "sample"
        self.draw_background(False)
        if not retry:
            for d in self.dot_grid_left:
                d.visible = False
                d.selected = False
                d.peck_count = 0
            for d in self.dot_grid_right:
                d.visible = False
                d.selected = False
                d.peck_count = 0
            self.current_trial_config = {}
            self.right_first_dot = None
            self.dashed_line_ids = []
            mode = self.phase_config.get("sample_selection", "single")
            sample_line_pairs = []
            chosen_left = []
            if mode == "single":
                ld = choice(self.dot_grid_left)
                ld.visible = True
                chosen_left.append(ld)
            elif mode == "two_random":
                lds = sample(self.dot_grid_left, 2)
                for d in lds:
                    d.visible = True
                chosen_left = lds
                if self.phase_config.get("lines", False):
                    p1 = (lds[0].row, lds[0].col)
                    p2 = (lds[1].row, lds[1].col)
                    sample_line_pairs.append((p1, p2))
            elif mode == "standard_triangle_3":
                coords = [(0, 0), (1, 2), (2, 1)]
                found = []
                for co in coords:
                    dotf = self.find_left_dot(co[0], co[1])
                    if dotf:
                        found.append(dotf)
                left_two = sample(found, 2)
                for f in found:
                    f.visible = True
                chosen_left = found
                p1 = (left_two[0].row, left_two[0].col)
                p2 = (left_two[1].row, left_two[1].col)
                sample_line_pairs.append((p1, p2))
            elif mode == "three_random_noncollinear":
                while True:
                    picked = sample(self.dot_grid_left, 3)
                    if not self.three_dots_collinear(picked):
                        break
                for d in picked:
                    d.visible = True
                chosen_left = picked
                left_two = sample(chosen_left, 2)
                p1 = (left_two[0].row, left_two[0].col)
                p2 = (left_two[1].row, left_two[1].col)
                sample_line_pairs.append((p1, p2))
            elif mode == "rectangle_4":
                found = []
                tries = 0
                while tries < 100:
                    tries += 1
                    cands = sample(self.dot_grid_left, 2)
                    r1, c1 = cands[0].row, cands[0].col
                    r2, c2 = cands[1].row, cands[1].col
                    if r1 == r2 or c1 == c2:
                        continue
                    corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
                    dt = []
                    for co in corners:
                        dd = self.find_left_dot(co[0], co[1])
                        if dd:
                            dt.append(dd)
                    if len(dt) == 4:
                        found = dt
                        break
                if not found:
                    found = sample(self.dot_grid_left, 4)
                for d in found:
                    d.visible = True
                chosen_left = found
                two = sample(found, 2)
                p1 = (two[0].row, two[0].col)
                p2 = (two[1].row, two[1].col)
                sample_line_pairs.append((p1, p2))
            elif mode == "four_random_noncollinear":
                while True:
                    found = sample(self.dot_grid_left, 4)
                    if not self.four_has_3_collinear(found):
                        break
                for d in found:
                    d.visible = True
                chosen_left = found
                two = sample(found, 2)
                p1 = (two[0].row, two[0].col)
                p2 = (two[1].row, two[1].col)
                sample_line_pairs.append((p1, p2))
            else:
                ld = choice(self.dot_grid_left)
                ld.visible = True
                chosen_left.append(ld)
            if self.phase_config.get("sketch_total", None) and sample_line_pairs:
                target_coords = sample_line_pairs[0]
                filtered = []
                for d in chosen_left:
                    if (d.row, d.col) in target_coords:
                        filtered.append(d)
                    else:
                        d.visible = False
                chosen_left = filtered
            self.current_trial_config["sample_dots"] = chosen_left
            if sample_line_pairs:
                self.current_trial_config["sample_line"] = sample_line_pairs
        else:
            for d in self.current_trial_config.get("sample_dots", []):
                d.peck_count = 0
                d.selected = False
                d.visible = True
            for d in self.dot_grid_right:
                d.peck_count = 0
                d.selected = False
                d.visible = False
            if "distractor_dot" in self.current_trial_config:
                d_dot = self.current_trial_config["distractor_dot"]
                d_dot.peck_count = 0
                d_dot.selected = False
                d_dot.visible = False
            if "distractor_dots" in self.current_trial_config:
                for d_dot in self.current_trial_config["distractor_dots"]:
                    d_dot.peck_count = 0
                    d_dot.selected = False
                    d_dot.visible = False
            self.right_first_dot = None
            for line_id in self.dashed_line_ids:
                self.canvas.delete(line_id)
            self.dashed_line_ids = []
        self.draw_all_dots()
        self.canvas.bind("<Button-1>", self.on_click_sample_side)

    ########## CLICK HANDLERS
    def on_click_sample_side(self, event):
        x, y = event.x, event.y
        region = "Sample" if x < self.screen_width/2 else "Canvas"
        IRI = round(time() - self.previous_peck_time, 4)
        self.previous_peck_time = time()
        clicked_dot = None
        for d in self.dot_grid_left:
            if d.visible and d.is_clicked(x, y):
                clicked_dot = d
                break
        if not clicked_dot:
            self.write_data(x, y, "background_peck", region, IRI)
            return
        if clicked_dot.selected:
            self.write_data(x, y, "inactive_dot_peck", region, IRI)
            return
        prevC = self.last_dot_coord if self.last_dot_coord else "NA"
        dotC = f"({clicked_dot.row},{clicked_dot.col})"
        clicked_dot.peck_count += 1
        self.write_data(x, y, "sample_peck", region, IRI, curr_dot_coord=dotC, prev_dot_coord=prevC)
        self.last_dot_coord = dotC
        if clicked_dot.peck_count >= self.FR_requirement:
            clicked_dot.selected = True
            clicked_dot.draw(self.canvas, highlight=True)
            all_fr = True
            for dd in self.current_trial_config["sample_dots"]:
                if dd.peck_count < self.FR_requirement:
                    all_fr = False
            if all_fr:
                self.canvas.unbind("<Button-1>")
                if (self.phase_config.get("matching_dot", False) or
                    self.phase_config.get("distractor", False) or
                    self.phase_config.get("sketch_total", None) or
                    self.phase_key in ["1d", "1c2"]):
                    self.activate_sketch_side()
                else:
                    self.root.after(1000, self.provide_reinforcement)

    def activate_sketch_side(self):
        self.current_phase_side = "sketch"
        self.draw_background(active_right=True)
        self.draw_all_dots()
        if self.phase_config.get("matching_dot", False):
            sample_dots = self.current_trial_config["sample_dots"]
            for sd in sample_dots:
                rd = self.find_right_dot(sd.row, sd.col)
                if rd:
                    rd.visible = True
                    rd.color = sd.color
            if self.phase_config.get("distractor", False):
                if self.phase_key == "1c2":
                    if "distractor_dots" not in self.current_trial_config:
                        available = [d for d in self.dot_grid_right 
                                     if (d.row, d.col) not in [(sd.row, sd.col) for sd in sample_dots]
                                     and not d.visible]
                        num = choice([2, 3])
                        if len(available) >= num:
                            distractors = sample(available, num)
                        else:
                            distractors = available
                        self.current_trial_config["distractor_dots"] = distractors
                    else:
                        distractors = self.current_trial_config["distractor_dots"]
                    for d_dot in distractors:
                        d_dot.visible = True
                        d_dot.color = "#3b3b3b"
                else:
                    if "distractor_dot" in self.current_trial_config:
                        dist = self.current_trial_config["distractor_dot"]
                    else:
                        rdot_choices = [d for d in self.dot_grid_right 
                                        if (d.row, d.col) not in [(sd.row, sd.col) for sd in sample_dots]
                                        and not d.visible]
                        dist = choice(rdot_choices) if rdot_choices else None
                        if dist is not None:
                            self.current_trial_config["distractor_dot"] = dist
                    if dist is not None:
                        dist.visible = True
                        dist.color = "#3b3b3b"
        elif self.phase_config.get("sketch_total", None) or self.phase_key == "1d":
            sample_dots = self.current_trial_config["sample_dots"]
            for sd in sample_dots:
                rd = self.find_right_dot(sd.row, sd.col)
                if rd:
                    rd.visible = True
                    rd.color = sd.color
            if self.phase_key in ["2a_standard"]:
                rdot_choices = [d for d in self.dot_grid_right if not d.visible]
                if rdot_choices:
                    dist = choice(rdot_choices)
                    dist.visible = True
                    dist.color = "#3b3b3b"
                    self.current_trial_config["distractor_dot"] = dist
            elif self.phase_key in ["2b_random", "3a_standard", "3b_random"]:
                distractor_candidates = [d for d in self.dot_grid_right if not d.visible]
                if distractor_candidates:
                    dist = choice(distractor_candidates)
                    dist.visible = True
                    dist.color = "#3b3b3b"
                    self.current_trial_config["distractor_dot"] = dist
        self.draw_all_dots()
        self.right_first_dot = None
        for line_id in self.dashed_line_ids:
            self.canvas.delete(line_id)
        self.dashed_line_ids = []
        self.canvas.bind("<Button-1>", self.on_click_sketch_side)

    def on_click_sketch_side(self, event):
        x, y = event.x, event.y
        region = "Sample" if x < self.screen_width/2 else "Canvas"
        IRI = round(time() - self.previous_peck_time, 4)
        self.previous_peck_time = time()
        if x < self.screen_width // 2:
            self.write_data(x, y, "sample_inactive_peck", region, IRI)
            return
        clicked_dot = None
        for d in self.dot_grid_right:
            if d.visible and d.is_clicked(x, y):
                clicked_dot = d
                break
        if not clicked_dot:
            self.write_data(x, y, "background_peck", region, IRI)
            return
        if clicked_dot.selected:
            self.write_data(x, y, "inactive_dot_peck", region, IRI)
            return
        prevC = self.last_dot_coord if self.last_dot_coord else "NA"
        dotC = f"({clicked_dot.row},{clicked_dot.col})"
        clicked_dot.peck_count += 1
        self.write_data(x, y, "dot_peck", region, IRI, curr_dot_coord=dotC, prev_dot_coord=prevC)
        self.last_dot_coord = dotC
        if clicked_dot.peck_count >= self.FR_requirement:
            clicked_dot.selected = True
            clicked_dot.draw(self.canvas, highlight=True)
            if self.phase_key == "1c2":
                sample_dot = self.current_trial_config["sample_dots"][0]
                target_coords = (sample_dot.row, sample_dot.col)
                if (clicked_dot.row, clicked_dot.col) == target_coords:
                    self.canvas.unbind("<Button-1>")
                    self.root.after(1000, self.provide_reinforcement)
                else:
                    self.canvas.unbind("<Button-1>")
                    self.root.after(1000, self.blackout_then_repeat)
            elif self.phase_config.get("matching_dot", False):
                if self.phase_config.get("distractor", False):
                    dist_dot = self.current_trial_config.get("distractor_dot", None)
                    if dist_dot and (clicked_dot is dist_dot):
                        self.canvas.unbind("<Button-1>")
                        self.root.after(1000, self.blackout_then_repeat)
                    else:
                        self.canvas.unbind("<Button-1>")
                        self.root.after(1000, self.provide_reinforcement)
                else:
                    self.canvas.unbind("<Button-1>")
                    self.root.after(1000, self.provide_reinforcement)
            elif self.phase_config.get("sketch_total", None) or self.phase_key == "1d":
                if not self.right_first_dot:
                    self.right_first_dot = clicked_dot
                    for d in self.dot_grid_right:
                        if d.visible and (d != self.right_first_dot) and (not d.selected):
                            cx1, cy1 = self.right_first_dot.center()
                            cx2, cy2 = d.center()
                            line_id = self.canvas.create_line(cx1, cy1, cx2, cy2,
                                                                fill="black", dash=(4, 2), width=2, tags="dots")
                            self.dashed_line_ids.append(line_id)
                else:
                    for line_id in self.dashed_line_ids:
                        self.canvas.delete(line_id)
                    self.dashed_line_ids = []
                    dot1 = self.right_first_dot
                    dot2 = clicked_dot
                    good_line = False
                    if "sample_line" in self.current_trial_config:
                        linePair = self.current_trial_config["sample_line"][0]
                        chosen_sorted = sorted([(dot1.row, dot1.col), (dot2.row, dot2.col)])
                        if chosen_sorted == sorted([linePair[0], linePair[1]]):
                            good_line = True
                    cx1, cy1 = dot1.center()
                    cx2, cy2 = dot2.center()
                    if good_line:
                        self.canvas.create_line(cx1, cy1, cx2, cy2,
                                                fill="black", width=3, tags="dots")
                    else:
                        self.canvas.create_line(cx1, cy1, cx2, cy2,
                                                fill="red", dash=(4, 2), width=3, tags="dots")
                    self.canvas.unbind("<Button-1>")
                    self.root.after(1000, self.provide_reinforcement if good_line else self.blackout_then_repeat)
            else:
                if not self.right_first_dot:
                    self.right_first_dot = clicked_dot
                else:
                    d1 = self.right_first_dot
                    d2 = clicked_dot
                    if d1 != d2:
                        self.canvas.unbind("<Button-1>")
                        self.root.after(1000, self.provide_reinforcement)
                    else:
                        self.canvas.unbind("<Button-1>")
                        self.root.after(1000, self.blackout_then_repeat)

    ########## TIMEOUT / ITI / REINFORCEMENT
    def blackout_then_repeat(self):
        self.canvas.delete("all")
        self.canvas.config(bg="black")
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, False)
        if not operant_box_version:
            self.canvas.create_text(self.screen_width/2, self.screen_height/2,
                                    text="Time Out", fill="white", font=("Helvetica", 32))
        self.write_data("NA", "NA", "time_out", "NA", 0)
        self.root.after(self.reinforcement_duration, self.end_incorrect_period)

    def end_incorrect_period(self):
        self.start_ITI(incorrect=True)

    def start_ITI(self, incorrect=False):
        self.canvas.delete("all")
        self.canvas.config(bg="black")
        if not operant_box_version:
            self.canvas.create_text(self.screen_width/2, self.screen_height/2,
                                    text="ITI", fill="white", font=("Helvetica", 32))
        self.canvas.bind("<Button-1>", self.iti_peck_handler)
        self.root.after(self.ITI_duration, lambda: self.finish_ITI(incorrect))

    def finish_ITI(self, was_incorrect):
        self.canvas.unbind("<Button-1>")
        self.canvas.delete("all")
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True)
        if was_incorrect:
            self.next_trial(new_trial=False)
        else:
            self.next_trial(new_trial=True)

    def iti_peck_handler(self, event):
        x, y = event.x, event.y
        region = "Sample" if x < self.screen_width/2 else "Canvas"
        IRI = round(time() - self.previous_peck_time, 4)
        self.previous_peck_time = time()
        self.write_data(x, y, "ITI_peck", region, IRI)

    def provide_reinforcement(self):
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, False)
            rpi_board.write(hopper_light_GPIO_num, True)
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_up_val)
        self.write_data("NA", "NA", "reinforcer_provided", "NA", 0)
        self.canvas.delete("all")
        self.canvas.config(bg="black")
        if not operant_box_version:
            self.canvas.create_text(self.screen_width/2, self.screen_height/2,
                                    text="Reinforcement", fill="white", font=("Helvetica", 32))
        self.root.after(self.reinforcement_duration, self.end_reinforcement)

    def end_reinforcement(self):
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num, False)
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_down_val)
            # Note: House light is not turned on here as per specifications.
        self.start_ITI(incorrect=False)

    ########## EXIT
    def exit_program(self, event=None):
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, False)
            rpi_board.write(hopper_light_GPIO_num, False)
        if self.record_data:
            self.write_data("NA", "NA", "SessionEnds", "NA", 0)
            fname = path.join(self.data_folder_directory, self.subject_ID,
                              f"{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_{self.experiment_name}_{self.exp_phase_title}.csv")
            with open(fname, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerows(self.session_data)
            print(f"Data file written => {fname}")
        try:
            self.root.destroy()
        except TclError:
            pass
        print("Session ended. You may close the terminal.")
        sys.exit(0)

    ########## DATA LOGGING
    def write_data(self, x, y, event_type, region, IRI, curr_dot_coord=None, prev_dot_coord=None):
        session_time_str = str(datetime.now() - self.start_time)
        x_str = str(x)
        y_str = str(y)
        prev_x, prev_y = "NA", "NA"
        if "peck" in event_type:
            if self.last_peck_x is not None and self.last_peck_y is not None:
                prev_x, prev_y = str(self.last_peck_x), str(self.last_peck_y)
            self.last_peck_x = x if isinstance(x, (int, float)) else None
            self.last_peck_y = y if isinstance(y, (int, float)) else None
        ccoord = curr_dot_coord if curr_dot_coord else "NA"
        pcoord = prev_dot_coord if prev_dot_coord else "NA"
        phase_label = PHASE_LABELS.get(self.phase_key, "NA")
        
        # Calculate Correct Dot(s)
        if "sample_dots" in self.current_trial_config and self.current_trial_config["sample_dots"]:
            correct_dot = str([[dot.row, dot.col] for dot in self.current_trial_config["sample_dots"]])
        else:
            correct_dot = "NA"
        
        # Calculate Distractor Dot(s)
        if "distractor_dots" in self.current_trial_config and self.current_trial_config["distractor_dots"]:
            distractor_dot = str([[dot.row, dot.col] for dot in self.current_trial_config["distractor_dots"]])
        elif "distractor_dot" in self.current_trial_config and self.current_trial_config["distractor_dot"]:
            distractor_dot = str([[self.current_trial_config["distractor_dot"].row,
                                    self.current_trial_config["distractor_dot"].col]])
        else:
            distractor_dot = "NA"
        
        # Build the row without a proximity value.
        row = [
            str(self.trial_counter),
            str(self.attempt_counter),
            session_time_str,
            x_str,
            y_str,
            prev_x,
            prev_y,
            event_type,
            ccoord,
            pcoord,
            str(IRI),
            self.start_time.strftime('%Y-%m-%d_%H.%M.%S'),
            phase_label,
            "NA",  # Line Distance (always NA for now)
            correct_dot,
            distractor_dot,
            region,
            self.experiment_name,
            self.box_number,
            self.subject_ID,
            date.today().strftime("%y-%m-%d")
        ]
        self.session_data.append(row)
        print(f"LOG => {event_type:>20} | Trial:{self.trial_counter}, Att:{self.attempt_counter} | x:{x_str}, y:{y_str}, region:{region}, Phase:{phase_label}, cCoord:{ccoord}, pCoord:{pcoord} | {session_time_str}")
        
    ########## UTILS
    def three_dots_collinear(self, three_dots):
        coords = []
        for d in three_dots:
            cx, cy = d.center()
            coords.append((cx, cy))
        return self.collinear_3points(coords[0], coords[1], coords[2])

    def collinear_3points(self, p1, p2, p3):
        (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
        area = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
        return (area == 0)

    def four_has_3_collinear(self, four_dots):
        from itertools import combinations
        for combo in combinations(four_dots, 3):
            if self.three_dots_collinear(combo):
                return True
        return False

########### MAIN
try:
    if __name__ == "__main__":
        cp = ExperimenterControlPanel()
except:
    if operant_box_version:
        rpi_board.set_PWM_dutycycle(servo_GPIO_num, False)
        rpi_board.set_PWM_frequency(servo_GPIO_num, False)
        rpi_board.stop()
