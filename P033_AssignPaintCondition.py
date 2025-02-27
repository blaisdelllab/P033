#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 14:05:07 2025

@author: cyruskirkman
"""

# Import libraries
from csv import DictReader
from tkinter import Toplevel, Canvas, Tk, Label, Button, \
     StringVar, OptionMenu, IntVar, Radiobutton
from sys import path as sys_path
from os import path as os_path
from pathlib import Path

# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It is changed automatically based on whether
# the program is running in operant boxes (True) or not (False). It is
# automatically set to True if the user is "blaisdelllab" (e.g., running
# on a rapberry pi) or False if not. The output of os_path.expanduser('~')
# should be "/home/blaisdelllab" on the RPis

if os_path.expanduser('~').split("/")[2] =="blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")

# Below is a dictionary containing the name of each experimental program (keys)
# and the directory location of the primary paint file that corresponds with
# each (values). Whenever a paint program is added, this dictionary needs to
# be updated.

paint_programs_location_dict = {
    'P033a: Genesis BW Project'                         : "/P033a", 
    'P033b: Random Color and Shape'                     : "/P033b",
    'P033c: Stained Glass'                              : "/P033c",
    'P033d: Stained Glass vs. Alter Background Choice'  : "/P033d",
    'P033e: Stained Glass vs. Food Choice'              : "/P033e",
    'P033f: Three-Choice Polygon Art'                   : "/P033f"
    }

# Other dynamic variables:
height_operantboxscreen = 768 # height of the experimental canvas screen
width_operantboxscreen = 1024 # width of the experimental canvas screen


# Define global functions
def return_P033_assignment(subject):
    #try:
    # Import CSV containing subject info
    P033_assignments_csv_path = str(Path(__file__).resolve().parent) + "Assignments/P033_Subject_Assignments.csv"
    with open(P033_assignments_csv_path, 'r', encoding='utf-8-sig') as f:
        dict_reader = DictReader(f) 
        P033_assignments_dict = list(dict_reader)
    
    # Only select one subject's data
    subject_info = "NA"
    for d in P033_assignments_dict:
        if d["Subject"] == subject:
            subject_info = d
            break
    
    # Extract subject data from dictionary:
    if subject_info == "NA":
        print("\nERROR: Cannot find subject's P033 art assignment")
    
    else:
        paint_or_not          = subject_info["PostSessionPaint"]
        paint_program_version = subject_info["P033Version"]
        # Get path from dict above
        for k in list(paint_programs_location_dict.keys()):
            if k.split(":")[0] == paint_program_version:
                paint_program_path = paint_programs_location_dict[k]

    # Return as vars
    return paint_or_not, paint_program_version, paint_program_path
    
    #except:
     #   print("\nError: Cannot assign P033 art program")
     
     
def call_specific_P003_program(subject, paint_or_not, paint_program_version,
                               paint_program_path):
    # Once the green "start program" button is pressed, then the mainscreen
    # object is created and pops up in a new window. It gets passed the
    # important inputs from the control panel (importantly the subject name
    # and condition)
    if paint_or_not == 0: # Black rectangle if pigeon shouldn't paint
        root = Toplevel()
        root.title("P033: Blank Screen")
        root.bind("<Escape>", root.destroy)
        mastercanvas = Canvas(root,
                              bg="black")
        mastercanvas.create_rectangle(0,0,
                                      height_operantboxscreen,
                                      width_operantboxscreen,
                                      fill = "black",
                                      outline = "black")
    else: # if pigeon should paint
        # Change directory to specific paint program's
        current_path = str(Path(__file__).resolve().parent)
        target_path  = current_path + paint_program_path + "/"
        sys_path.insert(0, target_path)
        if paint_program_version == "P033f":
            # Import project-specific code
            import P033f_MainProgram
            # Run code file w/ subject name
            P033f_MainProgram.toplevel(subject, target_path)
        else:
            # TO-DO make work for other programs
            print("Select ")
        

class ExperimenterControlPanel(object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self):
        # setup the root Tkinter window
        self.control_window = Tk()
        self.control_window.title("P033 Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = [
            'Mario', 'Thoth', 'Odin', 'Itzamna', 'Vonnegut',
            'Hawthorne',  'Durrell', 'Darwin', 'Wario', 'Waluigi', 'Athena',
            'Shy Guy', 'Bowser', 'Wenchang', 'Peach', 'Luigi', 'Yoshi',
            'Bon Jovi', 'Cousteau', 'Evaristo', 'Jubilee', 'Zappa', 'Sting',
            'Hendrix', 'Iggy', 'Kurt', 'Herriot', 'Bowie', 'Joplin', 'Jagger'
            ]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        
        
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list).pack()
        
        # Condition list
        self.P033_conditions_list = list(paint_programs_location_dict.keys())
        
        
        Label(self.control_window, text="P033 Condition:").pack()
        self.condition_variable = StringVar(self.control_window)
        self.condition_variable.set(self.P033_conditions_list[-1])
        self.condition_menu = OptionMenu(self.control_window,
                                         self.condition_variable,
                                         *self.P033_conditions_list).pack()
        


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
                                   command = self.gather_variables).pack()

        # This makes sure that the control panel remains onscreen until exited
        self.control_window.mainloop() # This loops around the CP object
        
    def gather_variables(self):
        # First, grab the relevant info from the control panel.
        subject                 = str(self.subject_ID_variable.get())
        paint_or_not            = 1 # Always paint if run from the control panel
        paint_program_path      = paint_programs_location_dict[str(self.condition_variable.get())]
        paint_program_version   = str(self.condition_variable.get()).split(":")[0] # Just grab "P033x"
        
        # Then, pipe it to the call_specific_P003_program() function
        call_specific_P003_program(subject, paint_or_not, paint_program_version, paint_program_path)

    
        
        
#%% Finally, this is the code that actually runs:

# If this specific code file is directly run, then we set up the control panel 
# as the main object, then collect info to run a chosen paint program
if __name__ == '__main__':
    cp = ExperimenterControlPanel()

# If called from an experimental program, simply run the prompt inside the
# experimental code.
else:
    # Grab data from meta data
    subject = "TEST"
    paint_or_not,  paint_program_version, paint_program_path = return_P033_assignment(subject)
    call_specific_P003_program(subject,
                               paint_or_not,
                               paint_program_version,
                               paint_program_path)
    






