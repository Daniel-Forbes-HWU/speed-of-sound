import csv
import datetime
import os
from typing import Literal
import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb
import tkinter.ttk as ttk

import serial
from serial.tools import list_ports

def find_pico_com() -> str:
    """Returns the com port str for the device with vendor id 11914 (assumed to be the same for all raspberry pi picos).\n
    Raises a ConnectionError if not device is found."""
    com = None
    for device in list_ports.comports():
        if device.vid == 11914:  # Check if its a pico
            com = device.name  # Recall com port
            break  # Only first device with this vid
    if com is None:
        raise ConnectionError("Cannot find serial device with vendor id of 11914...")
    
    return com
    

class SpeedOfSoundGUI:
    """A gui for communicating with a raspberry pi pico to run an experiment for calculating the speed of sound.\n
    Enables easy distance labelling and saving of acquired data!\n
    Distances are in cm, and times are in us"""
    def __init__(self, com_port:str|None=None):
        # Detect pico com port
        if com_port is None:
            try:
                com_port = find_pico_com()
            except ConnectionError:
                tkmb.showerror("Cannot connect to PICO", "Could not connect to Pico, \
                    \nCheck the USB connection and try restarting the device.")
                raise

        self.com_port = com_port

        # Attempt to connect to pico
        self.connect()

        self.root = tk.Tk()  # Create gui event loop
        self.root.title("Speed of Sound Experiment")  # Change title
        self.root.resizable(False, False)  # Disable resizing

        # Key bindings
        self.root.bind('<Return>', lambda _: self.measure(int(self.repetitions_var.get()), self.distance_var.get(), self.temperature_var.get()))
        self.root.bind("<Delete>", lambda _: self.delete_selected_data())

        # Close behaviour
        self.root.protocol("WM_DELETE_WINDOW", self.ask_close)

        self.create_gui_elements()

    def create_gui_elements(self):
        """Creates the gui's elements"""
        # Control Frame #########################
        self.control_frame = ttk.LabelFrame(self.root, text="Control")
        self.control_frame.grid(column=0, sticky="nsew", padx=10, pady=10)

        # Distance entry box
        ttk.Label(self.control_frame, text="Distance (cm):").grid(column=0, row=0)
        self.default_distance_text:str = "Enter Distance Here"
        self.distance_var = tk.StringVar(self.control_frame, self.default_distance_text)
        self.distance_entry = ttk.Entry(self.control_frame, textvariable=self.distance_var)
        self.distance_entry.grid(column=0, row=1)
        self.distance_entry.bind("<FocusIn>", lambda _: self.distance_entry.delete(0, 19))
        
        # Temperature entry box
        ttk.Label(self.control_frame, text="Temperature (°C):").grid(column=0, row=2)
        self.default_temperature_text:str = "Enter Temperature Here"
        self.temperature_var = tk.StringVar(self.control_frame, self.default_temperature_text)
        self.temperature_entry = ttk.Entry(self.control_frame, textvariable=self.temperature_var)
        self.temperature_entry.grid(column=0, row=3)
        self.temperature_entry.bind("<FocusIn>", lambda _: self.temperature_entry.delete(0, 22))

        ttk.Separator(self.control_frame, orient='horizontal').grid(row=4, padx=5, pady=10, sticky="nsew")

        # Repetitions entry
        ttk.Label(self.control_frame, text="Repetitions:").grid(column=0, row=5)
        self.repetitions_var = tk.StringVar(self.control_frame, "5")
        self.repetitions_entry = ttk.Spinbox(self.control_frame, from_=1, to=50, wrap=True, textvariable=self.repetitions_var)
        self.repetitions_entry.grid(column=0, row=6, sticky="nsew")

        # Control buttons
        self.measure_button = ttk.Button(
            self.control_frame,
            text="Measure",
            command=lambda:self.measure(
                int(self.repetitions_var.get()),
                self.distance_var.get(),
                self.temperature_var.get()
            )
        )
        self.measure_button.grid(column=0, row=7, sticky="nsew")

        self.reconnect_button = ttk.Button(self.control_frame, text="Reconnect", command=self.connect)
        self.reconnect_button.grid(column=0, row=8, sticky="nsew")
        #########################################

        # Data Frame ############################
        self.data_frame = ttk.LabelFrame(self.root, text="Data")
        self.data_frame.grid(column=1, row=0, sticky="nsew", padx=10, pady=10)

        # Data - Scrollable
        columns = ('#1', '#2', '#3')
        self.data_view = ttk.Treeview(self.data_frame, columns=columns, show='headings')
        
        # Name columns
        self.data_view.heading('#1', text='Temperature (°C)')
        self.data_view.heading('#2', text='Distance (cm)')
        self.data_view.heading('#3', text='Time (us)')
        
        # Place treeview in results window
        scrollbar = ttk.Scrollbar(self.data_frame, orient=tk.VERTICAL, command=self.data_view.yview)
        self.data_view.pack(side="left", fill="both")

        # Add a scrollbar
        self.data_view.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Data control buttons
        self.save_data_button = ttk.Button(self.data_frame, text="Save", command=self.save_data)
        self.save_data_button.pack(side=tk.BOTTOM)

        self.clear_data_button = ttk.Button(self.data_frame, text="Clear", command=self.clear_data)
        self.clear_data_button.pack(side=tk.BOTTOM)

        self.delete_data_button = ttk.Button(self.data_frame, text="Delete Selection", command=self.delete_selected_data)
        self.delete_data_button.pack(side=tk.BOTTOM)

        # Check for if current data has been saved
        self.data_saved: bool = True

        #########################################

    def measure(self, repetitions:int=1, distance_label:str="", temperature_label:str="") -> list[int]:
        """Instructs the pico to measure the time taken (in us) for a sound pressure wave from a speaker
        to travel to a microphone.\n
        Repetitions is the number of times to repeat the measurement.\n"""
        self.port.flushInput()
        
        # Instruct Pico to perform measurement 
        try:
            self.port.write((str(repetitions) + "\r\n").encode("utf-8"))
        except Exception as exc:
            tkmb.showerror("Could not communicate with controller", f"Failed to communicate with the controller, reset the controller and click the reconnect button.\
            \nIf this problem persists contact a lab demonstrator for help!")
            raise exc

        # Listen for response
        response:list[bytes] = []
        reads = 0
        while reads < repetitions + 1:
            read = self.port.readline()
            if read == b"":
                tkmb.showerror("Data read timeout", "The data request timed out, try pressing the red button on the microphone and restarting the controller.")
                raise TimeoutError("The data request timed out, try pressing the red button on the microphone and restarting the controller.")
            response.append(read)
            reads += 1

        # Cleanup response
        if distance_label == self.default_distance_text:
            distance_label = "Un-Labeled"
        if temperature_label == self.default_temperature_text:
            temperature_label = "Un-Labeled"
        times = [int(resp.decode("utf-8").strip("\r\n")) for resp in response[1:]]

        # Add data to dataset
        for time in times:
            self.data_view.insert("", "end", values=(temperature_label, distance_label, time))
        print(f"{temperature_label} °C, {distance_label} cm: \n",times)

        # Update saved check
        self.data_saved = False

        return times

    def save_data(self):
        """Saves the data currently in the data view to a user defined csv file.\n
        Default location is the desktop and default filename includes the current data and time"""
        # Desktop location
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')  

        # Current date and time as day_month_year-hours_minutes_seconds
        timetag = datetime.datetime.now().strftime("%d_%m_%y-%H_%M_%S")  
        
        default_filename = f"{timetag}_speed_of_sound"

        # Let user select save location
        filename: str = tkfd.asksaveasfilename(
            parent=self.root, 
            initialdir=desktop, 
            defaultextension=".csv", 
            initialfile=default_filename,
            filetypes=[("csv", "*.csv")]
            )
        if filename == "":
            print("No filename selected")
            tkmb.showerror("No filename", "No filename given...")
            return
        print(f"Saving as: \n{filename}")

        # Convert data for saving
        data = [self.data_view.item(index)["values"] for index in self.data_view.get_children()]

        try:  # Try to save
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f, delimiter=",")  # Create csv writer
                writer.writerow(("Temperature (°C)", "Distance (cm)", "Time Taken (us)"))  # Write header
                [writer.writerow(row) for row in data]  # Write data

        except Exception as exc:
            tkmb.showerror("Failed to save", f"Failed to save file to {filename}. Please try again.")
            raise exc

        self.data_saved = True
        
        print(f"Saved successfully")
        tkmb.showinfo("Saved Successfully!", f"Saved successfully to: \n{filename}")

    def delete_selected_data(self):
        """Removes the selected data from the program."""
        selected = self.data_view.selection()
        for sel in selected:
            self.data_view.delete(sel)

    def clear_data(self):
        """Deletes all data entries in the program."""
        response: Literal["yes","no"] = tkmb.askquestion("Are you sure?", "Do you really want to clear the data?")
        if response == "no":
            return

        # Clear all data from data_view
        for item in self.data_view.get_children():
            self.data_view.delete(item)
        
        # No data
        self.data_saved = True

    def run(self):
        """Runs the gui - BLOCKING"""
        self.root.mainloop()

    def connect(self):
        """Connects to the com port"""
        try:
            self.port = serial.Serial(port=self.com_port,
                timeout=1,
                baudrate = 115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS)
        
        except serial.SerialException as exc:
            if "PermissionError" in exc.args[0]:  # if the com port is already connected to something
                tkmb.showinfo("Failed to connect", f"Failed to connect to controller, as it already has a connection. \
                \nCheck that no other software is using the controller and try again.")
                raise exc
            else:  # Other connection errors
                tkmb.showerror("Failed to connect", f"Failed to connect to controller, check the connections, then try resetting the controller and this software.")
                raise exc

        except Exception as exc:  # Catch all just in case
            tkmb.showerror("Failed to connect", f"Failed to connect to controller, check the connections, then try resetting the controller and this software.")
            raise exc

    def ask_close(self):
        # Check if any data needs saved
        if self.data_saved:
            self.root.destroy()
            return
        
        # If data needs saved
        response: bool|None = tkmb.askyesnocancel("Really close?", "Save before closing?")
        # Cancel
        if response is None:
            return
        # No
        elif not response:
            self.root.destroy()
        # Yes
        elif response:
            self.save_data()
            self.root.destroy()

def run_gui():
    """Runs the interactive gui"""
    gui = SpeedOfSoundGUI()
    gui.run()

    

# Boilerplate to prevent gui from accidentally being called
if __name__ == "__main__": 
    run_gui()
