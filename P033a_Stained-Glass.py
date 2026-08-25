#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P033a: Original stained glass code, by Cyrus F. Kirkman, Robert Tsai, Paul Gan, 
and Cameron Guo. 


This code was created on Tue Aug 25 10:29:59 2026 to execue independently on 
lab monitors by Megan K. Cady

@author: megancady
"""

# P033 – Stained Glass Art Program

# This is a python program written by Paul Gan, Robert Tsai, Cameron Guo, & 
# Cyrus Kirkman originally in the Spring of 2022. The goal of the program was
# to create a "stained-glass" type of canvas for pigeons to draw on.

# This version of the program adopted a "press-to-play" procedure wherein every
# 60 s the canvas would go blank and a key would appear. Pigeons needed to 
# peck this key to access their canvas.

# It was last updated April 07, 2026

# First we import the libraries relevant for this project
from tkinter import Tk, Toplevel, Canvas, BOTH, Label, Button, StringVar, OptionMenu
try:
    from graph import Graph
except ModuleNotFoundError:
    from math import atan2

    class Graph:
        def __init__(self, graph):
            self.graph = graph

        def solve(self):
            nodes = {}
            edges = set()

            for point, neighbors in self.graph.items():
                nodes[point.ind] = point.coord
                for neighbor in neighbors:
                    nodes[neighbor.ind] = neighbor.coord
                    edges.add(tuple(sorted((point.ind, neighbor.ind))))

            if len(edges) < 3:
                return []

            adjacency = {node: set() for node in nodes}
            for a, b in edges:
                adjacency[a].add(b)
                adjacency[b].add(a)

            sorted_neighbors = {}
            for node, neighbors in adjacency.items():
                x, y = nodes[node]
                sorted_neighbors[node] = sorted(
                    neighbors,
                    key=lambda neighbor: atan2(nodes[neighbor][1] - y, nodes[neighbor][0] - x),
                )

            visited = set()
            faces = []

            for edge in edges:
                for a, b in (edge, edge[::-1]):
                    if (a, b) in visited:
                        continue

                    face = []
                    current, next_node = a, b

                    while (current, next_node) not in visited:
                        visited.add((current, next_node))
                        face.append(current)

                        neighbors = sorted_neighbors[next_node]
                        current_index = neighbors.index(current)
                        current, next_node = next_node, neighbors[(current_index - 1) % len(neighbors)]

                    if len(face) >= 3:
                        area = self._signed_area([nodes[node] for node in face])
                        if abs(area) > 1:
                            faces.append((abs(area), self._normalize(face)))

            unique_faces = []
            seen = set()
            for area, face in sorted(faces, key=lambda item: item[0]):
                key = tuple(face)
                if key not in seen:
                    seen.add(key)
                    unique_faces.append((area, face))

            if len(unique_faces) > 1:
                unique_faces = unique_faces[:-1]

            return [face for _, face in unique_faces]

        @staticmethod
        def _signed_area(coords):
            area = 0
            for i, (x1, y1) in enumerate(coords):
                x2, y2 = coords[(i + 1) % len(coords)]
                area += x1 * y2 - x2 * y1
            return area / 2

        @staticmethod
        def _normalize(face):
            rotations = []
            for cycle in (face, list(reversed(face))):
                smallest = min(range(len(cycle)), key=cycle.__getitem__)
                rotations.append(cycle[smallest:] + cycle[:smallest])
            return min(rotations)

from tkinter import messagebox
import functools
from time import perf_counter, sleep
from datetime import datetime, date
from random import randint
from os import path, mkdir
from csv import writer, QUOTE_MINIMAL
from PIL import Image
from csv import reader


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

if path.expanduser('~').split("/")[2] =="blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")
    
# Global variables 
TIME = 0 # Gives a metric for relevative efficiency
program_folder_path = path.dirname(path.abspath(__file__))

if operant_box_version:
    data_folder_directory = str(path.expanduser('~'))+"/Desktop/Data/P033_data/P033a_StainedGlass_Data"
else:
    data_folder_directory  = path.join(program_folder_path, "P033a_StainedGlass_Data")

# Create macro folder if it does not exist
try:
    if not path.isdir(data_folder_directory):
        mkdir(path.join(data_folder_directory))
        print("\n ** NEW DATA FOLDER CREATED **")
except FileExistsError:
    print("Data folder exists.")
    
## Define functions:
    
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
    def __init__(self, root, artist_name):
        self.root = root
        #ubbindKeys()
        self.cover_id = None
        self.button_id = None
        if operant_box_version:
            self.width, self.height = 1024, 768
            self.root.geometry(f"{self.width}x{self.height}+1920+0")
            self.root.attributes('-fullscreen',
                                 True)
            self.canvas = Canvas(root,
                                 bg="black")
            self.canvas.pack(fill = BOTH,
                                   expand = True)
            
        else:
            self.width, self.height = 1024, 500 #768
            self.canvas = Canvas(root, width=self.width, height=self.height)
            self.canvas.pack()
            
        # Data file save directory
        self.save_directory = path.join(data_folder_directory, artist_name)
        try:
            if not path.isdir(self.save_directory):
                mkdir(self.save_directory)
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
        
        # Stores the name of the painter
        self.subject = artist_name
        
        # Data is written every time a peck happens
        self.session_data_frame = [] #This where trial-by-trial data is stored
        data_headers = [
            "EventType", "SessionTime", "IRI", "X1","Y1","PrevX","PrevY", "SizeOfLine", 
             "NPolygons","NDots", "NLines", "Efforts", "PaintButtonPeck", "ColorButtonPeck",
             "Placement", "BackgroundColor","StartTime", "Experiment", "P033_Phase",
             "PrevReinforcersEarned", "BoxNumber",  "Subject",  "Date"
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
        self.paint_button_peck_counter = 0 # Counts the number of paint button pecks
        self.color_button_peck_counter = 0 # Counts the number of color button pecks
        self.num_islands = "NA"
        self.polygon_type = "NA"
        # This subject assigning process is limited to birds that are currently running
        if self.subject in ["Peach","Luigi",
                       "Waluigi", "Wario", "Wenchang"]:
            self.experiment = "P034b"
        elif self.subject in ["Athena", "Bon Jovi", "Cousteau", "Darwin",
                         "Shy Guy", "Bowser", "Yoshi"]:
            self.experiment = "P035"
        elif self.subject in ["Hendrix", "Zappa", "Joplin", "Sting",
                         "Jagger", "Iggy", "Evaristo", "Kurt", "Bowie"]:
            self.experiment = "P003e"
        else:
            self.experiment = "NA"
            
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
            
        self.prev_reinforcers_earned = "NA"
        self.P033_phase = "P033a-StainedGlass"

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
        
        # # Remove lines from drawing (can add back in with keybound command)
        # self.toggleLines("event")
        self.coverState = False
        self.firstTime = True
        self.paintButtonPressed = False
        self.colorButtonPressed = False
        self.lastTwoPlacements = []
        self.random_placement_index = "NA"
        self.visible_paint_button_id = None
        self.visible_color_button_id = None
        
    def get_random_placement(self):
        # Generate the new placement
        if len(self.lastTwoPlacements) < 2:
            new_placement = randint(0, 1)
        else:
            if self.lastTwoPlacements[-1] == self.lastTwoPlacements[-2]:
                # If the last two are the same, flip the next value
                new_placement = 1 - self.lastTwoPlacements[-1]
            else:
                # Otherwise, randomly choose again
                new_placement = randint(0, 1)
        
        # Update the last two placements
        self.lastTwoPlacements.append(new_placement)
        if len(self.lastTwoPlacements) > 2:
            self.lastTwoPlacements.pop(0)  # Keep only the last two values
    
        return new_placement
        
    # covers canvas
    def canvasCover(self):
        return
        self.coverState = True
        self.colorButtonPressed = False
        # data point for timing when exactly the cover is presented
        self.write_data(None, "canvas_covered")
        self.x, self.y, self.draw = None, None, False
        # Make a rectangle to literally cover the canvas
        self.cover_id = self.canvas.create_rectangle(0, 0, self.width,
                       self.height, fill="black", outline="black", tag="cover")
                                 
        self.random_placement_index = self.get_random_placement() # randomizing button position
        
        if self.random_placement_index:
            # print(self.random_placement_index)
            # Condition: Paint Button On the Right, Color Button on the Left
            
            # PAINT BUTTON
            # Define visible triangle coordinates
            x11, y11 = self.width - 200, self.height - 200 # top
            x12, y12 = self.width - 125, self.height - 100 # right
            x13, y13 = self.width - 275, self.height - 100 # left

            # Draw the visible triangle
            self.visible_paint_button_id = self.canvas.create_polygon(x11, y11, 
                                    x12, y12, x13, y13, fill="pale violet red")
            
            # Define invisible response field
            #larger_x11, larger_y11 = self.width - 200, self.height - 250
            #larger_x12, larger_y12 = self.width - 75, self.height - 75
            #larger_x13, larger_y13 = self.width - 325, self.height - 75
            
            # Draw the invisible response field
            #self.button_id = self.canvas.create_polygon(larger_x11, larger_y11,
                                #larger_x12, larger_y12, larger_x13, larger_y13,
                                #outline="", fill="", tag="paint_button")
                                
            x1_center = self.width - 200
            y1_center = self.height - 130
            radius = 100
            
            # Top-left corner
            x0 = x1_center - radius
            y0 = y1_center - radius
            
            # Bottom-right corner
            x1 = x1_center + radius
            y1 = y1_center + radius
            
            # Create the circle
            self.invisible_paint_button_id = self.canvas.create_oval(x0, y0, x1, y1, fill="", outline="", tag="paint_button")

            # COLORED BACKGROUND BUTTON
            # Define visible square coordinates
            x21, y21 = 125, self.height - 200 # buttom-left
            x22, y22 = 225, self.height - 200 # buttom-right
            x23, y23 = 125, self.height - 100 # top-left
            x24, y24 = 225, self.height - 100 # top-right
            
            # Draw the visible square
            self.visible_color_button_id = self.canvas.create_polygon(x21, y21, x22,
                              y22, x24, y24, x23, y23, fill="olivedrab")
            
            x2_center = 175
            y2_center = self.height - 150
            radius = 100
            
            # Top-left corner
            x2 = x2_center - radius
            y2 = y2_center - radius
            
            # Bottom-right corner
            x3 = x2_center + radius
            y3 = y2_center + radius
            
            # Create the circle
            self.invisible_color_button_id = self.canvas.create_oval(x2, y2, x3, y3, fill="", outline="", tag="color_button")

        else:
            # Condition: Paint Button On Left, Color Button on the Right
            
            # PAINT BUTTON
            # Define visible square coordinates
            x11, y11 = 200, self.height - 200 # top
            x12, y12 = 125, self.height - 100 # left
            x13, y13 = 275, self.height - 100 # right

            # Draw the visible triangle
            self.visible_paint_button_id = self.canvas.create_polygon(x11, y11, 
                                    x12, y12, x13, y13, fill="pale violet red")
            
            x1_center = 200
            y1_center = self.height - 130
            radius = 100
            
            # Top-left corner
            x0 = x1_center - radius
            y0 = y1_center - radius
            
            # Bottom-right corner
            x1 = x1_center + radius
            y1 = y1_center + radius
            
            # Create the circle
            self.invisible_paint_button_id = self.canvas.create_oval(x0, y0, x1, y1, fill="", outline="", tag="paint_button")
            
            # COLORED BACKGROUND BUTTON
            # Define visible square coordinates
            x21, y21 = self.width - 125, self.height - 200 # top-right
            x22, y22 = self.width - 225, self.height - 200 # top-left
            x23, y23 = self.width - 125, self.height - 100 # buttom-right
            x24, y24 = self.width - 225, self.height - 100 # buttom-left
            
            # Draw the visible square
            self.visible_color_button_id = self.canvas.create_polygon(x21, y21, x22,
                              y22, x24, y24, x23, y23, fill="olivedrab")
            
            x2_center = self.width - 175
            y2_center = self.height - 150
            radius = 100
            
            # Top-left corner
            x2 = x2_center - radius
            y2 = y2_center - radius
            
            # Bottom-right corner
            x3 = x2_center + radius
            y3 = y2_center + radius
            
            # Create the circle
            self.invisible_color_button_id = self.canvas.create_oval(x2, y2, x3, y3, fill="", outline="", tag="color_button")
            
        # Next, build a triangular button
        # This is the function tied to button
        def coverToPaint(event):
            # Delete cover and button
            self.write_data(event, "paint_button_pressed")
            self.paint_button_peck_counter += 1
            print(f"\n{'*'*30} Effort {self.paint_button_peck_counter + self.color_button_peck_counter} begins (P{self.paint_button_peck_counter}C{self.color_button_peck_counter}) {'*'*30}") 
            self.delete_items()
            # Bind our painting tools
            #bindKeys()
            self.coverState = False
            self.paintButtonPressed = True
            # Last, set up a timer for the next cover
            self.root.after(30 * 1000,
                            self.canvasCover)
        
        self.canvas.tag_bind("paint_button",
                             "<Button-1>",
                             lambda event: coverToPaint(event))
        
        def coverToColor(event):
            # Delete cover and button
            self.write_data(event, "color_button_pressed")
            self.color_button_peck_counter += 1
            print(f"\n{'*'*30} Effort {self.paint_button_peck_counter + self.color_button_peck_counter} begins (P{self.paint_button_peck_counter}C{self.color_button_peck_counter}) {'*'*30}") 
            self.delete_items()
            # Bind our painting tools
            #bindKeys()
            self.coverState = False
            self.colorButtonPressed = True
 
            # Last, set up a timer for the next cover
            self.root.after(30 * 1000,
                            self.canvasCover)
            
         
        self.canvas.tag_bind("color_button",
                             "<Button-1>",
                             lambda event: coverToColor(event))
        
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
        
        # P033a runs as open-ended stained glass drawing. The canvas is never
        # covered on a timer, so pigeons can continue drawing for the session.
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
        if self.coverState:
            self.write_data(event, "cover_peck")
        elif self.paintButtonPressed:
            self.paintButtonPressed = False
            self.canvas.delete("background")
        elif self.colorButtonPressed:
            self.write_data(event, "color_peck")
            # Generate a random color
            random_color = "#{:06x}".format(randint(0, 0xFFFFFF))
        
            # Delete any existing polygons with the tag "background"
            self.canvas.delete("background")
        
            # Draw a new polygon with the random color
            self.canvas.create_rectangle(0, 0, self.width, self.height,
                          fill=random_color, outline="black", tag="background")
            
        else:
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
        if self.coverState or self.colorButtonPressed:
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
            event_type = "Session_End"
        if x is None:
            x = "NA"
        if y is None:
            y = "NA"
            
        print(f"{event_type:>24} | x: {x: ^3} y: {y:^3} | {str(datetime.now() - self.start_time)} | nPoly: {len(self.polygons) - 1}")
        
        self.session_data_frame.append([
            event_type,
            str(datetime.now() - self.start_time), # SessionTime as datetime object
            str(datetime.now() - self.previous_response), # IRI
            x, # X coordinate of a peck
            y, # Y coordinate of a peck
            self.PrevX, # Previous x coordinate
            self.PrevY, # Previous y coordinate
            line_length,
            #outcome,
            len(self.polygons) - 1, # Number of polygons w/o background (?)
            self.dot_counter, # Number of points
            len(self.lineIds) - 4, # Number of lines
            self.color_button_peck_counter + self.paint_button_peck_counter,
            self.paint_button_peck_counter,
            self.color_button_peck_counter,
            self.random_placement_index,
            self.background_color,
            self.start_time,
            self.experiment,
            self.P033_phase,
            self.prev_reinforcers_earned,
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
            "EventType", "SessionTime", "IRI", "X1","Y1","PrevX","PrevY", "SizeOfLine", 
              "NPolygons","NDots", "NLines", "Efforts", "PaintButtonPeck", "ColorButtonPeck",
             "Placement", "BackgroundColor","StartTime", "Experiment", "P033_Phase",
             "PrevReinforcersEarned", "BoxNumber",  "Subject",  "Date"
            ]

    def delete_items(self):
        if self.cover_id is not None:
            self.canvas.delete(self.cover_id)
            self.cover_id = None
        if self.visible_paint_button_id is not None or self.visible_color_button_id is not None:
            self.canvas.delete(self.invisible_paint_button_id)
            self.invisible_paint_button_id = None
            self.canvas.delete(self.invisible_color_button_id)
            self.invisible_color_button_id = None
            self.canvas.delete(self.visible_paint_button_id)
            self.visible_paint_button_id = None
            self.canvas.delete(self.visible_color_button_id)
            self.visible_color_button_id = None
            
    def write_comp_data(self):
        # The following function creates a .csv data document. It is once
        # the session finishes (SessionEnded). If the first time the 
        # function is called, it will produce a new .csv out of the
        # session_data_matrix variable, named after the subject, date, and
        # training phase.
        self.write_data(None, None) # Writes end of session row to df
        myFile_loc = f"{data_folder_directory}/{self.subject}/P033a_{self.subject}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_StainedGlass.csv" # location of written .csv
        
        # This loop writes the data in the matrix to the .csv              
        edit_myFile = open(myFile_loc, 'w', newline='')
        with edit_myFile as myFile:
            w = writer(myFile, quoting=QUOTE_MINIMAL)
            w.writerows(self.session_data_frame) # Write all event/trial data 
            print(f"\n- Data file written to {myFile_loc}")
            
    def exit_program(self, event):
        self.write_comp_data()
        print("Escape key pressed")
        # Remove lines from drawing (can add back in with keybound command)
        self.toggleLines("event")
        print("- Lines removed from Canvas")
        #self.write_comp_data()
        self.delete_items()
        self.canvas.delete("background")
        self.save_file()
        self.canvas.destroy()
        self.root.after(1, self.root.destroy())

    # This builds a popup save_file window and saves as a .eps file
    def save_file(self):
        list_of_options = ["Masterpiece", "Artwork", "Impressions", "Portrait",
                           "Future NFT", "Money-Maker", "Handiwork",
                           "Magnum Opus", "Craft", "Thesis Project",
                           "Life's Purpose"]
        rand_select_index = randint(0, len(list_of_options) - 1)
        rand_select = list_of_options[rand_select_index]
        if messagebox.askyesno("Save?", f"Save {self.subject}'s {rand_select}? \n (lines will be removed)"):
            now = datetime.now()
            file_name = f"{self.save_directory}/{self.subject}_{now.strftime('%m-%d-%Y_Time-%H-%M-%S')}_stained_glass_3"
            filepng = file_name + ".png"
    
            if not path.exists(filepng) or messagebox.askyesno("File already exists", "Overwrite?"):
                fileps = file_name + ".eps"
    
                self.canvas.postscript(file=fileps)
                Image.open(fileps)
                #img.save(filepng, 'png')
                #os.remove(fileps)
    
                messagebox.showinfo("File Save", "File saved!")
            else:
                messagebox.showwarning("File Save", "File not saved!")
        

class ExperimenterControlPanel(object):
    def __init__(self):
        self.control_window = Tk()
        self.control_window.title("P033a Control Panel")

        self.pigeon_name_list = [
            "Shy Guy",
            "Darwin",
            "Bon Jovi",
            "Athena",
            "Hendrix",
            "Kurt",
            "Cousteau",
            "Peach",
            "Hawthorne",
            "Wario",
            "Yoshi",
            "Iggy",
            "Mario",
            "Joplin",
            "Wenchang",
            "Bowser",
        ]
        self.pigeon_name_list.sort()

        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        self.subject_ID_menu = OptionMenu(
            self.control_window,
            self.subject_ID_variable,
            *self.pigeon_name_list,
            command=self.set_pigeon_ID,
        )
        self.subject_ID_menu.pack()

        self.start_button = Button(
            self.control_window,
            text="Start program",
            bg="green2",
            command=self.build_chamber_screen,
        )
        self.start_button.pack()

        self.control_window.mainloop()

    def set_pigeon_ID(self, pigeon_name):
        try:
            subject_directory = path.join(data_folder_directory, pigeon_name)
            if not path.isdir(subject_directory):
                mkdir(subject_directory)
                print("\n ** NEW DATA FOLDER FOR %s CREATED **" % pigeon_name.upper())
        except FileExistsError:
            print(f"DATA FOLDER FOR {pigeon_name.upper()} EXISTS")

    def build_chamber_screen(self):
        if self.subject_ID_variable.get() in self.pigeon_name_list:
            print("Operant Box Screen Built")
            self.start_button.config(state="disabled")
            chamber_window = Toplevel(self.control_window)
            chamber_window.title("P033a Stained Glass")
            self.paint = Paint(chamber_window, self.subject_ID_variable.get())
            chamber_window.bind("<ButtonPress-1>", self.paint.onLeftButton)
            chamber_window.bind("<ButtonPress-2>", self.paint.onRightButton)
            chamber_window.bind("<Motion>", self.paint.onMouseMove)
            chamber_window.bind("<space>", self.paint.toggleDemo)
            chamber_window.bind("l", self.paint.toggleLines)
        else:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")


def main(artist_name=None):
    global root, paint
    print("(l) toggle lines")
    print("(spacebar) toggle labels")
    print("left mouse button to draw")
    print("right mouse button to cancel draw")
    if artist_name is None:
        ExperimenterControlPanel()
        return
    # Setup Canvas
    root = Tk()
    root.title("Paint Program with Polygon Detection")
    root.resizable(False, False)
    paint = Paint(root, artist_name) # Pass artist name to program
    #bindKeys(paint)
    root.bind("<ButtonPress-1>", paint.onLeftButton)
    root.bind("<ButtonPress-2>", paint.onRightButton)
    root.bind("<Motion>", paint.onMouseMove)
    root.bind("<space>", paint.toggleDemo)
    root.bind("l", paint.toggleLines)

    root.mainloop()
    
#def bindKeys(p):
    #global root
    # Bind out keys...
    #root.bind("<ButtonPress-1>", paint.onLeftButton)
    #root.bind("<ButtonPress-2>", paint.onRightButton)
    #root.bind("<Motion>", paint.onMouseMove)
    #root.bind("<space>", paint.toggleDemo)
    #root.bind("l", paint.toggleLines)

#def ubbindKeys():
    #global root
    # Bind out keys...
    #root.unbind("<ButtonPress-1>")
    #root.unbind("<ButtonPress-2>")
   # root.unbind("<Motion>")
   # root.unbind("<space>")
    #root.unbind("l")
    

# This runs at the start
if __name__ == "__main__":
    main()
