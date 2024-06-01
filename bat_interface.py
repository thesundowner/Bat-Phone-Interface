# (c) thesundowner/Samuel Birhanu
# Universal Bat Phone Interface
# 28/5/2024
# 20/09/2016


import customtkinter as ctk
from tkinter import *
from datetime import date, datetime
import os
import threading
import pythoncom
import wmi
import re
import subprocess
import json


SHOWCASE = 0  # To test the log output. Dumb showcase.
VERSION = "2.0.0"

BAT_STR = f"              *         *      *         *\n          ***          **********          ***\n       *****           **********           *****\n     *******           **********           *******\n   **********         ************         **********\n  ****************************************************\n ******************************************************\n********************************************************\n********************************************************\n********************************************************\n ******************************************************\n  ********      ************************      ********\n   *******       *     *********      *       *******\n     ******             *******              ******\n       *****             *****              *****\n          ***             ***              ***\n            **             *              **\n\n\t\t  BAT PHONE INTERFACE\n\n\t\t    VERSION:  {VERSION}\n\n\t\t MADE BY: thesundowner\n\n"

class LogTextBox(ctk.CTkTextbox):
    def __init__(self, master, *a, width=450, unixtimestamps=False, **kw):
        super().__init__(*a, master=master, width=width, **kw)
        self.unixtime = unixtimestamps
        self.configure(
            scrollbar_button_color="#404040",
            scrollbar_button_hover_color="#505050",
            fg_color="#202020",
            text_color="#d4d4d4",
            font=("Consolas", 11),
            wrap="word",
            height=master.winfo_height() - 100,
        )

        self.insert_log(
            f"Bat Phone Interface v{VERSION}", severity="conn"
        )  # Welcome Message

        self.tag_config("error", foreground="#ff3f31")  # Red
        self.tag_config("info", foreground="#03dde9")  # Blue

        self.tag_config("discon", foreground="#ffb422")  # Orange?Yellow
        self.tag_config("conn", foreground="#00fa3d")  # Green

    def insert_log(self, log: str, severity: str | None):
        if not self.unixtime:  # unixtime is the seconds elapsed since 1/1/1970
            tstamp = (
                date.today().strftime("%d-%m")
                + " "
                + str(datetime.time(datetime.now()))[:8]
            )
            frmt = tstamp + ": " + log + "\n"
        else:
            import time

            frmt = str(int(time.time())) + ": " + log + "\n\n"

        self.configure(state=NORMAL)
        if severity:
            if severity == "easter":
                self.delete('1.0' , 'end')
                self.insert("end", log, tags='conn')
                
            else:
                self.insert("end", frmt, tags=severity)
        else:
            self.insert("end", frmt)
        self.configure(state=DISABLED)
        self.see("end")


#  Custom dropdown menu with a label heading.
# NOTE: When removing the component, Call the destroy() method for both _label and _frame.
# Overriding the method led to some kind of recursion in which i don't know how to solve.
class DropdownMenu(ctk.CTkOptionMenu):
    def __init__(self, master, *a, label: str | None, **kw):
        self._frame = ctk.CTkFrame(master=master, width=180)
        self._label = ctk.CTkLabel(
            master=self._frame,
            text=label,
            fg_color="#303030",
            corner_radius=6,
            width=170,
            anchor="w",
        )
        self._label.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        super().__init__(master=self._frame, text_color_disabled="#dddddd", *a, **kw)
        self.grid(row=1, column=0, padx=5, pady=5, sticky="w")


# unused Custom Frame object with a label heading. Don't know  much on how to make these things.
# But too afraid to remove it entirely.

# class LabelFrame(ctk.CTkFrame):
#     def __init__(self , master , *a , label:str | None , **kw):

#         self._label = ctk.CTkLabel(master , text=label , fg_color="#303030" , corner_radius=6 , anchor='w')
#         super().__init__(master=master,*a , **kw)
#         self._label.grid(row=0 , column=0 , padx=5,pady=5,sticky='nw')
#         self.grid(row=1 , column=0 , padx=5  , pady=5 , sticky='w')


class AdbInterface:
    def __init__(self, path: str):

        self.path = path

        # I'm not letting this go over my head.

        # The class purpose is to organize the inputs from user and send it 
        #to adb.exe passing it as args and return output regardless of error or not.
        # The GUI will take appropiate measure in parsing stdout/stderr.
        # It's not effcient, but it does the work.

    def get_device_serial(self) -> tuple:
        try:
            command = f"{self.path}/adb.exe devices"
            proc = subprocess.run(command, capture_output=True).stdout.decode("utf-8")
            # proc.remove('List of Devices attached')

            serial_numbers = []
            pattern = r"([a-fA-F0-9]+)\s+device"
            for line in proc.splitlines():
                match = re.search(pattern, line)
                if match:
                    serial_numbers.append(match.group(1))

            serial_numbers.remove("f")

            # if serial_numbers == []:
            #     serial_numbers.append("No device connected.")

            return tuple(serial_numbers)
        except:
            return ()

    def get_prop(self, device_serial: str):
        proc = self.send_command(device_serial=device_serial, command=f"getprop")
        return proc

    def send_command(
        self, device_serial: str, command: str
    ) -> subprocess.CompletedProcess | None:
        try:
            command = f"{self.path}/adb.exe -s {device_serial} shell {command}"
            proc = subprocess.run(command, capture_output=True)
            return proc
        except:
            return None


class Bat(ctk.CTk):
    # The GUI class

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.title("Bat Phone Interface")
        self.geometry("680x480")
        self.after(201, lambda: self.iconbitmap("./icon.ico"))

        self.adb = AdbInterface(".\\bin")
        threading.Thread(
            target=self.update_usb_handles, daemon=1
        ).start()  # threaded, waiting for a connection.

        self.buttonframe = ctk.CTkScrollableFrame(
            self,
            label_text="Controls",
            bg_color="transparent",
            width=180,
            height=320,
            label_anchor="w",
            label_fg_color="#303030",
            scrollbar_button_color="#404040",
            scrollbar_button_hover_color="#505050",
            label_text_color="#fff",
            corner_radius=6,
        )

        self.updatefunc = self.select_device()

        # Here goes the shitshow
        # Don't mind the same variable for the buttons. Bad practice, i know.

        button = ctk.CTkButton(
            self.buttonframe,
            text="Get Info (getprop)",
            width=175,
            command=lambda: self.get_info(self.optionvar.get()),
        ).grid(padx=1, pady=5)
        button = ctk.CTkButton(
            self.buttonframe,
            text="Reboot Device",
            width=175,
            command=lambda: threading.Thread(
                target=self.svc, args=["reboot"], daemon=1
            ).start(),
        ).grid(padx=1, pady=5)
        button = ctk.CTkButton(
            self.buttonframe,
            text="Shutdown Device",
            width=175,
            command=lambda: threading.Thread(
                target=self.svc, args=["shutdown"], daemon=1
            ).start(),
        ).grid(padx=1, pady=5)

        button = ctk.CTkButton(
            self.buttonframe,
            text="Mirror Screen (scrcpy)",
            width=175,
            command=lambda: threading.Thread(target=self.scrcpy, daemon=1).start(),
        ).grid(padx=1, pady=5)

        button = ctk.CTkButton(
            self.buttonframe,
            text="Enable Data",
            width=175,
            command=lambda: threading.Thread(
                target=self.svc, args=["data1"], daemon=1
            ).start(),
        ).grid(padx=1, pady=5)
        button = ctk.CTkButton(
            self.buttonframe,
            text="Disable Data",
            width=175,
            command=lambda: threading.Thread(
                target=self.svc, args=["data0"], daemon=1
            ).start(),
        ).grid(padx=1, pady=5)

        button = ctk.CTkButton(
            self.buttonframe,
            text="logcat",
            width=175,
            command=lambda: threading.Thread(target=self.logcat, daemon=1).start(),
        ).grid(padx=1, pady=5)
        button = ctk.CTkButton(
            self.buttonframe,
            text="Start shell",
            width=175,
            command=lambda: threading.Thread(target=self.shell, daemon=1).start(),
        ).grid(padx=1, pady=5)

        
        # button = ctk.CTkButton(
        #     self.buttonframe, text="AUTOMAN (in development)", width=175
        # ).grid(padx=1, pady=5)




        # TODO: Write a program that crashes the phone.
        # button = ctk.CTkButton(
        #     self.buttonframe, text="Fuck Up the Phone", width=175
        # ).grid(padx=1, pady=5)



        button = ctk.CTkButton(
            self.buttonframe,
            text="Clear Log",
            width=150,
            command=lambda: self.log.configure(state="normal")
            or self.log.delete("1.0", "end")
            or self.log.configure(state="disabled"),
        ).grid(padx=1, pady=5)

        self.log = LogTextBox(self, unixtimestamps=False)


        self.log.grid(row=0, column=1, padx=5, pady=5, sticky="ne")
        self.buttonframe.grid(row=0, column=0, padx=5, pady=5, sticky="nw")




        # This is where the log showcase happens.
        if SHOWCASE:
            self.log.insert_log("lOG DEBUG", "info")
            self.log.insert_log("LOG ERROR", "error")
            self.log.insert_log("LOG WARNING", "discon")
            self.log.insert_log("LOG INFO", "conn")
            self.log.insert_log("LOG DEFAULT", None)
        self.log.insert_log(BAT_STR , severity='easter')

        self.protocol('WM_DELETE_WINDOW' , lambda: os.system('taskkill /f /im "adb.exe"') or os._exit(0))

    def get_info(self, serial):
        # It retrieves information from adb.exe by running a shell command "getprop"
        # It parses all information and makes a python dict for convienece.
        if not serial:
            self.log.insert_log(
                "Please select a device before continuing.", severity="error"
            )
            return

        # this simple guy parses it into a Json-compatible object
        def parse_prop(prop):
            prop = prop.strip()
            prop = prop.replace("[", '"')
            prop = prop.replace("]", '"')
            prop = prop.replace("\n", ",\n")
            prop = "{" + prop + "}"

            prop = json.loads(prop)
            return prop

        proc = self.adb.get_prop(serial)
        if proc:
            if proc.returncode != 0:
                self.log.insert_log(
                    proc.stderr.decode("utf-8").strip(), severity="error"
                )
            else:
                self.deviceprop = parse_prop(proc.stdout.decode("utf-8").strip())

                # I only displayed basic information. But you can see every property by running the command "getprop" in the adb shell.
                self.log.insert_log(
                    f"""Device Information:\nDevice Manufacturer: '{self.deviceprop['ro.product.manufacturer']}'\nDevice Model: '{self.deviceprop['ro.product.model']}'\nSerial Number: '{self.deviceprop['ro.serialno'] }'\nAndroid Version: '{self.deviceprop['ro.build.version.release']}'\nBuild Description: '{self.deviceprop['ro.build.description']}'""",
                    severity="info",
                )
        else:
            return

    # The following 3 functions run external programs like screen mirroring, log output and a
    # shell window for the device. I opted for a simple os.system() enclosed by a thread but
    # it can be done using subprocess. I will come back at it at a later version. Or someone will.

    def scrcpy(self):
        dev_ser = self.optionvar.get()
        if not dev_ser:
            self.log.insert_log(
                "Please select a device before continuing.", severity="error"
            )
            return
        self.log.insert_log("Starting scrcpy...", severity="info")
        os.system(f"start .\\bin\\scrcpy.exe  -s   {dev_ser} -S")

    def logcat(self):
        dev_ser = self.optionvar.get()
        if not dev_ser:
            self.log.insert_log(
                "Please select a device before continuing.", severity="error"
            )
            return
        self.log.insert_log("Starting Logcat...", severity="info")
        os.system(f"start .\\bin\\adb.exe  -s   {dev_ser} shell logcat -C")

    def shell(self):
        dev_ser = self.optionvar.get()
        if not dev_ser:
            self.log.insert_log(
                "Please select a device before continuing.", severity="error"
            )
            return
        self.log.insert_log("Starting Shell...", severity="info")
        if os.system(f"start cmd /c .\\bin\\adb.exe  -s {dev_ser} shell") != 0:
            self.log.insert_log("Error occured while Starting shell.", severity="error")

    def select_device(self):
        self.optionvar = StringVar()
        self.opf = DropdownMenu(
            self,
            label="Device Selection",
            command=lambda _: self.get_info(self.optionvar.get()),
        )
        self.devices = self.adb.get_device_serial()
        self.opf.configure(variable=self.optionvar)
        if self.devices:
            self.opf.configure(values=self.devices, state="normal")
        else:
            self.opf.configure(state="disabled")
            self.opf.option_clear()
        self.opf._frame.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # The best option i have now is to re-render the component whenever a device state changes
        # ie. Disconnection. If only there's a more refined way to make Desktop apps that doesn't involve
        # JS or TS any of their accolite Frameworks :(

        def update_state():
            self.opf.destroy()
            self.opf._frame.destroy()
            self.opf._label.destroy()
            self.optionvar.set("")
            self.devices = []

            self.opf = DropdownMenu(
                self,
                label="Device Selection",
                command=lambda _: self.get_info(self.optionvar.get()),
            )
            self.devices = self.adb.get_device_serial()
            self.opf.configure(variable=self.optionvar)
            if self.devices:
                self.opf.configure(values=self.devices, state="normal")
            else:
                self.opf.configure(state="disabled")
                self.opf.option_clear()
            self.opf._frame.grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.update()

        update_state()

        return update_state  # return the function so that it can be called outside of the method

    # This function calls the svc program inside the device to control Power, Wi-Fi and
    # Mobile data. I haven't implemented Wifi yet. Due to its insignificance adding such
    # thing I've dropped it entirely.

    def svc(self, command: str):
        dev_ser = self.optionvar.get()
        if not dev_ser:
            self.log.insert_log(
                "Please select a device before continuing.", severity="error"
            )
            return

        match command:

            case "reboot":
                self.log.insert_log("Rebooting Device...", severity="info")
                proc = self.adb.send_command(dev_ser, "svc power reboot")
                if proc:
                    if proc.returncode != 0:
                        self.log.insert_log(
                            proc.stderr.decode("utf-8").strip(), severity="error"
                        )
                    else:
                        self.log.insert_log(
                            "Device rebooted successfully. Refresh the device list to see changes.",
                            severity="info",
                        )
                else:
                    return
                self.updatefunc()

            case "shutdown":
                self.log.insert_log("Shutting Down Device...", severity="info")
                proc = self.adb.send_command(dev_ser, "svc power shutdown")
                if proc:
                    if proc.returncode != 0:
                        self.log.insert_log(proc.stderr.decode("utf-8").strip())
                    else:

                        self.log.insert_log(
                            "Device shut down successfully. Refresh the device list to see changes.",
                            severity="info",
                        )
                else:
                    return
                self.updatefunc()

            case "data0":
                self.log.insert_log("Disabling data...", severity="info")
                proc = self.adb.send_command(dev_ser, "svc data disable")
                if proc:
                    if proc.returncode != 0:
                        self.log.insert_log(
                            proc.stderr.decode("utf-8").strip(), severity="error"
                        )
                    else:
                        self.log.insert_log(
                            "Data connection disabled.", severity="discon"
                        )
                else:
                    return

            case "data1":
                self.log.insert_log("Enabling data...", severity="info")
                proc = self.adb.send_command(dev_ser, "svc data enable")
                if proc:
                    if proc.returncode != 0:
                        self.log.insert_log(
                            proc.stderr.decode("utf-8").strip(), severity="error"
                        )
                    else:
                        self.log.insert_log("Data connection enabled.", severity="conn")
                else:
                    return

    # This does the job of looking for new device connections and device disconnects. The first option
    # Was to use pyudev but it had a system call not available in Windows. The best option was to use
    # This SQL-looking query system that's only available on Windows. It runs indefnitely in a daemon thread.
    # Android Devices in MTP connection have a Device name of "Composite USB Device"
    # Flash Drives are known as "Mass Storage Device".
    # To avoid complications, There's a regex statment to let an update function run only if a MTP
    # device connnects or disconnects. Other USB peripherals will not interfrere with this.

    def update_usb_handles(self):
        pythoncom.CoInitialize()
        del_wql = "SELECT * FROM __InstanceDeletionEvent WITHIN 2 WHERE TargetInstance ISA 'Win32_USBHub'"
        con_wql = "SELECT * FROM __InstanceCreationEvent WITHIN 2 WHERE TargetInstance ISA 'Win32_USBHub'"

        self.c = wmi.WMI()

        con_watcher = self.c.watch_for(raw_wql=con_wql)
        del_watcher = self.c.watch_for(raw_wql=del_wql)
        while 1:
            try:
                connected = con_watcher(timeout_ms=10)
            except wmi.x_wmi_timed_out:
                pass
            else:
                if connected:
                    # Update variables here
                    event = str(connected).splitlines()
                    result = re.search(r'"(.*?)"', event[3][1:])
                    if result:
                        self.updatefunc()
                        self.log.insert_log(
                            f'Device "{result.group(1).strip()}" is connected.',
                            severity="conn",
                        )

            try:
                disconnected = del_watcher(timeout_ms=10)
            except wmi.x_wmi_timed_out:
                pass
            else:
                if disconnected:
                    # Update variables here
                    event = str(disconnected).splitlines()
                    result = re.search(r'"(.*?)"', event[3][1:])
                    if result:
                        self.updatefunc()
                        if "Composite" in result.group(1):
                            self.log.insert_log(
                                f'Device "{result.group(1).strip()}" has left the building.',
                                severity="discon",
                            )


if __name__ == "__main__":

    ctk.set_default_color_theme(
        "./anther.json"
    )  # Tried making it look like Dark Mode Win 11.
    ctk.set_appearance_mode("dark") # I wouldn't recommend setting this to "light".
    bat = Bat()
    bat.mainloop()


# end main
