# Speed of Sound Experiment

## Requirements
1. Ensure the latest version of [Python](https://www.python.org/downloads/) is installed
2. From the command line, pip install pyserial to allow serial communication with the controller
```
py -m pip install pyserial
```

## Installation
1. First update the Raspberry Pi Pico's MicroPython firmware to the latest verion, follow [this](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html) guide.
2. Install [Thonny](https://thonny.org/) to allow you to upload files to the Pico.
3. Upload **main.py,** and **pico_speed_of_sound.py** to the Pico. See [this](https://www.freva.com/transfer-files-between-computer-and-raspberry-pi-pico/) guide.
4. Run **pc_speed_of_sound.py** on a connected computer with the latest version of python installed to check everything is working.
5. Create a shortcut to **pc_speed_of_sound.pyw** on the desktop for normal use, feel free to rename this to something slightly friendlier.
    - The difference between the **.py** and **.pyw** files is that the **.pyw** file will run without opening a terminal. This makes the application look a bit more professional. If you are having problems, try running the **.py** version to see more error outputs in the terminal. 

## Usage
Once everything is setup and working, ensure the Pico is connected and then run the **pc_speed_of_sound.pyw** file to launch the GUI.
