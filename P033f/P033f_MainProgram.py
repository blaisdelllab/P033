import tkinter as tk
import random
import time
import math
import csv
from datetime import datetime, date
from PIL import Image, ImageTk
from os import path, getcwd, mkdir
from screeninfo import get_monitors

# With Pillow 11.1, use the new resampling API:
resample_filter = Image.Resampling.LANCZOS

class PigeonPainter:
    def __init__(self, root, subject, target_path):
        """Revised code to hide the main buttons only one time right after the first round of choices
           (after the color is picked) and then show them after the first shape is drawn.
           In subsequent rounds the buttons always remain visible.
           Also, a coordinate adjustment variable is introduced.
        """
        if path.expanduser('~').split("/")[2] == "blaisdelllab":
            operant_box_version = True
            print("*** Running operant box version *** \n")
            self.save_directory = str(path.expanduser('~')) + "/Desktop/Data/Pigeon_Art"
            self.data_folder_directory = str(path.expanduser('~')) + "/Desktop/Data/P033_data/P033f_ThreeChoice_Data"
        else:
            operant_box_version = False
            print("*** Running test version (no hardware) *** \n")
            self.save_directory = getcwd() + "/saved_art/"
            self.data_folder_directory = getcwd() + "/P033f_ThreeChoice_Data"
            try:
                if not path.isdir(self.save_directory):
                    mkdir(path.join(self.save_directory))
            except FileExistsError:
                print("Saved art folder exists")
    
        # Create macro data folder if it does not exist
        try:
            if not path.isdir(self.data_folder_directory):
                mkdir(path.join(self.data_folder_directory))
                print("\n ** NEW DATA FOLDER CREATED **")
        except FileExistsError:
            print("Data folder exists.")
    
        # Data subject file save directory
        try:
            if not path.isdir(self.data_folder_directory + subject):
                mkdir(path.join(self.data_folder_directory, subject))
                print("\n ** NEW DATA FOLDER FOR %s CREATED **" % subject.upper())
        except FileExistsError:
            pass
    
        self.root = root
        self.root.title("PigeonPainter - Separate Panel & Paint Canvases")
    
        # Close on Escape
        self.root.bind('<Escape>', self.on_close)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
        # -------------------------------
        #   BASIC SESSION INFO
        # -------------------------------
        self.start_time = time.time()
        self.session_start_datetime = datetime.now()
        self.prev_event_time = self.start_time
        self.subject = subject
        self.target_path = target_path
        self.experiment = "P033e"
        self.box_number = "NA"
        self.date_str = date.today()
    
        # Data logging store
        self.data_log = []
    
        # T, S, C selections
        self.selected_thickness = None
        self.selected_shape = None
        self.selected_color = None
    
        # Counting shapes
        self.n_shapes = 0
    
        # For logging coords
        self.prev_x = None
        self.prev_y = None
    
        # State flags
        self.canvas_active = False
        self.sample_shape_id = None
        self.choices_open = False
        self.waiting_for_second_peck = False
        self.first_peck = None
    
        # New flags for controlling first-round behavior
        self.first_round_done = False      # becomes True once the very first shape is drawn
        self.first_sample_shown = False      # sample shape is drawn only once
    
        # Probability for "surprise" fill
        self.SURPRISE_PROB = 0.05
    
        # 3s cooldown after T,S,C main button presses
        self.cooldown = False
    
        # For tracking user responses
        self.NDots = 0
        self.NChoice = 0
    
        # We will show bricks only AFTER T/S/C are all chosen
        self.bricks_shown = False
    
        # Panel width
        self.panel_width = 300
    
        # Full screen
        self.screen_width = 1024 
        self.screen_height = 768
    
        # The original offset for T,S,C
        self.vertical_offset = 30
    
        # NEW: Coordinate adjustment variable (adjustable)
        self.coord_adjust = -100
    
        # NEW: Additional shifts to top/middle/bottom so they are closer
        self.top_button_shift = 80
        self.middle_button_shift = 0
        self.bottom_button_shift = -80
    
        # =========== LOAD IMAGES (relative paths) ===========
        self.bricks_img = None
        try:
            bg_raw = Image.open(self.target_path + "bricks.jpg")  # relative path
            bg_resized = bg_raw.resize(
                (self.screen_width - self.panel_width, self.screen_height),
                resample_filter
            )
            self.bricks_img = ImageTk.PhotoImage(bg_resized)
            print("[DEBUG] bricks loaded but not displayed yet.")
        except Exception as e:
            print(f"[DEBUG] Could not load bricks: {e}")
            self.bricks_img = None
    
        # We'll enlarge T/S/C from 80x80 to ~104x104 (~30% bigger)
        self.stim1_img = self.stim2_img = self.stim3_img = None
        try:
            stim1 = Image.open(self.target_path + "Stimulus1.jpg")
            stim1 = stim1.resize((104,104), resample_filter)
            self.stim1_img = ImageTk.PhotoImage(stim1)
    
            stim2 = Image.open(self.target_path + "Stimulus2.jpg")
            stim2 = stim2.resize((104,104), resample_filter)
            self.stim2_img = ImageTk.PhotoImage(stim2)
    
            stim3 = Image.open(self.target_path + "Stimulus3.jpg")
            stim3 = stim3.resize((104,104), resample_filter)
            self.stim3_img = ImageTk.PhotoImage(stim3)
            print("[DEBUG] T,S,C images loaded (30% bigger).")
        except Exception as e:
            print(f"[DEBUG] Could not load T/S/C images: {e}")
    
        # Panel canvas for T,S,C
        self.width, self.height = 1024, 768
        if operant_box_version:
            monitors = get_monitors()
            if len(monitors) > 1:
                secondary_monitor = monitors[1]
                x_offset = secondary_monitor.x
            else:
                x_offset = self.root.winfo_screenwidth()
            self.root.geometry(f"{self.width}x{self.height}+{x_offset}+0")
            self.root.attributes('-fullscreen', True)
    
            self.panel_canvas = tk.Canvas(self.root,
                                          width=self.panel_width,
                                          height=self.screen_height,
                                          bg="white",
                                          highlightthickness=0)
            self.panel_canvas.place(x=0, y=0)
    
            self.paint_width = self.screen_width - self.panel_width
            self.paint_height = self.screen_height
            self.paint_canvas = tk.Canvas(self.root,
                                          width=self.paint_width,
                                          height=self.paint_height,
                                          highlightthickness=0,
                                          bg="white")
            self.paint_canvas.place(x=self.panel_width, y=0)
    
        else:
            self.root.geometry(f"{self.width}x{self.height}")
            self.panel_canvas = tk.Canvas(self.root,
                                          width=self.panel_width,
                                          height=self.screen_height,
                                          bg="white",
                                          highlightthickness=0)
            self.panel_canvas.place(x=0, y=0)
    
            self.paint_width = self.screen_width - self.panel_width
            self.paint_height = self.screen_height
            self.paint_canvas = tk.Canvas(self.root, width=self.paint_width, height=self.paint_height,
                                          highlightthickness=0, bg="white")
            self.paint_canvas.place(x=self.panel_width, y=0)
    
        # Define vertical spacing for T,S,C in panel_canvas
        slot_count = 4
        slot_height = self.screen_height / slot_count
    
        # Update the centers by subtracting the coordinate adjustment
        self.T_center = (
            self.panel_width // 2,
            int(slot_height * 1 - self.vertical_offset + self.top_button_shift - self.coord_adjust)
        )
        self.S_center = (
            self.panel_width // 2,
            int(slot_height * 2 - self.vertical_offset + self.middle_button_shift - self.coord_adjust)
        )
        self.C_center = (
            self.panel_width // 2,
            int(slot_height * 3 - self.vertical_offset + self.bottom_button_shift - self.coord_adjust)
        )
    
        self.panel_choice_items = []
    
        # Create T button initially
        self.create_T_button()
    
        # Binds:
        self.panel_canvas.bind("<Button-1>", self.panel_on_click)
        self.paint_canvas.bind("<Button-1>", self.paint_on_click)
    
    # -----------------------------------------------------------
    #  Logging and Saving
    # -----------------------------------------------------------
    def log_event(self, event_label, x=None, y=None, choice_location=None):
        current_time = time.time()
        session_time = current_time - self.start_time
        iri = current_time - self.prev_event_time
        prev_x = self.prev_x if self.prev_x is not None else "NA"
        prev_y = self.prev_y if self.prev_y is not None else "NA"
    
        row = {
            "SessionTime": session_time,
            "IRI": iri,
            "X1": x if x is not None else "NA",
            "Y1": y if y is not None else "NA",
            "PrevX": prev_x,
            "PrevY": prev_y,
            "Event": event_label,
            "ChoiceLocation": choice_location if choice_location else "NA",
            "NDots": self.NDots,
            "NChoice": self.NChoice,
            "NShapes": self.n_shapes,
            "Shape": self.selected_shape if self.selected_shape else "NA",
            "Thickness": self.selected_thickness if self.selected_thickness else "NA",
            "Color": self.selected_color if self.selected_color else "NA",
            "StartTime": str(self.session_start_datetime),
            "Experiment": self.experiment,
            "BoxNumber": self.box_number,
            "Subject": self.subject,
            "Date": str(self.date_str),
            "SurpriseProb": self.SURPRISE_PROB
        }
        self.data_log.append(row)
        self.prev_event_time = current_time
        if x is not None and y is not None:
            self.prev_x = x
            self.prev_y = y
    
    def save_data(self):
        fieldnames = [
            "SessionTime", "IRI", "X1", "Y1", "PrevX", "PrevY", "Event",
            "ChoiceLocation",
            "NDots", "NChoice", "NShapes", "Shape", "Thickness", "Color",
            "StartTime", "Experiment", "BoxNumber", "Subject", "Date",
            "SurpriseProb"
        ]
        filename = f"{self.data_folder_directory}/{self.subject}/P033f_3choice_pigeon_painter_data_{self.subject}_{self.session_start_datetime.strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.data_log)
            print(f"[DEBUG] data saved => {filename}")
        except Exception as e:
            print(f"[DEBUG] error saving data => {e}")
    
    # -----------------------------------------------------------
    #  MAIN BUTTONS T, S, C on the panel
    # -----------------------------------------------------------
    def create_T_button(self):
        cx, cy = self.T_center
        r = 52
        invis_r = int(r * 1.5)
        self.panel_canvas.create_oval(cx - invis_r, cy - invis_r, cx + invis_r, cy + invis_r,
                                      fill="", outline="", width=0,
                                      tags=("T_invisible", "rf_invisible", "top_choice"))
        if self.stim1_img:
            self.T_button_id = self.panel_canvas.create_image(cx, cy, anchor="center",
                                                              image=self.stim1_img,
                                                              tags=("T_button", "top_choice"))
        else:
            self.T_button_id = self.panel_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                                             fill="white", outline="black", width=2,
                                                             tags=("T_button", "top_choice"))
    
    def create_S_button(self):
        cx, cy = self.S_center
        r = 52
        invis_r = int(r * 1.5)
        self.panel_canvas.create_oval(cx - invis_r, cy - invis_r, cx + invis_r, cy + invis_r,
                                      fill="", outline="", width=0,
                                      tags=("S_invisible", "rf_invisible", "middle_choice"))
        if self.stim2_img:
            self.S_button_id = self.panel_canvas.create_image(cx, cy, anchor="center",
                                                              image=self.stim2_img,
                                                              tags=("S_button", "middle_choice"))
        else:
            self.S_button_id = self.panel_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                                             fill="white", outline="black", width=2,
                                                             tags=("S_button", "middle_choice"))
    
    def create_C_button(self):
        cx, cy = self.C_center
        r = 52
        invis_r = int(r * 1.5)
        self.panel_canvas.create_oval(cx - invis_r, cy - invis_r, cx + invis_r, cy + invis_r,
                                      fill="", outline="", width=0,
                                      tags=("C_invisible", "rf_invisible", "bottom_choice"))
        if self.stim3_img:
            self.C_button_id = self.panel_canvas.create_image(cx, cy, anchor="center",
                                                              image=self.stim3_img,
                                                              tags=("C_button", "bottom_choice"))
        else:
            self.C_button_id = self.panel_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                                             fill="white", outline="black", width=2,
                                                             tags=("C_button", "bottom_choice"))
    
    def show_all_three_buttons(self):
        self.create_T_button()
        self.create_S_button()
        self.create_C_button()
    
    def hide_all_main_buttons(self):
        self.panel_canvas.delete("T_button")
        self.panel_canvas.delete("T_invisible")
        self.panel_canvas.delete("S_button")
        self.panel_canvas.delete("S_invisible")
        self.panel_canvas.delete("C_button")
        self.panel_canvas.delete("C_invisible")
    
    # -----------------------------------------------------------
    #  Panel On-Click
    # -----------------------------------------------------------
    def panel_on_click(self, event):
        x, y = event.x, event.y
    
        if self.cooldown:
            self.log_event("cooldown_click_ignored_panel", x, y, choice_location="NA")
            return
    
        items = self.panel_canvas.find_overlapping(x, y, x, y)
        found_something = False
    
        def get_button_location(tags):
            if "top_choice" in tags:
                return "top"
            elif "middle_choice" in tags:
                return "middle"
            elif "bottom_choice" in tags:
                return "bottom"
            return "NA"
    
        for it in items:
            tags = self.panel_canvas.gettags(it)
            loc = get_button_location(tags)
    
            if "T_invisible" in tags:
                self.NChoice += 1
                self.hide_all_main_buttons()
                self.log_event("T_button_press", x, y, choice_location=loc)
                self.show_thickness_choices()
                self.start_cooldown()
                found_something = True
                break
            elif "S_invisible" in tags:
                self.NChoice += 1
                self.hide_all_main_buttons()
                self.log_event("S_button_press", x, y, choice_location=loc)
                self.show_shape_choices()
                self.start_cooldown()
                found_something = True
                break
            elif "C_invisible" in tags:
                self.NChoice += 1
                self.hide_all_main_buttons()
                self.log_event("C_button_press", x, y, choice_location=loc)
                self.show_color_choices()
                self.start_cooldown()
                found_something = True
                break
            elif "panel_choice" in tags:
                choice_label = None
                for t in tags:
                    if t in ["thin", "middle", "thick",
                             "triangle", "circle", "square",
                             "lime", "cyan", "magenta", "red", "blue", "green"]:
                        choice_label = t
                        break
                if choice_label:
                    self.handle_panel_choice(choice_label, x, y, loc)
                    found_something = True
                    break
    
        if not found_something:
            self.log_event("panel_background_peck", x, y, choice_location="NA")
    
    # -----------------------------------------------------------
    #  Paint On-Click
    # -----------------------------------------------------------
    def paint_on_click(self, event):
        x, y = event.x, event.y
    
        if self.choices_open:
            self.log_event("canvas_inactive_peck", x, y, choice_location="NA")
            return
    
        if not self.canvas_active:
            self.log_event("canvas_inactive_peck", x, y, choice_location="NA")
            return
    
        self.NDots += 1
        if not self.waiting_for_second_peck:
            self.first_peck = (x, y)
            self.waiting_for_second_peck = True
            self.log_event("shape_first_peck", x, y, choice_location="NA")
            # In the very first round, do not hide buttons on subsequent shape creation.
            if not self.first_round_done:
                self.hide_all_main_buttons()
        else:
            x1, y1 = self.first_peck
            x2, y2 = x, y
            self.log_event("shape_second_peck", x2, y2, choice_location="NA")
    
            if self.selected_shape == "circle":
                self.create_circle_2peck(x1, y1, x2, y2)
            elif self.selected_shape == "triangle":
                self.create_equilateral_2peck(x1, y1, x2, y2)
            elif self.selected_shape == "square":
                self.create_square_2peck(x1, y1, x2, y2)
    
            if self.sample_shape_id:
                self.paint_canvas.delete(self.sample_shape_id)
                self.sample_shape_id = None
    
            self.waiting_for_second_peck = False
            self.first_peck = None
    
            # For the first complete trial, re-show the buttons and mark round as done.
            if not self.first_round_done:
                self.show_all_three_buttons()
                self.first_round_done = True
            # In subsequent rounds, the buttons remain visible.
    
    # -----------------------------------------------------------
    #  Show Choices on the Panel with Updated Previews
    # -----------------------------------------------------------
    def show_thickness_choices(self):
        self.choices_open = True
        for it in self.panel_choice_items:
            self.panel_canvas.delete(it)
        self.panel_choice_items = []
    
        thick_list = [("thin", "thin_choice"),
                      ("middle", "middle_choice"),
                      ("thick", "thick_choice")]
        coords = [self.T_center, self.S_center, self.C_center]
        loc_tags = ["top_choice", "middle_choice", "bottom_choice"]
    
        for ((lbl, _), (cx, cy), loc_tag) in zip(thick_list, coords, loc_tags):
            invis_r = 52
            invis_id = self.panel_canvas.create_oval(cx - invis_r, cy - invis_r,
                                                     cx + invis_r, cy + invis_r,
                                                     fill="", outline="", width=0,
                                                     tags=("panel_choice", lbl, "rf_invisible", loc_tag))
            self.panel_choice_items.append(invis_id)
    
            if self.selected_shape is not None:
                candidate_thickness = {"thin": 2, "middle": 5, "thick": 8}[lbl]
                preview_color = self.selected_color if self.selected_color is not None else "black"
                if self.selected_shape == "circle":
                    r = 30
                    preview_id = self.panel_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                                               outline=preview_color, fill="",
                                                               width=candidate_thickness,
                                                               tags=("panel_choice", lbl, loc_tag))
                elif self.selected_shape == "triangle":
                    pts = [cx, cy - 30, cx - 26, cy + 22, cx + 26, cy + 22]
                    preview_id = self.panel_canvas.create_polygon(pts,
                                                                    outline=preview_color, fill="",
                                                                    width=candidate_thickness,
                                                                    tags=("panel_choice", lbl, loc_tag))
                elif self.selected_shape == "square":
                    half = 30
                    preview_id = self.panel_canvas.create_rectangle(cx - half, cy - half, cx + half, cy + half,
                                                                      outline=preview_color, fill="",
                                                                      width=candidate_thickness,
                                                                      tags=("panel_choice", lbl, loc_tag))
                self.panel_choice_items.append(preview_id)
            else:
                circ_r = 45
                circ_id = self.panel_canvas.create_oval(cx - circ_r, cy - circ_r,
                                                        cx + circ_r, cy + circ_r,
                                                        outline="black", fill="", width=2,
                                                        tags=("panel_choice", lbl, loc_tag))
                self.panel_choice_items.append(circ_id)
                thickness_map = {"thin": 2, "middle": 5, "thick": 8}
                lw = thickness_map[lbl]
                line_id = self.panel_canvas.create_line(cx - 30, cy, cx + 30, cy,
                                                        width=lw, fill='black',
                                                        tags=("panel_choice", lbl, loc_tag))
                self.panel_choice_items.append(line_id)
    
    def show_shape_choices(self):
        self.choices_open = True
        for it in self.panel_choice_items:
            self.panel_canvas.delete(it)
        self.panel_choice_items = []
    
        shape_list = [("triangle", "triangle_choice"),
                      ("circle", "circle_choice"),
                      ("square", "square_choice")]
        coords = [self.T_center, self.S_center, self.C_center]
        loc_tags = ["top_choice", "middle_choice", "bottom_choice"]
    
        for ((lbl, _), (cx, cy), loc_tag) in zip(shape_list, coords, loc_tags):
            invis_r = 52
            invis_id = self.panel_canvas.create_oval(cx - invis_r, cy - invis_r,
                                                     cx + invis_r, cy + invis_r,
                                                     fill="", outline="", width=0,
                                                     tags=("panel_choice", lbl, "rf_invisible", loc_tag))
            self.panel_choice_items.append(invis_id)
            if self.selected_thickness is not None:
                candidate_thickness = {"thin": 2, "middle": 5, "thick": 8}[self.selected_thickness]
                lw = candidate_thickness
                preview_color = self.selected_color if self.selected_color is not None else "black"
                if lbl == "triangle":
                    pts = [cx, cy - 45, cx - 39, cy + 33, cx + 39, cy + 33]
                    preview_id = self.panel_canvas.create_polygon(pts,
                                                                    outline=preview_color, fill="",
                                                                    width=lw,
                                                                    tags=("panel_choice", lbl, loc_tag))
                elif lbl == "circle":
                    preview_id = self.panel_canvas.create_oval(cx - 45, cy - 45,
                                                               cx + 45, cy + 45,
                                                               outline=preview_color, fill="",
                                                               width=lw,
                                                               tags=("panel_choice", lbl, loc_tag))
                elif lbl == "square":
                    preview_id = self.panel_canvas.create_rectangle(cx - 45, cy - 45,
                                                                    cx + 45, cy + 45,
                                                                    outline=preview_color, fill="",
                                                                    width=lw,
                                                                    tags=("panel_choice", lbl, loc_tag))
                self.panel_choice_items.append(preview_id)
            else:
                if lbl == "triangle":
                    pts = [cx, cy - 45, cx - 39, cy + 33, cx + 39, cy + 33]
                    preview_id = self.panel_canvas.create_polygon(pts,
                                                                    outline="black", fill="",
                                                                    width=2,
                                                                    tags=("panel_choice", lbl, loc_tag))
                elif lbl == "circle":
                    preview_id = self.panel_canvas.create_oval(cx - 45, cy - 45,
                                                               cx + 45, cy + 45,
                                                               outline="black", fill="",
                                                               width=2,
                                                               tags=("panel_choice", lbl, loc_tag))
                elif lbl == "square":
                    preview_id = self.panel_canvas.create_rectangle(cx - 45, cy - 45,
                                                                    cx + 45, cy + 45,
                                                                    outline="black", fill="",
                                                                    width=2,
                                                                    tags=("panel_choice", lbl, loc_tag))
                self.panel_choice_items.append(preview_id)
    
    def show_color_choices(self):
        self.choices_open = True
        for it in self.panel_choice_items:
            self.panel_canvas.delete(it)
        self.panel_choice_items = []
    
        color_list = [("lime", "lime_choice"),
                      ("cyan", "cyan_choice"),
                      ("magenta", "magenta_choice")]
        coords = [self.T_center, self.S_center, self.C_center]
        loc_tags = ["top_choice", "middle_choice", "bottom_choice"]
    
        for ((lbl, _), (cx, cy), loc_tag) in zip(color_list, coords, loc_tags):
            invis_r = 52
            invis_id = self.panel_canvas.create_oval(cx - invis_r, cy - invis_r,
                                                     cx + invis_r, cy + invis_r,
                                                     fill="", outline="", width=0,
                                                     tags=("panel_choice", lbl, "rf_invisible", loc_tag))
            self.panel_choice_items.append(invis_id)
            if self.selected_thickness is not None and self.selected_shape is not None:
                candidate_thickness = {"thin": 2, "middle": 5, "thick": 8}[self.selected_thickness]
                lw = candidate_thickness
                if self.selected_shape == "circle":
                    preview_id = self.panel_canvas.create_oval(cx - 45, cy - 45,
                                                               cx + 45, cy + 45,
                                                               outline=lbl, fill="",
                                                               width=lw,
                                                               tags=("panel_choice", lbl, loc_tag))
                elif self.selected_shape == "triangle":
                    pts = [cx, cy - 45, cx - 39, cy + 33, cx + 39, cy + 33]
                    preview_id = self.panel_canvas.create_polygon(pts,
                                                                    outline=lbl, fill="",
                                                                    width=lw,
                                                                    tags=("panel_choice", lbl, loc_tag))
                elif self.selected_shape == "square":
                    preview_id = self.panel_canvas.create_rectangle(cx - 45, cy - 45,
                                                                    cx + 45, cy + 45,
                                                                    outline=lbl, fill="",
                                                                    width=lw,
                                                                    tags=("panel_choice", lbl, loc_tag))
                self.panel_choice_items.append(preview_id)
            else:
                circ_id = self.panel_canvas.create_oval(cx - 45, cy - 45,
                                                        cx + 45, cy + 45,
                                                        outline="black", fill=lbl, width=2,
                                                        tags=("panel_choice", lbl, loc_tag))
                self.panel_choice_items.append(circ_id)
    
    def clear_panel_choices(self):
        for it in self.panel_choice_items:
            self.panel_canvas.delete(it)
        self.panel_choice_items = []
        self.choices_open = False
        self.start_cooldown()
    
    def handle_panel_choice(self, choice_label, x, y, choice_loc):
        if choice_label in ["thin", "middle", "thick"]:
            self.selected_thickness = choice_label
            emap = {"thin": "thin_choice", "middle": "middle_choice", "thick": "thick_choice"}
            self.log_event(emap[choice_label], x, y, choice_location=choice_loc)
            self.clear_panel_choices()
            if not self.selected_shape and not self.selected_color:
                self.create_S_button()
            else:
                if self.canvas_active:
                    self.show_all_three_buttons()
    
        elif choice_label in ["triangle", "circle", "square"]:
            self.selected_shape = choice_label
            emap = {"triangle": "triangle_choice", "circle": "circle_choice", "square": "square_choice"}
            self.log_event(emap[choice_label], x, y, choice_location=choice_loc)
            self.clear_panel_choices()
            if not self.selected_color:
                self.create_C_button()
            else:
                if self.canvas_active:
                    self.show_all_three_buttons()
    
        elif choice_label in ["lime", "cyan", "magenta", "red", "blue", "green"]:
            self.selected_color = choice_label
            emap = {"lime": "lime_choice", "cyan": "cyan_choice", "magenta": "magenta_choice",
                    "red": "red_choice", "blue": "blue_choice", "green": "green_choice"}
            self.log_event(emap[choice_label], x, y, choice_location=choice_loc)
            self.clear_panel_choices()
            if self.selected_thickness and self.selected_shape and self.selected_color:
                self.show_bricks_background()
                if not self.first_sample_shown:
                    self.create_sample_shape()
                    self.first_sample_shown = True
                self.canvas_active = True
                # In the first round, let the buttons remain hidden until the first shape is drawn.
                # In later rounds, immediately show them.
                if self.first_round_done:
                    self.show_all_three_buttons()
    
    def show_bricks_background(self):
        if not self.bricks_shown:
            if self.bricks_img:
                self.paint_canvas_bg = self.paint_canvas.create_image(0, 0, anchor="nw", image=self.bricks_img)
            else:
                self.paint_canvas.configure(bg="white")
            self.bricks_shown = True
    
    def create_circle_2peck(self, x1, y1, x2, y2):
        color = self.selected_color or "black"
        lw = self.get_line_width()
        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        r = dist / 2
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        if random.random() < self.SURPRISE_PROB:
            self.log_event("surprise_triggered")
            self.draw_rainbow_shape("circle", cx, cy, (x1, y1), (x2, y2))
        else:
            self.paint_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                          outline=color, fill="", width=lw)
        self.n_shapes += 1
    
    def create_equilateral_2peck(self, x1, y1, x2, y2):
        color = self.selected_color or "black"
        lw = self.get_line_width()
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        dx = x1 - mx
        dy = y1 - my
        def rotate(px, py, c, s):
            return px * c - py * s, px * s + py * c
        c120 = -0.5
        s120 = math.sqrt(3) / 2
        rxp, ryp = rotate(dx, dy, c120, s120)
        xp, yp = mx + rxp, my + ryp
        rxm, rym = rotate(dx, dy, c120, -s120)
        xm, ym = mx + rxm, my + rym
        if random.random() < self.SURPRISE_PROB:
            self.log_event("surprise_triggered")
            self.draw_rainbow_equilateral(x1, y1, xp, yp, xm, ym)
        else:
            self.paint_canvas.create_polygon(x1, y1, xp, yp, xm, ym,
                                             outline=color, fill="", width=lw)
        self.n_shapes += 1
    
    def create_square_2peck(self, topmidx, topmidy, botmidx, botmidy):
        color = self.selected_color or "black"
        lw = self.get_line_width()
        dx = botmidx - topmidx
        dy = botmidy - topmidy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return
        half = dist / 2
        perp_x = -dy / dist
        perp_y = dx / dist
        left_top_x = topmidx + perp_x * half
        left_top_y = topmidy + perp_y * half
        right_top_x = topmidx - perp_x * half
        right_top_y = topmidy - perp_y * half
        left_bot_x = botmidx + perp_x * half
        left_bot_y = botmidy + perp_y * half
        right_bot_x = botmidx - perp_x * half
        right_bot_y = botmidy - perp_y * half
        if random.random() < self.SURPRISE_PROB:
            self.log_event("surprise_triggered")
            self.draw_rainbow_shape("square",
                                    (topmidx + botmidx) / 2, (topmidy + botmidy) / 2,
                                    (topmidx, topmidy), (botmidx, botmidy))
        else:
            self.paint_canvas.create_polygon(
                left_top_x, left_top_y,
                right_top_x, right_top_y,
                right_bot_x, right_bot_y,
                left_bot_x, left_bot_y,
                outline=color, fill="", width=lw
            )
        self.n_shapes += 1
    
    def get_line_width(self):
        thickness_map = {"thin": 2, "middle": 5, "thick": 8}
        return thickness_map.get(self.selected_thickness, 2)
    
    def draw_rainbow_shape(self, shape_type, cx, cy, p1, p2):
        rainbow = ["red", "orange", "yellow", "green", "blue", "indigo", "purple"]
        steps = len(rainbow)
        if shape_type == "circle":
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.sqrt(dx * dx + dy * dy)
            r = dist / 2
            step_factor = (2.0 - 1.0) / steps
            for i, col in enumerate(rainbow):
                f = 2.0 - i * step_factor
                rr = r * f * 0.5
                self.paint_canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr,
                                              outline="", fill=col)
        elif shape_type == "square":
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.sqrt(dx * dx + dy * dy)
            half = dist / 2
            step_factor = (2.0 - 1.0) / steps
            for i, col in enumerate(rainbow):
                f = 2.0 - i * step_factor
                side = half * f
                self.paint_canvas.create_rectangle(cx - side, cy - side, cx + side, cy + side,
                                                   outline="", fill=col)
        else:
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.sqrt(dx * dx + dy * dy)
            r = dist / 2
            step_factor = (2.0 - 1.0) / steps
            for i, col in enumerate(rainbow):
                f = 2.0 - i * step_factor
                rr = r * f * 0.5
                self.paint_canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr,
                                              outline="", fill=col)
    
    def draw_rainbow_equilateral(self, ax, ay, bx, by, cx_, cy_):
        centroid_x = (ax + bx + cx_) / 3
        centroid_y = (ay + by + cy_) / 3
        rainbow = ["red", "orange", "yellow", "green", "blue", "indigo", "purple"]
        steps = len(rainbow)
        for i, col in enumerate(rainbow):
            factor = 1.0 - i * (1.0 / steps)
            Apx = centroid_x + (ax - centroid_x) * factor
            Apy = centroid_y + (ay - centroid_y) * factor
            Bpx = centroid_x + (bx - centroid_x) * factor
            Bpy = centroid_y + (by - centroid_y) * factor
            Cpx = centroid_x + (cx_ - centroid_x) * factor
            Cpy = centroid_y + (cy_ - centroid_y) * factor
            self.paint_canvas.create_polygon(Apx, Apy, Bpx, Bpy, Cpx, CPy,
                                             outline="", fill=col)
    
    def create_sample_shape(self):
        margin = 100
        rx = random.randint(margin, self.paint_width - margin)
        ry = random.randint(margin, self.paint_height - margin)
        shape_id = self.draw_sample_shape(rx, ry)
        self.sample_shape_id = shape_id
    
    def draw_sample_shape(self, x, y):
        if not (self.selected_shape and self.selected_thickness and self.selected_color):
            return None
        shape_type = self.selected_shape
        lw = self.get_line_width()
        color = self.selected_color
        if shape_type == "circle":
            r = 30
            return self.paint_canvas.create_oval(x - r, y - r, x + r, y + r,
                                                 outline=color, fill="", width=lw)
        elif shape_type == "triangle":
            pts = [x, y - 30, x - 26, y + 22, x + 26, y + 22]
            return self.paint_canvas.create_polygon(pts, outline=color, fill="", width=lw)
        elif shape_type == "square":
            half = 30
            return self.paint_canvas.create_rectangle(x - half, y - half, x + half, y + half,
                                                      outline=color, fill="", width=lw)
        return None
    
    def start_cooldown(self):
        self.cooldown = True
        self.root.after(3000, self.end_cooldown)
    
    def end_cooldown(self):
        self.cooldown = False
    
    def on_close(self, event=None):
        print("[DEBUG] on_close => saving data & canvas, then exiting.")
        try:
            self.save_data()
            self.save_paint_canvas_eps()
        except Exception as e:
            print(f"[DEBUG] error in on_close => {e}")
        finally:
            self.panel_canvas.destroy()
            self.paint_canvas.destroy()
            self.root.after(1, self.root.destroy())
    
    def save_paint_canvas_eps(self):
        file_eps = f"{self.save_directory}/{self.subject}_{datetime.now().strftime('%m-%d-%Y_Time-%H-%M-%S')}_P033f_three-choice-brick.eps"
        try:
            print("[DEBUG] generating EPS from paint_canvas only.")
            self.paint_canvas.postscript(file=file_eps, colormode='color')
            print(f"[DEBUG] paint_canvas saved to => {file_eps}")
        except Exception as e:
            print(f"[DEBUG] error saving paint canvas => {e}")
    
    @staticmethod
    def main():
        root = tk.Tk()
        app = PigeonPainter(root, subject="TEST", target_path="")
        root.mainloop()
    
def toplevel(subject, target_path):
    root = tk.Toplevel()
    app = PigeonPainter(root, subject=subject, target_path=target_path)
    root.mainloop()


if __name__ == "__main__":
    PigeonPainter.main()
