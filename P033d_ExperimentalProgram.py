'''
P033d: Preference for Digital Paint Access Compared to Food Reinforcers
    
# This is a python program written by Paul Gan, Robert Tsai, Cameron Guo, & 
# Cyrus Kirkman starting in Spring of 2022. The goal of the program was to create a 
# "stained-glass" type of canvas for pigeons to draw on.

# This version of the program adopted a "press-to-play" procedure wherein every
# 60 s the canvas would go blank and a key would appear. Pigeons needed to 
# peck this key to access their canvas.

# This version of the procedure pioloted choice of food reinforcement with 
choice of art creation (perhaps reinforcement).

# It was last updated Sep 30, 2024
'''

# First we import the libraries relevant for this project
from tkinter import Toplevel, Canvas, BOTH, TclError, Tk, Label, Button, \
     StringVar, OptionMenu, IntVar, Radiobutton, Entry
from graph import Graph
from tkinter import messagebox
import functools
from time import perf_counter, sleep
from datetime import datetime, date
from random import randint, choice, shuffle
from csv import writer, QUOTE_MINIMAL
from PIL import Image
from csv import reader
from sys import setrecursionlimit, path as sys_path
from os import getcwd, popen, mkdir, path as os_path

# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It is changed automatically based on whether
# the program is running in operant boxes (True) or not (False). It is
# automatically set to True if the user is "blaisdelllab" (e.g., running
# on a rapberry pi) or False if not. The output of os_path.expanduser('~')
# should be "/home/blaisdelllab" on the RPis

# Updated to run on 1024x768p screens.

if os_path.expanduser('~').split("/")[2] =="blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")
    
# Global variables 
TIME = 0 # Gives a metric for relevative efficiency

if operant_box_version:
    data_folder_directory = str(os_path.expanduser('~'))+"/Desktop/Data/P033_data/P033d_FoodvArt"
else:
    data_folder_directory  = getcwd() + "/P033d_FoodvArt"

# Create macro folder if it does not exist
try:
    if not os_path.isdir(data_folder_directory):
        mkdir(os_path.join(data_folder_directory))
        print("\n ** NEW DATA FOLDER FOR %s CREATED **")
except FileExistsError:
    print("Data folder for %s exists.")
    
    
# Import hopper/other specific libraries from files on operant box computers
try:
    if operant_box_version:
        # Import additional libraries...
        import pigpio # import pi, OUTPUT
        import csv
        
        # Setup GPIO numbers (NOT PINS; gpio only compatible with GPIO num)
        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        house_light_GPIO_num = 21
        
        # Setup use of pi()
        rpi_board = pigpio.pi()
        
        # Then set each pin to output 
        rpi_board.set_mode(servo_GPIO_num,
                           pigpio.OUTPUT) # Servo motor...
        rpi_board.set_mode(hopper_light_GPIO_num,
                           pigpio.OUTPUT) # Hopper light LED...
        rpi_board.set_mode(house_light_GPIO_num,
                           pigpio.OUTPUT) # House light LED...
        
        # Setup the servo motor 
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    50) # Default frequency is 50 MhZ
        
        # Next grab the up/down 
        hopper_vals_csv_path = str(os_path.expanduser('~')+"/Desktop/Box_Info/Hopper_vals.csv")
        
        # Store the proper UP/DOWN values for the hopper from csv file
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        hopper_up_val = up_down_table[1][0]
        hopper_down_val = up_down_table[1][1]
        
        # Lastly, run the shell script that maps the touchscreen to operant box monitor
        popen("sh /home/blaisdelllab/Desktop/Hardware_Code/map_touchscreen.sh")
                             
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")

    
## Define art-based global functions:
    
# Timer (for debugging).
# Remember to remove the @timer decorator calls if deleting this function.
def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = perf_counter()
        value = func(*args, **kwargs)
        toc = perf_counter()
        elapsed_time = toc - tic
        if TIME:
            print(f"{func.__name__}: {elapsed_time:0.4f} seconds")
        return value
    return wrapper_timer

class Point:
    def __init__(self, coord, ind):
        self.ind = ind
        self.coord = coord

class Paint:
    def __init__(self, root, artist_name, VR_val, record_data):
        self.root = root
        self.VR_val = int(VR_val)
        self.record_data = record_data
        self.cover_id = None
        self.button_id = None
        self.subject = artist_name # Stores the name of the painter
        if operant_box_version:
            self.width, self.height = 1024, 768
            self.root.geometry(f"1920x{self.height}+{self.width}+0")
            self.root.attributes('-fullscreen',
                                 True)
            self.canvas = Canvas(root,
                                 bg="black")
            self.canvas.pack(fill = BOTH,
                                   expand = True)
            
            # Canvas save directory
            self.save_directory = str(os_path.expanduser('~'))+"/Desktop/Data/Pigeon_Art"
            
        else:
            self.width, self.height = 1024, 768 
            self.canvas = Canvas(root, width=self.width, height=self.height)
            self.canvas.pack()
            # Canvas save directory
            self.save_directory = getcwd() + "/saved_art/"
            try:
                if not os_path.isdir(self.save_directory):
                    mkdir(os_path.join(self.save_directory))
            except FileExistsError:
                pass
            
        # Data file save directory
        try:
            if not os_path.isdir(data_folder_directory + artist_name):
                mkdir(os_path.join(data_folder_directory, artist_name))
                print("\n ** NEW DATA FOLDER FOR %s CREATED **" % artist_name.upper())
        except FileExistsError:
            pass
            
        # Bind escape key
        root.bind("<Escape>", self.exit_program) # bind exit program to the "esc" key

        # variables needed for drawing
        self.x, self.y = None, None
        self.draw = False
        self.guideLine = None

        # store all demo label ids
        self.demoLabels = []

        # toggle variables
        self.demo = 0
        self.showLines = 1
        
        # Below, we store all necessary data
        self.currLineIndex = 0 # increment after every line drawn
        self.currPointIndex = 0 # increment after every point of intersection is found

        # Stores all lines and the lines they intersect with by their index
        # {line0 : [(line1, line2), (line3, line4)... ], ...}
        self.lines = {}

        # Store all line ids in a list. When we need to remove lines, this is useful.
        self.lineIds = []
        
        # An adjacency list to store all vertices and edges of our directed graph
        self.graph = {}

        # Stores all points of intersection
        # {line0 : [P1, P2, ... ]} where P1, P2, etc. are Point objects defined in the Point class
        self.intersects = {}

        # Maps line intersect coords to pos coords
        # {(lineIndex0, lineIndex1) : (x, y)}
        self.lineToPosCoords = {}

        # Maps point index to position coordinates
        self.pointToPosCoords = {}

        # Maps point position coordinates to indices
        self.posCoordsToPoints = {}

        # Maps point index (0-n) to their line indices (0-m)
        self.pointToLineIndices = {}

        # Stores all polygons and their ids
        # {[p1,p2,...pn] : id, ...}
        self.polygons = {}

        # Create data objects
        self.start_time = datetime.now() # Set start time
    
        
        # Data is written every time a peck happens
        self.session_data_frame = [] #This where trial-by-trial data is stored
        data_headers = [
            "TrialNum", "TrialType", "LeftButtonStim", "RightButtonStim",
            "EventType", "SessionTime", "IRI", "X1","Y1","PrevX","PrevY",
            "PaintBackgroundColor", "SizeOfLine", "NPolygons","NDots",
            "NLines", "PaintChoices", "FoodChoices", "NumReinforcers",
            "StartTime", "Experiment", "P033_Phase", "BoxNumber",  "Subject",
            "Date"
            ]
        self.session_data_frame.append(data_headers) # First row of matrix is the column headers
        
        
        self.previous_response = datetime.now() # Will update with every peck
        
        # Stores the date of the painting
        self.date = date.today().strftime("%y-%m-%d")
        
        # Stores previous x-coordinate of point
        self.PrevX = "NA"
        self.PrevY = "NA"
        self.background_color = "NA" # Starts NA, gets changed at beginning of trial
        self.dot_counter = 0 # Counts the number of pecks
        self.num_islands = "NA"
        self.polygon_type = "NA"
        
        # Experimental data...
        self.experiment = "P033d"
        self.P033_phase = "P033d-PaintVsFood"
        self.trial_num = 0
        self.food_choices = 0
        self.paint_choices = 0
        self.reinforcers_earned = 0
        self.trial_type = "NA" # Will be updated
        self.left_button = "NA"
        self.right_button = "NA"
        self.SessionEnds = False
        if self.subject == "TEST":
            self.hopper_duration  = 1000
        elif self.subject in ["Iggy", "Jagger", "Bowie", "Hendrix"]:
            self.hopper_duration  = 4500
        else:
            self.hopper_duration = 3000 # 3 sec
        self.ITI_duration = 5000 # ms
        
        
        # Assign the stimulus roles per bird (counterbalanced)
        if self.subject in ["TEST", "Jagger", "Herriot", "Kurt"]:
            self.food_button_icon = "triangle"
            self.art_button_icon = "hexagon"
        else:
            self.food_button_icon = "hexagon"
            self.art_button_icon = "triangle"
            
        if operant_box_version:
            box_num_csv_path = "/home/blaisdelllab/Desktop/Box_Info/Box_number.txt"
            with open(box_num_csv_path, 'r') as file:
                f = reader(file)
                # Assuming there is only one row and one column in the CSV file...
                for row in f:
                    # Convert the value to the appropriate data type (e.g., int)
                    self.box_num = int(row[0])
        else:
            self.box_num = "NA"
            
        # Determine trial order...
        self.max_number_of_trials = 90
        self.num_of_forced_food = self.max_number_of_trials // 3
        self.num_of_forced_art = self.max_number_of_trials // 3
        self.num_of_free_choice_trials = self.max_number_of_trials - self.num_of_forced_food - self.num_of_forced_art 
        
        '''
        Create a list of dictionaries of trial attributes in the following format:
            [{"TrialType": "ForcedArt",
             "LeftChoice": "Art",
             "RightChoice": NA
             },
            {"TrialType": "Choice",
             "LeftChoice": "Art",
             "RightChoice": "Food"
             }
             ]
        '''
        self.trial_assignment_list = [] # This will be appended to...
        
        # Add our forced food trials
        while len(self.trial_assignment_list) < self.num_of_forced_food:
            # Flip a coin
            heads_or_tails = choice([0, 1])
            if heads_or_tails:
                left = "Food"
                right = "NA"
            else:
                left = "NA"
                right = "Food"
                
            self.trial_assignment_list.append({"TrialType": "ForcedFood",
                                               "LeftChoice": left,
                                               "RightChoice": right})
        # Add our forced art trials
        while len(self.trial_assignment_list) < self.num_of_forced_food + self.num_of_forced_art:
            # Flip a coin
            heads_or_tails = choice([0, 1])
            if heads_or_tails:
                left = "Art"
                right = "NA"
            else:
                left = "NA"
                right = "Art"
                
            self.trial_assignment_list.append({"TrialType": "ForcedArt",
                                               "LeftChoice": left,
                                               "RightChoice": right})
            
        # Add our forced art trials
        while len(self.trial_assignment_list) < self.max_number_of_trials:
            # Flip a coin
            heads_or_tails = choice([0, 1])
            if heads_or_tails:
                left = "Art"
                right = "Food"
            else:
                left = "Food"
                right = "Art"
                
            self.trial_assignment_list.append({"TrialType": "Choice",
                                               "LeftChoice": left,
                                               "RightChoice": right})
            
        # Now, determine order of this list such that there are no more than
        # two of one consecutive trial types
        proper_order = False
        
        while proper_order == False:
            shuffle(self.trial_assignment_list)
            counter = 0 
            perhaps_proper_order = True # Innocent until proven guilty
            # Check if each shuffled order list meets the criterion
            for i in self.trial_assignment_list:
                if counter > 2:
                    if self.trial_assignment_list[counter]["TrialType"] == self.trial_assignment_list[counter - 1]["TrialType"] == self.trial_assignment_list[counter - 2]["TrialType"]:
                        perhaps_proper_order = False
                counter += 1
            # If this trial order passes, then we can break the loop
            if perhaps_proper_order == True:
                proper_order = True

        # Canvas creation stuff
        # make the entire canvas a polygon
        offset = 4
        self.drawLine([(0-offset, 0-offset),
                       (self.width+offset, 0-offset)]) # upper-left to upper-right
        self.drawLine([(self.width+offset, 0-offset),
                       (self.width+offset, self.height+offset)]) # upper-right to lower-right
        self.drawLine([(self.width+offset, self.height+offset),
                       (0-offset, self.height+offset)]) # lower-right to lower-left
        self.drawLine([(0-offset, self.height+offset),
                       (0-offset, 0-offset)]) # lower-left to upper-left
        
        self.coverState = None
        self.paintButtonPressed = False
        self.foodButtonPressed = False
        self.lastTwoPlacements = []
        self.random_placement_index = "NA"
        self.visible_paint_button_id = None
        self.visible_color_button_id = None
        
        self.place_birds_in_box()

    def place_birds_in_box(self):
        
        def first_ITI(event):
            print("Spacebar pressed -- SESSION STARTED") 
            self.canvas.delete("text")
            root.bind("<space>", paint.toggleDemo)
            
            # Call cover for first trial's choice
            if self.subject != "TEST":
                self.root.after(30 * 1000, 
                                self.choicePhase)
            else:
                self.choicePhase()
            
            
        self.canvas.create_rectangle(0, 0, self.width,
                                     self.height,
                                     fill="black",
                                     outline="black",
                                     tag = "bkgrd")
        
        self.canvas.create_text(512,374,
                                      fill="white",
                                      font="Times 25 italic bold",
                                      text=f"P033d \n Place bird in box, then press space \n Subject: {self.subject} \n VR: {self.VR_val}",
                                      tag = "text") 
        root.unbind("<space>")
        root.bind("<space>", first_ITI) # bind cursor state to "space" key
        
        
    # covers canvas; where buttons are presented
    def choicePhase(self):
        # First, check if session is over
        if self.trial_num >= self.max_number_of_trials:
            # Make a black rectangle to literally cover the canvas
            self.SessionEnds = True
            self.write_data(None, "SessionEnds")
            self.delete_items()
            self.canvas.create_rectangle(0, 0, self.width,
                                         self.height,
                                         fill="black",
                                         outline="black",
                                         tag="bkgrd")
            self.canvas.tag_bind("bkgrd",
                                 "<Button-1>",
                                 lambda event, 
                                 event_type = "Session_Ended_Peck": 
                                     self.write_data(event, event_type))   
            if operant_box_version: # Turn off lights and lower hopper (just in case)
                rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
                rpi_board.write(hopper_light_GPIO_num,
                                False) # Turn off the hopper light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val) # Move hopper to up position
        # If we want to run a trial... 
        else: 
            # Houselight needs to be turned on always...
            if operant_box_version:
                rpi_board.write(house_light_GPIO_num,
                                True)
                
            # At each choice phase, first reset booleans for rest of trial
            self.coverState = True
            self.foodButtonPressed = False
            self.x, self.y, self.draw = None, None, False # Reset our lines
            self.food_interval_start = None # Reset

            # Get trial info
            trial_info_dict = self.trial_assignment_list[self.trial_num]
            self.trial_type = trial_info_dict["TrialType"]
            self.left_button = trial_info_dict["LeftChoice"]
            self.right_button = trial_info_dict["RightChoice"]
            
            self.trial_num += 1 # Increment after indexing to avoid n-1 errors
            
            print(f"\n{'*'*40} Trial {self.trial_num} begins {'*'*40}") 
            print(f"{'Event Type':>25} | Xcord. Ycord. |  Session Time  | Food | Art | Trial Type")
            print(f"{' ' * 15}{'-' * 69}")
            
            ### Building onscreen stimuli
            # Make a black rectangle to literally cover the canvas
            self.canvas.create_rectangle(0, 0, self.width,
                                         self.height,
                                         fill="black",
                                         outline="black", 
                                         tag="bkgrd")
            
            self.canvas.tag_bind("bkgrd",
                                 "<Button-1>",
                                 lambda event, 
                                 event_type = "background_peck": 
                                     self.write_data(event, event_type))
        
            if self.left_button != "NA":
                # Left button base
                x1, y1 = 125, self.height - 325
                x2, y2 = 275, self.height - 175
                
                self.canvas.create_oval(x1 - 10, # Receptive field
                                        y1 - 10,
                                        x2 + 10,
                                        y2 + 10,
                                        fill = "black",
                                        outline = "black",
                                        tag = self.left_button)
                
                self.canvas.create_oval(x1, # Choice button
                                        y1,
                                        x2,
                                        y2,
                                        fill = "white",
                                        tag = self.left_button)
                
                # Declare our LEFT HEXAGON coords
                Hx1, Hy1 = 200, self.height - 300  # top
                Hx2, Hy2 = 150, self.height - 275  # top-right
                Hx3, Hy3 = 150, self.height - 225  # bottom-right
                Hx4, Hy4 = 200, self.height - 200  # bottom
                Hx5, Hy5 = 250, self.height - 225  # bottom-left
                Hx6, Hy6 = 250, self.height - 275  # top-left
                left_hex_coords = [Hx1, Hy1, Hx2, Hy2, Hx3, Hy3, Hx4, Hy4, Hx5, Hy5, Hx6, Hy6]
                
                # Declare our LEFT TRIANGLE coords
                Tx1, Ty1 = 200, self.height - 300 # top
                Tx2, Ty2 = 140, self.height - 215 # left
                Tx3, Ty3 = 260, self.height - 215 # right
                left_tri_coords = [Tx1, Ty1, Tx2, Ty2, Tx3, Ty3]
                
                # Build icon on button depending on assigment and counterbalancing
                if (self.left_button == "Art" and self.art_button_icon == "hexagon") or (self.left_button == "Food" and self.food_button_icon == "hexagon"):
                    # Build a left hexagon
                    self.canvas.create_polygon(*left_hex_coords,
                                               fill="yellow green",
                                               tag = self.left_button)
                  
                elif (self.left_button == "Art" and self.art_button_icon == "triangle") or (self.left_button == "Food" and self.food_button_icon == "triangle"):
                    # Build a left triangle
                    self.canvas.create_polygon(*left_tri_coords,
                                               fill="cadet blue",
                                               tag = self.left_button)

            if self.right_button != "NA":
                # Right button base
                x1, y1 = self.width - 125, self.height - 325
                x2, y2 = self.width - 275, self.height - 175
                
                self.canvas.create_oval(x1 + 10, # Receptive field
                                        y1 - 10,
                                        x2 - 10,
                                        y2 + 10,
                                        fill = "black",
                                        outline = "black",
                                        tag = self.right_button)
                
                self.canvas.create_oval(x1, # Choice button
                                        y1,
                                        x2,
                                        y2,
                                        fill = "white",
                                        tag = self.right_button)
                
                # Declare our RIGHT HEXAGON coords
                Hx1, Hy1 = self.width - 200, self.height - 300  # top
                Hx2, Hy2 = self.width - 150, self.height - 275  # top-right
                Hx3, Hy3 = self.width - 150, self.height - 225  # bottom-right
                Hx4, Hy4 = self.width - 200, self.height - 200  # bottom
                Hx5, Hy5 = self.width - 250, self.height - 225  # bottom-left
                Hx6, Hy6 = self.width - 250, self.height - 275  # top-left
                right_hex_coords = [Hx1, Hy1, Hx2, Hy2, Hx3, Hy3, Hx4, Hy4, Hx5, Hy5, Hx6, Hy6]
                
                # Declare our RIGHT TRIANGLE coords
                Tx1, Ty1 = self.width - 200, self.height - 300 # top
                Tx2, Ty2 = self.width - 140, self.height - 215 # left
                Tx3, Ty3 =  self.width - 260, self.height - 215 # right
                right_tri_coords = [Tx1, Ty1, Tx2, Ty2, Tx3, Ty3]
                
                # Build icon on button depending on assigment and counterbalancing
                if (self.right_button == "Art" and self.art_button_icon == "hexagon") or (self.right_button == "Food" and self.food_button_icon == "hexagon"):
                    # Build a right hexagon
                    self.canvas.create_polygon(*right_hex_coords,
                                               fill="yellow green",
                                               tag = self.right_button)
                  
                elif (self.right_button == "Art" and self.art_button_icon == "triangle") or (self.right_button == "Food" and self.food_button_icon == "triangle"):
                    # Build a right triangle
                    self.canvas.create_polygon(*right_tri_coords,
                                               fill="cadet blue",
                                               tag = self.right_button)
            
            # Now we need to build functionality into the buttons
            # Start by binding any tags to a functions
            if self.left_button == "Art":
                self.canvas.tag_bind(self.left_button,
                                     "<Button-1>",
                                     self.coverToPaint)
            elif self.left_button == "Food":
                self.canvas.tag_bind(self.left_button,
                                     "<Button-1>",
                                     self.coverToFood)
            if self.right_button == "Art":
                self.canvas.tag_bind(self.right_button,
                                     "<Button-1>",
                                     self.coverToPaint)
            elif self.right_button == "Food":
                self.canvas.tag_bind(self.right_button,
                                     "<Button-1>",
                                     self.coverToFood)
    
                
    # These are the functions tied to each button
    
    def coverToPaint(self, event):
        # Delete cover and button
        self.write_data(event, "paint_choice_pressed")
        if self.trial_type == "Choice":
            self.paint_choices += 1
        self.delete_items() # Remove buttons/background cover
        # Bind our painting tools
        #bindKeys()
        self.coverState = False
        self.paintButtonPressed = True
        # Last, set up a timer for the next cover
        self.root.after(30 * 1000,
                        self.ITI)
        
        
    def coverToFood(self, event):
        if event != None:
            self.write_data(event, "food_choice_pressed")
            self.food_interval_start = datetime.now()
        else: # Always turn off hopper
            if operant_box_version:
                rpi_board.write(house_light_GPIO_num,
                                True) # Turn on the house light
                rpi_board.write(hopper_light_GPIO_num,
                                False) # Turn on the house light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val) # Move hopper to up position
        # Only track choices if its the first time the function is called
        if self.trial_type == "Choice" and event != None:
            self.food_choices += 1 
        self.delete_items() # Remove buttons/background cover
        # Bind our painting tools
        #bindKeys()
        self.coverState = False
        self.foodButtonPressed = True
        
        # Set the VR for this iteration:
        lower_bound = 1
        upper_bound = self.VR_val * 2
        self.trial_vr = randint(lower_bound, upper_bound)
        
        # Build the food key
        radius = 125
        x1, y1 = self.width // 2 - radius, self.height // 2 - radius
        x2, y2 = self.width // 2 + radius, self.height // 2 + radius
        food_button_coords = [x1, y1, x2, y2]
        
         # Make a black rectangle to literally cover the canvas
        self.canvas.create_rectangle(0, 0, self.width,
                                      self.height,
                                      fill="black",
                                      outline="black", 
                                      tag="bkgrd")
        self.canvas.tag_bind("bkgrd",
                             "<Button-1>",
                             lambda event, 
                             event_type = "background_peck": 
                                 self.write_data(event, event_type))
        
        # Build the buttons
        self.canvas.create_oval(x1 - 10,
                                y1 - 10,
                                x2 + 10,
                                y2 + 10,
                                fill = "black",
                                outline = "black",
                                tag = "food_key"
                                )
        
        self.canvas.create_oval(*food_button_coords,
                                fill = "white",
                                tag = "food_key"
                                )
        
        self.canvas.tag_bind("food_key",
                             "<Button-1>", 
                             self.foodKeyPress)
                             
        # Last, set up a timer for the next cover
        timer_length = (self.food_interval_start - datetime.now()).total_seconds() + 30
        if timer_length > 0:
            self.food_timer = self.root.after(int(timer_length * 1000),
                                              self.ITI)
        else:
            self.ITI()
        
    def foodKeyPress(self, event):
        self.write_data(event, "food_button_pressed")
        self.trial_vr -= 1
        if self.trial_vr == 0:
            self.provide_food()
            

    def provide_food(self):
        # This function is contingent upon correct and timely choice key
        # response. It opens the hopper and then leads to ITI after a preset
        # reinforcement interval (i.e., hopper down duration)
        
        self.root.after_cancel(self.food_timer)
        self.reinforcers_earned += 1 # Increment food counter
        self.write_data(None, "food_provided")
        
        if self.subject == "TEST":
            self.canvas.create_text(512,374,
                                          fill="red",
                                          font="Times 25 italic bold", 
                                          text=f"Correct Key Pecked \nFood accessible ({int(self.hopper_duration/1000)} s)",
                                          tag = "text") # just onscreen feedback
            
        self.canvas.tag_bind("text",
                             "<Button-1>",
                             lambda event, 
                             event_type = "reinforcement_active_peck": 
                                 self.write_data(event, event_type))
            
        self.canvas.tag_bind("bkgrd",
                             "<Button-1>",
                             lambda event, 
                             event_type = "reinforcement_active_peck": 
                                 self.write_data(event, event_type))
            
        self.canvas.tag_bind("food_key",
                             "<Button-1>",
                             lambda event, 
                             event_type = "reinforcement_active_peck": 
                                 self.write_data(event, event_type))
            
        # Next send output to the box's hardware
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num,
                            True) # Turn on the hopper light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                           hopper_up_val) # Move hopper to up position
            rpi_board.write(house_light_GPIO_num,
                                False)
        # Pass back to food choice
        self.root.after(self.hopper_duration,
                        lambda event = None: self.coverToFood(event))

    def ITI(self):
        # Delete items from trial and reset booleans
        self.delete_items()
        self.paintButtonPressed = False
        self.foodButtonPressed = False
        
         # Make a black rectangle to literally cover the canvas
        self.canvas.create_rectangle(0, 0, self.width,
                                      self.height,
                                      fill="black",
                                      outline="black", 
                                      tag="bkgrd")
        self.canvas.tag_bind("bkgrd",
                             "<Button-1>",
                             lambda event, 
                             event_type = "ITI_peck": 
                                 self.write_data(event, event_type))
        if self.subject == "TEST":
            self.canvas.create_text(512,374,
                                          fill="white",
                                          font="Times 25 italic bold", 
                                          text=f"ITI ({int(self.ITI_duration/1000)} s)",
                                          tag = "text") # just onscreen feedback
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num,
                            False) # Turn off the house light
            
        #Update data .csv file 
        self.write_comp_data()
        # Pass back to food choice
        self.root.after(self.ITI_duration,
                        self.choicePhase)
        
    # generates a random color
    def generateColor(self):
        rand = lambda: randint(50, 200)
        color_choice = '#%02X%02X%02X' % (rand(), rand(), rand())
        if self.background_color == "NA":
            self.background_color = color_choice
        return color_choice
    

    # Return true if line segments AB and CD intersect.
    # This will be used in the findIntersects method
    def hasIntersect(self, A, B, C, D):
        def ccw(A,B,C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

    # Every time a line segment is drawn, we will call this function on that line segment
    # For each line that the new line intersects, we will append the intersect coord (x, y) to 
    # the values (lists) of both lines in self.intersects
    # Return all intersects between line and all stored lines as a list of 2D points
    @timer
    def findIntersects(self, line):
        # helper function to find intersection between 2 lines
        def getIntersect(line1, line2):

            xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
            ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

            def det(a, b):
                return a[0] * b[1] - a[1] * b[0]

            div = det(xdiff, ydiff)
            if div == 0:
                return None

            d = (det(*line1), det(*line2))
            x = det(d, xdiff) / div
            y = det(d, ydiff) / div
            return (x, y)

        # loop through all stored lines, check intersect between line and each line l2 in list
        for lineNum, l2 in self.lines.items():
            if self.hasIntersect(line[0], line[1], l2[0], l2[1]) == False:
                continue
            p = getIntersect(line, l2)
            if p is not None: # if line and l2 intersecting
                self.lineToPosCoords[(lineNum, self.currLineIndex)] = p
                self.pointToPosCoords[self.currPointIndex] = p
                self.posCoordsToPoints[p] = self.currPointIndex

                # add indices of intersecting lines (values) associated with point (key) to the pointToLineIndices dict
                self.pointToLineIndices[self.currPointIndex] = [self.currLineIndex, lineNum]

                # update self.intersects dict
                self.intersects.setdefault(lineNum, []).append(Point(p, self.currPointIndex))
                self.intersects.setdefault(self.currLineIndex, []).append(Point(p, self.currPointIndex))
                
                # sort lists in self.intersects
                self.intersects[lineNum] = sorted(self.intersects[lineNum], key=lambda x : x.coord)
                self.intersects[self.currLineIndex] = sorted(self.intersects[self.currLineIndex], key=lambda x : x.coord)

                self.currPointIndex += 1

    # Function to update self.graph after new shapes are drawn onto canvas
    @timer
    def updateEdges(self):
        self.graph = {} # clear the graph

        # identify all points that are not involved in a cycle
        self.toExclude = set()
        for points in self.intersects.values():
            if len(points) == 1:
                self.toExclude.add(points[0].ind)

        for _list in self.intersects.values():
            if len(_list) < 2: continue
            for i in range(len(_list)-1):
                u, v = _list[i], _list[i+1]
                if (u.ind not in self.toExclude) and (v.ind not in self.toExclude):
                    self.graph.setdefault(u, []).append(v)

    # draws a red dot at specified point
    def drawDot(self, point):
        r = 6
        id = self.canvas.create_oval(point[0]-r//2, point[1]-r//2, point[0]+r//2, point[1]+r//2,
                                fill="#FF0000", outline="#FF0000")
        return id

    # function to find all new polygons since last shape drawn
    def findNewPolygons(self):
        def printPolygon(p, end='\n'):
            for point in p:
                print(self.posCoordsToPoints[point], end=' ')
            print(end=end)

        # if graph contains only 1 directed edge, there are no polygons
        if len(self.graph) <= 1:
            return None

        g = Graph(self.graph) # passing in directed graph
        regions = g.solve() # list of sublists containing point indices (0 - n)
        
        polygons = set()

        # for each polygon
        for r in regions:
            # convert point index to position coords
            polygon = [self.pointToPosCoords[p] for p in r] 

            # reorder polygon vertices while preserving edge relationships
            # we want the top-left-most vertex as the first item
            forwardList = polygon + polygon
            left = forwardList.index(min(polygon))
            if forwardList[left][0] > forwardList[left + 1][0]:
                forwardList.reverse() 
                left = forwardList.index(min(polygon))
            polygon = forwardList[left:left+len(polygon)]
            polygons.add(tuple(polygon))

        newPolygons = list(polygons - set(self.polygons.keys()))
        
        # if polygon is new
        for polygon in newPolygons:
            isNew = True
            # if polygon is already in stored polygons, don't add it again
            for curr in self.polygons.keys():
                currSet, polygonSet = set(curr), set(polygon)
                if currSet == polygonSet or len(currSet - polygonSet) == 0 or len(polygonSet - currSet) == 0: 
                    isNew = False
            
            # if new polygon, fill with random color and add its vertices and id to the polygons dict
            if isNew:
                color = self.generateColor()
                id = self.canvas.create_polygon(polygon, fill=color, outline=color, width=0.5)
                self.polygons[polygon] = id # add new polygon to list
                # 
        # print("polygons:")
        # for p in self.polygons:
        #     printPolygon(p, end=' | ')

    # redraw all lines
    def drawLines(self):
        # remove all current lines
        for id in self.lineIds:
            self.canvas.delete(id)
        
        self.lineIds = []
        
        # draw all lines
        for line in self.lines.values():
            id = self.canvas.create_line(line, width=0.5)
            self.lineIds.append(id)

    # function to extend line by a factor of d. 
    # this is useful for intersection detection
    def extendLine(self, line, d):
        p1, p2 = line[0], line[1]
        mag = ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2) ** (1/2) # magnitude
        
        if mag != 0:
            # new coords
            x1 = p1[0] - d * (p2[0]-p1[0]) / mag
            y1 = p1[1] - d * (p2[1]-p1[1]) / mag
            x2 = p2[0] + d * (p2[0]-p1[0]) / mag
            y2 = p2[1] + d * (p2[1]-p1[1]) / mag
        else:
            # new coords
            x1 = p1[0] - d * (p2[0]-p1[0])
            y1 = p1[1] - d * (p2[1]-p1[1])
            x2 = p2[0] + d * (p2[0]-p1[0])
            y2 = p2[1] + d * (p2[1]-p1[1])
        
        return [(x1, y1), (x2, y2)]

    # draw line onto canvas, update data
    def drawLine(self, line):
        # increase line length slightly
        line = self.extendLine(line, 3)

        # sort line endpoints
        # if line is already in list, don't do anything
        line = sorted(line)
        if line in self.lines.values():
            print("line already drawn")
            return

        # find intersects between new line and all existing lines
        self.findIntersects(line)
        
        # add new line to lines dict
        self.lines[self.currLineIndex] = line

        # increment current line number
        self.currLineIndex += 1

        # update edges
        self.updateEdges()

        # find all polygons and fill them
        self.findNewPolygons()

        # draw all lines onto canvas
        if self.showLines: self.drawLines()

        if self.demo:
            self.drawDemoLabels()

    @timer
    def drawDemoLabels(self):
        for id in self.demoLabels:
            self.canvas.delete(id)
        self.demoLabels = []

        # draw edges
        for u in self.graph:
            for v in self.graph[u]:
                id = self.canvas.create_line((*u.coord, *v.coord), width=2, fill="blue", arrow='last')
                self.demoLabels.append(id)

        # draw point numbers
        for point, coord in self.pointToPosCoords.items():
            id = self.canvas.create_text(coord[0], coord[1] + 14, text=f"{point}")
            self.demoLabels.append(id)

        # draw points
        for point in self.lineToPosCoords.values():
            id = self.drawDot(point)
            self.demoLabels.append(id)

# Keybound commands:
    
    # callback for left click
    def onLeftButton(self, event):
        if self.paintButtonPressed:
        # Write a data event on every press
            if self.draw:
                self.drawLine([(self.x, self.y), (event.x, event.y)])
                if self.guideLine: self.canvas.delete(self.guideLine)
                self.draw = False
                self.x, self.y = None, None
            else:
                self.x, self.y = event.x, event.y
                self.draw = True
            # Write data for click
            self.write_data(event, "paint_peck")

    # callback for right click
    def onRightButton(self, event):
        if self.draw:
            self.canvas.delete(self.guideLine)
            self.draw = False
            self.x, self.y = None, None

    # callback for mouse move
    def onMouseMove(self, event):
        # redraw guideline
        if self.coverState or self.foodButtonPressed:
            pass
        else:
            if self.guideLine: self.canvas.delete(self.guideLine)
            if self.x is not None and self.y is not None:
                self.guideLine = self.canvas.create_line((self.x, self.y, event.x, event.y), fill="red")

    def toggleLines(self, event):
        if not self.showLines:
            self.drawLines()
            self.showLines = 1
        else:
            # remove all current lines
            for id in self.lineIds:
                self.canvas.delete(id)
            self.showLines = 0

    def toggleDemo(self, event):
        if not self.demo:
            self.drawDemoLabels()
            self.demo = 1
        else:
            for id in self.demoLabels:
                self.canvas.delete(id)
            self.demoLabels = []
            self.demo = 0
        
    def write_data(self, event, event_type):
        # This function writes a new data line after EVERY peck. Data is
        # organized into a matrix (just a list/vector with two dimensions,
        # similar to a table). This matrix is appended to throughout the 
        # session, then written to a .csv once at the end of the session.
        if event != None: 
            x, y = event.x, event.y
            if self.paintButtonPressed:
                self.dot_counter += 1
            #event_type = "peck"
        else: # There are certain data events that are not pecks.
            x, y = "NA", "NA"   
            #event_type = "SessionEnds"
        
        # Line length calcultion
        if "NA" not in [self.PrevX, self.PrevY, x, y]:
            line_length = int(((x-self.PrevX)**2 + (y-self.PrevY)**2) ** 0.5) # Length of line rounded to nearest pixel
        else:
            line_length = "NA"
            
        if event_type is None:
            event_type = "NA"
        if x is None:
            x = "NA"
        if y is None:
            y = "NA"
        print(f"{event_type:>25} | x: {x: ^3} y: {y:^3} | {str(datetime.now() - self.start_time)} | {self.food_choices:^4} | {self.paint_choices:^3} | {self.trial_type}")
        
        self.session_data_frame.append([
            self.trial_num,
            self.trial_type,
            self.left_button,
            self.right_button,
            event_type,
            str(datetime.now() - self.start_time), # SessionTime as datetime object
            str(datetime.now() - self.previous_response), # IRI
            x, # X coordinate of a peck
            y, # Y coordinate of a peck
            self.PrevX, # Previous x coordinate
            self.PrevY, # Previous y coordinate
            self.background_color,
            line_length,
            len(self.polygons) - 1, # Number of polygons w/o background (?)
            self.dot_counter, # Number of points
            len(self.lineIds) - 4, # Number of lines
            self.paint_choices,
            self.food_choices,
            self.reinforcers_earned,
            self.start_time,
            self.experiment,
            self.P033_phase,
            self.box_num,
            self.subject,
            date.today() # Today's date as "MM-DD-YYYY"
            ])
        
        # Update the "previous" response time
        if event != None:
            self.previous_response = datetime.now()
            self.PrevX = x
            self.PrevY = y
        
        data_headers = [
            "TrialNum", "TrialType", "LeftButtonStim", "RightButtonStim",
            "EventType", "SessionTime", "IRI", "X1","Y1","PrevX","PrevY",
            "PaintBackgroundColor", "SizeOfLine", "NPolygons","NDots",
            "NLines", "PaintChoices", "FoodChoices", "NumReinforcers",
            "StartTime", "Experiment", "P033_Phase", "BoxNumber",  "Subject",
            "Date"
            ]

    def delete_items(self):
        self.canvas.delete("bkgrd") # Remove cover
        self.canvas.delete("Art") # Get rid of art buttons (if they exist)
        self.canvas.delete("Food") # Get rid of food buttons (if they exist)
        self.canvas.delete("text")
        self.canvas.delete("food_key")
            
    def write_comp_data(self):
        # The following function creates a .csv data document. It is run during
        # each ITI. If the first time the function is called, it will produce
        # a new .csv out of the session_data_matrix variable, named after the
        # subject, date, and training phase.
        
        myFile_loc = f"{data_folder_directory}/{self.subject}/P033d_{self.subject}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_CoverWButton.csv" # location of written .csv
        
        # This loop writes the data in the matrix to the .csv              
        edit_myFile = open(myFile_loc, 'w', newline='')
        with edit_myFile as myFile:
            w = writer(myFile, quoting=QUOTE_MINIMAL)
            w.writerows(self.session_data_frame) # Write all event/trial data 
            print(f"\n- Data file written to {myFile_loc}")
            
    def exit_program(self, event):
        self.write_comp_data()
        self.save_image()
        rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
        rpi_board.write(hopper_light_GPIO_num,
                                False) # Turn off the hopper light
        rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val)
        self.delete_items()
        print("Escape key pressed")
        # Remove lines from drawing (can add back in with keybound command)
        self.toggleLines("event")
        # print("- Lines removed from Canvas")
        self.canvas.destroy()
        self.root.after(1, self.root.destroy())

    # This builds a popup save_image window and saves as a .eps file
    def save_image(self):
        self.delete_items()
        now = datetime.now()
        file_name = f"{self.save_directory}/{self.subject}_{now.strftime('%m-%d-%Y_Time-%H-%M-%S')}_{self.P033_phase}" 
        fileps = file_name + ".eps" 
        self.canvas.postscript(file=fileps)
        Image.open(fileps)
        

def main(artist_name, VR_val, record_data):
    global root, paint
    print("(l) toggle lines")
    print("(spacebar) toggle labels")
    print("left mouse button to draw")
    print("right mouse button to cancel draw")
    # Setup Canvas
    root = Toplevel()
    root.title("Paint Program with Polygon Detection")
    root.resizable(False, False)
    paint = Paint(root, artist_name, VR_val, record_data) # Pass artist name to program
    #bindKeys(paint)
    root.bind("<ButtonPress-1>", paint.onLeftButton)
    root.bind("<ButtonPress-2>", paint.onRightButton)
    root.bind("<Motion>", paint.onMouseMove)
    # root.bind("<space>", paint.toggleDemo)
    root.bind("l", paint.toggleLines)

    root.mainloop()
    

class ExperimenterControlPanel(object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self):
        # setup the root Tkinter window
        self.control_window = Tk()
        self.control_window.title("P033d Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = ["Jagger",
                                 "Herriot",
                                 "Bowie",
                                 "Iggy",
                                 "Kurt",
                                 "Hendrix"]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        
        
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list).pack()
        
        
        Label(self.control_window, text = "Input food VR:").pack()
        self.food_VR_variable = IntVar(self.control_window)
        self.food_VR_textbox = Entry(self.control_window)
        self.food_VR_textbox.insert(0, 5)
        self.food_VR_textbox.pack()
        

        # Record data variable?
        Label(self.control_window,
              text = "Record data in seperate data sheet?").pack()
        self.record_data_variable = IntVar()
        self.record_data_rad_button1 =  Radiobutton(self.control_window,
                                   variable = self.record_data_variable, text = "Yes",
                                   value = True).pack()
        self.record_data_rad_button2 = Radiobutton(self.control_window,
                                  variable = self.record_data_variable, text = "No",
                                  value = False).pack()
        self.record_data_variable.set(True) # Default set to True
        
        
        # Start button
        self.start_button = Button(self.control_window,
                                   text = 'Start program',
                                   bg = "green2",
                                   command = self.build_chamber_screen).pack()
        
        # This makes sure that the control panel remains onscreen until exited
        self.control_window.mainloop() # This loops around the CP object

              
    def build_chamber_screen(self):
        # Once the green "start program" button is pressed, then the mainscreen
        # object is created and pops up in a new window. It gets passed the
        # important inputs from the control panel.
        print("Operant Box Screen Built") 
        main(
            str(self.subject_ID_variable.get()), # subject_ID
            self.food_VR_textbox.get(),
            self.record_data_variable.get() # Boolean for recording data (or not)
            )
            

#%% Finally, this is the code that actually runs:
# try:   
if __name__ == '__main__':
    cp = ExperimenterControlPanel()
# except:
#        self.save_image()
#     # If an unexpected error, make sure to clean up the GPIO board
#     if operant_box_version:
#         rpi_board.set_PWM_dutycycle(servo_GPIO_num,
#                                     False)
#         rpi_board.set_PWM_frequency(servo_GPIO_num,
#                                     False)
#         rpi_board.stop()

