# Imports--------------------------------------------------------------------
import os
import pathlib
import pickle
import shutil
import subprocess
import sys
import threading
import tkinter.scrolledtext as scrolledtextwidget
import webbrowser
from collections import Counter
from configparser import ConfigParser
from ctypes import windll
from datetime import datetime
from glob import glob
from idlelib.tooltip import Hovertip
from random import randint
from time import sleep
from tkinter import (
    filedialog,
    StringVar,
    ttk,
    messagebox,
    PhotoImage,
    Menu,
    NORMAL,
    DISABLED,
    N,
    S,
    W,
    E,
    Toplevel,
    LabelFrame,
    END,
    INSERT,
    Label,
    Checkbutton,
    Spinbox,
    CENTER,
    GROOVE,
    OptionMenu,
    Entry,
    HORIZONTAL,
    SUNKEN,
    Button,
    TclError,
    font,
    Frame,
    Scrollbar,
    VERTICAL,
    Listbox,
    EXTENDED,
)

import psutil
import pyperclip
from pyautogui import hotkey as pya_hotkey
from pymediainfo import MediaInfo
from tkinterdnd2 import DND_FILES, TkinterDnD

from Packages.About import openaboutwindow
from Packages.SimpleYoutubeDLGui import youtube_dl_launcher_for_ffmpegaudioencoder
from Packages.config_params import create_config_params
from Packages.general_settings import open_general_settings
from Packages.icon import gui_icon
from Packages.show_streams import (
    show_streams_mediainfo_function,
    exit_stream_window,
    stream_menu,
)
from Packages.window_geometry_settings import set_window_geometry_settings

# Set variable to True if you want errors to pop up in window + log to file + console, False for console only
log_error_to_file = (
    True  # Change this to false if you don't want to log errors to file + pop up window
)

# Set main window title variable
main_root_title = "FFMPEG Audio Encoder v4.11"

# default an empty variable to be updated based off user input
batch_mode = None

# Checks for App Folder and Sub-Directories - Creates Folders if they are missing ---------
pathlib.Path(pathlib.Path.cwd() / "Runtime").mkdir(parents=True, exist_ok=True)
pathlib.Path(pathlib.Path.cwd() / "Runtime" / "logs").mkdir(parents=True, exist_ok=True)
pathlib.Path(pathlib.Path.cwd() / "Runtime" / "logs" / "error_logs").mkdir(
    parents=True, exist_ok=True
)
pathlib.Path(pathlib.Path.cwd() / "Runtime" / "logs" / "job_manager_multi").mkdir(
    parents=True, exist_ok=True
)
pathlib.Path(pathlib.Path.cwd() / "Runtime" / "logs" / "job_manager_single").mkdir(
    parents=True, exist_ok=True
)
pathlib.Path(pathlib.Path.cwd() / "Runtime" / "logs" / "manual_auto").mkdir(
    parents=True, exist_ok=True
)
pathlib.Path(pathlib.Path.cwd() / "Apps" / "FFMPEG").mkdir(parents=True, exist_ok=True)
pathlib.Path(pathlib.Path.cwd() / "Apps" / "MediaInfo").mkdir(
    parents=True, exist_ok=True
)
pathlib.Path(pathlib.Path.cwd() / "Apps" / "fdkaac").mkdir(parents=True, exist_ok=True)
pathlib.Path(pathlib.Path.cwd() / "Apps" / "qaac").mkdir(parents=True, exist_ok=True)
pathlib.Path(pathlib.Path.cwd() / "Apps" / "qaac" / "QTfiles64").mkdir(
    parents=True, exist_ok=True
)
pathlib.Path(pathlib.Path.cwd() / "Apps" / "mpv").mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------- Folder Check


# Main Gui & Windows --------------------------------------------------------
def root_exit_function():
    def save_root_pos():  # Function to write to config.ini
        func_parser = ConfigParser()
        func_parser.read(config_file)
        if func_parser["save_window_locations"]["ffmpeg audio encoder"] == "yes":
            try:  # If auto-save position on exit is checked
                func_parser.set(
                    "save_window_locations",
                    "ffmpeg audio encoder position",
                    root.geometry(),
                )
                with open(config_file, "w") as configfile:
                    func_parser.write(configfile)
            except (Exception,):
                pass

    open_tops = False  # Set variable for open toplevel windows
    for widget in root.winfo_children():  # Loop through roots children
        if isinstance(
            widget, Toplevel
        ):  # If any of roots children is a TopLevel window
            open_tops = True  # Set variable for open tops to True
    if open_tops:  # If open_tops is True
        confirm_exit = messagebox.askyesno(
            title="Prompt",
            message="Are you sure you want to exit the program?\n\n"
            "Warning:\nThis will end all current tasks, "
            "child-processes, and close all open windows!",
            parent=root,
        )
        if confirm_exit:  # If user wants to exit, kill app and all of it's children
            parent = psutil.Process(root_pid)  # Set psutil parent ID
            for child in parent.children(recursive=True):
                child.kill()  # Loop through all the children processes and kill them with psutil module
            save_root_pos()  # Save root position
            root.destroy()  # Root destroy
            exit_and_clean_empty_logs()  # Exit and clean empty error log files
    if not open_tops:  # If no top levels are found, exit the program without prompt
        parent = psutil.Process(root_pid)  # Set psutil parent ID
        for child in parent.children(recursive=True):
            child.kill()  # Loop through all the children processes and kill them with psutil module
        save_root_pos()  # Save root position
        root.destroy()  # Root destroy
        exit_and_clean_empty_logs()  # Exit and clean empty error log files


# ------------------------------------------------------------------------------------------------------- Config Parser
create_config_params()  # Runs the function to define/create all the parameters in the needed .ini files
# Defines the path to config.ini and opens it for reading/writing
config_file = "Runtime/config.ini"  # Creates (if doesn't exist) and defines location of config.ini
config = ConfigParser()
config.read(config_file)

# Defines the path to profiles.ini and opens it for reading/writing
config_profile_ini = "Runtime/profiles.ini"  # Creates (if doesn't exist) and defines location of profile.ini
config_profile = ConfigParser()
config_profile.read(config_profile_ini)


# Config Parser -------------------------------------------------------------------------------------------------------


# Clean log files -----------------------------------------------------------------------------------------------------
def clean_manual_auto():  # Code to clean auto/manual job log files on start
    log_path = "Runtime/logs/manual_auto/"
    pathlib.Path(log_path).resolve().mkdir(parents=True, exist_ok=True)
    max_log_files = 50
    files = glob(os.path.join(log_path, "*.txt"))  # Collect all files.
    # Choose files to be deleted.
    to_delete = sorted(files, key=lambda x: os.stat(x).st_mtime)[
        : len(files) - max_log_files
    ]
    for error_files in to_delete:  # Delete files
        os.remove(error_files)


def clean_job_window_single():  # Code to clean job manager window single encodes log files on start
    log_path = "Runtime/logs/job_manager_single/"
    pathlib.Path(log_path).resolve().mkdir(parents=True, exist_ok=True)
    max_log_files = 100
    files = glob(os.path.join(log_path, "*.txt"))  # Collect all files.
    # Choose files to be deleted.
    to_delete = sorted(files, key=lambda x: os.stat(x).st_mtime)[
        : len(files) - max_log_files
    ]
    for error_files in to_delete:  # Delete files
        os.remove(error_files)


def clean_job_window_multi():  # Code to clean job manager window multi encodes log files on start
    log_path = "Runtime/logs/job_manager_multi/"
    pathlib.Path(log_path).resolve().mkdir(parents=True, exist_ok=True)
    max_log_files = 100
    files = glob(os.path.join(log_path, "*.txt"))  # Collect all files.
    # Choose files to be deleted.
    to_delete = sorted(files, key=lambda x: os.stat(x).st_mtime)[
        : len(files) - max_log_files
    ]
    for error_files in to_delete:  # Delete files
        os.remove(error_files)


def clean_main_program_error_logs():  # Clean main gui error files
    path = "Runtime/logs/error_logs/"  # Set path to log files
    empty_files = glob(os.path.join(path, "*.txt"))
    to_delete = (f for f in empty_files if os.stat(f).st_size == 0)
    for f in to_delete:  # Get rid of any empty log files on start, if there is any
        os.remove(f)

    pathlib.Path(path).resolve().mkdir(
        parents=True, exist_ok=True
    )  # Remove older error files over 10
    max_error_files = 10  # Set maximum amount of error files in directory
    files = glob(os.path.join(path, "*.txt"))  # Collect all files.
    # Choose files to be deleted.
    to_delete = sorted(files, key=lambda x: os.stat(x).st_mtime)[
        : len(files) - max_error_files
    ]
    for error_files in to_delete:  # Delete files
        os.remove(error_files)


clean_manual_auto()
clean_job_window_single()
clean_job_window_multi()
clean_main_program_error_logs()
# ----------------------------------------------------------------------------------------------------- Clean log files

root = TkinterDnD.Tk()
root.title(main_root_title)
root.iconphoto(True, PhotoImage(data=gui_icon))
root.configure(background="#434547")
if (
    config["save_window_locations"]["ffmpeg audio encoder position"] == ""
    or config["save_window_locations"]["ffmpeg audio encoder"] == "no"
):
    window_height = 325
    window_width = 570
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coordinate = int((screen_width / 2) - (window_width / 2))
    y_coordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
elif (
    config["save_window_locations"]["ffmpeg audio encoder position"] != ""
    and config["save_window_locations"]["ffmpeg audio encoder"] == "yes"
):
    root.geometry(config["save_window_locations"]["ffmpeg audio encoder position"])
root.protocol("WM_DELETE_WINDOW", root_exit_function)
root_pid = os.getpid()  # Get root process ID

# Block of code to fix DPI awareness issues on Windows 7 or higher
try:
    windll.shcore.SetProcessDpiAwareness(2)  # if your Windows version >= 8.1
except (Exception,):
    windll.user32.SetProcessDPIAware()  # Windows 8.0 or less
# Block of code to fix DPI awareness issues on Windows 7 or higher

for n in range(4):
    root.grid_columnconfigure(n, weight=1)
for n in range(4):
    root.grid_rowconfigure(n, weight=1)

# Themes --------------------------------------------------------------------------------------------------------------
# Font Variables ---------------------------------------------
detect_font = font.nametofont(
    "TkDefaultFont"
)  # Get default font value into Font object
set_font = detect_font.actual().get("family")
set_font_size = detect_font.actual().get("size")
# ---------------------------------------------- Font Variables
# Custom Tkinter Theme-----------------------------------------
custom_style = ttk.Style()
custom_style.theme_create(
    "jlw_style",
    parent="alt",
    settings={
        # Notebook Theme Settings -------------------
        "TNotebook": {"configure": {"tabmargins": [5, 5, 5, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "padding": [5, 1],
                "background": "grey",
                "foreground": "white",
                "focuscolor": "",
            },
            "map": {
                "background": [("selected", "#434547")],
                "expand": [("selected", [1, 1, 1, 0])],
            },
        },
        # Notebook Theme Settings -------------------
        # ComboBox Theme Settings -------------------
        "TCombobox": {
            "configure": {
                "selectbackground": "#23272A",
                "fieldbackground": "#23272A",
                "background": "white",
                "foreground": "white",
            }
        },
    }
    # ComboBox Theme Settings -------------------
)
custom_style.theme_use("jlw_style")  # Enable the use of the custom theme
custom_style.configure("custom.Horizontal.TProgressbar", background="#3a4145")


# ------------------------------------------ Custom Tkinter Theme
# Hover over button theme ---------------------------------------
class HoverButton(Button):
    def __init__(self, master, **kw):
        Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self["background"] = self["activebackground"]
        if self.cget("text") == "Input":
            status_label.configure(text="Open input menu or drag and drop a file...")
        if self.cget("text") == "Display\nCommand":
            status_label.configure(text="Display command-line...")
        if self.cget("text") == "Save File":
            status_label.configure(text="Specify save location...")
        if self.cget("text") == "Auto Encode:\nLast Used Options":
            global rightclick_on_off
            status_label.configure(text="Right click for more options...")
            rightclick_on_off = 1
        if self.cget("text") == "Codec Settings":
            status_label.configure(text="Configure selected audio codec..")
        if self.cget("text") == "Start Job":
            status_label.configure(text="Start job..")
        if self.cget("text") == "Add to Jobs List":
            status_label.configure(text="Add configured job to jobs list...")

    def on_leave(self, e):
        self["background"] = self.defaultBackground
        if self.cget("text") == "Auto Encode:\nLast Used Options":
            global rightclick_on_off
            status_label.configure(text="Right Click For More Options...")
            rightclick_on_off = 0
            status_label.configure(text="")
        else:
            status_label.configure(text="")


# --------------------------------------- Hover over button theme
# -------------------------------------------------------------------------------------------------------------- Themes


# Open GitHub tracker for program -------------------------------------------------------------------------------------
def open_github_error_tracker():
    webbrowser.open("https://github.com/jlw4049/FFMPEG-Audio-Encoder/issues")


# ------------------------------------------------------------------------------------- Open github tracker for program

# Logger class, handles all traceback/stdout errors for program, writes to file and to window -------------------------
if log_error_to_file:

    class Logger(
        object
    ):  # Logger class, this class puts stderr errors into a window and file at the same time
        def __init__(self):
            self.terminal = sys.stderr  # Redirects sys.stderr
            error_folder = pathlib.Path(
                "Runtime/logs/error_logs/"
            ).resolve()  # Define error folder
            pathlib.Path(error_folder).mkdir(
                parents=False, exist_ok=True
            )  # Create the folder if it doesn't exist
            error_log_txt = pathlib.Path(
                f"{str(error_folder)}/{datetime.now().strftime('%m-%d-%y - %I.%M.%S')}"
                f"-errorlog.txt"
            )
            self.error_log_file = open(
                error_log_txt, "w", encoding="utf-8"
            )  # Set log file name + open/write

        def write(self, message):
            global info_scrolled
            self.terminal.write(message)
            self.error_log_file.write(message)
            root.bell()  # Error bell sound
            try:
                info_scrolled.config(state=NORMAL)
                if str(message).rstrip():
                    info_scrolled.insert(END, str(message).strip())
                if not str(message).rstrip():
                    info_scrolled.insert(END, f"{str(message)}\n")
                info_scrolled.see(END)
                info_scrolled.config(state=DISABLED)
            except (NameError, TclError):
                error_window = Toplevel()
                error_window.title("Traceback Error(s)")
                error_window.configure(background="#434547")
                window_height = 400
                window_width = 600
                screen_width = error_window.winfo_screenwidth()
                screen_height = error_window.winfo_screenheight()
                x_coordinate = int((screen_width / 2) - (window_width / 2))
                y_coordinate = int((screen_height / 2) - (window_height / 2))
                error_window.geometry(
                    f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}"
                )
                error_window.grab_set()  # Brings attention to this window until it's closed
                for e_w in range(4):
                    error_window.grid_columnconfigure(e_w, weight=1)
                error_window.grid_rowconfigure(0, weight=1)
                info_scrolled = scrolledtextwidget.ScrolledText(
                    error_window, tabs=10, spacing2=3, spacing1=2, spacing3=3
                )
                info_scrolled.grid(
                    row=0, column=0, columnspan=4, pady=5, padx=5, sticky=E + W + N + S
                )
                info_scrolled.configure(bg="black", fg="#CFD2D1", bd=8)
                info_scrolled.insert(END, message)
                info_scrolled.see(END)
                info_scrolled.config(state=DISABLED)

                report_error = HoverButton(
                    error_window,
                    text="Report Error",
                    command=open_github_error_tracker,
                    foreground="white",
                    background="#23272A",
                    borderwidth="3",
                    activebackground="grey",
                )
                report_error.grid(
                    row=1,
                    column=3,
                    columnspan=1,
                    padx=10,
                    pady=(5, 4),
                    sticky=S + E + N,
                )

                force_close_root = HoverButton(
                    error_window,
                    text="Force Close Program",
                    command=root.destroy,
                    foreground="white",
                    background="#23272A",
                    borderwidth="3",
                    activebackground="grey",
                )
                force_close_root.grid(
                    row=1,
                    column=0,
                    columnspan=1,
                    padx=10,
                    pady=(5, 4),
                    sticky=S + W + N,
                )

                def right_click_menu_func(
                    x_y_pos,
                ):  # Function for mouse button 3 (right click) to pop up menu
                    right_click_menu.tk_popup(
                        x_y_pos.x_root, x_y_pos.y_root
                    )  # This gets the position of cursor

                right_click_menu = Menu(
                    info_scrolled, tearoff=False
                )  # This is the right click menu
                right_click_menu.add_command(
                    label="Copy to clipboard",
                    command=lambda: pyperclip.copy(info_scrolled.get(1.0, END).strip()),
                )
                info_scrolled.bind(
                    "<Button-3>", right_click_menu_func
                )  # Uses mouse button 3 to open the menu
                Hovertip(
                    info_scrolled, "Right click to copy", hover_delay=1200
                )  # Hover tip tool-tip

        def flush(self):
            pass

        def __exit__(self):  # Class exit function
            sys.stderr = sys.__stderr__  # Redirect stderr back to original stderr
            self.error_log_file.close()  # Close file


def start_logger():
    if log_error_to_file:  # If True
        sys.stderr = Logger()  # Start the Logger() class to write to console and file


threading.Thread(target=start_logger).start()


def exit_and_clean_empty_logs():  # Function to exit logger() and delete logfile if it's empty
    if log_error_to_file:  # If True
        Logger().__exit__()  # Run Logger()__exit__() function
        empty_files = glob(os.path.join("Runtime/logs/error_logs/", "*.txt"))
        to_delete = (f for f in empty_files if os.stat(f).st_size == 0)
        for f in to_delete:  # Check and delete empty files, if there is any
            os.remove(f)
    elif (
        not log_error_to_file
    ):  # If error logging is set to false, do nothing inside this function
        return


# ------------------------- Logger class, handles all traceback/stdout errors for program, writes to file and to window

# Bundled Apps --------------------------------------------------------------------------------------------------------
# define tool paths ------------------------------------------------------------------------
# define ffmpeg
ffmpeg = config["ffmpeg_path"]["path"]

# define mediainfo
mediainfo = config["mediainfogui_path"]["path"]


# define fdk-aac at program launch
# config_writer for fdk-aac
def write_fdk_config(fdk_var):
    config.set("fdkaac_path", "path", fdk_var)
    with open(config_file, "w") as fdk_cfg:
        config.write(fdk_cfg)  # write path to fdkaac to the config.ini file


if config["fdkaac_path"]["path"] != "":  # if fdk path is defined
    if not pathlib.Path(
        str(config["fdkaac_path"]["path"]).replace('"', "")
    ).is_file():  # if fdk is not present
        if pathlib.Path("Apps/fdkaac/fdkaac.exe").is_file():
            write_fdk_config(f'"{str(pathlib.Path("Apps/fdkaac/fdkaac.exe"))}"')
        elif not pathlib.Path("Apps/fdkaac/fdkaac.exe").is_file():
            write_fdk_config("")  # clear fdk_path in config.ini
elif (
    pathlib.Path("Apps/fdkaac/fdkaac.exe").is_file()
    and config["fdkaac_path"]["path"] == ""
):
    write_fdk_config(
        f'"{str(pathlib.Path("Apps/fdkaac/fdkaac.exe"))}"'
    )  # add path to fdk in apps folder to config.ini
elif (
    not pathlib.Path("Apps/fdkaac/fdkaac.exe").is_file()
    and config["fdkaac_path"]["path"] == ""
):
    write_fdk_config("")  # clear fdk_path in config.ini

fdkaac = config["fdkaac_path"]["path"]  # define path to fdkaac via config.ini


# # define qaac at program launch
# # config_writer for qaac
def write_qaac_config(qaac_var):
    config.set("qaac_path", "path", qaac_var)
    with open(config_file, "w") as qaac_writer_cfg:
        config.write(qaac_writer_cfg)  # write path to fdkaac to the config.ini file


if config["qaac_path"]["path"] != "":  # if qaac is defined
    if not pathlib.Path(
        str(config["qaac_path"]["path"]).replace('"', "")
    ).is_file():  # if qaac is not present
        if pathlib.Path("Apps/qaac/qaac64.exe").is_file():
            write_qaac_config(f'"{str(pathlib.Path("Apps/qaac/qaac64.exe"))}"')
            config.set(
                "qaac_path", "qt_path", f'"{str(pathlib.Path("Apps/qaac/QTfiles64"))}"'
            )
            with open(config_file, "w") as qaac_cfg:
                config.write(qaac_cfg)  # write path to qaac to the config.ini file
        elif not pathlib.Path("Apps/qaac/qaac64.exe").is_file():
            write_qaac_config("")  # clear fdk_path in config.ini
            config.set("qaac_path", "qt_path", "")
            with open(config_file, "w") as qaac_cfg:
                config.write(qaac_cfg)  # write path to qaac to the config.ini file

elif (
    pathlib.Path("Apps/qaac/qaac64.exe").is_file() and config["qaac_path"]["path"] == ""
):
    write_qaac_config(f'"{str(pathlib.Path("Apps/qaac/qaac64.exe"))}"')
    config.set("qaac_path", "qt_path", f'"{str(pathlib.Path("Apps/qaac/QTfiles64"))}"')
    with open(config_file, "w") as qaac_cfg:
        config.write(qaac_cfg)  # write path to qaac to the config.ini file

elif (
    not pathlib.Path("Apps/qaac/qaac64.exe").is_file()
    and config["qaac_path"]["path"] == ""
):
    write_qaac_config("")  # clear fdk_path in config.ini
    config.set("qaac_path", "qt_path", "")
    with open(config_file, "w") as qaac_cfg:
        config.write(qaac_cfg)  # write path to qaac to the config.ini file

qaac = config["qaac_path"]["path"]

# define mpv player
mpv_player = config["mpv_player_path"]["path"]


# ------------------------------------------------------------------------ define tool paths
# -------------------------------------------------------------------------------------------------------- Bundled Apps


# Open InputFile with portable MediaInfo ------------------------------------------------------------------------------
def mediainfogui():
    try:
        file_input_quoted = '"' + file_input + '"'
        commands = mediainfo + " " + file_input_quoted
        subprocess.Popen(commands)
    except (Exception,):
        commands = mediainfo
        subprocess.Popen(commands)


# ----------------------------------------------------------------------------------------------------------- MediaInfo


# Open InputFile with portable mpv ------------------------------------------------------------------------------------
def mpv_gui_main_gui():
    try:
        file_input_quoted = '"' + file_input + '"'
        commands = mpv_player + " " + file_input_quoted
        subprocess.Popen(commands)
    except (Exception,):
        commands = mpv_player
        subprocess.Popen(commands)


# ----------------------------------------------------------------------------------------------------------------- mpv

# Menu Items and Sub-Bars ---------------------------------------------------------------------------------------------
my_menu_bar = Menu(root, tearoff=0)
root.config(menu=my_menu_bar)

file_menu = Menu(my_menu_bar, tearoff=0, activebackground="dim grey")
my_menu_bar.add_cascade(label="File", menu=file_menu)

options_menu = Menu(my_menu_bar, tearoff=0, activebackground="dim grey")
my_menu_bar.add_cascade(label="Options", menu=options_menu)

options_submenu = Menu(root, tearoff=0, activebackground="dim grey")
options_menu.add_cascade(label="Progress Output", menu=options_submenu)
progress_output_view = StringVar()
progress_output_view.set(config["debug_option"]["option"])
if progress_output_view.get() == "":
    progress_output_view.set("Default")
elif progress_output_view.get() != "":
    progress_output_view.set(config["debug_option"]["option"])


def update_shell_option():
    try:
        config.set("debug_option", "option", progress_output_view.get())
        with open(config_file, "w") as configfile:
            config.write(configfile)
    except (Exception,):
        pass


update_shell_option()
options_submenu.add_radiobutton(
    label="Progress Bars",
    variable=progress_output_view,
    value="Default",
    command=update_shell_option,
)
options_submenu.add_radiobutton(
    label="CMD Shell (Debug)",
    variable=progress_output_view,
    value="Debug",
    command=update_shell_option,
)

auto_close_window = StringVar()
auto_close_window.set(config["auto_close_progress_window"]["option"])
if auto_close_window.get() == "":
    auto_close_window.set("on")
elif auto_close_window.get() != "":
    auto_close_window.set(config["auto_close_progress_window"]["option"])


def update_auto_close():
    try:
        config.set("auto_close_progress_window", "option", auto_close_window.get())
        with open(config_file, "w") as configfile:
            config.write(configfile)
    except (Exception,):
        pass


update_auto_close()
options_submenu2 = Menu(root, tearoff=0, activebackground="dim grey")
options_menu.add_cascade(
    label="Auto-Close Progress Window On Completion", menu=options_submenu2
)
options_submenu2.add_radiobutton(
    label="On", variable=auto_close_window, value="on", command=update_auto_close
)
options_submenu2.add_radiobutton(
    label="Off", variable=auto_close_window, value="off", command=update_auto_close
)

options_menu.add_separator()

options_menu.add_command(
    label="Window Location Settings     [CTRL + W]",
    command=set_window_geometry_settings,
)
root.bind("<Control-w>", lambda event: set_window_geometry_settings())


def open_settings_window():
    open_tops = False  # Set variable for open toplevel windows
    for widget in root.winfo_children():  # Loop through roots children
        if isinstance(
            widget, Toplevel
        ):  # If any of roots children is a TopLevel window
            open_tops = True  # Set variable for open tops to True
    if open_tops:  # If open_tops is True
        prompt = messagebox.askyesno(
            title="Prompt",
            message="This will close all secondary windows, are you sure "
            "you want to continue?",
        )
        if prompt:
            set_fresh_launch()
            open_general_settings()
    if not open_tops:
        set_fresh_launch()
        open_general_settings()


options_menu.add_command(
    label="General Settings                    [CTRL + S]", command=open_settings_window
)
root.bind("<Control-s>", lambda event: open_settings_window())

options_menu.add_separator()


def reset_config():
    msg = messagebox.askyesno(
        title="Warning",
        message="Are you sure you want to reset the config.ini file settings?",
    )
    if msg:
        try:
            pathlib.Path(config_file).unlink()
            messagebox.showinfo(title="Prompt", message="Please restart the program")
        except FileNotFoundError:
            messagebox.showerror(
                title="Error!",
                message='"Config.ini" is already deleted, please restart the program',
            )
        root.destroy()


options_menu.add_command(label="Reset Configuration File", command=reset_config)


def clean_all_logs():  # Function to clean all log files if hit
    msg = messagebox.askyesno(
        title="Warning", message="Are you sure you want to delete all log files?"
    )
    if msg:
        log_folder_manual = pathlib.Path("Runtime/logs/manual_auto/").resolve()
        log_folder_job_manager_single = pathlib.Path(
            "Runtime/logs/job_manager_single/"
        ).resolve()
        log_folder_job_manager_multi = pathlib.Path(
            "Runtime/logs/job_manager_multi/"
        ).resolve()
        error_log_folder = pathlib.Path("Runtime/logs/error_logs/").resolve()
        [f.unlink() for f in pathlib.Path(log_folder_manual).glob("*") if f.is_file()]
        [
            f.unlink()
            for f in pathlib.Path(log_folder_job_manager_single).glob("*")
            if f.is_file()
        ]
        [
            f.unlink()
            for f in pathlib.Path(log_folder_job_manager_multi).glob("*")
            if f.is_file()
        ]
        try:
            [
                f.unlink()
                for f in pathlib.Path(error_log_folder).glob("*")
                if f.is_file()
            ]
        except (
            PermissionError
        ):  # If file is in use (1 always will be, ignore the error)
            pass
        if (
            len(os.listdir(log_folder_manual)) == 0
            and len(os.listdir(log_folder_job_manager_single)) == 0
            and len(os.listdir(log_folder_job_manager_multi))
            and len(os.listdir(error_log_folder)) <= 1
        ):
            messagebox.showinfo(
                title="Info",
                message="All log directories have been cleaned, other then file in use",
            )


options_menu.add_command(label="Clean Log Files", command=clean_all_logs)

tools_submenu = Menu(my_menu_bar, tearoff=0, activebackground="dim grey")
my_menu_bar.add_cascade(label="Tools", menu=tools_submenu)
tools_submenu.add_command(label="MediaInfo", command=mediainfogui)
tools_submenu.add_command(label="MPV (Media Player)", command=mpv_gui_main_gui)
tools_submenu.add_command(
    label="Simple-Youtube-DL-Gui", command=youtube_dl_launcher_for_ffmpegaudioencoder
)

help_menu = Menu(my_menu_bar, tearoff=0, activebackground="dim grey")
my_menu_bar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(
    label="Documentation                 [F1]",  # Open GitHub wiki
    command=lambda: webbrowser.open(
        "https://github.com/jlw4049/FFMPEG-Audio-Encoder/wiki"
    ),
)
root.bind(
    "<F1>",
    lambda event: webbrowser.open(
        "https://github.com/jlw4049/FFMPEG-Audio-Encoder/wiki"
    ),
)  # Hotkey
help_menu.add_command(
    label="Project Page",  # Open GitHub project page
    command=lambda: webbrowser.open("https://github.com/jlw4049/FFMPEG-Audio-Encoder"),
)
help_menu.add_command(
    label="Report Error / Feature Request",  # Open GitHub tracker link
    command=lambda: webbrowser.open(
        "https://github.com/jlw4049/FFMPEG-Audio-Encoder/" "issues/new/choose"
    ),
)
help_menu.add_separator()
help_menu.add_command(
    label="Info", command=lambda: openaboutwindow(main_root_title)
)  # Opens about window


# --------------------------------------------------------------------------------------------- Menu Items and Sub-Bars

# # Help Button for FDK -----------------------------------------------------------------------------------------
# def gotofdkaachelp():
#     helpfile_window = Toplevel()
#     helpfile_window.title("FDK-AAC Advanced Settings Help")
#     helpfile_window.configure(background="#434547")
#     Label(helpfile_window, text="Advanced Settings Information",
#           font=("Times New Roman", 14), background='#434547', foreground="white").grid(column=0, row=0)
#     helpfile_window.grid_columnconfigure(0, weight=1)
#     helpfile_window.grid_rowconfigure(0, weight=1)
#     text_area = scrolledtextwidget.ScrolledText(helpfile_window, width=80, height=25)
#     text_area.grid(column=0, pady=10, padx=10)
#     with open("Apps/fdkaac/FDK-AAC-Help.txt", "r") as helpfile:
#         text_area.insert(INSERT, helpfile.read())
#         text_area.configure(font=("Helvetica", 14))
#         text_area.configure(state=DISABLED)
#
#
# # ---------------------------------------------------------------------------------------------------- FDK Help
#
# # Help --------------------------------------------------------------------------------------------------------
# def gotoqaachelp():
#     helpfile_window = Toplevel()
#     helpfile_window.title("QAAC Advanced Settings Help")
#     helpfile_window.configure(background="#434547")
#     Label(helpfile_window, text="Advanced Settings Information",
#           font=("Times New Roman", 14), background='#434547', foreground="white").grid(column=0, row=0)
#     helpfile_window.grid_columnconfigure(0, weight=1)
#     helpfile_window.grid_rowconfigure(0, weight=1)
#     text_area = scrolledtextwidget.ScrolledText(helpfile_window, width=80, height=25)
#     text_area.grid(column=0, pady=10, padx=10)
#     with open("Apps/qaac/qaac information.txt", "r") as helpfile:
#         text_area.insert(INSERT, helpfile.read())
#         text_area.configure(font=("Helvetica", 14))
#         text_area.configure(state=DISABLED)
#
# # -------------------------------------------------------------------------------------------------------- Help


# Hide/Open all top level window function -----------------------------------------------------------------------------
def hide_all_toplevels():
    for widget in root.winfo_children():
        if isinstance(widget, Toplevel):
            widget.withdraw()


def open_all_toplevels():
    for widget in root.winfo_children():
        if isinstance(widget, Toplevel):
            widget.deiconify()


# ----------------------------------------------------------------------------- Hide/Open all top level window function


# function to check state of root, then deiconify it accordingly ------------------------------------------------------
def advanced_root_deiconify():
    if root.winfo_viewable():
        root.deiconify()
    elif not root.winfo_viewable():
        root.iconify()
        root.deiconify()


# ------------------------------------------------------ function to check state of root, then deiconify it accordingly


# Calls to show_streams.py show_streams_mediainfo_function to display a window with track information -----------------
def show_streams_mediainfo():  # All audio codecs can call this function in their menu's
    show_streams_mediainfo_function(file_input)


# ----------------- Calls to show_streams.py show_streams_mediainfo_function to display a window with track information

# Root Frames ---------------------------------------------------------------------------------------------------------
input_frame = LabelFrame(root, text="Input", labelanchor="nw")
input_frame.grid(
    column=0, row=0, columnspan=4, padx=5, pady=(0, 3), sticky=N + S + E + W
)
input_frame.configure(fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold"))
input_frame.grid_rowconfigure(0, weight=1)
for i_f in range(4):
    input_frame.grid_columnconfigure(i_f, weight=1)

audio_setting_frame = LabelFrame(root, text="Codec Settings", labelanchor="n")
audio_setting_frame.grid(
    column=1, row=1, columnspan=3, padx=5, pady=(0, 3), sticky=N + S + E + W
)
audio_setting_frame.configure(
    fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold")
)
audio_setting_frame.grid_rowconfigure(0, weight=1)
audio_setting_frame.grid_columnconfigure(0, weight=1)
audio_setting_frame.grid_columnconfigure(1, weight=1)
audio_setting_frame.grid_columnconfigure(2, weight=1)

start_buttons_frame = LabelFrame(root, text="Job Control", labelanchor="nw")
start_buttons_frame.grid(
    column=0, row=3, columnspan=4, padx=5, pady=(0, 3), sticky=N + S + E + W
)
start_buttons_frame.configure(
    fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold")
)
start_buttons_frame.grid_rowconfigure(0, weight=1)
for s_b_f in range(4):
    start_buttons_frame.grid_columnconfigure(s_b_f, weight=1)

output_frame = LabelFrame(root, text="Output", labelanchor="nw")
output_frame.grid(
    column=0, row=2, columnspan=4, padx=5, pady=(0, 3), sticky=N + S + E + W
)
output_frame.configure(fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold"))
output_frame.grid_rowconfigure(0, weight=1)
for o_f in range(4):
    output_frame.grid_columnconfigure(o_f, weight=1)


# --------------------------------------------------------------------------------------------------------- Root Frames


# File Auto Save Function ---------------------------------------------------------------------------------------------
def set_auto_save_suffix():
    global file_out, autofilesave_dir_path

    func_parser = ConfigParser()
    func_parser.read(config_file)
    autofilesave_file_path = pathlib.Path(
        file_input
    )  # Command to get file input location
    saved_dir = func_parser["output_path"]["path"]
    if saved_dir != "file input directory" and pathlib.Path(saved_dir).is_dir():
        autofilesave_dir_path = saved_dir
    elif saved_dir == "file input directory":
        autofilesave_dir_path = autofilesave_file_path.parents[
            0
        ]  # Final command to get only the directory

    if encoder.get() != "Set Codec":
        convert_filename = (
            f"{str(autofilesave_dir_path)}/{str(pathlib.Path(file_input).name)}"
        )
        if encoder.get() == "AAC":
            file_out = pathlib.Path(convert_filename).with_suffix("._new_.mp4")
        elif encoder.get() == "AC3" or encoder.get() == "E-AC3":
            file_out = pathlib.Path(convert_filename).with_suffix("._new_.ac3")
        elif encoder.get() == "DTS":
            file_out = pathlib.Path(convert_filename).with_suffix("._new_.dts")
        elif encoder.get() == "Opus":
            file_out = pathlib.Path(convert_filename).with_suffix("._new_.opus")
        elif encoder.get() == "MP3":
            file_out = pathlib.Path(convert_filename).with_suffix("._new_.mp3")
        elif (
            encoder.get() == "FDK-AAC"
            or encoder.get() == "QAAC"
            or encoder.get() == "ALAC"
        ):
            file_out = pathlib.Path(convert_filename).with_suffix("._new_.m4a")
        elif encoder.get() == "FLAC":
            file_out = pathlib.Path(convert_filename).with_suffix("._new_.flac")


def encoder_changed(*args):
    global file_output, autosavefilename, file_out, batch_mode
    batch_mode = "no"
    track_counter()
    exit_cmd_window()  # Close cmd window if it's opened
    if encoder.get() != "Set Codec":
        set_auto_save_suffix()
        file_output = str(file_out)
        output_entry.configure(state=NORMAL)
        output_entry.delete(0, END)
        output_entry.insert(0, file_out)
        output_entry.configure(state=DISABLED)
        output_button.config(state=DISABLED)
        audiosettings_button.configure(state=NORMAL)
        command_line_button.config(state=DISABLED)
        start_audio_button.config(state=DISABLED)
        auto_encode_last_options.configure(state=DISABLED)
        add_job_button.config(state=DISABLED)
        autosavefilename = file_out.name


# --------------------------------------------------------------------------------------------- File Auto Save Function


# Uses MediaInfo to get total audio track count and gives us a total track count --------------------------------------
def track_counter(*args):  # Thanks for helping me shorten this 'gmes78'
    global acodec_stream_track_counter, t_info, track_count
    formatting_string = stream_menu(file_input)
    t_info = formatting_string
    acodec_stream_track_counter = {}
    for i in range(int(track_count)):
        acodec_stream_track_counter[
            f"Track #{i + 1}  |  {t_info[i]}"
        ] = f" -map 0:a:{i} "


# ---------------------------------------------------------------------------------------------------------------------

# Encoder Codec Drop Down ---------------------------------------------------------------------------------------------
encoder_dropdownmenu_choices = {
    "AC3": "-c:a ac3 ",
    "AAC": "-c:a aac ",
    "E-AC3": "-c:a eac3 ",
    "DTS": "-c:a dts ",
    "Opus": "-c:a libopus ",
    "MP3": "-c:a libmp3lame ",
    "FLAC": "-c:a flac ",
    "ALAC": "-c:a alac ",
    "FDK-AAC": fdkaac,
    "QAAC": qaac,
}
encoder = StringVar(root)
encoder.set("Set Codec")
encoder_menu = OptionMenu(
    audio_setting_frame,
    encoder,
    *encoder_dropdownmenu_choices.keys(),
    command=encoder_changed,
)
encoder_menu.grid(
    row=0, column=0, columnspan=2, padx=(10, 5), pady=5, sticky=N + S + W + E
)
encoder_menu.config(
    state=DISABLED,
    background="#23272A",
    foreground="white",
    highlightthickness=1,
    width=7,
)
encoder_menu["menu"].configure(activebackground="dim grey")


# -------------------------------------------------------------------------------------------------------- Encoder Menu


# Audio Codec Window --------------------------------------------------------------------------------------------------
def openaudiowindow():
    global audio_window, acodec_bitrate, acodec_channel, acodec_channel_choices, acodec_bitrate_choices, acodec_stream, acodec_stream_choices, acodec_volume, acodec_volume_choices, dts_settings, dts_settings_choices, acodec_vbr_choices, acodec_vbr, acodec_samplerate, acodec_samplerate_choices, acodec_application, acodec_application_choices, acodec_profile, acodec_profile_choices, acodec_atempo, acodec_atempo_choices, opus_mapping_family_choices, opus_mapping_family, gotosavefile, set_encode_manual

    try:  # Checks if existing "codec settings" window is already opened if exists don't open a new one
        if audio_window.winfo_exists():
            # Open a message: Let the user know they need to close already opened window before opening another
            messagebox.showinfo(
                title=f"{audio_window.wm_title()} already opened",  # Get title of opened window
                message=f'Close "{audio_window.wm_title()}" window before attempting to open '
                f'settings for "{str(encoder.get())}" encoder',
            )
            return  # Code to return 'None', to break from function
    except NameError:  # If no "codec settings" window exists, open a new one
        pass  # Continue

    hide_all_toplevels()  # Hide all top levels
    root.withdraw()  # Hide root

    def acodec_bitrate_menu_hover(e):
        acodec_bitrate_menu["bg"] = "grey"
        acodec_bitrate_menu["activebackground"] = "grey"

    def acodec_bitrate_menu_hover_leave(e):
        acodec_bitrate_menu["bg"] = "#23272A"

    def acodec_stream_menu_hover(e):
        acodec_stream_menu["bg"] = "grey"
        acodec_stream_menu["activebackground"] = "grey"

    def acodec_stream_menu_hover_leave(e):
        acodec_stream_menu["bg"] = "#23272A"

    def achannel_menu_hover(e):
        achannel_menu["bg"] = "grey"
        achannel_menu["activebackground"] = "grey"

    def achannel_menu_hover_leave(e):
        achannel_menu["bg"] = "#23272A"

    def acodec_samplerate_menu_hover(e):
        acodec_samplerate_menu["bg"] = "grey"
        acodec_samplerate_menu["activebackground"] = "grey"

    def acodec_samplerate_menu_hover_leave(e):
        acodec_samplerate_menu["bg"] = "#23272A"

    def dts_settings_menu_hover(e):
        dts_settings_menu["bg"] = "grey"
        dts_settings_menu["activebackground"] = "grey"

    def dts_settings_menu_hover_leave(e):
        dts_settings_menu["bg"] = "#23272A"

    def acodec_vbr_menu_hover(e):
        acodec_vbr_menu["bg"] = "grey"
        acodec_vbr_menu["activebackground"] = "grey"

    def acodec_vbr_menu_hover_leave(e):
        acodec_vbr_menu["bg"] = "#23272A"

    def acodec_application_menu_hover(e):
        acodec_application_menu["bg"] = "grey"
        acodec_application_menu["activebackground"] = "grey"

    def acodec_application_menu_hover_leave(e):
        acodec_application_menu["bg"] = "#23272A"

    def per_frame_metadata_menu_hover(e):
        per_frame_metadata_menu["bg"] = "grey"
        per_frame_metadata_menu["activebackground"] = "grey"

    def per_frame_metadata_menu_hover_leave(e):
        per_frame_metadata_menu["bg"] = "#23272A"

    def dolby_surround_mode_menu_hover(e):
        dolby_surround_mode_menu["bg"] = "grey"
        dolby_surround_mode_menu["activebackground"] = "grey"

    def dolby_surround_mode_menu_hover_leave(e):
        dolby_surround_mode_menu["bg"] = "#23272A"

    def room_type_menu_hover(e):
        room_type_menu["bg"] = "grey"
        room_type_menu["activebackground"] = "grey"

    def room_type_menu_hover_leave(e):
        room_type_menu["bg"] = "#23272A"

    def downmix_mode_menu_hover(e):
        downmix_mode_menu["bg"] = "grey"
        downmix_mode_menu["activebackground"] = "grey"

    def downmix_mode_menu_hover_leave(e):
        downmix_mode_menu["bg"] = "#23272A"

    def dolby_surround_ex_mode_menu_hover(e):
        dolby_surround_ex_mode_menu["bg"] = "grey"
        dolby_surround_ex_mode_menu["activebackground"] = "grey"

    def dolby_surround_ex_mode_menu_hover_leave(e):
        dolby_surround_ex_mode_menu["bg"] = "#23272A"

    def dolby_headphone_mode_menu_hover(e):
        dolby_headphone_mode_menu["bg"] = "grey"
        dolby_headphone_mode_menu["activebackground"] = "grey"

    def dolby_headphone_mode_menu_hover_leave(e):
        dolby_headphone_mode_menu["bg"] = "#23272A"

    def a_d_converter_type_menu_hover(e):
        a_d_converter_type_menu["bg"] = "grey"
        a_d_converter_type_menu["activebackground"] = "grey"

    def a_d_converter_type_menu_hover_leave(e):
        a_d_converter_type_menu["bg"] = "#23272A"

    def stereo_rematrixing_menu_hover(e):
        stereo_rematrixing_menu["bg"] = "grey"
        stereo_rematrixing_menu["activebackground"] = "grey"

    def stereo_rematrixing_menu_hover_leave(e):
        stereo_rematrixing_menu["bg"] = "#23272A"

    def q_acodec_profile_hover(e):
        q_acodec_profile_menu["bg"] = "grey"
        q_acodec_profile_menu["activebackground"] = "grey"

    def q_acodec_profile_hover_leave(e):
        q_acodec_profile_menu["bg"] = "#23272A"

    def q_acodec_quality_menu_hover(e):
        q_acodec_quality_menu["bg"] = "grey"
        q_acodec_quality_menu["activebackground"] = "grey"

    def q_acodec_quality_menu_hover_leave(e):
        q_acodec_quality_menu["bg"] = "#23272A"

    def q_gapless_mode_menu_hover(e):
        q_gapless_mode_menu["bg"] = "grey"
        q_gapless_mode_menu["activebackground"] = "grey"

    def q_gapless_mode_menu_hover_leave(e):
        q_gapless_mode_menu["bg"] = "#23272A"

    def acodec_flac_lpc_type_menu_hover(e):
        acodec_flac_lpc_type_menu["bg"] = "grey"
        acodec_flac_lpc_type_menu["activebackground"] = "grey"

    def acodec_flac_lpc_type_menu_hover_leave(e):
        acodec_flac_lpc_type_menu["bg"] = "#23272A"

    def acodec_flac_lpc_passes_menu_hover(e):
        acodec_flac_lpc_passes_menu["bg"] = "grey"
        acodec_flac_lpc_passes_menu["activebackground"] = "grey"

    def acodec_flac_lpc_passes_menu_hover_leave(e):
        acodec_flac_lpc_passes_menu["bg"] = "#23272A"

    def opus_mapping_family_menu_hover(e):
        opus_mapping_family_menu["bg"] = "grey"
        opus_mapping_family_menu["activebackground"] = "grey"

    def opus_mapping_family_menu_hover_leave(e):
        opus_mapping_family_menu["bg"] = "#23272A"

    # Checks channel for dolby pro logic II checkbox ------------------------------------------------------------------
    def dolby_pro_logic_ii_enable_disable(*args):
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.config(state=NORMAL)
        else:
            dolby_pro_logic_ii.set("")
            dolby_pro_logic_ii_checkbox.config(state=DISABLED)

    # --------------------------------------------------------------------------------------------- dplII channel check

    # Get Selected Track Number for MPV Player ------------------------------------------------------------------------
    def track_number_mpv(*args):
        global mpv_track_number, acodec_stream
        if acodec_stream.get() != "None":
            mpv_track_number = str(acodec_stream.get().split()[1][-1])

    # ------------------------------------------------------------------------ Get Selected Track Number for MPV Player

    # Open InputFile Track X with portable mpv ------------------------------------------------------------------------
    def mpv_gui_audio_window():
        file_input_quoted = '"' + file_input + '"'
        commands = (
            mpv_player
            + " "
            + "--volume=50 "
            + "--aid="
            + mpv_track_number[0]
            + " "
            + file_input_quoted
        )
        subprocess.Popen(commands)

    # ------------------------------------------------------------------------------------------------------------- mpv

    # Combines -af filter settings ------------------------------------------------------------------------------------
    global audio_filter_function

    def audio_filter_function(*args):
        global audio_filter_setting
        audio_filter_setting = ""
        if encoder.get() == "E-AC3":
            ffmpeg_volume_cmd = '"volume=' + ffmpeg_volume.get() + '"'
            if (
                ffmpeg_volume.get() == "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] == ""
            ):
                audio_filter_setting = ""
            elif (
                ffmpeg_volume.get() != "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] == ""
            ):
                audio_filter_setting = "-af " + ffmpeg_volume_cmd + " "
            elif (
                ffmpeg_volume.get() == "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] != ""
            ):
                audio_filter_setting = (
                    "-af " + acodec_atempo_choices[acodec_atempo.get()] + " "
                )
            elif (
                ffmpeg_volume.get() != "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] != ""
            ):
                audio_filter_setting = (
                    "-af "
                    + ffmpeg_volume_cmd
                    + ","
                    + acodec_atempo_choices[acodec_atempo.get()]
                    + " "
                )
        else:
            ffmpeg_volume_cmd = '"volume=' + ffmpeg_volume.get() + '"'
            if (
                dolby_pro_logic_ii.get() == ""
                and ffmpeg_volume.get() == "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] == ""
            ):
                audio_filter_setting = ""
            elif (
                dolby_pro_logic_ii.get() == '"aresample=matrix_encoding=dplii"'
                and ffmpeg_volume.get() == "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] == ""
            ):
                audio_filter_setting = "-af " + dolby_pro_logic_ii.get() + " "

            elif (
                dolby_pro_logic_ii.get() == '"aresample=matrix_encoding=dplii"'
                and ffmpeg_volume.get() != "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] == ""
            ):
                audio_filter_setting = (
                    "-af " + dolby_pro_logic_ii.get() + "," + ffmpeg_volume_cmd + " "
                )
            elif (
                dolby_pro_logic_ii.get() == ""
                and ffmpeg_volume.get() != "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] == ""
            ):
                audio_filter_setting = "-af " + ffmpeg_volume_cmd + " "
            elif (
                dolby_pro_logic_ii.get() == '"aresample=matrix_encoding=dplii"'
                and ffmpeg_volume.get() == "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] != ""
            ):
                audio_filter_setting = (
                    "-af "
                    + dolby_pro_logic_ii.get()
                    + ","
                    + acodec_atempo_choices[acodec_atempo.get()]
                    + " "
                )
            elif (
                dolby_pro_logic_ii.get() == '"aresample=matrix_encoding=dplii"'
                and ffmpeg_volume.get() != "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] != ""
            ):
                audio_filter_setting = (
                    "-af "
                    + dolby_pro_logic_ii.get()
                    + ","
                    + ffmpeg_volume_cmd
                    + ","
                    + acodec_atempo_choices[acodec_atempo.get()]
                    + " "
                )
            elif (
                dolby_pro_logic_ii.get() == ""
                and ffmpeg_volume.get() != "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] != ""
            ):
                audio_filter_setting = (
                    "-af "
                    + ffmpeg_volume_cmd
                    + ","
                    + acodec_atempo_choices[acodec_atempo.get()]
                    + " "
                )
            elif (
                dolby_pro_logic_ii.get() == ""
                and ffmpeg_volume.get() == "0.0"
                and acodec_atempo_choices[acodec_atempo.get()] != ""
            ):
                audio_filter_setting = (
                    "-af " + acodec_atempo_choices[acodec_atempo.get()] + " "
                )

    # ---------------------------------------------------------------------------------------------------- combines -af

    # Set encoding_job_type to 'manual' when clicked by codecs in codec settings window -------------------------------
    def set_encode_manual():
        global encoding_job_type
        encoding_job_type = "manual"

    # ------------------------------- Set encoding_job_type to 'manual' when clicked by codecs in codec settings window

    # Save audio codec window size/positions --------------------------------------------------------------------------
    def save_codec_window_positions():
        if encoder.get() == "AC3":
            loc_codec_on_off = "audio window - ac3"
            loc_codec_pos_on_off = "audio window - ac3 - position"
        if encoder.get() == "AAC":
            loc_codec_on_off = "audio window - aac"
            loc_codec_pos_on_off = "audio window - aac - position"
        if encoder.get() == "E-AC3":
            loc_codec_on_off = "audio window - e-ac3"
            loc_codec_pos_on_off = "audio window - e-ac3 - position"
        if encoder.get() == "DTS":
            loc_codec_on_off = "audio window - dts"
            loc_codec_pos_on_off = "audio window - dts - position"
        if encoder.get() == "Opus":
            loc_codec_on_off = "audio window - opus"
            loc_codec_pos_on_off = "audio window - opus - position"
        if encoder.get() == "MP3":
            loc_codec_on_off = "audio window - mp3"
            loc_codec_pos_on_off = "audio window - mp3 - position"
        if encoder.get() == "FDK-AAC":
            loc_codec_on_off = "audio window - fdk-aac"
            loc_codec_pos_on_off = "audio window - fdk-aac - position"
        if encoder.get() == "QAAC":
            loc_codec_on_off = "audio window - qaac"
            loc_codec_pos_on_off = "audio window - qaac - position"
        if encoder.get() == "FLAC":
            loc_codec_on_off = "audio window - flac"
            loc_codec_pos_on_off = "audio window - flac - position"
        if encoder.get() == "ALAC":
            loc_codec_on_off = "audio window - alac"
            loc_codec_pos_on_off = "audio window - alac - position"
        func_parser = ConfigParser()
        func_parser.read(config_file)
        if (
            func_parser["save_window_locations"][loc_codec_on_off] == "yes"
        ):  # If auto-save on exit is checked
            try:
                func_parser.set(
                    "save_window_locations",
                    loc_codec_pos_on_off,
                    audio_window.geometry(),
                )
                with open(config_file, "w") as configfile:
                    func_parser.write(configfile)
            except (Exception,):
                pass

    # -------------------------------------------------------------------------- Save audio codec window size/positions

    # 'Apply' button function -----------------------------------------------------------------------------------------
    def gotosavefile():
        global file_input, language_string, delay_string, channel_string, encoding_job_type
        output_button.config(state=NORMAL)  # Enable buttons upon save file
        start_audio_button.config(state=NORMAL)
        command_line_button.config(state=NORMAL)
        add_job_button.config(state=NORMAL)
        open_all_toplevels()

        if encoding_job_type == "manual":
            save_codec_window_positions()  # Call functions to save window size/positions

        try:
            exit_stream_window()
        except NameError:
            pass

        try:  # If window is open update the command line
            if cmd_line_window.winfo_exists():
                print_command_line()
        except NameError:
            pass

        language_string = ""  # Place holder variable
        delay_string = ""  # Place holder variable
        channel_string = ""  # Place holder variable

        def update_video_output():  # Function to add language/delay strings to the output filename
            global file_output, autosavefilename, total_streams, language_string, delay_string, channel_string
            set_auto_save_suffix()  # Run function to apply default file_output before continuing code
            audio_track_number_string = f"[Audio#{acodec_stream.get().split()[1][-1]}]"
            if total_streams == 1:  # If total_streams equals 1
                file_output = str(file_output).replace(
                    "_new_", audio_track_number_string + channel_string
                )  # Replace _new_ with Audio#
            elif total_streams >= 2:  # If total_streams is 2 or greater
                file_output = str(file_output).replace(
                    "_new_",
                    audio_track_number_string
                    + language_string
                    + delay_string
                    + channel_string,
                )  # Replace '_new_'
            autosavefilename = pathlib.Path(file_output).stem
            command_line_button.config(
                state=NORMAL
            )  # Enable the display command button for main gui
            output_entry.config(state=NORMAL)  # Enable output_entry box for editing
            output_entry.delete(0, END)  # Remove all text from box
            output_entry.insert(0, file_output)  # Insert new file_output path
            output_entry.config(state=DISABLED)  # Disable output_entry box

        def delay_and_lang_check():
            global language_string, delay_string, channel_string, encoding_job_type, auto_track_input, total_streams
            # If input is only 1 track, parse input file name for language and delay string
            media_info = MediaInfo.parse(file_input)  # Parse file_input
            general_track = media_info.general_tracks[0]
            total_streams = 0  # Empty variable to add up all the tracks
            if general_track.count_of_video_streams is not None:
                total_streams += int(
                    general_track.count_of_video_streams
                )  # check for video track(s)
            if general_track.count_of_audio_streams is not None:
                total_streams += int(
                    general_track.count_of_audio_streams
                )  # check for audio track(s)
            if general_track.count_of_subtitle_streams is not None:
                total_streams += int(
                    general_track.count_of_subtitle_streams
                )  # check for subtitle track(s)
            if general_track.count_of_menu_streams is not None:
                total_streams += int(
                    general_track.count_of_menu_streams
                )  # check for menu track(s)

            if total_streams == 1:  # If total streams is equal to 1
                try:
                    if (
                        encoding_job_type == "manual"
                    ):  # If normal encoding is used with the start job button
                        audio_window.destroy()  # Close audio window
                        advanced_root_deiconify()
                        track_selection_mediainfo = media_info.audio_tracks[
                            int(acodec_stream_choices[acodec_stream.get()].strip()[-1])
                        ]
                except NameError:  # If encoding_job_type does not exist yet
                    pass

                try:
                    if encoding_job_type == "auto":
                        audio_window.destroy()  # Destroy audio window, only opens to define variables inside it
                        hide_all_toplevels()  # Hide all TopLevels
                        set_fresh_launch_for_auto_encode()  # Reset Main Gui
                    # parse input file name for language and delay string
                    # language_code_input = re_findall(r"\[([A-Za-z]+)\]", str(file_input))
                    # if language_code_input:  # If re finds language codes within '[]'
                    #     lng_input_lengths = [len(i) for i in language_code_input]
                    #     if 3 in lng_input_lengths:  # If anything within the brackets is 3 digits
                    #         index = lng_input_lengths.index(3)  # Finds index of string inside brackets that's 3 digits
                    #         language_string = str(f'[{language_code_input[index]}]')  # Set's language string to index
                    # if not language_code_input:
                    #     language_string = ''
                    #
                    # # parse input filename for delay string, it searches for ms and any numbers (- if it has it)
                    # input_delay_string = re_search('-*[^a-zA-Z [_{+]*ms', file_input)
                    # if input_delay_string:  # If re finds a delay string in the input filename
                    #     delay_string = f'[delay {str(input_delay_string[0])}]'
                    # if not input_delay_string:
                    #     delay_string = ''

                    language_string = ""
                    delay_string = ""
                    auto_track_input = 0  # Since there is only 1 stream, set 0 as value (-map 0:a:'value')

                except NameError:
                    audio_window.destroy()
                    hide_all_toplevels()  # Hide all TopLevels
                    advanced_root_deiconify()

            if (
                total_streams >= 2
            ):  # If total streams are greater than 1 (video input, remux, bluray, dvd, etc...)
                # Check delay and add delay string to variable --------------------------------------------------------
                try:
                    if (
                        encoding_job_type == "manual"
                    ):  # If normal encoding is used with the start job button
                        audio_window.destroy()  # Close audio window
                        advanced_root_deiconify()
                        track_selection_mediainfo = media_info.audio_tracks[
                            int(acodec_stream_choices[acodec_stream.get()].strip()[-1])
                        ]
                except NameError:  # If encoding_job_type does not exist yet
                    pass

                try:
                    if encoding_job_type == "auto":
                        audio_window.destroy()  # Destroy audio window, only opens to define variables inside it
                        hide_all_toplevels()  # Hide all TopLevels
                        set_fresh_launch_for_auto_encode()  # Reset Main Gui

                        def track_window():  # Function to select which audio track user would like to encode with
                            global auto_track_input, mini_acodec_stream, acodec_stream_choices

                            def mini_track_window_exit():
                                close_audio_cancel()

                            audio_track_win = Toplevel()  # Toplevel window
                            audio_track_win.configure(
                                background="#191a1a"
                            )  # Set color of audio_track_win background
                            audio_track_win.title("Audio Track Selection")
                            window_height = 340  # win height
                            window_width = 478  # win width
                            # Open on top left of root window
                            audio_track_win.geometry(
                                f"{window_width}x{window_height}+"
                                f'{root.geometry().split("+")[1]}+{root.geometry().split("+")[2]}'
                            )
                            audio_track_win.resizable(
                                0, 0
                            )  # makes window not resizable
                            audio_track_win.grab_set()  # forces audio_track_win to stay on top of root
                            audio_track_win.protocol(
                                "WM_DELETE_WINDOW", mini_track_window_exit
                            )

                            # Track Frame -----------------------------------------------------------------------------
                            # Define track frame
                            track_frame = LabelFrame(
                                audio_track_win,
                                text=" Track Selection ",
                                fg="#3498db",
                                bg="#434547",
                                bd=3,
                                font=(set_font, 10, "bold"),
                            )
                            track_frame.grid(
                                row=0,
                                column=0,
                                columnspan=5,
                                sticky=E + W,
                                padx=10,
                                pady=(8, 0),
                            )

                            track_frame.rowconfigure(0, weight=1)
                            track_frame.grid_columnconfigure(0, weight=1)

                            # ----------------------------------------------------------------------------- Track Frame

                            # Menu to show track(s) information -------------------------------------------------------
                            def update_track_window_text(*args):
                                try:
                                    mapping_number = (
                                        int(str(mini_acodec_stream.get()).split()[1][1])
                                        - 1
                                    )
                                except IndexError:
                                    return
                                show_cmd_scrolled.configure(
                                    state=NORMAL, bg="black", fg="#CFD2D1", bd=8
                                )
                                show_cmd_scrolled.delete(1.0, END)
                                show_cmd_scrolled.insert(
                                    END,
                                    f"-map 0:a:{str(mapping_number)} "
                                    f"{str(config_profile['Auto Encode']['command'])}",
                                )
                                show_cmd_scrolled.see(END)
                                show_cmd_scrolled.configure(state=DISABLED)

                            show_cmd_scrolled = scrolledtextwidget.ScrolledText(
                                track_frame,
                                width=30,
                                height=6,
                                tabs=10,
                                spacing2=3,
                                spacing1=2,
                                spacing3=3,
                            )
                            show_cmd_scrolled.grid(
                                row=1,
                                column=0,
                                columnspan=3,
                                pady=(20, 4),
                                padx=5,
                                sticky=E + W,
                            )
                            show_cmd_scrolled.configure(
                                state=NORMAL, bg="black", fg="#CFD2D1", bd=8
                            )
                            show_cmd_scrolled.insert(
                                END,
                                f"-map 0:a:0 {str(config_profile['Auto Encode']['command'])}",
                            )
                            show_cmd_scrolled.see(END)
                            show_cmd_scrolled.configure(state=DISABLED)

                            mini_acodec_stream = StringVar()
                            acodec_stream_choices = acodec_stream_track_counter
                            mini_acodec_stream.set(
                                next(iter(acodec_stream_track_counter))
                            )  # set the default option
                            acodec_stream_menu = OptionMenu(
                                track_frame,
                                mini_acodec_stream,
                                *acodec_stream_choices.keys(),
                            )
                            acodec_stream_menu.config(
                                background="#23272A",
                                foreground="white",
                                highlightthickness=1,
                                width=48,
                                anchor="w",
                            )
                            acodec_stream_menu.grid(
                                row=0,
                                column=0,
                                columnspan=3,
                                padx=10,
                                pady=6,
                                sticky=N + S + W + E,
                            )
                            acodec_stream_menu["menu"].configure(
                                activebackground="dim grey"
                            )
                            mini_acodec_stream.trace("w", update_track_window_text)

                            # ------------------------------------------------------- Menu to show track(s) information

                            def close_audio_start():  # Function is used when 'Confirm Track and Start' is clicked
                                global auto_track_input
                                open_all_toplevels()  # Open all top levels if they existed
                                advanced_root_deiconify()  # Re-Open root window
                                audio_track_win.grab_release()
                                audio_track_win.destroy()  # Closes audio window
                                # Get track number  and subtract 1 for ffmpeg (Track 1 = -map 0:a:0)
                                auto_track_input = (
                                    int(str(mini_acodec_stream.get()).split()[1][1]) - 1
                                )

                            def close_audio_cancel():  # Function is used when 'Cancel' is clicked
                                global encoder
                                open_all_toplevels()  # Open all top levels if they existed
                                advanced_root_deiconify()  # Re-Open root window
                                audio_track_win.grab_release()
                                audio_track_win.destroy()  # Closes audio window
                                encoder.set(
                                    "None"
                                )  # Set acodec_stream to None, so job does not start
                                output_entry.configure(
                                    state=NORMAL
                                )  # Enable output_entry
                                output_entry.delete(
                                    0, END
                                )  # Clear contents of output entry
                                output_entry.configure(
                                    state=DISABLED
                                )  # Disable output entry
                                auto_encode_last_options.configure(
                                    state=NORMAL
                                )  # Keeps auto_encode button enabled

                            # Button Code -----------------------------------------------------------------------------
                            select_track = HoverButton(
                                track_frame,
                                text="Confirm Track and Start",
                                command=close_audio_start,
                                foreground="white",
                                background="#23272A",
                                borderwidth="3",
                                activebackground="grey",
                            )
                            select_track.grid(
                                row=2,
                                column=2,
                                columnspan=1,
                                padx=5,
                                pady=(40, 5),
                                sticky=E,
                            )

                            cancel_select = HoverButton(
                                track_frame,
                                text="Cancel",
                                command=close_audio_cancel,
                                foreground="white",
                                background="#23272A",
                                borderwidth="3",
                                activebackground="grey",
                            )
                            cancel_select.grid(
                                row=2,
                                column=0,
                                columnspan=1,
                                padx=5,
                                pady=(40, 5),
                                sticky=W,
                            )
                            # ----------------------------------------------------------------------------- Button Code
                            audio_track_win.wait_window()  # Halts program until audio_track_win is closed

                        track_window()  # Opens audio_track_win to select tracks
                        track_selection_mediainfo = media_info.audio_tracks[
                            int(auto_track_input)
                        ]

                except NameError:
                    audio_window.destroy()

                try:
                    if "mp4" in str(pathlib.Path(file_input).suffix):
                        if track_selection_mediainfo.source_delay:
                            delay_string = f"[delay {str(track_selection_mediainfo.source_delay)}ms]"
                        else:
                            delay_string = str("[delay 0ms]")
                    else:
                        if (
                            track_selection_mediainfo.delay_relative_to_video
                            is not None
                        ):
                            delay_string = f"[delay {str(track_selection_mediainfo.delay_relative_to_video)}ms]"
                        else:
                            delay_string = str("[delay 0ms]")
                except UnboundLocalError:
                    pass

                try:
                    # Obtain language string from file_input's parsed track
                    if (
                        track_selection_mediainfo.other_language is not None
                    ):  # If language is not None
                        l_lengths = [
                            len(i) for i in track_selection_mediainfo.other_language
                        ]  # List of language codes
                        if (
                            3 in l_lengths
                        ):  # Find strings in l_lengths that only are equal to 3 characters
                            l_index = l_lengths.index(
                                3
                            )  # Save the index of the 3 character string to variable
                        language_string = f"[{str(track_selection_mediainfo.other_language[l_index])}]"
                    else:
                        language_string = "[und]"
                except UnboundLocalError:
                    pass

                try:
                    if track_selection_mediainfo.channel_s:
                        channel_string = (
                            f"[chnl {str(track_selection_mediainfo.channel_s)}]"
                        )
                except UnboundLocalError:
                    pass

        delay_and_lang_check()
        update_video_output()
        # ------------------------------------------------------------ Check delay and add delay string to variable

    def gotosavefile_batch():
        save_codec_window_positions()  # Call functions to save window size/positions
        audio_window.destroy()  # Close audio window
        collect_final_job_commands()
        open_all_toplevels()

    # ----------------------------------------------------------------------------------------- 'Apply' button function

    # Modify what the 'X' does at the top right of the audio window ---------------------------------------------------
    def audio_window_exit_function():  # When the 'X' is clicked, it does the same thing as the "Apply" button
        if batch_mode == "no":
            set_encode_manual()  # Calls set_encode_manual() function
            gotosavefile()  # Calls gotosavefile() function
        elif batch_mode == "yes":
            gotosavefile_batch()

    # --------------------------------------------------- Modify what the 'X' does at the top right of the audio window

    # Profile Functions -----------------------------------------------------------------------------------------------
    def save_profile():
        """function to save current settings in codec window"""

        if encoder.get() == "AC3":
            config_profile.set(
                "FFMPEG AC3 - SETTINGS", "ac3_bitrate", acodec_bitrate.get()
            )
            config_profile.set(
                "FFMPEG AC3 - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set(
                "FFMPEG AC3 - SETTINGS", "ffmpeg_volume", ffmpeg_volume.get()
            )
            config_profile.set(
                "FFMPEG AC3 - SETTINGS", "ac3_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG AC3 - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set("FFMPEG AC3 - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG AC3 - SETTINGS",
                "custom_command_line",
                ac3_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "AAC":
            config_profile.set(
                "FFMPEG AAC - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set(
                "FFMPEG AAC - SETTINGS", "ffmpeg_volume", ffmpeg_volume.get()
            )
            if aac_vbr_toggle.get() == "-c:a ":
                config_profile.set(
                    "FFMPEG AAC - SETTINGS", "aac_bitrate", aac_bitrate_spinbox.get()
                )
            if aac_vbr_toggle.get() == "-q:a ":
                config_profile.set(
                    "FFMPEG AAC - SETTINGS",
                    "aac_vbr_quality",
                    aac_quality_spinbox.get(),
                )
            config_profile.set(
                "FFMPEG AAC - SETTINGS", "aac_vbr_toggle", aac_vbr_toggle.get()
            )
            config_profile.set(
                "FFMPEG AAC - SETTINGS", "aac_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG AAC - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set("FFMPEG AAC - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG AAC - SETTINGS",
                "custom_command_line",
                aac_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "DTS" and dts_settings.get() != "DTS Encoder":
            messagebox.showinfo(
                parent=audio_window,
                title="Information",
                message="You can only save 'DTS' settings if 'DTS Settings' is set to 'Encoder'",
            )

        elif encoder.get() == "DTS" and dts_settings.get() == "DTS Encoder":
            config_profile.set(
                "FFMPEG DTS - SETTINGS", "dts_bitrate", dts_bitrate_spinbox.get()
            )
            config_profile.set(
                "FFMPEG DTS - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set(
                "FFMPEG DTS - SETTINGS", "ffmpeg_volume", ffmpeg_volume.get()
            )
            config_profile.set(
                "FFMPEG DTS - SETTINGS", "dts_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG DTS - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set("FFMPEG DTS - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG DTS - SETTINGS",
                "custom_command_line",
                dts_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "E-AC3":
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_bitrate", eac3_spinbox.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_volume", ffmpeg_volume.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_per_frame_metadata",
                per_frame_metadata.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_mixing_level", eac3_mixing_level.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_room_type", room_type.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_copyright_bit", copyright_bit.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_dialogue_level", dialogue_level.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_surround_mode",
                dolby_headphone_mode.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_original_bitstream",
                original_bit_stream.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_downmix_mode", downmix_mode.get()
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_lt_rt_center_mix",
                lt_rt_center_mix.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_lt_rt_surround_mix",
                lt_rt_surround_mix.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_lo_ro_center_mix",
                lo_ro_center_mix.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_lo_ro_surround_mix",
                lo_ro_surround_mix.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_dolby_surround_ex_mode",
                dolby_surround_ex_mode.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_dolby_headphone_mode",
                dolby_headphone_mode.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_a_d_converter_type",
                a_d_converter_type.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_dolby_stereo_rematrixing",
                stereo_rematrixing.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "e-ac3_channel_coupling",
                channel_coupling.get(),
            )
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS", "e-ac3_cpl_start_band", cpl_start_band.get()
            )
            config_profile.set("FFMPEG E-AC3 - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG E-AC3 - SETTINGS",
                "custom_command_line",
                eac3_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "Opus":
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "opus_bitrate", acodec_bitrate.get()
            )
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set("FFMPEG Opus - SETTINGS", "acodec_vbr", acodec_vbr.get())
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "acodec_application", acodec_application.get()
            )
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "frame_duration", frame_duration.get()
            )
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "packet_loss", packet_loss.get()
            )
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "acodec_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "ffmpeg_volume", ffmpeg_volume.get()
            )
            config_profile.set("FFMPEG Opus - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG Opus - SETTINGS", "mapping_family", opus_mapping_family.get()
            )
            config_profile.set(
                "FFMPEG Opus - SETTINGS",
                "custom_command_line",
                opus_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "FDK-AAC":
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_bitrate", acodec_bitrate.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "acodec_channel", acodec_channel.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "ffmpeg_volume", ffmpeg_volume.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_profile", acodec_profile.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_lowdelay", acodec_lowdelay.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_sbr_ratio", acodec_sbr_ratio.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_gapless", acodec_gapless_mode.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS",
                "fdk_aac_transport_format",
                acodec_transport_format.get(),
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_afterburner", afterburnervar.get()
            )
            config_profile.set(
                "FDK-AAC - SETTINGS",
                "fdk_aac_crccheck",
                crccheck.get().replace(" ", "."),
            )
            config_profile.set(
                "FDK-AAC - SETTINGS",
                "fdk_aac_headerperiod",
                headerperiod.get().replace(" ", "."),
            )
            config_profile.set(
                "FDK-AAC - SETTINGS",
                "fdk_aac_sbrdelay",
                sbrdelay.get().replace(" ", "."),
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_moovbox", moovbox.get().replace(" ", ".")
            )
            config_profile.set(
                "FDK-AAC - SETTINGS", "fdk_aac_tempo", acodec_atempo.get()
            )

            config_profile.set(
                "FDK-AAC - SETTINGS",
                "custom_command_line",
                ffmpeg_cmd_entrybox.get().strip(),
            )
            config_profile.set(
                "FDK-AAC - SETTINGS",
                "fdk_custom_command_line",
                fdkaac_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "MP3":
            config_profile.set(
                "FFMPEG MP3 - SETTINGS", "acodec_bitrate", acodec_bitrate.get()
            )
            config_profile.set(
                "FFMPEG MP3 - SETTINGS", "acodec_channel", acodec_channel.get()
            )
            config_profile.set("FFMPEG MP3 - SETTINGS", "mp3_vbr", mp3_vbr.get())
            config_profile.set("FFMPEG MP3 - SETTINGS", "mp3_abr", mp3_abr.get())
            config_profile.set(
                "FFMPEG MP3 - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set(
                "FFMPEG MP3 - SETTINGS", "ffmpeg_volume", ffmpeg_volume.get()
            )
            config_profile.set(
                "FFMPEG MP3 - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set("FFMPEG MP3 - SETTINGS", "tempo", acodec_atempo.get())
            if mp3_vbr.get() == "-q:a":
                config_profile.set(
                    "FFMPEG MP3 - SETTINGS", "acodec_bitrate_vbr", acodec_bitrate.get()
                )
            if mp3_vbr.get() == "off":
                config_profile.set(
                    "FFMPEG MP3 - SETTINGS",
                    "acodec_bitrate_cbr_abr",
                    acodec_bitrate.get(),
                )
            config_profile.set(
                "FFMPEG MP3 - SETTINGS",
                "custom_command_line",
                mp3_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "QAAC":
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "q_acodec_profile", q_acodec_profile.get()
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "acodec_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "q_acodec_quality", q_acodec_quality.get()
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "q_acodec_quality_amnt",
                q_acodec_quality_amnt.get(),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "q_acodec_bitrate", q_acodec_bitrate.get()
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "q_acodec_gain", q_acodec_gain.get()
            )
            config_profile.set("FFMPEG QAAC - SETTINGS", "volume", ffmpeg_volume.get())
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_normalize",
                qaac_normalize.get().replace(" ", "."),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_high_efficiency",
                qaac_high_efficiency.get().replace(" ", "."),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_nodither",
                qaac_nodither.get().replace(" ", "."),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_nodelay",
                qaac_nodelay.get().replace(" ", "."),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS", "q_gapless_mode", q_gapless_mode.get()
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_nooptimize",
                qaac_nooptimize.get().replace(" ", "."),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_threading",
                qaac_threading.get().replace(" ", "."),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_limiter",
                qaac_limiter.get().replace(" ", "."),
            )
            config_profile.set("FFMPEG QAAC - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "qaac_custom_command_line",
                qaac_cmd_entrybox.get().strip(),
            )
            config_profile.set(
                "FFMPEG QAAC - SETTINGS",
                "custom_command_line",
                ffmpeg_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "FLAC":
            config_profile.set(
                "FFMPEG FLAC - SETTINGS", "acodec_bitrate", acodec_bitrate.get()
            )
            config_profile.set(
                "FFMPEG FLAC - SETTINGS", "acodec_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG FLAC - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set("FFMPEG FLAC - SETTINGS", "volume", ffmpeg_volume.get())
            config_profile.set(
                "FFMPEG FLAC - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set("FFMPEG FLAC - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG FLAC - SETTINGS", "flac_lpc_type", acodec_flac_lpc_type.get()
            )
            config_profile.set(
                "FFMPEG FLAC - SETTINGS",
                "flac_coefficient",
                flac_acodec_coefficient.get(),
            )
            config_profile.set(
                "FFMPEG FLAC - SETTINGS",
                "flac_lpc_passes",
                acodec_flac_lpc_passes.get(),
            )
            config_profile.set(
                "FFMPEG FLAC - SETTINGS",
                "custom_command_line",
                flac_cmd_entrybox.get().strip(),
            )

        elif encoder.get() == "ALAC":
            config_profile.set(
                "FFMPEG ALAC - SETTINGS", "acodec_channel", acodec_channel.get()
            )
            config_profile.set(
                "FFMPEG ALAC - SETTINGS", "dolbyprologicii", dolby_pro_logic_ii.get()
            )
            config_profile.set("FFMPEG ALAC - SETTINGS", "volume", ffmpeg_volume.get())
            config_profile.set(
                "FFMPEG ALAC - SETTINGS", "samplerate", acodec_samplerate.get()
            )
            config_profile.set("FFMPEG ALAC - SETTINGS", "tempo", acodec_atempo.get())
            config_profile.set(
                "FFMPEG ALAC - SETTINGS",
                "alac_min_prediction_order",
                min_prediction_order.get(),
            )
            config_profile.set(
                "FFMPEG ALAC - SETTINGS",
                "alac_max_prediction_order",
                max_prediction_order.get(),
            )
            config_profile.set(
                "FFMPEG ALAC - SETTINGS",
                "custom_command_line",
                alac_cmd_entrybox.get().strip(),
            )

        # check if an invalid command is being saved
        check_for_af_filter_miss_match = grab_mini_cmd_lines()
        if check_for_af_filter_miss_match.count("-af") > 1:
            messagebox.showerror(
                parent=audio_window,
                title="Error",
                message='You cannot use multiple "-af" filter commands at once. Instead combine '
                "the commands separated by a comma.\nExample:\n\n-af "
                '"volume=0.1","atempo=23.976/24"',
            )
            return  # exit this function without saving

        # write config to file
        with open(config_profile_ini, "w") as configfile_two:
            config_profile.write(configfile_two)

    def reset_profile():  # This function resets settings to 'default'
        msg = messagebox.askyesno(
            title="Prompt",
            message="Are you sure you want to reset to default settings?",
            parent=audio_window,
        )
        if msg:
            if encoder.get() == "AC3":
                config_profile.set("FFMPEG AC3 - SETTINGS", "ac3_bitrate", "224k")
                config_profile.set("FFMPEG AC3 - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FFMPEG AC3 - SETTINGS", "ffmpeg_volume", "0.0")
                config_profile.set("FFMPEG AC3 - SETTINGS", "ac3_channel", "Original")
                config_profile.set("FFMPEG AC3 - SETTINGS", "samplerate", "Original")
                config_profile.set("FFMPEG AC3 - SETTINGS", "tempo", "Original")
                config_profile.set("FFMPEG AC3 - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "AAC":
                config_profile.set("FFMPEG AAC - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FFMPEG AAC - SETTINGS", "ffmpeg_volume", "0.0")
                config_profile.set("FFMPEG AAC - SETTINGS", "aac_bitrate", "192")
                config_profile.set("FFMPEG AAC - SETTINGS", "aac_vbr_quality", "2")
                config_profile.set("FFMPEG AAC - SETTINGS", "aac_vbr_toggle", "-c:a")
                config_profile.set("FFMPEG AAC - SETTINGS", "aac_channel", "Original")
                config_profile.set("FFMPEG AAC - SETTINGS", "samplerate", "Original")
                config_profile.set("FFMPEG AAC - SETTINGS", "tempo", "Original")
                config_profile.set("FFMPEG AAC - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "DTS":
                config_profile.set("FFMPEG DTS - SETTINGS", "dts_bitrate", "448")
                config_profile.set("FFMPEG DTS - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FFMPEG DTS - SETTINGS", "ffmpeg_volume", "0.0")
                config_profile.set("FFMPEG DTS - SETTINGS", "dts_channel", "2 (Stereo)")
                config_profile.set("FFMPEG DTS - SETTINGS", "samplerate", "Original")
                config_profile.set("FFMPEG DTS - SETTINGS", "tempo", "Original")
                config_profile.set("FFMPEG DTS - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "E-AC3":
                config_profile.set("FFMPEG E-AC3 - SETTINGS", "e-ac3_bitrate", "448k")
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_channel", "Original"
                )
                config_profile.set("FFMPEG E-AC3 - SETTINGS", "e-ac3_volume", "0.0")
                config_profile.set("FFMPEG E-AC3 - SETTINGS", "samplerate", "Original")
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_per_frame_metadata", "Default"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_mixing_level", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_room_type", "Default"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_copyright_bit", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_dialogue_level", "-31"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_surround_mode", "Default"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_original_bitstream", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_downmix_mode", "Default"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_lt_rt_center_mix", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_lt_rt_surround_mix", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_lo_ro_center_mix", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_lo_ro_surround_mix", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_dolby_surround_ex_mode", "Default"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_dolby_headphone_mode", "Default"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_a_d_converter_type", "Default"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS",
                    "e-ac3_dolby_stereo_rematrixing",
                    "Default",
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_channel_coupling", "-1"
                )
                config_profile.set(
                    "FFMPEG E-AC3 - SETTINGS", "e-ac3_cpl_start_band", "-1"
                )
                config_profile.set("FFMPEG E-AC3 - SETTINGS", "tempo", "Original")
                config_profile.set("FFMPEG E-AC3 - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "Opus":
                config_profile.set("FFMPEG Opus - SETTINGS", "opus_bitrate", "160k")
                config_profile.set("FFMPEG Opus - SETTINGS", "samplerate", "Original")
                config_profile.set("FFMPEG Opus - SETTINGS", "acodec_vbr", "VBR: On")
                config_profile.set(
                    "FFMPEG Opus - SETTINGS", "acodec_application", "Audio"
                )
                config_profile.set("FFMPEG Opus - SETTINGS", "frame_duration", "20")
                config_profile.set("FFMPEG Opus - SETTINGS", "packet_loss", "0")
                config_profile.set(
                    "FFMPEG Opus - SETTINGS", "acodec_channel", "2 (Stereo)"
                )
                config_profile.set("FFMPEG Opus - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FFMPEG Opus - SETTINGS", "ffmpeg_volume", "0.0")
                config_profile.set("FFMPEG Opus - SETTINGS", "tempo", "Original")
                config_profile.set(
                    "FFMPEG Opus - SETTINGS", "mapping_family", "Mapping -1: Auto"
                )
                config_profile.set("FFMPEG Opus - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "FDK-AAC":
                config_profile.set("FDK-AAC - SETTINGS", "fdk_aac_bitrate", "CBR: 192k")
                config_profile.set("FDK-AAC - SETTINGS", "acodec_channel", "Original")
                config_profile.set("FDK-AAC - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FDK-AAC - SETTINGS", "ffmpeg_volume", "0.0")
                config_profile.set("FDK-AAC - SETTINGS", "samplerate", "Original")
                config_profile.set(
                    "FDK-AAC - SETTINGS", "fdk_aac_profile", "AAC LC (Default)"
                )
                config_profile.set(
                    "FDK-AAC - SETTINGS", "fdk_aac_lowdelay", "Disable SBR on ELD (DEF)"
                )
                config_profile.set(
                    "FDK-AAC - SETTINGS", "fdk_aac_sbr_ratio", "Library Default"
                )
                config_profile.set(
                    "FDK-AAC - SETTINGS", "fdk_aac_gapless", "iTunSMPB (Def)"
                )
                config_profile.set(
                    "FDK-AAC - SETTINGS", "fdk_aac_transport_format", "M4A (Def)"
                )
                config_profile.set("FDK-AAC - SETTINGS", "fdk_aac_afterburner", "-a0")
                config_profile.set("FDK-AAC - SETTINGS", "fdk_aac_crccheck", "")
                config_profile.set("FDK-AAC - SETTINGS", "fdk_aac_headerperiod", "")
                config_profile.set("FDK-AAC - SETTINGS", "fdk_aac_sbrdelay", "")
                config_profile.set("FDK-AAC - SETTINGS", "fdk_aac_moovbox", "")
                config_profile.set("FDK-AAC - SETTINGS", "fdk_aac_tempo", "Original")
                config_profile.set("FDK-AAC - SETTINGS", "custom_command_line", "")
                config_profile.set("FDK-AAC - SETTINGS", "fdk_custom_command_line", "")

            elif encoder.get() == "MP3":
                config_profile.set(
                    "FFMPEG MP3 - SETTINGS", "acodec_bitrate", "VBR: -V 0"
                )
                config_profile.set(
                    "FFMPEG MP3 - SETTINGS", "acodec_channel", "Original"
                )
                config_profile.set("FFMPEG MP3 - SETTINGS", "mp3_vbr", "-q:a")
                config_profile.set("FFMPEG MP3 - SETTINGS", "mp3_abr", "")
                config_profile.set("FFMPEG MP3 - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FFMPEG MP3 - SETTINGS", "ffmpeg_volume", "0.0")
                config_profile.set("FFMPEG MP3 - SETTINGS", "samplerate", "Original")
                config_profile.set("FFMPEG MP3 - SETTINGS", "tempo", "Original")
                config_profile.set("FFMPEG MP3 - SETTINGS", "acodec_bitrate_vbr", "")
                config_profile.set(
                    "FFMPEG MP3 - SETTINGS", "acodec_bitrate_cbr_abr", ""
                )
                config_profile.set("FFMPEG MP3 - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "QAAC":
                config_profile.set(
                    "FFMPEG QAAC - SETTINGS", "q_acodec_profile", "True VBR"
                )
                config_profile.set("FFMPEG QAAC - SETTINGS", "dolbyprologicii", "")
                config_profile.set(
                    "FFMPEG QAAC - SETTINGS", "acodec_channel", "Original"
                )
                config_profile.set("FFMPEG QAAC - SETTINGS", "samplerate", "Original")
                config_profile.set(
                    "FFMPEG QAAC - SETTINGS", "q_acodec_quality", "High (Default)"
                )
                config_profile.set(
                    "FFMPEG QAAC - SETTINGS", "q_acodec_quality_amnt", "109"
                )
                config_profile.set("FFMPEG QAAC - SETTINGS", "q_acodec_bitrate", "256")
                config_profile.set("FFMPEG QAAC - SETTINGS", "q_acodec_gain", "0")
                config_profile.set("FFMPEG QAAC - SETTINGS", "volume", "0.0")
                config_profile.set("FFMPEG QAAC - SETTINGS", "qaac_normalize", "")
                config_profile.set("FFMPEG QAAC - SETTINGS", "qaac_high_efficiency", "")
                config_profile.set("FFMPEG QAAC - SETTINGS", "qaac_nodither", "")
                config_profile.set("FFMPEG QAAC - SETTINGS", "qaac_nodelay", "")
                config_profile.set(
                    "FFMPEG QAAC - SETTINGS", "q_gapless_mode", "iTunSMPB (Default)"
                )
                config_profile.set("FFMPEG QAAC - SETTINGS", "qaac_nooptimize", "")
                config_profile.set("FFMPEG QAAC - SETTINGS", "qaac_threading", "")
                config_profile.set("FFMPEG QAAC - SETTINGS", "qaac_limiter", "")
                config_profile.set("FFMPEG QAAC - SETTINGS", "tempo", "Original")
                config_profile.set(
                    "FFMPEG QAAC - SETTINGS", "qaac_custom_command_line", ""
                )
                config_profile.set("FFMPEG QAAC - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "FLAC":
                config_profile.set(
                    "FFMPEG FLAC - SETTINGS",
                    "acodec_bitrate",
                    "Level 5 - Default Compression/Speed",
                )
                config_profile.set(
                    "FFMPEG FLAC - SETTINGS", "acodec_channel", "Original"
                )
                config_profile.set("FFMPEG FLAC - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FFMPEG FLAC - SETTINGS", "volume", "0.0")
                config_profile.set("FFMPEG FLAC - SETTINGS", "samplerate", "Original")
                config_profile.set("FFMPEG FLAC - SETTINGS", "tempo", "Original")
                config_profile.set("FFMPEG FLAC - SETTINGS", "flac_lpc_type", "Default")
                config_profile.set("FFMPEG FLAC - SETTINGS", "flac_coefficient", "15")
                config_profile.set(
                    "FFMPEG FLAC - SETTINGS", "flac_lpc_passes", "Default"
                )
                config_profile.set("FFMPEG FLAC - SETTINGS", "custom_command_line", "")

            elif encoder.get() == "ALAC":
                config_profile.set(
                    "FFMPEG ALAC - SETTINGS", "acodec_channel", "Original"
                )
                config_profile.set("FFMPEG ALAC - SETTINGS", "dolbyprologicii", "")
                config_profile.set("FFMPEG ALAC - SETTINGS", "volume", "0.0")
                config_profile.set("FFMPEG ALAC - SETTINGS", "samplerate", "Original")
                config_profile.set("FFMPEG ALAC - SETTINGS", "tempo", "Original")
                config_profile.set(
                    "FFMPEG ALAC - SETTINGS", "alac_min_prediction_order", "4"
                )
                config_profile.set(
                    "FFMPEG ALAC - SETTINGS", "alac_max_prediction_order", "6"
                )
                config_profile.set("FFMPEG ALAC - SETTINGS", "custom_command_line", "")

            with open(config_profile_ini, "w") as configfile_two:
                config_profile.write(configfile_two)
            audio_window.destroy()  # Closes Audio Window
            sleep(0.25)  # Sleeps the program for 1/4th of a second
            openaudiowindow()  # Re-Opens the Audio Window with the 'Default' settings

    # ----------------------------------------------------------------------------------------------- Profile Functions

    # FFMPEG Volume Spinbox Menu + HoverToolTip -----------------------------------------------------------------------
    def volume_right_click_options():
        def popup_auto_e_b_menu(
            e,
        ):  # Function for mouse button 3 (right click) to pop up menu
            reset_volume_menu.tk_popup(
                e.x_root, e.y_root
            )  # This gets the posision of 'e'

        reset_volume_menu = Menu(
            ffmpeg_volume_spinbox, tearoff=False
        )  # Right click menu
        reset_volume_menu.add_command(
            label="Reset to 0", command=lambda: ffmpeg_volume.set("0.0")
        )
        reset_volume_menu.add_separator()
        reset_volume_menu.add_command(
            label="Set to 5", command=lambda: ffmpeg_volume.set("5.0")
        )
        reset_volume_menu.add_command(
            label="Set to 10", command=lambda: ffmpeg_volume.set("10.0")
        )
        reset_volume_menu.add_command(
            label="Set to 15", command=lambda: ffmpeg_volume.set("15.0")
        )
        reset_volume_menu.add_command(
            label="Set to 20", command=lambda: ffmpeg_volume.set("20.0")
        )
        reset_volume_menu.add_separator()
        reset_volume_menu.add_command(
            label="Set to -5", command=lambda: ffmpeg_volume.set("-5.0")
        )
        reset_volume_menu.add_command(
            label="Set to -10", command=lambda: ffmpeg_volume.set("-10.0")
        )
        reset_volume_menu.add_command(
            label="Set to -15", command=lambda: ffmpeg_volume.set("-15.0")
        )
        reset_volume_menu.add_command(
            label="Set to -20", command=lambda: ffmpeg_volume.set("-20.0")
        )
        ffmpeg_volume_spinbox.bind(
            "<Button-3>", popup_auto_e_b_menu
        )  # Uses mouse button 3 (right click) to open
        Hovertip(
            ffmpeg_volume_spinbox, "Right click for more options", hover_delay=600
        )  # Hover tip tool-tip

    # ----------------------------------------------------------------------- FFMPEG Volume Spinbox Menu + HoverToolTip

    # Parsers ---------------------------------------------------------------------------------------------------------
    # Audio Codec ConfigParser
    config_profile = ConfigParser()
    config_profile.read(config_profile_ini)
    # Audio Codec Window Local ConfigParser
    audio_win_parser = ConfigParser()
    audio_win_parser.read(config_file)
    # --------------------------------------------------------------------------------------------------------- Parsers

    def acodec_atempo_selected(event):
        selection = acodec_atempo_combobox.get()
        if selection in acodec_atempo_choices:
            acodec_atempo = acodec_atempo_choices[selection]

    # AC3 Window ------------------------------------------------------------------------------------------------------
    if encoder.get() == "AC3":
        audio_window = Toplevel()
        audio_window.title("AC3 Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - ac3 - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - ac3"] == "no"
        ):
            window_height = 410
            window_width = 590
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - ac3 - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - ac3"] == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - ac3 - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for ac3_n in range(3):
            audio_window.grid_columnconfigure(ac3_n, weight=1)
        for ac3_n in range(8):
            audio_window.grid_rowconfigure(ac3_n, weight=1)

        # Buttons -------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=8, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )

        # ------------------------------------------------------------------------------------------------- Buttons

        # Audio Bitrate Selection ---------------------------------------------------------------------------------
        acodec_bitrate = StringVar(audio_window)
        acodec_bitrate_choices = {
            "64k": "-b:a 64k ",
            "128k": "-b:a 128k ",
            "160k": "-b:a 160k ",
            "192k": "-b:a 192k ",
            "224k": "-b:a 224k ",
            "256k": "-b:a 256k ",
            "288k": "-b:a 288k ",
            "320k": "-b:a 320k ",
            "352k": "-b:a 352k ",
            "384k": "-b:a 384k ",
            "448k": "-b:a 448k ",
            "512k": "-b:a 512k ",
            "576k": "-b:a 576k ",
            "640k": "-b:a 640k ",
        }
        acodec_bitrate.set(
            config_profile["FFMPEG AC3 - SETTINGS"]["ac3_bitrate"]
        )  # set the default option
        acodec_bitrate_menu_label = Label(
            audio_window, text="Bitrate :", background="#434547", foreground="white"
        )
        acodec_bitrate_menu_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_bitrate_menu = OptionMenu(
            audio_window, acodec_bitrate, *acodec_bitrate_choices.keys()
        )
        acodec_bitrate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_bitrate_menu.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_bitrate_menu["menu"].configure(activebackground="dim grey")
        acodec_bitrate_menu.bind("<Enter>", acodec_bitrate_menu_hover)
        acodec_bitrate_menu.bind("<Leave>", acodec_bitrate_menu_hover_leave)
        # ------------------------------------------------------------------------------------------- Audio Bitrate

        # Audio Stream Selection ----------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(
            next(iter(acodec_stream_track_counter))
        )  # set the default option
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # ---------------------------------------------------------------------------------------------------------

        # Audio Channel Selection ---------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "2.1 (Stereo)": "-ac 3 ",
            "4.0 (Quad)": "-ac 4 ",
            "5.0 (Surround)": "-ac 5 ",
            "5.1 (Surround)": "-ac 6 ",
        }
        acodec_channel.set(
            config_profile["FFMPEG AC3 - SETTINGS"]["ac3_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ------------------------------------------------------------------------------------------- Audio Channel

        # Dolby Pro Logic II --------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=4,
            column=2,
            columnspan=1,
            rowspan=1,
            padx=10,
            pady=(20, 5),
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG AC3 - SETTINGS"]["dolbyprologicii"]
        )
        # -------------------------------------------------------------------------------------------------- DPL II

        # Audio Volume Selection ----------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG AC3 - SETTINGS"]["ffmpeg_volume"])
        volume_right_click_options()  # Run function for right click options for volume spinbox
        # -------------------------------------------------------------------------------------------------- Volume

        # Audio Sample Rate Selection -----------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "32000 Hz": "-ar 32000 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG AC3 - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_samplerate_menu.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)

        # --------------------------------------------------------------------------------------------- Sample Rate

        # Entry Box for Custom Command Line -----------------------------------------------------------------------
        def ac3_cmd(*args):
            global ac3_custom_cmd_input
            if ac3_custom_cmd.get().strip() == "":
                ac3_custom_cmd_input = ""
            else:
                cstmcmd = ac3_custom_cmd.get().strip()
                ac3_custom_cmd_input = cstmcmd + " "

        ac3_custom_cmd = StringVar()
        ac3_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        ac3_cmd_entrybox_label.grid(
            row=5, column=0, columnspan=2, padx=10, pady=(15, 0), sticky=N + S + W + E
        )
        ac3_cmd_entrybox = Entry(
            audio_window,
            textvariable=ac3_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        ac3_cmd_entrybox.grid(
            row=6, column=0, columnspan=3, padx=10, pady=(0, 15), sticky=W + E
        )
        ac3_custom_cmd.trace("w", ac3_cmd)
        ac3_custom_cmd.set(
            config_profile["FFMPEG AC3 - SETTINGS"]["custom_command_line"]
        )
        # ------------------------------------------------------------------------------------- Custom Command Line

        # Audio Atempo Selection ----------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ------------------------------------------------------------------------------------------------ Audio Atempo
    # ------------------------------------------------------------------------------------------------------------- AC3

    # AAC Window ------------------------------------------------------------------------------------------------------
    elif encoder.get() == "AAC":
        audio_window = Toplevel()
        audio_window.title("AAC Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - aac - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - aac"] == "no"
        ):
            window_height = 480
            window_width = 628
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - aac - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - aac"] == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - aac - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for aac_n in range(3):
            audio_window.grid_columnconfigure(aac_n, weight=1)
        for aac_n in range(10):
            audio_window.grid_rowconfigure(aac_n, weight=1)

        # Buttons -----------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=10, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )

        # ----------------------------------------------------------------------------------------------------- Buttons

        # Entry Box for Custom Command Line ---------------------------------------------------------------------------
        def aac_cmd(*args):
            global aac_custom_cmd_input
            if aac_custom_cmd.get().strip() == "":
                aac_custom_cmd_input = ""
            else:
                cstmcmd = aac_custom_cmd.get().strip()
                aac_custom_cmd_input = cstmcmd + " "

        aac_custom_cmd = StringVar()
        aac_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        aac_cmd_entrybox_label.grid(
            row=6, column=0, columnspan=2, padx=10, pady=(0, 0), sticky=N + S + W + E
        )
        aac_cmd_entrybox = Entry(
            audio_window,
            textvariable=aac_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        aac_cmd_entrybox.grid(
            row=7, column=0, columnspan=3, padx=10, pady=(0, 0), sticky=W + E
        )
        aac_custom_cmd.trace("w", aac_cmd)
        aac_custom_cmd.set(
            config_profile["FFMPEG AAC - SETTINGS"]["custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- Custom Command Line

        # Entry Box for Track Title -----------------------------------------------------------------------------------
        def aac_title_check(*args):
            global aac_title_input
            if aac_title.get().strip() == "":
                aac_title_input = ""
            else:
                title_cmd = aac_title.get().strip()
                aac_title_input = "-metadata:s:a:0 title=" + '"' + title_cmd + '"' + " "

        aac_title = StringVar()
        aac_title_entrybox_label = Label(
            audio_window,
            text="Track Name :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        aac_title_entrybox_label.grid(
            row=8, column=0, columnspan=2, padx=10, pady=(5, 0), sticky=N + S + W + E
        )
        aac_title_entrybox = Entry(
            audio_window, textvariable=aac_title, borderwidth=4, background="#CACACA"
        )
        aac_title_entrybox.grid(
            row=9, column=0, columnspan=3, padx=10, pady=(0, 10), sticky=W + E
        )
        aac_title.trace("w", aac_title_check)
        aac_title.set("")
        # ------------------------------------------------------------------------------------------------- Track Title

        # Audio Channel Selection -------------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "2.1 (Stereo)": "-ac 3 ",
            "4.0 (Surround)": "-ac 4 ",
            "5.0 (Surround)": "-ac 5 ",
            "5.1 (Surround)": "-ac 6 ",
            "6.1 (Surround)": "-ac 7 ",
            "7.1 (Surround)": "-ac 8 ",
        }
        acodec_channel.set(
            config_profile["FFMPEG AAC - SETTINGS"]["aac_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ------------------------------------------------------------------------------------- Audio Channel Selection

        # Dolby Pro Logic II ------------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=4,
            column=0,
            columnspan=1,
            rowspan=1,
            padx=10,
            pady=(15, 15),
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG AAC - SETTINGS"]["dolbyprologicii"]
        )
        # ------------------------------------------------------------------------------------------------------ DPL II

        # Audio Volume Selection --------------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG AAC - SETTINGS"]["ffmpeg_volume"])
        volume_right_click_options()
        # ------------------------------------------------------------------------------------------------------ Volume

        # Audio Bitrate Spinbox ---------------------------------------------------------------------------------------
        global aac_bitrate_spinbox
        aac_bitrate_spinbox = StringVar()
        aac_acodec_bitrate_spinbox_label = Label(
            audio_window, text="Bitrate :", background="#434547", foreground="white"
        )
        aac_acodec_bitrate_spinbox_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        aac_acodec_bitrate_spinbox = Spinbox(
            audio_window,
            from_=1,
            to=800,
            increment=2.0,
            justify=CENTER,
            wrap=True,
            textvariable=aac_bitrate_spinbox,
        )
        aac_acodec_bitrate_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        aac_acodec_bitrate_spinbox.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        aac_bitrate_spinbox.set(
            int(config_profile["FFMPEG AAC - SETTINGS"]["aac_bitrate"])
        )
        # --------------------------------------------------------------------------------------- Audio Bitrate Spinbox

        # Vbr Toggle --------------------------------------------------------------------------------------------------
        global aac_vbr_toggle
        aac_vbr_toggle = StringVar()
        aac_vbr_toggle.set(
            config_profile["FFMPEG AAC - SETTINGS"]["aac_vbr_toggle"] + " "
        )

        def aac_vbr_trace(*args):  # Swap Spin Box Between CBR and VBR
            if aac_vbr_toggle.get() == "-c:a ":
                global aac_bitrate_spinbox
                aac_acodec_bitrate_spinbox_label = Label(
                    audio_window,
                    text="Bitrate :",
                    background="#434547",
                    foreground="white",
                )
                aac_acodec_bitrate_spinbox_label.grid(
                    row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
                )
                aac_acodec_bitrate_spinbox = Spinbox(
                    audio_window,
                    from_=1,
                    to=800,
                    increment=2.0,
                    justify=CENTER,
                    wrap=True,
                    textvariable=aac_bitrate_spinbox,
                )
                aac_acodec_bitrate_spinbox.configure(
                    background="#23272A",
                    foreground="white",
                    highlightthickness=1,
                    buttonbackground="black",
                    width=15,
                    readonlybackground="#23272A",
                )
                aac_acodec_bitrate_spinbox.grid(
                    row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
                )
                aac_bitrate_spinbox.set(
                    int(config_profile["FFMPEG AAC - SETTINGS"]["aac_bitrate"])
                )
            elif (
                aac_vbr_toggle.get() == "-q:a "
            ):  # This enables VBR Spinbox -----------------------------------------
                global aac_quality_spinbox
                aac_quality_spinbox = StringVar()
                aac_acodec_quality_spinbox_label = Label(
                    audio_window,
                    text="VBR Quality :",
                    background="#434547",
                    foreground="white",
                )
                aac_acodec_quality_spinbox_label.grid(
                    row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
                )
                aac_acodec_quality_spinbox = Spinbox(
                    audio_window,
                    from_=0.1,
                    to=5,
                    increment=0.1,
                    justify=CENTER,
                    wrap=True,
                    textvariable=aac_quality_spinbox,
                )
                aac_acodec_quality_spinbox.configure(
                    background="#23272A",
                    foreground="white",
                    highlightthickness=1,
                    buttonbackground="black",
                    width=15,
                    readonlybackground="#23272A",
                )
                aac_acodec_quality_spinbox.grid(
                    row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
                )
                aac_quality_spinbox.set(
                    float(config_profile["FFMPEG AAC - SETTINGS"]["aac_vbr_quality"])
                )
                # ----------------------------------------------------------------------------------------- VBR Spinbox

        aac_vbr_toggle_checkbox = Checkbutton(
            audio_window,
            text=" Variable\n Bit-Rate",
            variable=aac_vbr_toggle,
            onvalue="-q:a ",
            offvalue="-c:a ",
            command=aac_vbr_trace,
        )
        aac_vbr_toggle_checkbox.grid(
            row=4,
            column=1,
            columnspan=1,
            rowspan=2,
            padx=10,
            pady=3,
            sticky=N + S + E + W,
        )
        aac_vbr_toggle_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        aac_vbr_trace()
        aac_vbr_toggle.trace("w", aac_vbr_trace)
        # -------------------------------------------------------------------------------------------------- Vbr Toggle

        # Audio Stream Selection --------------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(next(iter(acodec_stream_track_counter)))
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # -------------------------------------------------------------------------------------- Audio Stream Selection

        # Audio Sample Rate Selection ---------------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "8000 Hz": "-ar 8000 ",
            "11025 Hz": "-ar 11025 ",
            "12000 Hz": "-ar 12000 ",
            "16000 Hz": "-ar 16000 ",
            "22050 Hz": "-ar 22050 ",
            "24000 Hz": "-ar 24000 ",
            "32000 Hz": "-ar 32000 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG AAC - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_samplerate_menu.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)
        # --------------------------------------------------------------------------------- Audio Sample Rate Selection

        # Audio Atempo Selection -------------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ----------------------------------------------------------------------------------------------- Audio Atempto
    # ------------------------------------------------------------------------------------------------------ AAC Window

    # DTS Window ------------------------------------------------------------------------------------------------------
    elif encoder.get() == "DTS":
        audio_window = Toplevel()
        audio_window.title("DTS Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - dts - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - dts"] == "no"
        ):
            window_height = 420
            window_width = 550
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - dts - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - dts"] == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - dts - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for dts_n in range(3):
            audio_window.grid_columnconfigure(dts_n, weight=1)
        for dts_n in range(9):
            audio_window.grid_rowconfigure(dts_n, weight=1)

        def dts_setting_choice_trace(*args):
            if dts_settings.get() == "DTS Encoder":
                achannel_menu.config(state=NORMAL)
                acodec_channel.set(
                    config_profile["FFMPEG DTS - SETTINGS"]["dts_channel"]
                )
                ffmpeg_volume_spinbox.config(state=NORMAL)
                ffmpeg_volume.set(
                    config_profile["FFMPEG DTS - SETTINGS"]["ffmpeg_volume"]
                )
                acodec_samplerate_menu.config(state=NORMAL)
                acodec_samplerate.set(
                    config_profile["FFMPEG DTS - SETTINGS"]["samplerate"]
                )
                dts_acodec_bitrate_spinbox.config(state=NORMAL)
                dts_bitrate_spinbox.set(
                    int(config_profile["FFMPEG DTS - SETTINGS"]["dts_bitrate"])
                )
                acodec_atempo.set(config_profile["FFMPEG DTS - SETTINGS"]["tempo"])
            else:
                achannel_menu.config(state=DISABLED)
                ffmpeg_volume_spinbox.config(state=DISABLED)
                acodec_samplerate_menu.config(state=DISABLED)
                dts_acodec_bitrate_spinbox.config(state=DISABLED)
                dolby_pro_logic_ii_checkbox.config(state=DISABLED)

        # Buttons -----------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=9, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )

        # ----------------------------------------------------------------------------------------------------- Buttons

        # Entry Box for Custom Command Line ---------------------------------------------------------------------------
        def dts_cmd(*args):
            global dts_custom_cmd_input
            if dts_custom_cmd.get().strip() == "":
                dts_custom_cmd_input = ""
            else:
                cstmcmd = dts_custom_cmd.get().strip()
                dts_custom_cmd_input = cstmcmd + " "

        dts_custom_cmd = StringVar()
        dts_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        dts_cmd_entrybox_label.grid(
            row=7, column=0, columnspan=2, padx=10, pady=(15, 0), sticky=N + S + W + E
        )
        dts_cmd_entrybox = Entry(
            audio_window,
            textvariable=dts_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        dts_cmd_entrybox.grid(
            row=8, column=0, columnspan=3, padx=10, pady=(0, 10), sticky=W + E
        )
        dts_custom_cmd.trace("w", dts_cmd)
        dts_custom_cmd.set(
            config_profile["FFMPEG DTS - SETTINGS"]["custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- Custom Command Line

        # Audio Bitrate Spinbox ---------------------------------------------------------------------------------------
        global dts_bitrate_spinbox
        dts_bitrate_spinbox = StringVar()
        dts_acodec_bitrate_spinbox_label = Label(
            audio_window, text="Bitrate :", background="#434547", foreground="white"
        )
        dts_acodec_bitrate_spinbox_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dts_acodec_bitrate_spinbox = Spinbox(
            audio_window,
            from_=250,
            to=3840,
            increment=1.0,
            justify=CENTER,
            wrap=True,
            textvariable=dts_bitrate_spinbox,
            state=DISABLED,
            disabledbackground="grey",
        )
        dts_acodec_bitrate_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        dts_acodec_bitrate_spinbox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dts_bitrate_spinbox.set(
            int(config_profile["FFMPEG DTS - SETTINGS"]["dts_bitrate"])
        )
        # --------------------------------------------------------------------------------------- Audio Bitrate Spinbox

        # Audio Channel Selection -------------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {"(Mono)": "-ac 1 ", "2 (Stereo)": "-ac 2 "}
        acodec_channel.set(
            config_profile["FFMPEG DTS - SETTINGS"]["dts_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=W + E + N + S
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            state=DISABLED,
        )
        achannel_menu.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ------------------------------------------------------------------------------------- Audio Channel Selection

        # DTS Encoder(s) ----------------------------------------------------------------------------------------------
        dts_settings = StringVar(audio_window)
        dts_settings_choices = {
            "Reduce to Core": "-bsf:a dca_core -c:a copy ",
            "Extract HD Track": "-c:a copy ",
            "DTS Encoder": "-strict -2 -c:a dca ",
        }
        dts_settings.set("Reduce to Core")  # set the default option
        dts_settings_label = Label(
            audio_window,
            text="DTS Settings :",
            background="#434547",
            foreground="white",
        )
        dts_settings_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dts_settings_menu = OptionMenu(
            audio_window, dts_settings, *dts_settings_choices.keys()
        )
        dts_settings_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        dts_settings_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dts_settings_menu.bind("<Enter>", dts_settings_menu_hover)
        dts_settings_menu.bind("<Leave>", dts_settings_menu_hover_leave)
        dts_settings.trace("w", dts_setting_choice_trace)
        # ------------------------------------------------------------------------------------------------ DTS Encoders

        # Dolby Pro Logic II ------------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)" and dts_settings.get() == "DTS Encoder":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=4,
            column=0,
            columnspan=1,
            rowspan=2,
            padx=10,
            pady=(10, 3),
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG DTS - SETTINGS"]["dolbyprologicii"]
        )
        # ------------------------------------------------------------------------------------------------------ DPL II

        # Audio Volume Selection --------------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG DTS - SETTINGS"]["ffmpeg_volume"])
        volume_right_click_options()
        # ------------------------------------------------------------------------------------------------------ Volume

        # Audio Sample Rate Selection ---------------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "16000 Hz": "-ar 16000 ",
            "22050 Hz": "-ar 22050 ",
            "24000 Hz": "-ar 24000 ",
            "32000 Hz": "-ar 32000 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG DTS - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            state=DISABLED,
        )
        acodec_samplerate_menu.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)
        # --------------------------------------------------------------------------------- Audio Sample Rate Selection

        # Audio Stream Selection --------------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(next(iter(acodec_stream_track_counter)))
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # ------------------------------------------------------------------------------------------------ Audio Stream

        # Audio Atempo Selection ---------------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ------------------------------------------------------------------------------------------------ Audio Atempo
    # ------------------------------------------------------------------------------------------------------------- DTS

    # Opus Window -----------------------------------------------------------------------------------------------------
    elif encoder.get() == "Opus":
        audio_window = Toplevel()
        audio_window.title("Opus Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - opus - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - opus"] == "no"
        ):
            window_height = 580
            window_width = 650
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - opus - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - opus"]
            == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - opus - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        advanced_label = Label(
            audio_window,
            text="- - - - - - - - - - - - - - - - - - - - Advanced Settings - - - - - - - - - - - "
            "- - - - - - - - -",
            background="#434547",
            foreground="white",
            relief=GROOVE,
        )
        advanced_label.grid(
            row=7, column=0, columnspan=3, padx=10, pady=(5, 0), sticky=W + E
        )

        advanced_label_end = Label(
            audio_window,
            text="- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - "
            "- - - - - - - - -",
            background="#434547",
            foreground="white",
            relief=GROOVE,
        )
        advanced_label_end.grid(
            row=10, column=0, columnspan=3, padx=10, pady=(5, 0), sticky=W + E
        )

        for opus_n in range(3):
            audio_window.grid_columnconfigure(opus_n, weight=1)
        for opus_n in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13]:
            audio_window.grid_rowconfigure(opus_n, weight=1)

        # Buttons -----------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=13, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        # ----------------------------------------------------------------------------------------------------- Buttons

        # Audio Bitrate Menu ------------------------------------------------------------------------------------------
        acodec_bitrate = StringVar(audio_window)
        acodec_bitrate_choices = {
            "6k": "-b:a 6k ",
            "8k": "-b:a 8k ",
            "16k": "-b:a 16k ",
            "24k": "-b:a 24k ",
            "40k": "-b:a 40k ",
            "48k": "-b:a 48k ",
            "64k": "-b:a 64k ",
            "96k": "-b:a 96k ",
            "112k": "-b:a 112k ",
            "128k": "-b:a 128k ",
            "160k": "-b:a 160k ",
            "192k": "-b:a 192k ",
            "256k": "-b:a 256k ",
            "320k": "-b:a 320k ",
            "448k": "-b:a 448k ",
            "510k": "-b:a 510k ",
        }
        acodec_bitrate.set(
            config_profile["FFMPEG Opus - SETTINGS"]["opus_bitrate"]
        )  # set the default option
        acodec_bitrate_menu_label = Label(
            audio_window, text="Quality :", background="#434547", foreground="white"
        )
        acodec_bitrate_menu_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_bitrate_menu = OptionMenu(
            audio_window, acodec_bitrate, *acodec_bitrate_choices.keys()
        )
        acodec_bitrate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_bitrate_menu.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_bitrate_menu["menu"].configure(activebackground="dim grey")
        acodec_bitrate_menu.bind("<Enter>", acodec_bitrate_menu_hover)
        acodec_bitrate_menu.bind("<Leave>", acodec_bitrate_menu_hover_leave)
        # ----------------------------------------------------------------------------------------------- Audio Bitrate

        # Audio Sample Rate Selection ---------------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "8000 Hz": "-ar 8000 ",
            "12000 Hz": "-ar 12000 ",
            "16000 Hz": "-ar 16000 ",
            "24000 Hz": "-ar 24000 ",
            "48000 Hz": "-ar 48000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG Opus - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_samplerate_menu.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)

        # --------------------------------------------------------------------------------- Audio Sample Rate Selection

        # Entry Box for Custom Command Line ---------------------------------------------------------------------------
        def opus_cmd(*args):
            global opus_custom_cmd_input
            if opus_custom_cmd.get().strip() == "":
                opus_custom_cmd_input = ""
            else:
                cstmcmd = opus_custom_cmd.get().strip()
                opus_custom_cmd_input = cstmcmd + " "

        opus_custom_cmd = StringVar()
        opus_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        opus_cmd_entrybox_label.grid(
            row=11, column=0, columnspan=2, padx=10, pady=(10, 0), sticky=N + S + W + E
        )
        opus_cmd_entrybox = Entry(
            audio_window,
            textvariable=opus_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        opus_cmd_entrybox.grid(
            row=12, column=0, columnspan=3, padx=10, pady=(0, 15), sticky=W + E
        )
        opus_custom_cmd.trace("w", opus_cmd)
        opus_custom_cmd.set(
            config_profile["FFMPEG Opus - SETTINGS"]["custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- Custom Command Line

        # Audio VBR Toggle --------------------------------------------------------------------------------------------
        acodec_vbr = StringVar(audio_window)
        acodec_vbr_choices = {
            "VBR: On": "",
            "VBR: Off": "-vbr 0 ",
            "VBR: Constrained": "-vbr 2 ",
        }
        acodec_vbr.set(
            config_profile["FFMPEG Opus - SETTINGS"]["acodec_vbr"]
        )  # set the default option
        acodec_vbr_menu_label = Label(
            audio_window, text="VBR :", background="#434547", foreground="white"
        )
        acodec_vbr_menu_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_vbr_menu = OptionMenu(
            audio_window, acodec_vbr, *acodec_vbr_choices.keys()
        )
        acodec_vbr_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_vbr_menu.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_vbr_menu["menu"].configure(activebackground="dim grey")
        acodec_vbr_menu.bind("<Enter>", acodec_vbr_menu_hover)
        acodec_vbr_menu.bind("<Leave>", acodec_vbr_menu_hover_leave)
        # -------------------------------------------------------------------------------------------------- VBR Toggle

        # Audio Application Selection ---------------------------------------------------------------------------------
        acodec_application = StringVar(audio_window)
        acodec_application_choices = {
            "Audio": "",
            "VoIP": "-application 2048 ",
            "Low Delay": "-application 2051 ",
        }
        acodec_application.set(
            config_profile["FFMPEG Opus - SETTINGS"]["acodec_application"]
        )  # set the def option
        acodec_application_menu_label = Label(
            audio_window,
            text="Application:\n*Default is 'Audio'*",
            background="#434547",
            foreground="white",
        )
        acodec_application_menu_label.grid(
            row=8, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_application_menu = OptionMenu(
            audio_window, acodec_application, *acodec_application_choices.keys()
        )
        acodec_application_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_application_menu.grid(
            row=9, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_application_menu["menu"].configure(activebackground="dim grey")
        acodec_application_menu.bind("<Enter>", acodec_application_menu_hover)
        acodec_application_menu.bind("<Leave>", acodec_application_menu_hover_leave)
        # ------------------------------------------------------------------------------------------------- Application

        # Audio Frame Duration Spinbox --------------------------------------------------------------------------------
        global frame_duration
        frame_duration_values = (2.5, 5, 10, 20, 40, 60, 80, 100, 120)
        frame_duration = StringVar(audio_window)
        frame_duration_label = Label(
            audio_window,
            text="Frame Duration:\n*Default is '20'*",
            background="#434547",
            foreground="white",
        )
        frame_duration_label.grid(
            row=8, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        frame_duration_spinbox = Spinbox(
            audio_window,
            values=frame_duration_values,
            justify=CENTER,
            wrap=True,
            textvariable=frame_duration,
            width=13,
        )
        frame_duration_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
        )
        frame_duration_spinbox.grid(
            row=9, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        frame_duration.set(
            int(config_profile["FFMPEG Opus - SETTINGS"]["frame_duration"])
        )  # default option
        # ---------------------------------------------------------------------------------------------- Frame Duration

        # Audio Packet Loss Spinbox --------------------------------------------------------------------------------
        global packet_loss
        packet_loss = StringVar(audio_window)
        packet_loss_label = Label(
            audio_window,
            text="Packet Loss:\n*Default is '0'*",
            background="#434547",
            foreground="white",
        )
        packet_loss_label.grid(
            row=8, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        packet_loss_spinbox = Spinbox(
            audio_window,
            from_=0,
            to=100,
            justify=CENTER,
            wrap=True,
            textvariable=packet_loss,
            width=13,
        )
        packet_loss_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
        )
        packet_loss_spinbox.grid(
            row=9, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        packet_loss.set(
            int(config_profile["FFMPEG Opus - SETTINGS"]["packet_loss"])
        )  # default option
        # ------------------------------------------------------------------------------------------------- Packet Loss

        # Audio Channel Selection -------------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "5.0 (Surround)": "-ac 5 ",
            "5.1 (Surround)": "-ac 6 ",
            "6.1 (Surround)": "-ac 7 ",
            "7.1 (Surround)": "-ac 8 ",
        }
        acodec_channel.set(config_profile["FFMPEG Opus - SETTINGS"]["acodec_channel"])
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ------------------------------------------------------------------------------------------- Channel Selection

        # Audio Stream Selection --------------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(next(iter(acodec_stream_track_counter)))
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # -------------------------------------------------------------------------------------- Audio Stream Selection

        # Dolby Pro Logic II ------------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=4,
            column=0,
            columnspan=1,
            rowspan=2,
            padx=10,
            pady=(15, 5),
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG Opus - SETTINGS"]["dolbyprologicii"]
        )
        # ------------------------------------------------------------------------------------------------------ DPL II

        # Opus Mapping Family -----------------------------------------------------------------------------------------
        opus_mapping_family = StringVar(audio_window)
        opus_mapping_family_choices = {
            "Mapping -1: Auto": "",
            "Mapping 0: Mono/Stereo": "-mapping_family 0 ",
            "Mapping 1: Multi-Channel": "-mapping_family 1 ",
        }
        opus_mapping_family.set(
            config_profile["FFMPEG Opus - SETTINGS"]["mapping_family"]
        )  # set the default option
        opus_mapping_family_menu_label = Label(
            audio_window,
            text="Mapping Family :",
            background="#434547",
            foreground="white",
        )
        opus_mapping_family_menu_label.grid(
            row=4, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        opus_mapping_family_menu = OptionMenu(
            audio_window, opus_mapping_family, *opus_mapping_family_choices.keys()
        )
        opus_mapping_family_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=10,
            anchor=W,
        )
        opus_mapping_family_menu.grid(
            row=5, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        opus_mapping_family_menu["menu"].configure(activebackground="dim grey")
        opus_mapping_family_menu.bind("<Enter>", opus_mapping_family_menu_hover)
        opus_mapping_family_menu.bind("<Leave>", opus_mapping_family_menu_hover_leave)
        # ----------------------------------------------------------------------------------------- Opus Mapping Family

        # Audio Volume Selection --------------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=(3, 10), sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG Opus - SETTINGS"]["ffmpeg_volume"])
        volume_right_click_options()
        # ------------------------------------------------------------------------------------------------------ Volume

        # Audio Atempo Selection ---------------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ------------------------------------------------------------------------------------------------ Audio Atempo
    # ----------------------------------------------------------------------------------------------------- Opus Window

    # MP3 Window ------------------------------------------------------------------------------------------------------
    elif encoder.get() == "MP3":
        audio_window = Toplevel()
        audio_window.title("MP3 Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - mp3 - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - mp3"] == "no"
        ):
            window_height = 360
            window_width = 550
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - mp3 - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - mp3"] == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - mp3 - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for mp3_n in range(3):
            audio_window.grid_columnconfigure(mp3_n, weight=1)
        for mp3_n in range(7):
            audio_window.grid_rowconfigure(mp3_n, weight=1)

        def update_cfg_mp3():
            config_profile.set("FFMPEG MP3 - SETTINGS", "mp3_vbr", mp3_vbr.get())
            config_profile.set("FFMPEG MP3 - SETTINGS", "mp3_abr", mp3_abr.get())
            with open(config_profile_ini, "w") as configfile_two:
                config_profile.write(configfile_two)

        # Using VBR or CBR/ABR ----------------------------------------------------------------------------------------
        def mp3_bitrate_type(*args):
            global acodec_bitrate
            global acodec_bitrate_choices

            def acodec_bitrate_menu_hover(e):
                acodec_bitrate_menu["bg"] = "grey"
                acodec_bitrate_menu["activebackground"] = "grey"

            def acodec_bitrate_menu_hover_leave(e):
                acodec_bitrate_menu["bg"] = "#23272A"

            acodec_bitrate = StringVar()

            if mp3_vbr.get() == "-q:a":
                mp3_abr.set("")
                mp3_abr_checkbox.config(state=DISABLED)

                acodec_bitrate_choices = {
                    "VBR: -V 0": "-q:a 0 ",
                    "VBR: -V 1": "-q:a 1 ",
                    "VBR: -V 2": "-q:a 2 ",
                    "VBR: -V 3": "-q:a 3 ",
                    "VBR: -V 4": "-q:a 4 ",
                    "VBR: -V 5": "-q:a 5 ",
                    "VBR: -V 6": "-q:a 6 ",
                    "VBR: -V 7": "-q:a 7 ",
                }
                if config_profile["FFMPEG MP3 - SETTINGS"]["acodec_bitrate_vbr"] == "":
                    acodec_bitrate.set("VBR: -V 0")
                else:
                    acodec_bitrate.set(
                        config_profile["FFMPEG MP3 - SETTINGS"]["acodec_bitrate_vbr"]
                    )
                acodec_bitrate_menu_label = Label(
                    audio_window,
                    text="Quality :",
                    background="#434547",
                    foreground="white",
                )
                acodec_bitrate_menu_label.grid(
                    row=2, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
                )
                acodec_bitrate_menu = OptionMenu(
                    audio_window, acodec_bitrate, *acodec_bitrate_choices.keys()
                )
                acodec_bitrate_menu.config(
                    background="#23272A", foreground="white", highlightthickness=1
                )
                acodec_bitrate_menu.grid(
                    row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
                )
                acodec_bitrate_menu["menu"].configure(activebackground="dim grey")
                acodec_bitrate_menu.bind("<Enter>", acodec_bitrate_menu_hover)
                acodec_bitrate_menu.bind("<Leave>", acodec_bitrate_menu_hover_leave)

            elif mp3_vbr.get() == "off":
                mp3_abr_checkbox.config(state=NORMAL)
                mp3_abr.set(config_profile["FFMPEG MP3 - SETTINGS"]["mp3_abr"] + " ")
                acodec_bitrate_choices = {
                    "8k": "-b:a 8k ",
                    "16k": "-b:a 16k ",
                    "24k": "-b:a 24k ",
                    "32k": "-b:a 32k ",
                    "40k": "-b:a 40k ",
                    "48k": "-b:a 48k ",
                    "64k": "-b:a 64k ",
                    "80k": "-b:a 80k ",
                    "96k": "-b:a 96k ",
                    "112k": "-b:a 112k ",
                    "128k": "-b:a 128k ",
                    "160k": "-b:a 160k ",
                    "192k": "-b:a 192k ",
                    "224k": "-b:a 224k ",
                    "256k": "-b:a 256k ",
                    "320k": "-b:a 320k ",
                }
                if (
                    config_profile["FFMPEG MP3 - SETTINGS"]["acodec_bitrate_cbr_abr"]
                    == ""
                ):
                    acodec_bitrate.set("192k")
                else:
                    acodec_bitrate.set(
                        config_profile["FFMPEG MP3 - SETTINGS"][
                            "acodec_bitrate_cbr_abr"
                        ]
                    )
                acodec_bitrate_menu_label = Label(
                    audio_window,
                    text="Bitrate :",
                    background="#434547",
                    foreground="white",
                )
                acodec_bitrate_menu_label.grid(
                    row=2, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
                )
                acodec_bitrate_menu = OptionMenu(
                    audio_window, acodec_bitrate, *acodec_bitrate_choices.keys()
                )
                acodec_bitrate_menu.config(
                    background="#23272A", foreground="white", highlightthickness=1
                )
                acodec_bitrate_menu.grid(
                    row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
                )
                acodec_bitrate_menu["menu"].configure(activebackground="dim grey")
                acodec_bitrate_menu.bind("<Enter>", acodec_bitrate_menu_hover)
                acodec_bitrate_menu.bind("<Leave>", acodec_bitrate_menu_hover_leave)
            # ------------------------------------------------------------------------------------------ VBR or CBR/ABR

        # Buttons -----------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=7, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        # ----------------------------------------------------------------------------------------------------- Buttons

        # Audio Channel Selection -------------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
        }
        acodec_channel.set(
            config_profile["FFMPEG MP3 - SETTINGS"]["acodec_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ----------------------------------------------------------------------------------------------- Audio Channel

        # VBR ---------------------------------------------------------------------------------------------------------
        global mp3_vbr
        mp3_vbr = StringVar()
        mp3_vbr.set(config_profile["FFMPEG MP3 - SETTINGS"]["mp3_vbr"])
        mp3_vbr_checkbox = Checkbutton(
            audio_window, text="VBR", variable=mp3_vbr, onvalue="-q:a", offvalue="off"
        )
        mp3_vbr_checkbox.grid(
            row=4,
            column=1,
            rowspan=1,
            columnspan=1,
            padx=10,
            pady=(15, 3),
            sticky=N + S + E + W,
        )
        mp3_vbr_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        mp3_vbr.trace("w", mp3_bitrate_type)
        # --------------------------------------------------------------------------------------------------------- VBR

        # ABR ---------------------------------------------------------------------------------------------------------
        global mp3_abr

        def mp3_abr_toggle(*args):
            update_cfg_mp3()

        mp3_abr = StringVar()
        mp3_abr.set(config_profile["FFMPEG MP3 - SETTINGS"]["mp3_abr"] + " ")
        mp3_abr_checkbox = Checkbutton(
            audio_window,
            text="ABR",
            variable=mp3_abr,
            onvalue="-abr 1 ",
            offvalue="",
            state=DISABLED,
        )
        if mp3_vbr.get() == "off ":
            mp3_abr_checkbox.configure(state=NORMAL)
        mp3_abr_checkbox.grid(
            row=4,
            column=2,
            rowspan=1,
            columnspan=1,
            padx=10,
            pady=(15, 3),
            sticky=N + S + E + W,
        )
        mp3_abr_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        mp3_abr.trace("w", mp3_abr_toggle)

        # --------------------------------------------------------------------------------------------------------- ABR

        # Entry Box for Custom Command Line ---------------------------------------------------------------------------
        def mp3_cmd(*args):
            global mp3_custom_cmd_input
            if mp3_custom_cmd.get().strip() == "":
                mp3_custom_cmd_input = ""
            else:
                cstmcmd = mp3_custom_cmd.get().strip()
                mp3_custom_cmd_input = cstmcmd + " "

        mp3_custom_cmd = StringVar()
        mp3_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        mp3_cmd_entrybox_label.grid(
            row=5, column=0, columnspan=2, padx=10, pady=(10, 0), sticky=N + S + W + E
        )
        mp3_cmd_entrybox = Entry(
            audio_window,
            textvariable=mp3_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        mp3_cmd_entrybox.grid(
            row=6, column=0, columnspan=3, padx=10, pady=(0, 15), sticky=W + E
        )
        mp3_custom_cmd.trace("w", mp3_cmd)
        mp3_custom_cmd.set(
            config_profile["FFMPEG MP3 - SETTINGS"]["custom_command_line"]
        )
        # ----------------------------------------------------------------------------------------- Custom Command Line

        # Audio Stream Selection --------------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(next(iter(acodec_stream_track_counter)))
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # ------------------------------------------------------------------------------------------------ Audio Stream

        # Dolby Pro Logic II ------------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=4,
            column=0,
            columnspan=1,
            rowspan=1,
            padx=10,
            pady=(15, 3),
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG MP3 - SETTINGS"]["dolbyprologicii"]
        )
        # ------------------------------------------------------------------------------------------------------ DPL II

        # Audio Volume Selection --------------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG MP3 - SETTINGS"]["ffmpeg_volume"])
        ffmpeg_volume.trace("w", audio_filter_function)
        volume_right_click_options()
        # ------------------------------------------------------------------------------------------------------ Volume

        # Audio Sample Rate Selection ---------------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "8000 Hz": "-ar 8000 ",
            "11025 Hz": "-ar 11025 ",
            "12000 Hz": "-ar 12000 ",
            "16000 Hz": "-ar 16000 ",
            "22050 Hz": "-ar 22050 ",
            "24000 Hz": "-ar 24000 ",
            "32000 Hz": "-ar 32000 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG MP3 - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_samplerate_menu.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)
        # ------------------------------------------------------------------------------------------------- Sample Rate

        # Audio Atempo Selection ---------------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        mp3_bitrate_type()
        # ------------------------------------------------------------------------------------------------ Audio Atempo
    # ------------------------------------------------------------------------------------------------------------- MP3

    # E-AC3 Window ----------------------------------------------------------------------------------------------------
    elif encoder.get() == "E-AC3":
        audio_window = Toplevel()
        audio_window.title("E-AC3 Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - e-ac3 - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - e-ac3"] == "no"
        ):
            window_height = 800
            window_width = 850
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - e-ac3 - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - e-ac3"]
            == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - e-ac3 - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for eac3_n in range(3):
            audio_window.grid_columnconfigure(eac3_n, weight=1)
        for eac3_n in range(22):
            audio_window.grid_rowconfigure(eac3_n, weight=1)

        advanced_label = Label(
            audio_window,
            text="- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - Advanced Settings - "
            "- - - - - - - - - - - - - - - - - - - - "
            "- - - - - - - - -\n *All settings are set to default below*",
            background="#434547",
            foreground="white",
            relief=GROOVE,
        )
        advanced_label.grid(
            row=4, column=0, columnspan=3, padx=10, pady=10, sticky=W + E
        )

        # Buttons -----------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=22, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )

        # ----------------------------------------------------------------------------------------------------- Buttons

        # Entry Box for Custom Command Line ---------------------------------------------------------------------------
        def eac3_cmd(*args):
            global eac3_custom_cmd_input
            if eac3_custom_cmd.get().strip() == "":
                eac3_custom_cmd_input = ""
            else:
                cstmcmd = eac3_custom_cmd.get().strip()
                eac3_custom_cmd_input = cstmcmd + " "

        eac3_custom_cmd = StringVar()
        eac3_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        eac3_cmd_entrybox_label.grid(
            row=20, column=0, columnspan=2, padx=10, pady=(10, 0), sticky=N + S + W + E
        )
        eac3_cmd_entrybox = Entry(
            audio_window,
            textvariable=eac3_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        eac3_cmd_entrybox.grid(
            row=21, column=0, columnspan=3, padx=10, pady=(0, 10), sticky=W + E
        )
        eac3_custom_cmd.trace("w", eac3_cmd)
        eac3_custom_cmd.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- Custom Command Line

        # Audio Bitrate Menu ------------------------------------------------------------------------------------------
        global eac3_spinbox
        acodec_spinbox_values = (
            "64k ",
            "96k ",
            "160k ",
            "128k ",
            "192k ",
            "224k ",
            "256k ",
            "288k ",
            "320k ",
            "352k ",
            "384k ",
            "416k ",
            "448k ",
            "480k ",
            "512k ",
            "544k ",
            "576k ",
            "608k ",
            "640k ",
            "672k ",
            "704k ",
            "736k ",
            "768k ",
            "800k ",
            "832k ",
            "864k ",
            "896k ",
            "928k ",
            "960k ",
            "1056k ",
            "1088k ",
            "1120k ",
            "1152k ",
            "1184k ",
            "1216k ",
            "1248k ",
            "1280k ",
            "1312k ",
            "1344k ",
            "1376k ",
            "1408k ",
            "1440k ",
            "1472k ",
            "1504k ",
            "1536k ",
            "1568 ",
            "1600k ",
            "1632k ",
            "1664k ",
            "1696k ",
            "1728k ",
            "1760k ",
            "1792k ",
            "1824k ",
            "1856k ",
            "1888k ",
            "1920k ",
            "1952k ",
            "1984k ",
            "2016k ",
            "2048k ",
            "2080k ",
            "2112k ",
            "2144k ",
            "2176k ",
            "2208k ",
            "2240k ",
            "2272k ",
            "2304k ",
            "2336k ",
            "2368k ",
            "2400k ",
            "2432k ",
            "2464k ",
            "2496k ",
            "2528k ",
        )
        eac3_spinbox = StringVar()
        q_acodec_quality_spinbox_label = Label(
            audio_window, text="Bitrate :", background="#434547", foreground="white"
        )
        q_acodec_quality_spinbox_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_quality_spinbox = Spinbox(
            audio_window,
            values=acodec_spinbox_values,
            justify=CENTER,
            wrap=True,
            textvariable=eac3_spinbox,
            state="readonly",
        )
        q_acodec_quality_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        q_acodec_quality_spinbox.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        eac3_spinbox.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_bitrate"] + " "
        )
        # ----------------------------------------------------------------------------------------------------- Bitrate

        # Audio Channel Selection -------------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "2.1 (Stereo)": "-ac 3 ",
            "4.0 (Quad)": "-ac 4 ",
            "5.0 (Quad)": "-ac 5 ",
            "5.1 (Surround)": "-ac 6 ",
        }
        acodec_channel.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        # ---------------------------------------------------------------------------------------------------- Channels

        # Audio Stream Selection --------------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(next(iter(acodec_stream_track_counter)))
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # ------------------------------------------------------------------------------------------------------ Stream

        # Audio Volume Selection --------------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_volume"])
        volume_right_click_options()
        # ------------------------------------------------------------------------------------------------------ Volume

        # Audio Sample Rate Selection ---------------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "32000 Hz": "-ar 32000 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_samplerate_menu.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)
        # ------------------------------------------------------------------------------------------------- Sample Rate

        # Audio Per Frame Metadata Selection --------------------------------------------------------------------------
        global per_frame_metadata, per_frame_metadata_choices
        per_frame_metadata = StringVar(audio_window)
        per_frame_metadata_choices = {
            "Default": "",
            "True": "-per_frame_metadata true ",
            "False": "-per_frame_metadata false ",
        }
        per_frame_metadata.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_per_frame_metadata"]
        )  # set def option
        per_frame_metadata_label = Label(
            audio_window,
            text="Per Frame Metadata :",
            background="#434547",
            foreground="white",
        )
        per_frame_metadata_label.grid(
            row=5, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        per_frame_metadata_menu = OptionMenu(
            audio_window, per_frame_metadata, *per_frame_metadata_choices.keys()
        )
        per_frame_metadata_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        per_frame_metadata_menu.grid(
            row=6, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        per_frame_metadata_menu["menu"].configure(activebackground="dim grey")
        per_frame_metadata_menu.bind("<Enter>", per_frame_metadata_menu_hover)
        per_frame_metadata_menu.bind("<Leave>", per_frame_metadata_menu_hover_leave)
        # ---------------------------------------------------------------------------------------------------- Metadata

        # Mixing Level Spinbox ----------------------------------------------------------------------------------------
        global eac3_mixing_level
        eac3_mixing_level = StringVar()
        eac3_mixing_level_label = Label(
            audio_window,
            text="Mixing Level :",
            background="#434547",
            foreground="white",
        )
        eac3_mixing_level_label.grid(
            row=5, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        eac3_mixing_level_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=111,
            justify=CENTER,
            wrap=True,
            textvariable=eac3_mixing_level,
            state="readonly",
        )
        eac3_mixing_level_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        eac3_mixing_level_spinbox.grid(
            row=6, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        eac3_mixing_level.set(
            int(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_mixing_level"])
        )
        # ------------------------------------------------------------------------------------------------ Mixing Level

        # Room Type Selection -----------------------------------------------------------------------------------------
        global room_type, room_type_choices
        room_type = StringVar(audio_window)
        room_type_choices = {
            "Default": "",
            "Not Indicated": "-room_type 0 ",
            "Large": "-room_type 1 ",
            "Small": "-room_type 2 ",
        }
        room_type.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_room_type"]
        )  # set the default option
        room_type_label = Label(
            audio_window, text="Room Type :", background="#434547", foreground="white"
        )
        room_type_label.grid(
            row=5, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        room_type_menu = OptionMenu(audio_window, room_type, *room_type_choices.keys())
        room_type_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        room_type_menu.grid(
            row=6, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        room_type_menu["menu"].configure(activebackground="dim grey")
        room_type_menu.bind("<Enter>", room_type_menu_hover)
        room_type_menu.bind("<Leave>", room_type_menu_hover_leave)
        # --------------------------------------------------------------------------------------------------- Room Type

        # Copyright Bit Spinbox ---------------------------------------------------------------------------------------
        global copyright_bit
        copyright_bit = StringVar()
        copyright_bit_label = Label(
            audio_window,
            text="Copyright Bit :",
            background="#434547",
            foreground="white",
        )
        copyright_bit_label.grid(
            row=7, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        copyright_bit_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=1,
            justify=CENTER,
            wrap=True,
            textvariable=copyright_bit,
            state="readonly",
        )
        copyright_bit_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        copyright_bit_spinbox.grid(
            row=8, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        copyright_bit.set(
            int(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_copyright_bit"])
        )
        # --------------------------------------------------------------------------------------------------- Copyright

        # Dialogue Level Spinbox --------------------------------------------------------------------------------------
        global dialogue_level
        dialogue_level = StringVar()
        dialogue_level_label = Label(
            audio_window,
            text="Dialogue Level (dB) :",
            background="#434547",
            foreground="white",
        )
        dialogue_level_label.grid(
            row=7, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dialogue_level_spinbox = Spinbox(
            audio_window,
            from_=-31,
            to=-1,
            justify=CENTER,
            wrap=True,
            textvariable=dialogue_level,
            state="readonly",
        )
        dialogue_level_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        dialogue_level_spinbox.grid(
            row=8, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dialogue_level.set(
            int(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_dialogue_level"])
        )
        # ---------------------------------------------------------------------------------------------- Dialogue Level

        # Dolby Surround Mode Selection -------------------------------------------------------------------------------
        global dolby_surround_mode, dolby_surround_mode_choices
        dolby_surround_mode = StringVar(audio_window)
        dolby_surround_mode_choices = {
            "Default": "",
            "Not Indicated": "-dsur_mode 0 ",
            "On": "-dsur_mode 1 ",
            "Off": "-dsur_mode 2 ",
        }
        dolby_surround_mode.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_surround_mode"]
        )  # set the def option
        dolby_surround_mode_label = Label(
            audio_window,
            text="Dolby Surround Mode :",
            background="#434547",
            foreground="white",
        )
        dolby_surround_mode_label.grid(
            row=7, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dolby_surround_mode_menu = OptionMenu(
            audio_window, dolby_surround_mode, *dolby_surround_mode_choices.keys()
        )
        dolby_surround_mode_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        dolby_surround_mode_menu.grid(
            row=8, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dolby_surround_mode_menu["menu"].configure(activebackground="dim grey")
        dolby_surround_mode_menu.bind("<Enter>", dolby_surround_mode_menu_hover)
        dolby_surround_mode_menu.bind("<Leave>", dolby_surround_mode_menu_hover_leave)
        # ---------------------------------------------------------------------------------------------- Dolby Surround

        # Original Bit Stream Spinbox ---------------------------------------------------------------------------------
        global original_bit_stream
        original_bit_stream = StringVar()
        original_bit_stream_label = Label(
            audio_window,
            text="Original Bit Stream :",
            background="#434547",
            foreground="white",
        )
        original_bit_stream_label.grid(
            row=9, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        original_bit_stream_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=1,
            justify=CENTER,
            wrap=True,
            textvariable=original_bit_stream,
            state="readonly",
        )
        original_bit_stream_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        original_bit_stream_spinbox.grid(
            row=10, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        original_bit_stream.set(
            int(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_original_bitstream"])
        )  # default
        # -------------------------------------------------------------------------------------------------- Bit Stream

        # Downmix Mode Selection --------------------------------------------------------------------------------------
        global downmix_mode, downmix_mode_choices
        downmix_mode = StringVar(audio_window)
        downmix_mode_choices = {
            "Default": "",
            "Not Indicated": "-dmix_mode 0 ",
            "Lt/RT Downmix": "-dmix_mode 1 ",
            "Lo/Ro Downmix": "-dmix_mode 2 ",
            "Dolby Pro Logic II": "-dmix_mode 3 ",
        }
        downmix_mode.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_downmix_mode"]
        )  # set the default option
        downmix_mode_label = Label(
            audio_window,
            text="Stereo Downmix Mode :",
            background="#434547",
            foreground="white",
        )
        downmix_mode_label.grid(
            row=9, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        downmix_mode_menu = OptionMenu(
            audio_window, downmix_mode, *downmix_mode_choices.keys()
        )
        downmix_mode_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        downmix_mode_menu.grid(
            row=10, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        downmix_mode_menu["menu"].configure(activebackground="dim grey")
        downmix_mode_menu.bind("<Enter>", downmix_mode_menu_hover)
        downmix_mode_menu.bind("<Leave>", downmix_mode_menu_hover_leave)
        # ------------------------------------------------------------------------------------------------ Downmix Mode

        # Lt/Rt Center Mix Level Spinbox ------------------------------------------------------------------------------
        global lt_rt_center_mix
        lt_rt_center_mix = StringVar()
        lt_rt_center_mix_label = Label(
            audio_window,
            text="Lt/Rt Center\nMix Level :",
            background="#434547",
            foreground="white",
        )
        lt_rt_center_mix_label.grid(
            row=9, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lt_rt_center_mix_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=1,
            justify=CENTER,
            wrap=True,
            textvariable=lt_rt_center_mix,
            state="readonly",
            increment=0.1,
        )
        lt_rt_center_mix_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        lt_rt_center_mix_spinbox.grid(
            row=10, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lt_rt_center_mix.set(
            float(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_lt_rt_center_mix"])
        )  # default
        # -------------------------------------------------------------------------------------- Lt/Rt Center Mix Level

        # Lt/Rt Surround Mix Level Spinbox ----------------------------------------------------------------------------
        global lt_rt_surround_mix
        lt_rt_surround_mix = StringVar()
        lt_rt_surround_mix_label = Label(
            audio_window,
            text="Lt/Rt Surround\nMix Level :",
            background="#434547",
            foreground="white",
        )
        lt_rt_surround_mix_label.grid(
            row=11, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lt_rt_surround_mix_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=1,
            justify=CENTER,
            wrap=True,
            textvariable=lt_rt_surround_mix,
            state="readonly",
            increment=0.1,
        )
        lt_rt_surround_mix_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        lt_rt_surround_mix_spinbox.grid(
            row=12, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lt_rt_surround_mix.set(
            float(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_lt_rt_surround_mix"])
        )  # default
        # ------------------------------------------------------------------------------------ Lt/Rt Surround Mix Level

        # Lo/Ro Center Mix Level Spinbox ------------------------------------------------------------------------------
        global lo_ro_center_mix
        lo_ro_center_mix = StringVar()
        lo_ro_center_mix_label = Label(
            audio_window,
            text="Lo/Ro Center\nMix Level :",
            background="#434547",
            foreground="white",
        )
        lo_ro_center_mix_label.grid(
            row=11, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lo_ro_center_mix_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=1,
            justify=CENTER,
            wrap=True,
            textvariable=lo_ro_center_mix,
            state="readonly",
            increment=0.1,
        )
        lo_ro_center_mix_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        lo_ro_center_mix_spinbox.grid(
            row=12, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lo_ro_center_mix.set(
            float(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_lo_ro_center_mix"])
        )  # default
        # -------------------------------------------------------------------------------------- Lo/Ro Center Mix Level

        # Lo/Ro Surround Mix Level Spinbox ----------------------------------------------------------------------------
        global lo_ro_surround_mix
        lo_ro_surround_mix = StringVar()
        lo_ro_surround_mix_label = Label(
            audio_window,
            text="Lo/Ro Surround\nMix Level :",
            background="#434547",
            foreground="white",
        )
        lo_ro_surround_mix_label.grid(
            row=11, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lo_ro_surround_mix_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=1,
            justify=CENTER,
            wrap=True,
            textvariable=lo_ro_surround_mix,
            state="readonly",
            increment=0.1,
        )
        lo_ro_surround_mix_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        lo_ro_surround_mix_spinbox.grid(
            row=12, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        lo_ro_surround_mix.set(
            float(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_lo_ro_surround_mix"])
        )
        # ------------------------------------------------------------------------------------ Lo/Ro Surround Mix Level

        # Dolby Surround EX Mode Selection ----------------------------------------------------------------------------
        global dolby_surround_ex_mode, dolby_surround_ex_mode_choices
        dolby_surround_ex_mode = StringVar(audio_window)
        dolby_surround_ex_mode_choices = {
            "Default": "",
            "Not Indicated": "-dsurex_mode 0 ",
            "On": "-dsurex_mode 2 ",
            "Off": "-dsurex_mode 1 ",
            "Dolby Pro Login IIz": "-dsurex_mode 3 ",
        }
        dolby_surround_ex_mode.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_dolby_surround_ex_mode"]
        )  # def
        dolby_surround_ex_mode_label = Label(
            audio_window,
            text="Dolby Surround EX Mode :",
            background="#434547",
            foreground="white",
        )
        dolby_surround_ex_mode_label.grid(
            row=13, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dolby_surround_ex_mode_menu = OptionMenu(
            audio_window, dolby_surround_ex_mode, *dolby_surround_ex_mode_choices.keys()
        )
        dolby_surround_ex_mode_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        dolby_surround_ex_mode_menu.grid(
            row=14, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dolby_surround_ex_mode_menu["menu"].configure(activebackground="dim grey")
        dolby_surround_ex_mode_menu.bind("<Enter>", dolby_surround_ex_mode_menu_hover)
        dolby_surround_ex_mode_menu.bind(
            "<Leave>", dolby_surround_ex_mode_menu_hover_leave
        )
        # -------------------------------------------------------------------------------------- Dolby Surround EX Mode

        # Dolby Headphone Mode Selection ------------------------------------------------------------------------------
        global dolby_headphone_mode, dolby_headphone_mode_choices
        dolby_headphone_mode = StringVar(audio_window)
        dolby_headphone_mode_choices = {
            "Default": "",
            "Not Indicated": "-dheadphone_mode 0 ",
            "On": "-dheadphone_mode 2 ",
            "Off": "-dheadphone_mode 1 ",
        }
        dolby_headphone_mode.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_dolby_headphone_mode"]
        )  # default
        dolby_headphone_mode_label = Label(
            audio_window,
            text="Dolby Headphone Mode :",
            background="#434547",
            foreground="white",
        )
        dolby_headphone_mode_label.grid(
            row=13, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dolby_headphone_mode_menu = OptionMenu(
            audio_window, dolby_headphone_mode, *dolby_headphone_mode_choices.keys()
        )
        dolby_headphone_mode_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        dolby_headphone_mode_menu.grid(
            row=14, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        dolby_headphone_mode_menu["menu"].configure(activebackground="dim grey")
        dolby_headphone_mode_menu.bind("<Enter>", dolby_headphone_mode_menu_hover)
        dolby_headphone_mode_menu.bind("<Leave>", dolby_headphone_mode_menu_hover_leave)
        # --------------------------------------------------------------------------------------------- Dolby Headphone

        # A/D Converter Type Selection --------------------------------------------------------------------------------
        global a_d_converter_type, a_d_converter_type_choices
        a_d_converter_type = StringVar(audio_window)
        a_d_converter_type_choices = {
            "Default": "",
            "Standard": "-ad_conv_type 0 ",
            "HDCD": "-ad_conv_type 1 ",
        }
        a_d_converter_type.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_a_d_converter_type"]
        )  # set default
        a_d_converter_type_label = Label(
            audio_window,
            text="A/D Converter Type :",
            background="#434547",
            foreground="white",
        )
        a_d_converter_type_label.grid(
            row=13, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        a_d_converter_type_menu = OptionMenu(
            audio_window, a_d_converter_type, *a_d_converter_type_choices.keys()
        )
        a_d_converter_type_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        a_d_converter_type_menu.grid(
            row=14, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        a_d_converter_type_menu["menu"].configure(activebackground="dim grey")
        a_d_converter_type_menu.bind("<Enter>", a_d_converter_type_menu_hover)
        a_d_converter_type_menu.bind("<Leave>", a_d_converter_type_menu_hover_leave)
        # ----------------------------------------------------------------------------------------------- A/D Converter

        # Stereo Rematrixing Selection --------------------------------------------------------------------------------
        global stereo_rematrixing, stereo_rematrixing_choices
        stereo_rematrixing = StringVar(audio_window)
        stereo_rematrixing_choices = {
            "Default": "",
            "True": "-stereo_rematrixing true ",
            "False": "-stereo_rematrixing false ",
        }
        stereo_rematrixing.set(
            config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_dolby_stereo_rematrixing"]
        )  # default
        stereo_rematrixing_label = Label(
            audio_window,
            text="Stereo Rematrixing :",
            background="#434547",
            foreground="white",
        )
        stereo_rematrixing_label.grid(
            row=15, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        stereo_rematrixing_menu = OptionMenu(
            audio_window, stereo_rematrixing, *stereo_rematrixing_choices.keys()
        )
        stereo_rematrixing_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        stereo_rematrixing_menu.grid(
            row=16, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        stereo_rematrixing_menu["menu"].configure(activebackground="dim grey")
        stereo_rematrixing_menu.bind("<Enter>", stereo_rematrixing_menu_hover)
        stereo_rematrixing_menu.bind("<Leave>", stereo_rematrixing_menu_hover_leave)
        # ------------------------------------------------------------------------------------------ Stereo Rematrixing

        # Channel Coupling Spinbox ------------------------------------------------------------------------------------
        global channel_coupling
        channel_coupling = StringVar()
        channel_coupling_label = Label(
            audio_window,
            text="Channel Coupling :",
            background="#434547",
            foreground="white",
        )
        channel_coupling_label.grid(
            row=15, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        channel_coupling_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=1,
            justify=CENTER,
            wrap=True,
            textvariable=channel_coupling,
            state="readonly",
        )
        channel_coupling_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        channel_coupling_spinbox.grid(
            row=16, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        channel_coupling.set(
            int(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_channel_coupling"])
        )  # default
        # -------------------------------------------------------------------------------------------- Channel Coupling

        # Channel CPL Band Spinbox ------------------------------------------------------------------------------------
        global cpl_start_band
        cpl_start_band = StringVar()
        cpl_start_band_label = Label(
            audio_window,
            text="Coupling Start Band :",
            background="#434547",
            foreground="white",
        )
        cpl_start_band_label.grid(
            row=15, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        cpl_start_band_spinbox = Spinbox(
            audio_window,
            from_=-1,
            to=15,
            justify=CENTER,
            wrap=True,
            textvariable=cpl_start_band,
            state="readonly",
        )
        cpl_start_band_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=10,
            readonlybackground="#23272A",
        )
        cpl_start_band_spinbox.grid(
            row=16, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        cpl_start_band.set(
            int(config_profile["FFMPEG E-AC3 - SETTINGS"]["e-ac3_cpl_start_band"])
        )
        # -------------------------------------------------------------------------------------------- Channel CPL Band

        # Audio Atempo Selection --------------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ------------------------------------------------------------------------------------------------ Audio Atempo
    # ----------------------------------------------------------------------------------------------------------- E-AC3

    # FDK-AAC Window --------------------------------------------------------------------------------------------------
    elif encoder.get() == "FDK-AAC":
        audio_window = Toplevel()
        audio_window.title("FDK-AAC Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"][
                "audio window - fdk-aac - position"
            ]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - fdk-aac"]
            == "no"
        ):
            window_height = 750
            window_width = 780
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"][
                "audio window - fdk-aac - position"
            ]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - fdk-aac"]
            == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - fdk-aac - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for fdk_n in range(3):
            audio_window.grid_columnconfigure(fdk_n, weight=1)
        for fdk_n in range(17):
            audio_window.grid_rowconfigure(fdk_n, weight=1)

        def acodec_lowdelay_menu_hover(e):
            acodec_lowdelay_menu["bg"] = "grey"
            acodec_lowdelay_menu["activebackground"] = "grey"

        def acodec_lowdelay_menu_hover_leave(e):
            acodec_lowdelay_menu["bg"] = "#23272A"

        def acodec_sbr_ratio_menu_hover(e):
            acodec_sbr_ratio_menu["bg"] = "grey"
            acodec_sbr_ratio_menu["activebackground"] = "grey"

        def acodec_sbr_ratio_menu_hover_leave(e):
            acodec_sbr_ratio_menu["bg"] = "#23272A"

        def acodec_gapless_mode_menu_hover(e):
            acodec_gapless_mode_menu["bg"] = "grey"
            acodec_gapless_mode_menu["activebackground"] = "grey"

        def acodec_gapless_mode_menu_hover_leave(e):
            acodec_gapless_mode_menu["bg"] = "#23272A"

        def acodec_transport_format_menu_hover(e):
            acodec_transport_format_menu["bg"] = "grey"
            acodec_transport_format_menu["activebackground"] = "grey"

        def acodec_transport_format_menu_hover_leave(e):
            acodec_transport_format_menu["bg"] = "#23272A"

        def acodec_profile_menu_hover(e):
            acodec_profile_menu["bg"] = "grey"
            acodec_profile_menu["activebackground"] = "grey"

        def acodec_profile_menu_hover_leave(e):
            acodec_profile_menu["bg"] = "#23272A"

        # Buttons -----------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=17, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        # ----------------------------------------------------------------------------------------------------- Buttons

        advanced_label = Label(
            audio_window,
            text="- - - - - - - - - - - - - - - - - - - - Advanced Settings - - - - - - - - - - - "
            "- - - - - - - - -",
            background="#434547",
            foreground="white",
            relief=GROOVE,
        )
        advanced_label.grid(
            row=4, column=0, columnspan=3, padx=10, pady=10, sticky=W + E
        )

        # Audio Bitrate Menu ------------------------------------------------------------------------------------------
        acodec_bitrate = StringVar(audio_window)
        acodec_bitrate_choices = {
            "CBR: 16k": "-b16 ",
            "CBR: 32k": "-b32 ",
            "CBR: 64k": "-b64 ",
            "CBR: 128k": "-b128 ",
            "CBR: 192k": "-b192 ",
            "CBR: 256k": "-b256 ",
            "CBR: 320k": "-b320 ",
            "CBR: 448k": "-b448 ",
            "CBR: 640k": "-b640 ",
            "VBR: 1": "-m1 ",
            "VBR: 2": "-m2 ",
            "VBR: 3": "-m3 ",
            "VBR: 4": "-m4 ",
            "VBR: 5": "-m5 ",
        }
        acodec_bitrate.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_bitrate"]
        )  # set the default option
        acodec_bitrate_menu_label = Label(
            audio_window, text="Quality :", background="#434547", foreground="white"
        )
        acodec_bitrate_menu_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_bitrate_menu = OptionMenu(
            audio_window, acodec_bitrate, *acodec_bitrate_choices.keys()
        )
        acodec_bitrate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_bitrate_menu.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_bitrate_menu["menu"].configure(activebackground="dim grey")
        acodec_bitrate_menu.bind("<Enter>", acodec_bitrate_menu_hover)
        acodec_bitrate_menu.bind("<Leave>", acodec_bitrate_menu_hover_leave)
        # ------------------------------------------------------------------------------------------------ Bitrate Menu

        # Audio Channel Selection -------------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "5.1 (Surround)": "-ac 6 ",
            "6.1 (Surround)": "-ac 7 ",
            "7.1 (Surround)": "-ac 8 ",
        }
        acodec_channel.set(
            config_profile["FDK-AAC - SETTINGS"]["acodec_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ----------------------------------------------------------------------------------------------------- Channel

        # Audio Stream Selection --------------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(
            next(iter(acodec_stream_track_counter))
        )  # set the default option
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # ------------------------------------------------------------------------------------------------------ Stream

        # Dolby Pro Logic II ------------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=10,
            column=2,
            columnspan=1,
            rowspan=1,
            padx=10,
            pady=3,
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(config_profile["FDK-AAC - SETTINGS"]["dolbyprologicii"])
        # ------------------------------------------------------------------------------------------------------ DPL II

        # Audio Volume Selection --------------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FDK-AAC - SETTINGS"]["ffmpeg_volume"])
        volume_right_click_options()
        # ------------------------------------------------------------------------------------------------------ Volume

        # Audio Sample Rate Selection ---------------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "11025 Hz": "-ar 11025 ",
            "22050 Hz": "-ar 22050 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
            "88200 Hz": "-ar 88200 ",
            "96000 Hz": "-ar 96000 ",
        }
        acodec_samplerate.set(
            config_profile["FDK-AAC - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_samplerate_menu.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)

        # ------------------------------------------------------------------------------------------------- Sample Rate

        # Entry Box for Custom Command Line ---------------------------------------------------------------------------
        def fdkaac_cmd(*args):
            global fdkaac_custom_cmd_input
            if fdkaac_custom_cmd.get().strip() == "":
                fdkaac_custom_cmd_input = ""
            else:
                cstmcmd = fdkaac_custom_cmd.get().strip()
                fdkaac_custom_cmd_input = cstmcmd + " "

        fdkaac_custom_cmd = StringVar()
        fdkaac_cmd_entrybox_label = Label(
            audio_window,
            text="FDK-AAC Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        fdkaac_cmd_entrybox_label.grid(
            row=11, column=0, columnspan=2, padx=10, pady=(0, 0), sticky=N + S + W + E
        )
        fdkaac_cmd_entrybox = Entry(
            audio_window,
            textvariable=fdkaac_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        fdkaac_cmd_entrybox.grid(
            row=12, column=0, columnspan=3, padx=10, pady=(0, 0), sticky=W + E
        )
        fdkaac_custom_cmd.trace("w", fdkaac_cmd)
        fdkaac_custom_cmd.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- Custom Command Line

        # Entry Box for FFMPEG Command Line ---------------------------------------------------------------------------
        def ffmpeg_cmd_function(*args):
            global ffmpeg_custom_cmd_input
            if ffmpeg_custom_cmd.get().strip() == "":
                ffmpeg_custom_cmd_input = ""
            else:
                cstmcmd = ffmpeg_custom_cmd.get().strip()
                ffmpeg_custom_cmd_input = cstmcmd + " "

        ffmpeg_custom_cmd = StringVar()
        ffmpeg_cmd_entrybox_label = Label(
            audio_window,
            text="FFMPEG Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        ffmpeg_cmd_entrybox_label.grid(
            row=13, column=0, columnspan=2, padx=10, pady=(0, 0), sticky=N + S + W + E
        )
        ffmpeg_cmd_entrybox = Entry(
            audio_window,
            textvariable=ffmpeg_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        ffmpeg_cmd_entrybox.grid(
            row=14, column=0, columnspan=3, padx=10, pady=(0, 0), sticky=W + E
        )
        ffmpeg_custom_cmd.trace("w", ffmpeg_cmd_function)
        ffmpeg_custom_cmd.set(
            config_profile["FDK-AAC - SETTINGS"]["custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- FFMPEG Command Line

        # Entry Box for Track Title -----------------------------------------------------------------------------------
        def fdkaac_title_check(*args):
            global fdkaac_title_input
            if fdkaac_title.get().strip() == "":
                fdkaac_title_input = ""
            else:
                title_cmd = fdkaac_title.get().strip()
                fdkaac_title_input = "--title " + '"' + title_cmd + '"' + " "

        fdkaac_title = StringVar()
        fdkaac_title_entrybox_label = Label(
            audio_window,
            text="Title :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        fdkaac_title_entrybox_label.grid(
            row=15, column=0, columnspan=2, padx=10, pady=(0, 0), sticky=N + S + W + E
        )
        fdkaac_title_entrybox = Entry(
            audio_window, textvariable=fdkaac_title, borderwidth=4, background="#CACACA"
        )
        fdkaac_title_entrybox.grid(
            row=16, column=0, columnspan=3, padx=10, pady=(0, 10), sticky=W + E
        )
        fdkaac_title.trace("w", fdkaac_title_check)
        fdkaac_title.set("")
        # ------------------------------------------------------------------------------------------------- Track Title

        # Audio Profile Selection -------------------------------------------------------------------------------------
        acodec_profile = StringVar(audio_window)
        acodec_profile_choices = {
            "AAC LC (Default)": "-p2 ",
            "HE-AAC SBR": "-p5 ",
            "HE-AAC V2 (SBR+PS)": "-p29 ",
            "AAC LD": "-p23 ",
            "AAC ELD": "-p39 ",
        }
        acodec_profile.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_profile"]
        )  # set the default option
        acodec_profile_label = Label(
            audio_window, text="Profile :", background="#434547", foreground="white"
        )
        acodec_profile_label.grid(
            row=5, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_profile_menu = OptionMenu(
            audio_window, acodec_profile, *acodec_profile_choices.keys()
        )
        acodec_profile_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_profile_menu.grid(
            row=6, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_profile_menu["menu"].configure(activebackground="dim grey")
        acodec_profile_menu.bind("<Enter>", acodec_profile_menu_hover)
        acodec_profile_menu.bind("<Leave>", acodec_profile_menu_hover_leave)
        # ------------------------------------------------------------------------------------------- Profile Selection

        # Audio Lowdelay SBR Selection --------------------------------------------------------------------------------
        global acodec_lowdelay
        global acodec_lowdelay_choices
        acodec_lowdelay = StringVar(audio_window)
        acodec_lowdelay_choices = {
            "Disable SBR on ELD (DEF)": "-L0 ",
            "ELD SBR Auto Conf": "-L-1 ",
            "Enable SBR on ELD": "-L1 ",
        }
        acodec_lowdelay.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_lowdelay"]
        )  # set the default option
        acodec_lowdelay_label = Label(
            audio_window,
            text="Lowdelay SBR :",
            background="#434547",
            foreground="white",
        )
        acodec_lowdelay_label.grid(
            row=5, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_lowdelay_menu = OptionMenu(
            audio_window, acodec_lowdelay, *acodec_lowdelay_choices.keys()
        )
        acodec_lowdelay_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_lowdelay_menu.grid(
            row=6, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_lowdelay_menu["menu"].configure(activebackground="dim grey")
        acodec_lowdelay_menu.bind("<Enter>", acodec_lowdelay_menu_hover)
        acodec_lowdelay_menu.bind("<Leave>", acodec_lowdelay_menu_hover_leave)
        # --------------------------------------------------------------------------------------------------- Low Delay

        # Audio SBR Ratio ---------------------------------------------------------------------------------------------
        global acodec_sbr_ratio
        global acodec_sbr_ratio_choices
        acodec_sbr_ratio = StringVar(audio_window)
        acodec_sbr_ratio_choices = {
            "Library Default": "-s0 ",
            "Downsampled SBR (ELD+SBR Def)": "-s1 ",
            "Dual-Rate SBR (HE-AAC-Def)": "-s2 ",
        }
        acodec_sbr_ratio.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_sbr_ratio"]
        )  # set the default option
        acodec_sbr_ratio_label = Label(
            audio_window, text="SBR Ratio :", background="#434547", foreground="white"
        )
        acodec_sbr_ratio_label.grid(
            row=5, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_sbr_ratio_menu = OptionMenu(
            audio_window, acodec_sbr_ratio, *acodec_sbr_ratio_choices.keys()
        )
        acodec_sbr_ratio_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_sbr_ratio_menu.grid(
            row=6, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_sbr_ratio_menu["menu"].configure(activebackground="dim grey")
        acodec_sbr_ratio_menu.bind("<Enter>", acodec_sbr_ratio_menu_hover)
        acodec_sbr_ratio_menu.bind("<Leave>", acodec_sbr_ratio_menu_hover_leave)
        # --------------------------------------------------------------------------------------------------- SBR Ratio

        # Audio Gapless Mode ------------------------------------------------------------------------------------------
        global acodec_gapless_mode
        global acodec_gapless_mode_choices
        acodec_gapless_mode = StringVar(audio_window)
        acodec_gapless_mode_choices = {
            "iTunSMPB (Def)": "-G0 ",
            "ISO Standard (EDTS+SGPD)": "-G1 ",
            "Both": "-G2 ",
        }
        acodec_gapless_mode.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_gapless"]
        )  # set the default option
        acodec_gapless_mode_label = Label(
            audio_window,
            text="Gapless Mode :",
            background="#434547",
            foreground="white",
        )
        acodec_gapless_mode_label.grid(
            row=7, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_gapless_mode_menu = OptionMenu(
            audio_window, acodec_gapless_mode, *acodec_gapless_mode_choices.keys()
        )
        acodec_gapless_mode_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_gapless_mode_menu.grid(
            row=8, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_gapless_mode_menu["menu"].configure(activebackground="dim grey")
        acodec_gapless_mode_menu.bind("<Enter>", acodec_gapless_mode_menu_hover)
        acodec_gapless_mode_menu.bind("<Leave>", acodec_gapless_mode_menu_hover_leave)
        # ------------------------------------------------------------------------------------------ Audio Gapless Mode

        # Audio Transport Format --------------------------------------------------------------------------------------
        global acodec_transport_format
        global acodec_transport_format_choices
        acodec_transport_format = StringVar(audio_window)
        acodec_transport_format_choices = {
            "M4A (Def)": "-f0 ",
            "ADIF": "-f1 ",
            "ADTS": "-f2 ",
            "LATM MCP=1": "-f6 ",
            "LATM MCP=0": "-f7 ",
            "LOAS/LATM (LATM w/in LOAS)": "-f10 ",
        }
        acodec_transport_format.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_transport_format"]
        )  # default option
        acodec_transport_format_label = Label(
            audio_window,
            text="Transport Format :",
            background="#434547",
            foreground="white",
        )
        acodec_transport_format_label.grid(
            row=7, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_transport_format_menu = OptionMenu(
            audio_window,
            acodec_transport_format,
            *acodec_transport_format_choices.keys(),
        )
        acodec_transport_format_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_transport_format_menu.grid(
            row=8, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_transport_format_menu["menu"].configure(activebackground="dim grey")
        acodec_transport_format_menu.bind("<Enter>", acodec_transport_format_menu_hover)
        acodec_transport_format_menu.bind(
            "<Leave>", acodec_transport_format_menu_hover_leave
        )
        # --------------------------------------------------------------------------------------------------- Transport

        # Misc Checkboxes - Afterburner -------------------------------------------------------------------------------
        global afterburnervar
        afterburnervar = StringVar()
        afterburnervar.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_afterburner"] + " "
        )
        afterburner_checkbox = Checkbutton(
            audio_window,
            text="Afterburner",
            variable=afterburnervar,
            onvalue="-a1 ",
            offvalue="-a0 ",
        )
        afterburner_checkbox.grid(
            row=8, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        afterburner_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # ------------------------------------------------------------------------------------------------- Afterburner

        # Misc Checkboxes - Add CRC Check on ADTS Header --------------------------------------------------------------
        global crccheck
        crccheck = StringVar()
        crccheck.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_crccheck"].replace(".", " ")
        )
        crccheck_checkbox = Checkbutton(
            audio_window,
            text="CRC Check on\n ADTS Header",
            variable=crccheck,
            onvalue="-C ",
            offvalue="",
        )
        crccheck_checkbox.grid(
            row=9, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        crccheck_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # --------------------------------------------------------------------------------------------------------- CRC

        # Misc Checkboxes - Header Period -----------------------------------------------------------------------------
        global headerperiod
        headerperiod = StringVar()
        headerperiod.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_headerperiod"].replace(
                ".", " "
            )
        )
        headerperiod_checkbox = Checkbutton(
            audio_window,
            text="Header Period",
            variable=headerperiod,
            onvalue="-h ",
            offvalue="",
        )
        headerperiod_checkbox.grid(
            row=9, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        headerperiod_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # ------------------------------------------------------------------------------------------------------ Header

        # Misc Checkboxes - Include SBR Delay -------------------------------------------------------------------------
        global sbrdelay
        sbrdelay = StringVar()
        sbrdelay.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_sbrdelay"].replace(".", " ")
        )
        sbrdelay_checkbox = Checkbutton(
            audio_window,
            text="SBR Delay",
            variable=sbrdelay,
            onvalue="--include-sbr-delay ",
            offvalue="",
        )
        sbrdelay_checkbox.grid(
            row=9, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        sbrdelay_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # --------------------------------------------------------------------------------------------------- SBR Delay

        # Misc Checkboxes - Place Moov Box Before Mdat Box ------------------------------------------------------------
        global moovbox
        moovbox = StringVar()
        moovbox.set(
            config_profile["FDK-AAC - SETTINGS"]["fdk_aac_moovbox"].replace(".", " ")
        )
        moovbox_checkbox = Checkbutton(
            audio_window,
            text="Place Moov Box Before Mdat Box",
            variable=moovbox,
            onvalue="--moov-before-mdat ",
            offvalue="",
        )
        moovbox_checkbox.grid(
            row=10, column=0, columnspan=2, padx=10, pady=3, sticky=N + S + E + W
        )
        moovbox_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # ---------------------------------------------------------------------------------------------------- Moov Box

        # Audio Atempo Selection ---------------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ------------------------------------------------------------------------------------------------ Audio Atempo
    # --------------------------------------------------------------------------------------------------------- FDK AAC

    # QAAC Window -----------------------------------------------------------------------------------------------------
    elif encoder.get() == "QAAC":
        audio_window = Toplevel()
        audio_window.title("QAAC Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - qaac - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - qaac"] == "no"
        ):
            window_height = 760
            window_width = 750
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - qaac - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - qaac"]
            == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - qaac - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for qaac_n in range(3):
            audio_window.grid_columnconfigure(qaac_n, weight=1)
        for qaac_n in range(19):
            audio_window.grid_rowconfigure(qaac_n, weight=1)

        # Gets gain information for QAAC ------------------------------------------------------------------------------
        def qaac_gain_trace(*args):
            global set_qaac_gain
            if q_acodec_gain.get() == "0":
                set_qaac_gain = ""
            elif q_acodec_gain.get() != "0":
                set_qaac_gain = "--gain " + q_acodec_gain.get() + " "

        # ----------------------------------------------------------------------------------------------- QAAC Get Gain

        # Buttons -----------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=19, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        # ----------------------------------------------------------------------------------------------------- Buttons

        advanced_label = Label(
            audio_window,
            text="- - - - - - - - - - - - - - - - - - - - Advanced Settings - - - - - - - - - - - "
            "- - - - - - - - -",
            background="#434547",
            foreground="white",
            relief=GROOVE,
        )
        advanced_label.grid(
            row=6, column=0, columnspan=3, padx=10, pady=10, sticky=W + E
        )

        # Quality or Bitrate ------------------------------------------------------------------------------------------
        def quality_or_bitrate(_):
            if q_acodec_profile.get() == "True VBR":
                qaac_high_efficiency.set("")
                qaac_high_efficiency_checkbox.configure(state=DISABLED)
                q_acodec_quality_spinbox_label.grid()
                q_acodec_quality_spinbox.grid()
                q_acodec_bitrate_label.grid_remove()
                q_acodec_bitrate_spinbox.grid_remove()

            elif q_acodec_profile.get() != "True VBR":
                qaac_high_efficiency.set(
                    config_profile["FFMPEG QAAC - SETTINGS"]["qaac_high_efficiency"]
                    + " "
                )
                q_acodec_quality_spinbox_label.grid_remove()
                q_acodec_quality_spinbox.grid_remove()
                q_acodec_bitrate_label.grid()
                q_acodec_bitrate_spinbox.grid()
                qaac_high_efficiency_checkbox.configure(state=NORMAL)

        # ------------------------------------------------------------------------------------------ Quality or Bitrate

        # Audio Channel Selection -------------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "5.1 (Surround)": "-ac 6 ",
            "6.1 (Surround)": "-ac 7 ",
            "7.1 (Surround)": "-ac 8 ",
        }
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.set(config_profile["FFMPEG QAAC - SETTINGS"]["acodec_channel"])
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ----------------------------------------------------------------------------------------------- Audio Channel

        # Dolby Pro Logic II ------------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro Logic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=5,
            column=2,
            columnspan=1,
            rowspan=1,
            padx=10,
            pady=3,
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["dolbyprologicii"]
        )
        # ------------------------------------------------------------------------------------------------------ DPL II

        # Audio Stream Selection --------------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(
            next(iter(acodec_stream_track_counter))
        )  # set the default option
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=12,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()

        # ------------------------------------------------------------------------------------------------ Audio Stream

        # Entry Box for Custom Command Line ---------------------------------------------------------------------------
        def qaac_cmd(*args):
            global qaac_custom_cmd_input
            if qaac_custom_cmd.get().strip() == "":
                qaac_custom_cmd_input = ""
            else:
                cstmcmd = qaac_custom_cmd.get().strip()
                qaac_custom_cmd_input = cstmcmd + " "

        qaac_custom_cmd = StringVar()
        qaac_cmd_entrybox_label = Label(
            audio_window,
            text="QAAC Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        qaac_cmd_entrybox_label.grid(
            row=12, column=0, columnspan=2, padx=10, pady=(0, 0), sticky=N + S + W + E
        )
        qaac_cmd_entrybox = Entry(
            audio_window,
            textvariable=qaac_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        qaac_cmd_entrybox.grid(
            row=13, column=0, columnspan=3, padx=10, pady=(0, 0), sticky=W + E
        )
        qaac_custom_cmd.trace("w", qaac_cmd)
        qaac_custom_cmd.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- Custom Command Line

        # Entry Box for FFMPEG Command Line ---------------------------------------------------------------------------
        def ffmpeg_cmd_function(*args):
            global ffmpeg_custom_cmd_input
            if ffmpeg_custom_cmd.get().strip() == "":
                ffmpeg_custom_cmd_input = ""
            else:
                cstmcmd = ffmpeg_custom_cmd.get().strip()
                ffmpeg_custom_cmd_input = cstmcmd + " "

        ffmpeg_custom_cmd = StringVar()
        ffmpeg_cmd_entrybox_label = Label(
            audio_window,
            text="FFMPEG Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        ffmpeg_cmd_entrybox_label.grid(
            row=14, column=0, columnspan=2, padx=10, pady=(0, 0), sticky=N + S + W + E
        )
        ffmpeg_cmd_entrybox = Entry(
            audio_window,
            textvariable=ffmpeg_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        ffmpeg_cmd_entrybox.grid(
            row=15, column=0, columnspan=3, padx=10, pady=(0, 0), sticky=W + E
        )
        ffmpeg_custom_cmd.trace("w", ffmpeg_cmd_function)
        ffmpeg_custom_cmd.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["custom_command_line"]
        )

        # ----------------------------------------------------------------------------------------- FFMPEG Command Line

        # Entry Box for Track Title -----------------------------------------------------------------------------------
        def qaac_title_check(*args):
            global qaac_title_input
            if qaac_title.get().strip() == "":
                qaac_title_input = ""
            else:
                title_cmd = qaac_title.get().strip()
                qaac_title_input = "--title " + '"' + title_cmd + '"' + " "

        qaac_title = StringVar()
        qaac_title_entrybox_label = Label(
            audio_window,
            text="Track Name :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        qaac_title_entrybox_label.grid(
            row=16, column=0, columnspan=2, padx=10, pady=(0, 0), sticky=N + S + W + E
        )
        qaac_title_entrybox = Entry(
            audio_window, textvariable=qaac_title, borderwidth=4, background="#CACACA"
        )
        qaac_title_entrybox.grid(
            row=17, column=0, columnspan=3, padx=10, pady=(0, 10), sticky=W + E
        )
        qaac_title.trace("w", qaac_title_check)
        qaac_title.set("")
        # ------------------------------------------------------------------------------------------------- Track Title

        # Audio Sample Rate Selection ---------------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "11025 Hz": "-ar 11025 ",
            "22050 Hz": "-ar 22050 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
            "88200 Hz": "-ar 88200 ",
            "96000 Hz": "-ar 96000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=4, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        acodec_samplerate_menu.grid(
            row=5, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)
        # -------------------------------------------------------------------------------------------------- Samplerate

        # Audio Quality Selection -------------------------------------------------------------------------------------
        global q_acodec_quality
        global q_acodec_quality_choices
        q_acodec_quality = StringVar(audio_window)
        q_acodec_quality_choices = {
            "High (Default)": "",
            "Medium": "--quality 1 ",
            "Low": "--quality 0 ",
        }
        q_acodec_quality.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["q_acodec_quality"]
        )  # set the default option
        q_acodec_quality_label = Label(
            audio_window, text="Quality :", background="#434547", foreground="white"
        )
        q_acodec_quality_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_quality_menu = OptionMenu(
            audio_window, q_acodec_quality, *q_acodec_quality_choices.keys()
        )
        q_acodec_quality_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        q_acodec_quality_menu.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_quality_menu["menu"].configure(activebackground="dim grey")
        q_acodec_quality_menu.bind("<Enter>", q_acodec_quality_menu_hover)
        q_acodec_quality_menu.bind("<Leave>", q_acodec_quality_menu_hover_leave)
        # -------------------------------------------------------------------------------------------------------------

        # Audio Quality Spinbox ---------------------------------------------------------------------------------------
        global q_acodec_quality_amnt
        q_acodec_quality_amnt = StringVar(audio_window)
        q_acodec_quality_amnt_choices = (
            "0",
            "9",
            "18",
            "27",
            "36",
            "45",
            "54",
            "63",
            "73",
            "82",
            "91",
            "100",
            "109",
            "118",
            "127",
        )
        q_acodec_quality_spinbox_label = Label(
            audio_window,
            text="T-VBR Quality :",
            background="#434547",
            foreground="white",
        )
        q_acodec_quality_spinbox_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_quality_spinbox = Spinbox(
            audio_window,
            values=q_acodec_quality_amnt_choices,
            justify=CENTER,
            wrap=True,
            textvariable=q_acodec_quality_amnt,
            width=13,
            state="readonly",
        )
        q_acodec_quality_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            disabledbackground="grey",
            readonlybackground="#23272A",
        )
        q_acodec_quality_spinbox.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_quality_amnt.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["q_acodec_quality_amnt"]
        )
        # ----------------------------------------------------------------------------------------------------- Quality

        # Audio Bitrate -----------------------------------------------------------------------------------------------
        global q_acodec_bitrate
        q_acodec_bitrate = StringVar(audio_window)
        q_acodec_bitrate.set(
            int(config_profile["FFMPEG QAAC - SETTINGS"]["q_acodec_bitrate"])
        )  # set default
        q_acodec_bitrate_label = Label(
            audio_window, text="Bitrate :", background="#434547", foreground="white"
        )
        q_acodec_bitrate_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_bitrate_spinbox = Spinbox(
            audio_window,
            from_=0,
            to=1280,
            justify=CENTER,
            wrap=True,
            textvariable=q_acodec_bitrate,
            width=13,
        )
        q_acodec_bitrate_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            disabledbackground="grey",
        )
        q_acodec_bitrate_spinbox.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )

        def disable_enable_bitrate():
            if q_acodec_profile.get() == "True VBR":
                q_acodec_quality_spinbox_label.grid()
                q_acodec_quality_spinbox.grid()
                q_acodec_bitrate_label.grid_remove()
                q_acodec_bitrate_spinbox.grid_remove()
            else:
                q_acodec_quality_spinbox_label.grid_remove()
                q_acodec_quality_spinbox.grid_remove()
                q_acodec_bitrate_label.grid()
                q_acodec_bitrate_spinbox.grid()

        # ----------------------------------------------------------------------------------------------------- Bitrate

        # Audio Volume Selection ----------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=4, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=5, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG QAAC - SETTINGS"]["volume"])
        volume_right_click_options()  # Run function for right click options for volume spinbox
        # -------------------------------------------------------------------------------------------------- Volume

        # QAAC Gain ---------------------------------------------------------------------------------------------------
        global q_acodec_gain
        q_acodec_gain = StringVar(audio_window)
        q_acodec_gain_label = Label(
            audio_window, text="Gain :", background="#434547", foreground="white"
        )
        q_acodec_gain_label.grid(
            row=10, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_gain_spinbox = Spinbox(
            audio_window,
            from_=-100,
            to=100,
            justify=CENTER,
            wrap=True,
            textvariable=q_acodec_gain,
            width=13,
        )
        q_acodec_gain_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            disabledbackground="grey",
        )
        q_acodec_gain_spinbox.grid(
            row=11, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_acodec_gain.trace("w", qaac_gain_trace)
        q_acodec_gain.set(
            int(config_profile["FFMPEG QAAC - SETTINGS"]["q_acodec_gain"])
        )
        # -------------------------------------------------------------------------------------------------------- Gain

        # Misc Checkboxes - Normalize ---------------------------------------------------------------------------------
        global qaac_normalize
        qaac_normalize = StringVar()
        qaac_normalize.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_normalize"].replace(".", " ")
        )
        qaac_normalize_checkbox = Checkbutton(
            audio_window,
            text="Normalize",
            variable=qaac_normalize,
            onvalue="--normalize ",
            offvalue="",
        )
        qaac_normalize_checkbox.grid(
            row=11, column=0, columnspan=1, padx=10, pady=(10, 3), sticky=N + S + E + W
        )
        qaac_normalize_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # --------------------------------------------------------------------------------------------------- Normalize

        # Misc Checkboxes - High Efficiency ---------------------------------------------------------------------------
        global qaac_high_efficiency
        qaac_high_efficiency = StringVar()
        qaac_high_efficiency_checkbox = Checkbutton(
            audio_window,
            text="High Efficiency",
            variable=qaac_high_efficiency,
            onvalue="--he ",
            offvalue="",
            state=DISABLED,
        )
        qaac_high_efficiency_checkbox.grid(
            row=8, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        qaac_high_efficiency_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        qaac_high_efficiency.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_high_efficiency"].replace(
                ".", " "
            )
        )

        def enable_disable_he():
            if q_acodec_profile.get() != "True VBR":
                qaac_high_efficiency_checkbox.configure(state=NORMAL)

        # --------------------------------------------------------------------------------------------- High Effeciency

        # Audio Profile Menu ------------------------------------------------------------------------------------------
        global q_acodec_profile
        global q_acodec_profile_choices
        q_acodec_profile = StringVar(audio_window)
        q_acodec_profile_choices = {
            "True VBR": "--tvbr ",
            "Constrained VBR": "--cvbr ",
            "ABR": "--abr ",
            "CBR": "--cbr ",
        }
        q_acodec_profile.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["q_acodec_profile"]
        )  # set the default option
        q_acodec_profile_menu_label = Label(
            audio_window, text="Mode :", background="#434547", foreground="white"
        )
        q_acodec_profile_menu_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        q_acodec_profile_menu = OptionMenu(
            audio_window,
            q_acodec_profile,
            *q_acodec_profile_choices.keys(),
            command=quality_or_bitrate,
        )
        q_acodec_profile_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        q_acodec_profile_menu.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        q_acodec_profile_menu["menu"].configure(activebackground="dim grey")
        q_acodec_profile_menu.bind("<Enter>", q_acodec_profile_hover)
        q_acodec_profile_menu.bind("<Leave>", q_acodec_profile_hover_leave)
        enable_disable_he()
        disable_enable_bitrate()
        # ------------------------------------------------------------------------------------------ Audio Profile Menu

        # Misc Checkboxes - No Dither When Quantizing to Lower Bit Depth ----------------------------------------------
        global qaac_nodither
        qaac_nodither = StringVar()
        qaac_nodither.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_nodither"].replace(".", " ")
        )
        qaac_nodither_checkbox = Checkbutton(
            audio_window,
            text="No Dither",
            variable=qaac_nodither,
            onvalue="--no-dither ",
            offvalue="",
        )
        qaac_nodither_checkbox.grid(
            row=7, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        qaac_nodither_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # --------------------------------------------------------------------------------------------------- No Dither

        # Misc Checkboxes - No Delay ----------------------------------------------------------------------------------
        global qaac_nodelay
        qaac_nodelay = StringVar()
        qaac_nodelay.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_nodelay"].replace(".", " ")
        )
        qaac_nodelay_checkbox = Checkbutton(
            audio_window,
            text="No Delay",
            variable=qaac_nodelay,
            onvalue="--no-delay ",
            offvalue="",
        )
        qaac_nodelay_checkbox.grid(
            row=7, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        qaac_nodelay_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # ---------------------------------------------------------------------------------------------------- No Delay

        # Gapless Mode ------------------------------------------------------------------------------------------------
        global q_gapless_mode
        global q_gapless_mode_choices
        q_gapless_mode = StringVar(audio_window)
        q_gapless_mode_choices = {
            "iTunSMPB (Default)": "",
            "ISO standard": "--gapless-mode 1 ",
            "Both": "--gapless-mode 2 ",
        }
        q_gapless_mode.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["q_gapless_mode"]
        )  # set the default option
        q_gapless_mode_label = Label(
            audio_window,
            text="Gapless Mode :",
            background="#434547",
            foreground="white",
        )
        q_gapless_mode_label.grid(
            row=8, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_gapless_mode_menu = OptionMenu(
            audio_window, q_gapless_mode, *q_gapless_mode_choices.keys()
        )
        q_gapless_mode_menu.config(
            background="#23272A", foreground="white", highlightthickness=1
        )
        q_gapless_mode_menu.grid(
            row=9, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        q_gapless_mode_menu["menu"].configure(activebackground="dim grey")
        q_gapless_mode_menu.bind("<Enter>", q_gapless_mode_menu_hover)
        q_gapless_mode_menu.bind("<Leave>", q_gapless_mode_menu_hover_leave)
        # ------------------------------------------------------------------------------------------------ Gapless Mode

        # Misc Checkboxes - No Optimize -------------------------------------------------------------------------------
        global qaac_nooptimize
        qaac_nooptimize = StringVar()
        qaac_nooptimize.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_nooptimize"].replace(
                ".", " "
            )
        )
        qaac_nooptimize_checkbox = Checkbutton(
            audio_window,
            text="No Optimize",
            variable=qaac_nooptimize,
            onvalue="--no-optimize ",
            offvalue="",
        )
        qaac_nooptimize_checkbox.grid(
            row=7, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        qaac_nooptimize_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # ------------------------------------------------------------------------------------------------- No Optimize

        # Misc Checkboxes - Threading ---------------------------------------------------------------------------------
        global qaac_threading
        qaac_threading = StringVar()
        qaac_threading.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_threading"].replace(".", " ")
        )
        qaac_threading_checkbox = Checkbutton(
            audio_window,
            text="Threading",
            variable=qaac_threading,
            onvalue="--threading ",
            offvalue="",
        )
        qaac_threading_checkbox.grid(
            row=10, column=0, columnspan=1, padx=10, pady=(10, 3), sticky=N + S + E + W
        )
        qaac_threading_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # --------------------------------------------------------------------------------------------------- Threading

        # Misc Checkboxes - Limiter -----------------------------------------------------------------------------------
        global qaac_limiter
        qaac_limiter = StringVar()
        qaac_limiter.set(
            config_profile["FFMPEG QAAC - SETTINGS"]["qaac_limiter"].replace(".", " ")
        )
        qaac_limiter_checkbox = Checkbutton(
            audio_window,
            text="Limiter",
            variable=qaac_limiter,
            onvalue="--limiter ",
            offvalue="",
        )
        qaac_limiter_checkbox.grid(
            row=9, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        qaac_limiter_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        # ----------------------------------------------------------------------------------------------------- Limiter

        # Audio Atempo Selection ---------------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ------------------------------------------------------------------------------------------------ Audio Atempo
    # ----------------------------------------------------------------------------------------------------------- QAAC

    # FLAC Window -----------------------------------------------------------------------------------------------------
    elif encoder.get() == "FLAC":
        audio_window = Toplevel()
        audio_window.title("FLAC Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - flac - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - flac"] == "no"
        ):
            window_height = 550
            window_width = 650
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - flac - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - flac"]
            == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - flac - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for flac_n in range(3):
            audio_window.grid_columnconfigure(flac_n, weight=1)
        for flac_n in [0, 1, 2, 3, 4, 6, 7, 10]:
            audio_window.grid_rowconfigure(flac_n, weight=1)

        # Buttons -------------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=10, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        # ------------------------------------------------------------------------------------------------- Buttons

        advanced_label = Label(
            audio_window,
            text="- - - - - - - - - - - - - - - - - - - - Advanced Settings - - - - - "
            "- - - - - - - - - - - - - - -",
            background="#434547",
            foreground="white",
            relief=GROOVE,
        )
        advanced_label.grid(
            row=5, column=0, columnspan=3, padx=10, pady=10, sticky=W + E
        )

        # Audio Bitrate Selection ---------------------------------------------------------------------------------
        acodec_bitrate = StringVar(audio_window)
        acodec_bitrate_choices = {
            "Level 0 - Lowest Compression/Fastest": "-compression_level 0 ",
            "Level 1 ......": "-compression_level 1 ",
            "Level 2 ......": "-compression_level 2 ",
            "Level 3 ......": "-compression_level 3 ",
            "Level 4 ......": "-compression_level 4 ",
            "Level 5 - Default Compression/Speed": "",
            "Level 6 ......": "-compression_level 6 ",
            "Level 7 ......": "-compression_level 7 ",
            "Level 8 ......": "-compression_level 8 ",
            "Level 9 ......": "-compression_level 9 ",
            "Level 10 ......": "-compression_level 10 ",
            "Level 11 ......": "-compression_level 11 ",
            "Level 12 - Highest Compression/Slow": "-compression_level 12 ",
        }
        acodec_bitrate.set(
            config_profile["FFMPEG FLAC - SETTINGS"]["acodec_bitrate"]
        )  # set the default option
        acodec_bitrate_menu_label = Label(
            audio_window,
            text="Compression Level :",
            background="#434547",
            foreground="white",
        )
        acodec_bitrate_menu_label.grid(
            row=0, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_bitrate_menu = OptionMenu(
            audio_window, acodec_bitrate, *acodec_bitrate_choices.keys()
        )
        acodec_bitrate_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=15,
            anchor=W,
        )
        acodec_bitrate_menu.grid(
            row=1, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_bitrate_menu["menu"].configure(activebackground="dim grey")
        acodec_bitrate_menu.bind("<Enter>", acodec_bitrate_menu_hover)
        acodec_bitrate_menu.bind("<Leave>", acodec_bitrate_menu_hover_leave)
        # ------------------------------------------------------------------------------------------- Audio Bitrate

        # Audio Stream Selection ----------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(
            next(iter(acodec_stream_track_counter))
        )  # set the default option
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=15,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # ---------------------------------------------------------------------------------------------------------

        # Audio Channel Selection ---------------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "5.0 (Surround)": "-ac 5 ",
            "5.1 (Surround)": "-ac 6 ",
            "6.1 (Surround)": "-ac 7 ",
            "7.1 (Surround)": "-ac 8 ",
        }
        acodec_channel.set(
            config_profile["FFMPEG FLAC - SETTINGS"]["acodec_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1, width=15
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # ----------------------------------------------------------------------------------------------- Audio Channel

        # Dolby Pro Logic II ------------------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=4,
            column=2,
            columnspan=1,
            rowspan=1,
            padx=10,
            pady=(20, 5),
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG FLAC - SETTINGS"]["dolbyprologicii"]
        )
        # -------------------------------------------------------------------------------------------------- DPL II

        # Audio Volume Selection ----------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-20,
            to=20,
            increment=0.1,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG FLAC - SETTINGS"]["volume"])
        volume_right_click_options()
        # -------------------------------------------------------------------------------------------------- Volume

        # Audio Sample Rate Selection -----------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "8000 Hz": "-ar 8000 ",
            "11025 Hz": "-ar 11025 ",
            "22050 Hz": "-ar 22050 ",
            "32000 Hz": "-ar 32000 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
            "96000 Hz": "-ar 96000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG FLAC - SETTINGS"]["samplerate"]
        )  # set the default option
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1, width=15
        )
        acodec_samplerate_menu.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)

        # --------------------------------------------------------------------------------------------- Sample Rate

        # Entry Box for Custom Command Line -----------------------------------------------------------------------
        def flac_cmd(*args):
            global flac_custom_cmd_input
            if flac_custom_cmd.get().strip() == "":
                flac_custom_cmd_input = ""
            else:
                cstmcmd = flac_custom_cmd.get().strip()
                flac_custom_cmd_input = cstmcmd + " "

        flac_custom_cmd = StringVar()
        flac_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        flac_cmd_entrybox_label.grid(
            row=8, column=0, columnspan=2, padx=10, pady=(15, 0), sticky=N + S + W + E
        )
        flac_cmd_entrybox = Entry(
            audio_window,
            textvariable=flac_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        flac_cmd_entrybox.grid(
            row=9, column=0, columnspan=3, padx=10, pady=(0, 15), sticky=W + E
        )
        flac_custom_cmd.trace("w", flac_cmd)
        flac_custom_cmd.set(
            config_profile["FFMPEG FLAC - SETTINGS"]["custom_command_line"]
        )
        # ------------------------------------------------------------------------------------- Custom Command Line

        # Audio Atempo Selection ----------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")
        # ------------------------------------------------------------------------------------------------ Audio Atempo

        # LPC Algorithm Selection ---------------------------------------------------------------------------------
        global acodec_flac_lpc_type, acodec_flac_lpc_type_choices
        acodec_flac_lpc_type = StringVar(audio_window)
        acodec_flac_lpc_type_choices = {
            "Default": "",
            "None": "-lpc_type 0 ",
            "Fixed": "-lpc_type 1 ",
            "Levinson": "-lpc_type 2 ",
            "Cholesky": "-lpc_type 3 ",
        }
        acodec_flac_lpc_type.set(
            config_profile["FFMPEG FLAC - SETTINGS"]["flac_lpc_type"]
        )  # set the default
        acodec_flac_lpc_type_label = Label(
            audio_window,
            text="LPC Algorithm :",
            background="#434547",
            foreground="white",
        )
        acodec_flac_lpc_type_label.grid(
            row=6, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_flac_lpc_type_menu = OptionMenu(
            audio_window, acodec_flac_lpc_type, *acodec_flac_lpc_type_choices.keys()
        )
        acodec_flac_lpc_type_menu.config(
            background="#23272A", foreground="white", highlightthickness=1, width=15
        )
        acodec_flac_lpc_type_menu.grid(
            row=7, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_flac_lpc_type_menu["menu"].configure(activebackground="dim grey")
        acodec_flac_lpc_type_menu.bind("<Enter>", acodec_flac_lpc_type_menu_hover)
        acodec_flac_lpc_type_menu.bind("<Leave>", acodec_flac_lpc_type_menu_hover_leave)

        # ------------------------------------------------------------------------------------------- LPC Algorithm

        # FLAC LPC Coefficient Precision --------------------------------------------------------------------------
        def flac_acodec_coefficient_trace(*args):
            global set_flac_acodec_coefficient
            if flac_acodec_coefficient.get() == "15":
                set_flac_acodec_coefficient = ""
            elif flac_acodec_coefficient.get() != "15":
                set_flac_acodec_coefficient = (
                    "-lpc_coeff_precision " + flac_acodec_coefficient.get() + " "
                )

        global flac_acodec_coefficient
        flac_acodec_coefficient = StringVar(audio_window)
        flac_acodec_coefficient_label = Label(
            audio_window,
            text="LPC Coefficient Precision :",
            background="#434547",
            foreground="white",
        )
        flac_acodec_coefficient_label.grid(
            row=6, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        flac_acodec_coefficient_spinbox = Spinbox(
            audio_window,
            from_=0,
            to=15,
            justify=CENTER,
            wrap=True,
            textvariable=flac_acodec_coefficient,
            width=13,
        )
        flac_acodec_coefficient_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            disabledbackground="grey",
        )
        flac_acodec_coefficient_spinbox.grid(
            row=7, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        flac_acodec_coefficient.trace("w", flac_acodec_coefficient_trace)
        flac_acodec_coefficient.set(
            int(config_profile["FFMPEG FLAC - SETTINGS"]["flac_coefficient"])
        )
        # -------------------------------------------------------------------------- FLAC LPC Coefficient Precision

        # LPC Passes ----------------------------------------------------------------------------------------------
        global acodec_flac_lpc_passes, acodec_flac_lpc_passes_choices
        acodec_flac_lpc_passes = StringVar(audio_window)
        acodec_flac_lpc_passes_choices = {
            "Default": "",
            "2 Passes": "-lpc_passes 2 ",
            "3 Passes": "-lpc_passes 3 ",
            "4 Passes": "-lpc_passes 4 ",
            "5 Passes": "-lpc_passes 5 ",
            "6 Passes": "-lpc_passes 6 ",
            "7 Passes": "-lpc_passes 7 ",
            "8 Passes": "-lpc_passes 8 ",
            "9 Passes": "-lpc_passes 9 ",
            "10 Passes": "-lpc_passes 10 ",
        }
        acodec_flac_lpc_passes.set(
            config_profile["FFMPEG FLAC - SETTINGS"]["flac_lpc_passes"]
        )
        acodec_flac_lpc_passes_label = Label(
            audio_window, text="LPC Passes :", background="#434547", foreground="white"
        )
        acodec_flac_lpc_passes_label.grid(
            row=6, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_flac_lpc_passes_menu = OptionMenu(
            audio_window, acodec_flac_lpc_passes, *acodec_flac_lpc_passes_choices.keys()
        )
        acodec_flac_lpc_passes_menu.config(
            background="#23272A", foreground="white", highlightthickness=1, width=15
        )
        acodec_flac_lpc_passes_menu.grid(
            row=7, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_flac_lpc_passes_menu["menu"].configure(activebackground="dim grey")
        acodec_flac_lpc_passes_menu.bind("<Enter>", acodec_flac_lpc_passes_menu_hover)
        acodec_flac_lpc_passes_menu.bind(
            "<Leave>", acodec_flac_lpc_passes_menu_hover_leave
        )

        # ---------------------------------------------------------------------------------------------- LPC Passes
    # -------------------------------------------------------------------------------------------------------- FLAC

    # ALAC Window -------------------------------------------------------------------------------------------------
    elif encoder.get() == "ALAC":
        audio_window = Toplevel()
        audio_window.title("ALAC Settings")
        audio_window.configure(background="#434547")
        if (
            audio_win_parser["save_window_locations"]["audio window - alac - position"]
            == ""
            or audio_win_parser["save_window_locations"]["audio window - alac"] == "no"
        ):
            window_height = 470
            window_width = 650
            screen_width = audio_window.winfo_screenwidth()
            screen_height = audio_window.winfo_screenheight()
            x_coordinate = int((screen_width / 2) - (window_width / 2))
            y_coordinate = int((screen_height / 2) - (window_height / 2))
            audio_window.geometry(
                "{}x{}+{}+{}".format(
                    window_width, window_height, x_coordinate, y_coordinate
                )
            )
        elif (
            audio_win_parser["save_window_locations"]["audio window - alac - position"]
            != ""
            and audio_win_parser["save_window_locations"]["audio window - alac"]
            == "yes"
        ):
            audio_window.geometry(
                audio_win_parser["save_window_locations"][
                    "audio window - alac - position"
                ]
            )
        audio_window.protocol("WM_DELETE_WINDOW", audio_window_exit_function)
        root.withdraw()  # Hide root

        for alac_n in range(3):
            audio_window.grid_columnconfigure(alac_n, weight=1)
        for alac_n in [0, 1, 2, 3, 4, 5, 6, 10]:
            audio_window.grid_rowconfigure(alac_n, weight=1)

        # Buttons ---------------------------------------------------------------------------------------------
        if batch_mode == "yes":
            apply_command = gotosavefile_batch
        if batch_mode == "no":
            apply_command = lambda: [set_encode_manual(), gotosavefile()]
        apply_button = HoverButton(
            audio_window,
            text="Apply",
            foreground="white",
            background="#23272A",
            command=apply_command,
            activebackground="grey",
        )
        apply_button.grid(
            row=10, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        # --------------------------------------------------------------------------------------------- Buttons

        advanced_label = Label(
            audio_window,
            text="- - - - - - - - - - - - - - - - - - - - Advanced Settings - - - - - "
            "- - - - - - - - - - - - - - -",
            background="#434547",
            foreground="white",
            relief=GROOVE,
        )
        advanced_label.grid(
            row=4, column=0, columnspan=3, padx=10, pady=10, sticky=W + E
        )

        # Audio Stream Selection ------------------------------------------------------------------------------
        acodec_stream = StringVar(audio_window)
        acodec_stream_choices = acodec_stream_track_counter
        acodec_stream.set(next(iter(acodec_stream_track_counter)))
        acodec_stream_label = Label(
            audio_window, text="Track :", background="#434547", foreground="white"
        )
        acodec_stream_label.grid(
            row=0, column=0, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        acodec_stream_menu = OptionMenu(
            audio_window, acodec_stream, *acodec_stream_choices.keys()
        )
        acodec_stream_menu.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            width=15,
            anchor="w",
        )
        acodec_stream_menu.grid(
            row=1, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_stream_menu["menu"].configure(activebackground="dim grey")
        acodec_stream_menu.bind("<Enter>", acodec_stream_menu_hover)
        acodec_stream_menu.bind("<Leave>", acodec_stream_menu_hover_leave)
        acodec_stream.trace("w", track_number_mpv)
        track_number_mpv()
        # -----------------------------------------------------------------------------------------------------

        # Audio Channel Selection -----------------------------------------------------------------------------
        acodec_channel = StringVar(audio_window)
        acodec_channel_choices = {
            "Original": "",
            "1 (Mono)": "-ac 1 ",
            "2 (Stereo)": "-ac 2 ",
            "3": "-ac 3 ",
            "4": "-ac 4 ",
            "5.0 (Surround)": "-ac 5 ",
            "5.1 (Surround)": "-ac 6 ",
            "6.1 (Surround)": "-ac 7 ",
            "7.1 (Surround)": "-ac 8 ",
        }
        acodec_channel.set(
            config_profile["FFMPEG ALAC - SETTINGS"]["acodec_channel"]
        )  # set the default option
        achannel_menu_label = Label(
            audio_window, text="Channels :", background="#434547", foreground="white"
        )
        achannel_menu_label.grid(
            row=0, column=1, columnspan=1, padx=10, pady=3, sticky=W + E
        )
        achannel_menu = OptionMenu(
            audio_window, acodec_channel, *acodec_channel_choices.keys()
        )
        achannel_menu.config(
            background="#23272A", foreground="white", highlightthickness=1, width=15
        )
        achannel_menu.grid(
            row=1, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        achannel_menu["menu"].configure(activebackground="dim grey")
        achannel_menu.bind("<Enter>", achannel_menu_hover)
        achannel_menu.bind("<Leave>", achannel_menu_hover_leave)
        acodec_channel.trace("w", dolby_pro_logic_ii_enable_disable)
        # --------------------------------------------------------------------------------------- Audio Channel

        # Dolby Pro Logic II ----------------------------------------------------------------------------------
        dolby_pro_logic_ii = StringVar()
        dolby_pro_logic_ii_checkbox = Checkbutton(
            audio_window,
            text=" Dolby Pro\nLogic II",
            variable=dolby_pro_logic_ii,
            state=DISABLED,
            onvalue='"aresample=matrix_encoding=dplii"',
            offvalue="",
        )
        if acodec_channel.get() == "2 (Stereo)":
            dolby_pro_logic_ii_checkbox.configure(state=NORMAL)
        dolby_pro_logic_ii_checkbox.grid(
            row=0,
            column=2,
            columnspan=1,
            rowspan=2,
            padx=10,
            pady=(20, 5),
            sticky=N + S + E + W,
        )
        dolby_pro_logic_ii_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 11),
        )
        dolby_pro_logic_ii.set(
            config_profile["FFMPEG ALAC - SETTINGS"]["dolbyprologicii"]
        )
        # ---------------------------------------------------------------------------------------------- DPL II

        # Audio Volume Selection ----------------------------------------------------------------------------------
        ffmpeg_volume = StringVar()
        ffmpeg_volume_label = Label(
            audio_window, text="Volume :", background="#434547", foreground="white"
        )
        ffmpeg_volume_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume_spinbox = Spinbox(
            audio_window,
            from_=-30,
            to=30,
            increment=0.5,
            justify=CENTER,
            wrap=True,
            textvariable=ffmpeg_volume,
            state="readonly",
        )
        ffmpeg_volume_spinbox.configure(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            width=15,
            readonlybackground="#23272A",
        )
        ffmpeg_volume_spinbox.grid(
            row=3, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        ffmpeg_volume.set(config_profile["FFMPEG ALAC - SETTINGS"]["volume"])
        volume_right_click_options()
        # -------------------------------------------------------------------------------------------------- Volume

        # Audio Sample Rate Selection -------------------------------------------------------------------------
        acodec_samplerate = StringVar(audio_window)
        acodec_samplerate_choices = {
            "Original": "",
            "8000 Hz": "-ar 8000 ",
            "11025 Hz": "-ar 11025 ",
            "22050 Hz": "-ar 22050 ",
            "32000 Hz": "-ar 32000 ",
            "44100 Hz": "-ar 44100 ",
            "48000 Hz": "-ar 48000 ",
            "96000 Hz": "-ar 96000 ",
        }
        acodec_samplerate.set(
            config_profile["FFMPEG ALAC - SETTINGS"]["samplerate"]
        )  # set the default
        acodec_samplerate_label = Label(
            audio_window, text="Sample Rate :", background="#434547", foreground="white"
        )
        acodec_samplerate_label.grid(
            row=2, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu = OptionMenu(
            audio_window, acodec_samplerate, *acodec_samplerate_choices.keys()
        )
        acodec_samplerate_menu.config(
            background="#23272A", foreground="white", highlightthickness=1, width=15
        )
        acodec_samplerate_menu.grid(
            row=3, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        acodec_samplerate_menu["menu"].configure(activebackground="dim grey")
        acodec_samplerate_menu.bind("<Enter>", acodec_samplerate_menu_hover)
        acodec_samplerate_menu.bind("<Leave>", acodec_samplerate_menu_hover_leave)

        # ----------------------------------------------------------------------------------------- Sample Rate

        # Entry Box for Custom Command Line -------------------------------------------------------------------
        def flac_cmd(*args):
            global alac_custom_cmd_input
            if alac_custom_cmd.get().strip() == "":
                alac_custom_cmd_input = ""
            else:
                cstmcmd = alac_custom_cmd.get().strip()
                alac_custom_cmd_input = cstmcmd + " "

        alac_custom_cmd = StringVar()
        alac_cmd_entrybox_label = Label(
            audio_window,
            text="Custom Command Line :",
            anchor=W,
            background="#434547",
            foreground="white",
        )
        alac_cmd_entrybox_label.grid(
            row=8, column=0, columnspan=2, padx=10, pady=(15, 0), sticky=N + S + W + E
        )
        alac_cmd_entrybox = Entry(
            audio_window,
            textvariable=alac_custom_cmd,
            borderwidth=4,
            background="#CACACA",
        )
        alac_cmd_entrybox.grid(
            row=9, column=0, columnspan=3, padx=10, pady=(0, 15), sticky=W + E
        )
        alac_custom_cmd.trace("w", flac_cmd)
        alac_custom_cmd.set(
            config_profile["FFMPEG ALAC - SETTINGS"]["custom_command_line"]
        )
        # --------------------------------------------------------------------------------- Custom Command Line

        # Audio Atempo Selection ------------------------------------------------------------------------------
        acodec_atempo = StringVar()
        acodec_atempo_choices = {
            "Original": "",
            "23.976 to 24": '"atempo=24/23.976"',
            "23.976 to 25": '"atempo=25/23.976"',
            "23.976 to 29.97": '"atempo=29.97/23.976"',
            "23.976 to 50": '"atempo=50/23.976"',
            "23.976 to 60": '"atempo=60/23.976"',
            "24 to 23.976": '"atempo=23.976/24"',
            "24 to 25": '"atempo=25/24"',
            "24 to 29.97": '"atempo=29.97/24"',
            "24 to 50": '"atempo=50/24"',
            "24 to 60": '"atempo=60/24"',
            "25 to 23.976": '"atempo=23.976/25"',
            "25 to 24": '"atempo=24/25"',
            "25 to 29.97": '"atempo=29.97/25"',
            "25 to 50": '"atempo=50/25"',
            "25 to 60": '"atempo=60/25"',
            "29.97 to 23.976": '"atempo=23.976/29.97"',
            "29.97 to 24": '"atempo=24/29.97"',
            "29.97 to 25": '"atempo=25/29.97"',
            "29.97 to 50": '"atempo=50/29.97"',
            "29.97 to 60": '"atempo=60/29.97"',
            "50 to 23.976": '"atempo=23.976/50"',
            "50 to 24": '"atempo=24/50"',
            "50 to 25": '"atempo=25/50"',
            "50 to 29.97": '"atempo=29.97/50"',
            "50 to 60": '"atempo=60/50"',
            "60 to 23.976": '"atempo=23.976/60"',
            "60 to 24": '"atempo=24/60"',
            "60 to 25": '"atempo=25/60"',
            "60 to 29.97": '"atempo=29.97/60"',
            "60 to 50": '"atempo=50/60"',
            "1/4 Slow-down": '"atempo=0.5,atempo=0.5"',
            "1/2 Slow-down": '"atempo=0.5"',
            "3/4 Slow-down": '"atempo=0.75"',
            "1/4 Speed-up": '"atempo=1.25"',
            "1/2 Speed-up": '"atempo=1.5"',
            "3/4 Speed-up": '"atempo=1.75"',
            "2x Speed-up": '"atempo=2.0"',
            "2.5x Speed-up": '"atempo=2.5"',
            "3x Speed-up": '"atempo=3.0"',
            "3.5x Speed-up": '"atempo=3.5"',
            "4x Speed-up": '"atempo=4.0"',
        }

        acodec_atempo_menu_label = Label(
            audio_window,
            text="Time Modification :",
            background="#434547",
            foreground="white",
        )
        acodec_atempo_menu_label.grid(
            row=2, column=2, columnspan=1, padx=10, pady=3, sticky=W + E
        )

        acodec_atempo_combobox = ttk.Combobox(
            audio_window, textvariable=acodec_atempo, state="readonly"
        )
        acodec_atempo_combobox["values"] = list(acodec_atempo_choices.keys())
        acodec_atempo_combobox.grid(
            row=3, column=2, columnspan=1, padx=10, pady=3, sticky=N + S + W + E
        )
        acodec_atempo_combobox.bind("<<ComboboxSelected>>", acodec_atempo_selected)

        acodec_atempo.set("Original")

        # -------------------------------------------------------------------------------------------- Audio Atempo

        # Min-Prediction-Order ------------------------------------------------------------------------------------
        def get_min_pre_order(*args):
            global min_pre_order
            if min_prediction_order.get() == "4":
                min_pre_order = ""
            elif min_prediction_order.get() != "4":
                min_pre_order = (
                    "-min_prediction_order " + min_prediction_order.get() + " "
                )

        min_prediction_order = StringVar(audio_window)
        min_prediction_order_label = Label(
            audio_window,
            text="Min-Prediction-Order :",
            background="#434547",
            foreground="white",
        )
        min_prediction_order_label.grid(
            row=5, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        min_prediction_order_spinbox = Spinbox(
            audio_window,
            from_=1,
            to=30,
            justify=CENTER,
            wrap=True,
            textvariable=min_prediction_order,
            width=13,
        )
        min_prediction_order.trace("w", get_min_pre_order)
        min_prediction_order.set(
            int(config_profile["FFMPEG ALAC - SETTINGS"]["alac_min_prediction_order"])
        )
        min_prediction_order_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            disabledbackground="grey",
        )
        min_prediction_order_spinbox.grid(
            row=6, column=0, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )

        # ------------------------------------------------------------------------------------ Min-Prediction-Order

        # Max-Prediction-Order ------------------------------------------------------------------------------------
        def get_max_pre_order(*args):
            global max_pre_order
            if max_prediction_order.get() == "6":
                max_pre_order = ""
            elif max_prediction_order.get() != "6":
                max_pre_order = (
                    "-max_prediction_order " + max_prediction_order.get() + " "
                )

        max_prediction_order = StringVar(audio_window)
        max_prediction_order_label = Label(
            audio_window,
            text="Max-Prediction-Order :",
            background="#434547",
            foreground="white",
        )
        max_prediction_order_label.grid(
            row=5, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        max_prediction_order_spinbox = Spinbox(
            audio_window,
            from_=1,
            to=30,
            justify=CENTER,
            wrap=True,
            textvariable=max_prediction_order,
            width=13,
        )
        max_prediction_order.trace("w", get_max_pre_order)
        max_prediction_order.set(
            int(config_profile["FFMPEG ALAC - SETTINGS"]["alac_max_prediction_order"])
        )
        max_prediction_order_spinbox.config(
            background="#23272A",
            foreground="white",
            highlightthickness=1,
            buttonbackground="black",
            disabledbackground="grey",
        )
        max_prediction_order_spinbox.grid(
            row=6, column=1, columnspan=1, padx=10, pady=3, sticky=N + S + E + W
        )
        # ------------------------------------------------------------------------------------ Max-Prediction-Order
    # -------------------------------------------------------------------------------------------------------- ALAC

    audio_settings_menu = Menu(audio_window, tearoff=0)
    audio_window.config(menu=audio_settings_menu)
    # if batch_mode is no, enable the codec menu options
    if batch_mode == "no":
        file_menu = Menu(audio_settings_menu, tearoff=0, activebackground="dim grey")
        audio_settings_menu.add_cascade(label="Track Tools", menu=file_menu)
        file_menu.add_command(label="View Audio Tracks", command=show_streams_mediainfo)
        file_menu.add_command(
            label="Play Selected Audio Track  |  9 and 0 for Volume",
            command=mpv_gui_audio_window,
        )
    options_menu = Menu(audio_settings_menu, tearoff=0, activebackground="dim grey")
    audio_settings_menu.add_cascade(label="Options", menu=options_menu)
    options_menu.add_command(label="Save Current Settings", command=save_profile)
    options_menu.add_command(label="Reset Settings To Default", command=reset_profile)

    cmd_frame = Frame(audio_window)
    cmd_frame.grid(column=0, columnspan=3, row=100, sticky=N + S + E + W)
    cmd_frame.config(bg="#434547")
    cmd_frame.grid_columnconfigure(0, weight=1)

    mini_cmd_window = scrolledtextwidget.ScrolledText(cmd_frame, height=3)
    mini_cmd_window.grid(column=0, row=0, sticky=N + S + E + W)
    mini_cmd_window.configure(state=NORMAL, bg="black", fg="#CFD2D1", bd=8)

    def grab_mini_cmd_lines():  # Create mini_command lines for each codec
        audio_filter_function()  # Run function, to create correct ffmpeg_audio_filter functions
        if encoder.get() == "AC3":
            mini_cmd_output = " ".join(
                str(
                    acodec_stream_choices[acodec_stream.get()]
                    + encoder_dropdownmenu_choices[encoder.get()]
                    + acodec_bitrate_choices[acodec_bitrate.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + ac3_custom_cmd_input
                ).split()
            )
        elif encoder.get() == "AAC":
            if aac_vbr_toggle.get() == "-c:a ":
                mini_cmd_output = " ".join(
                    str(
                        acodec_stream_choices[acodec_stream.get()]
                        + encoder_dropdownmenu_choices[encoder.get()]
                        + "-b:a "
                        + aac_bitrate_spinbox.get()
                        + "k "
                        + acodec_channel_choices[acodec_channel.get()]
                        + acodec_samplerate_choices[acodec_samplerate.get()]
                        + audio_filter_setting
                        + aac_custom_cmd_input
                        + aac_title_input
                    ).split()
                )
            elif aac_vbr_toggle.get() == "-q:a ":
                mini_cmd_output = " ".join(
                    str(
                        acodec_stream_choices[acodec_stream.get()]
                        + encoder_dropdownmenu_choices[encoder.get()]
                        + "-q:a "
                        + aac_quality_spinbox.get()
                        + " "
                        + acodec_channel_choices[acodec_channel.get()]
                        + acodec_samplerate_choices[acodec_samplerate.get()]
                        + audio_filter_setting
                        + aac_custom_cmd_input
                        + aac_title_input
                    ).split()
                )
        elif encoder.get() == "DTS":
            if dts_settings.get() == "DTS Encoder":
                mini_cmd_output = " ".join(
                    str(
                        acodec_stream_choices[acodec_stream.get()]
                        + dts_settings_choices[dts_settings.get()]
                        + "-b:a "
                        + dts_bitrate_spinbox.get()
                        + "k "
                        + acodec_channel_choices[acodec_channel.get()]
                        + acodec_samplerate_choices[acodec_samplerate.get()]
                        + audio_filter_setting
                        + dts_custom_cmd_input
                    ).split()
                )
            else:
                mini_cmd_output = " ".join(
                    str(
                        acodec_stream_choices[acodec_stream.get()]
                        + dts_settings_choices[dts_settings.get()]
                        + dts_custom_cmd_input
                    ).split()
                )
        elif encoder.get() == "Opus":
            mini_cmd_output = " ".join(
                str(
                    acodec_stream_choices[acodec_stream.get()]
                    + encoder_dropdownmenu_choices[encoder.get()]
                    + acodec_bitrate_choices[acodec_bitrate.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_vbr_choices[acodec_vbr.get()]
                    + acodec_application_choices[acodec_application.get()]
                    + opus_mapping_family_choices[opus_mapping_family.get()]
                    + "-packet_loss "
                    + packet_loss.get()
                    + " -frame_duration "
                    + frame_duration.get()
                    + " "
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + opus_custom_cmd_input
                ).split()
            )
        elif encoder.get() == "MP3":
            mini_cmd_output = " ".join(
                str(
                    acodec_stream_choices[acodec_stream.get()]
                    + encoder_dropdownmenu_choices[encoder.get()]
                    + acodec_bitrate_choices[acodec_bitrate.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + mp3_abr.get()
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + mp3_custom_cmd_input
                ).split()
            )
        elif encoder.get() == "E-AC3":
            mini_cmd_output = " ".join(
                str(
                    acodec_stream_choices[acodec_stream.get()]
                    + encoder_dropdownmenu_choices[encoder.get()]
                    + "-b:a "
                    + eac3_spinbox.get()
                    + " "
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + eac3_custom_cmd_input
                    + per_frame_metadata_choices[per_frame_metadata.get()]
                    + "-mixing_level "
                    + eac3_mixing_level.get()
                    + " "
                    + room_type_choices[room_type.get()]
                    + "-copyright "
                    + copyright_bit.get()
                    + " "
                    + "-dialnorm "
                    + dialogue_level.get()
                    + " "
                    + dolby_surround_mode_choices[dolby_surround_mode.get()]
                    + "-original "
                    + original_bit_stream.get()
                    + " "
                    + downmix_mode_choices[downmix_mode.get()]
                    + "-ltrt_cmixlev "
                    + lt_rt_center_mix.get()
                    + " "
                    + "-ltrt_surmixlev "
                    + lt_rt_surround_mix.get()
                    + " "
                    + "-loro_cmixlev "
                    + lo_ro_center_mix.get()
                    + " "
                    + "\n \n"
                    + "-loro_surmixlev "
                    + lo_ro_surround_mix.get()
                    + " "
                    + dolby_surround_ex_mode_choices[dolby_surround_ex_mode.get()]
                    + dolby_headphone_mode_choices[dolby_headphone_mode.get()]
                    + a_d_converter_type_choices[a_d_converter_type.get()]
                    + stereo_rematrixing_choices[stereo_rematrixing.get()]
                    + "-channel_coupling "
                    + channel_coupling.get()
                    + " "
                    + "-cpl_start_band "
                    + cpl_start_band.get()
                    + " "
                ).split()
            )
        elif encoder.get() == "FDK-AAC":
            mini_cmd_output = " ".join(
                str(
                    acodec_stream_choices[acodec_stream.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + ffmpeg_custom_cmd_input
                    + "-f caf - | "
                    + "fdkaac.exe"
                    + " "
                    + acodec_profile_choices[acodec_profile.get()]
                    + afterburnervar.get()
                    + fdkaac_title_input
                    + fdkaac_custom_cmd_input
                    + acodec_gapless_mode_choices[acodec_gapless_mode.get()]
                    + crccheck.get()
                    + moovbox.get()
                    + sbrdelay.get()
                    + headerperiod.get()
                    + acodec_lowdelay_choices[acodec_lowdelay.get()]
                    + acodec_sbr_ratio_choices[acodec_sbr_ratio.get()]
                    + acodec_transport_format_choices[acodec_transport_format.get()]
                    + acodec_bitrate_choices[acodec_bitrate.get()]
                    + "- -o "
                ).split()
            )
        elif encoder.get() == "QAAC":
            if q_acodec_profile.get() == "True VBR":
                mini_cmd_output = " ".join(
                    str(
                        acodec_stream_choices[acodec_stream.get()]
                        + acodec_channel_choices[acodec_channel.get()]
                        + acodec_samplerate_choices[acodec_samplerate.get()]
                        + audio_filter_setting
                        + ffmpeg_custom_cmd_input
                        + "-f wav - | "
                        + qaac
                        + " --ignorelength "
                        + q_acodec_profile_choices[q_acodec_profile.get()]
                        + q_acodec_quality_amnt.get()
                        + " "
                        + qaac_high_efficiency.get()
                        + qaac_nodither.get()
                        + set_qaac_gain
                        + q_acodec_quality_choices[q_acodec_quality.get()]
                        + qaac_normalize.get()
                        + qaac_nodelay.get()
                        + q_gapless_mode_choices[q_gapless_mode.get()]
                        + qaac_nooptimize.get()
                        + qaac_threading.get()
                        + qaac_limiter.get()
                        + qaac_title_input
                        + qaac_custom_cmd_input
                    ).split()
                )
            else:
                mini_cmd_output = " ".join(
                    str(
                        acodec_stream_choices[acodec_stream.get()]
                        + acodec_channel_choices[acodec_channel.get()]
                        + acodec_samplerate_choices[acodec_samplerate.get()]
                        + audio_filter_setting
                        + ffmpeg_custom_cmd_input
                        + "-f wav - | "
                        + qaac
                        + " --ignorelength "
                        + q_acodec_profile_choices[q_acodec_profile.get()]
                        + q_acodec_bitrate.get()
                        + " "
                        + qaac_high_efficiency.get()
                        + qaac_nodither.get()
                        + set_qaac_gain
                        + q_acodec_quality_choices[q_acodec_quality.get()]
                        + qaac_normalize.get()
                        + qaac_nodelay.get()
                        + q_gapless_mode_choices[q_gapless_mode.get()]
                        + qaac_nooptimize.get()
                        + qaac_threading.get()
                        + qaac_limiter.get()
                        + qaac_title_input
                        + qaac_custom_cmd_input
                    ).split()
                )
        elif encoder.get() == "FLAC":
            mini_cmd_output = " ".join(
                str(
                    acodec_stream_choices[acodec_stream.get()]
                    + encoder_dropdownmenu_choices[encoder.get()]
                    + acodec_bitrate_choices[acodec_bitrate.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + set_flac_acodec_coefficient
                    + acodec_flac_lpc_type_choices[acodec_flac_lpc_type.get()]
                    + acodec_flac_lpc_passes_choices[acodec_flac_lpc_passes.get()]
                    + flac_custom_cmd_input
                ).split()
            )
        elif encoder.get() == "ALAC":
            mini_cmd_output = " ".join(
                str(
                    acodec_stream_choices[acodec_stream.get()]
                    + encoder_dropdownmenu_choices[encoder.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + min_pre_order
                    + max_pre_order
                    + alac_custom_cmd_input
                ).split()
            )
        return mini_cmd_output  # Returns the variable when function is called

    def audio_settings_cmd_line_updater():  # Auto update the command line every 50 milliseconds
        try:
            if mini_cmd_window.winfo_viewable():  # If the mini_cmd_window is viewable
                input_command = grab_mini_cmd_lines()
                if mini_cmd_window.get(1.0, END).strip() != input_command.strip():
                    mini_cmd_window.configure(state=NORMAL)
                    mini_cmd_window.delete(1.0, END)
                    mini_cmd_window.insert(END, input_command)
                    mini_cmd_window.configure(state=DISABLED)
            root.after(50, audio_settings_cmd_line_updater)
        except (NameError, AttributeError, TclError):
            return

    audio_settings_cmd_line_updater()  # Start the auto updater

    def right_click_menu_func(
        x_y_pos,
    ):  # Function for mouse button 3 (right click) to pop up menu
        right_click_menu.tk_popup(
            x_y_pos.x_root, x_y_pos.y_root
        )  # This gets the position of cursor

    def copy_selected_text():  # Function to copy only selected text
        pya_hotkey("ctrl", "c")
        sleep(0.01)  # Slow program incase ctrl+c is slower

    right_click_menu = Menu(
        mini_cmd_window, tearoff=False
    )  # This is the right click menu
    right_click_menu.add_command(label="Copy Selected Text", command=copy_selected_text)
    right_click_menu.add_command(
        label="Copy All Text",
        command=lambda: pyperclip.copy(mini_cmd_window.get(1.0, END).strip()),
    )
    mini_cmd_window.bind(
        "<Button-3>", right_click_menu_func
    )  # Uses mouse button 3 (right click) to pop up menu
    Hovertip(
        mini_cmd_window, "Right click to copy", hover_delay=1200
    )  # Hover tip tool-tip

    # Local configparser for below code
    audio_func_parser = ConfigParser()
    audio_func_parser.read(config_file)
    # Add some options to the "Options" menu in each audio codec window
    options_menu.add_separator()
    options_submenu = Menu(root, tearoff=0, activebackground="dim grey")
    options_menu.add_cascade(label="View Command", menu=options_submenu)

    # Code to set the toggle each time window is opened
    view_mini_command_toggle = StringVar()
    view_mini_command_toggle.set(
        audio_func_parser["audio_settings_command_toggle"]["option"]
    )
    if view_mini_command_toggle.get() == "":
        view_mini_command_toggle.set("on")
    elif view_mini_command_toggle.get() != "":
        view_mini_command_toggle.set(
            audio_func_parser["audio_settings_command_toggle"]["option"]
        )

    def update_cmd_toggle():  # Enables/disables grid when on/off is selected from menu
        if view_mini_command_toggle.get() == "on":
            cmd_frame.grid()
        elif view_mini_command_toggle.get() == "off":
            cmd_frame.grid_remove()
        audio_func_parser.set(
            "audio_settings_command_toggle", "option", view_mini_command_toggle.get()
        )
        with open(config_file, "w") as configfile:
            audio_func_parser.write(configfile)  # Write selection to config.ini

    update_cmd_toggle()  # Run function once when window is opened
    options_submenu.add_radiobutton(
        label="On",
        variable=view_mini_command_toggle,
        value="on",
        command=update_cmd_toggle,
    )
    options_submenu.add_radiobutton(
        label="Off",
        variable=view_mini_command_toggle,
        value="off",
        command=update_cmd_toggle,
    )


# ---------------------------------------------------------------------------------------------- End Audio Codec Window


# File Output ---------------------------------------------------------------------------------------------------------
def file_save():
    global file_output
    if encoder.get() == "AAC":
        file_output = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            initialdir=autofilesave_dir_path,
            title="Select a Save Location",
            initialfile=autosavefilename,
            filetypes=[("AAC", "*.mp4")],
        )
    elif encoder.get() == "AC3" or encoder.get() == "E-AC3":
        file_output = filedialog.asksaveasfilename(
            defaultextension=".ac3",
            initialdir=autofilesave_dir_path,
            title="Select a Save Location",
            initialfile=autosavefilename,
            filetypes=[("'AC3', 'E-AC3,'", "*.ac3")],
        )
    elif encoder.get() == "DTS":
        file_output = filedialog.asksaveasfilename(
            defaultextension=".dts",
            initialdir=autofilesave_dir_path,
            title="Select a Save Location",
            initialfile=autosavefilename,
            filetypes=[("DTS", "*.dts")],
        )
    elif encoder.get() == "Opus":
        file_output = filedialog.asksaveasfilename(
            defaultextension=".opus",
            initialdir=autofilesave_dir_path,
            title="Select a Save Location",
            initialfile=autosavefilename,
            filetypes=[("Opus", "*.opus")],
        )
    elif encoder.get() == "MP3":
        file_output = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            initialdir=autofilesave_dir_path,
            title="Select a Save Location",
            initialfile=autosavefilename,
            filetypes=[("MP3", "*.mp3")],
        )
    elif (
        encoder.get() == "FDK-AAC" or encoder.get() == "QAAC" or encoder.get() == "ALAC"
    ):
        file_output = filedialog.asksaveasfilename(
            defaultextension=".m4a",
            initialdir=autofilesave_dir_path,
            title="Select a Save Location",
            initialfile=autosavefilename,
            filetypes=[("'AAC,' 'ALAC,'", "*.m4a")],
        )
    elif encoder.get() == "FLAC":
        file_output = filedialog.asksaveasfilename(
            defaultextension=".flac",
            initialdir=autofilesave_dir_path,
            title="Select a Save Location",
            initialfile=autosavefilename,
            filetypes=[("FLAC", "*.flac")],
        )

    if file_output:
        output_entry.configure(state=NORMAL)  # Enable entry box for commands under
        output_entry.delete(0, END)  # Remove current text in entry
        output_entry.insert(0, str(pathlib.Path(file_output)))  # Insert the 'path'
        output_entry.configure(state=DISABLED)  # Disables Entry Box


# --------------------------------------------------------------------------------------------------------- File Output
def encoder_menu_hover(e):
    encoder_menu["bg"] = "grey"
    encoder_menu["activebackground"] = "grey"


def encoder_menu_hover_leave(e):
    encoder_menu["bg"] = "#23272A"


# Print Command Line from ROOT ----------------------------------------------------------------------------------------
def exit_cmd_window():  # Global function to exit the command line window
    func_parser = ConfigParser()
    func_parser.read(config_file)
    try:
        if func_parser["save_window_locations"]["display command"] == "yes":
            try:  # If auto-save position on exit is checked
                func_parser.set(
                    "save_window_locations",
                    "display command position",
                    cmd_line_window.geometry(),
                )
                with open(config_file, "w") as configfile:
                    func_parser.write(configfile)
            except (Exception,):
                pass
        cmd_line_window.destroy()
    except NameError:  # If it doesn't exist return from the function
        return


def print_command_line():
    global cmd_line_window, show_cmd_scrolled_main

    audio_filter_function()
    collect_final_job_commands()

    cmd_line_parser = ConfigParser()
    cmd_line_parser.read(config_file)

    try:
        show_cmd_scrolled_main.configure(state=NORMAL)
        show_cmd_scrolled_main.delete(1.0, END)
    except (NameError, TclError):
        cmd_line_window = Toplevel()
        cmd_line_window.title("Display Command")
        cmd_line_window.configure(background="#434547")
        if (
            cmd_line_parser["save_window_locations"]["display command position"] != ""
            and cmd_line_parser["save_window_locations"]["display command"] == "yes"
        ):
            cmd_line_window.geometry(
                cmd_line_parser["save_window_locations"]["display command position"]
            )
        cmd_line_window.protocol("WM_DELETE_WINDOW", exit_cmd_window)
        show_cmd_scrolled_main = scrolledtextwidget.ScrolledText(
            cmd_line_window,
            width=90,
            height=10,
            tabs=10,
            spacing2=3,
            spacing1=2,
            spacing3=3,
        )
        show_cmd_scrolled_main.grid(row=0, column=0, pady=(5, 4), padx=5, sticky=E + W)
        show_cmd_scrolled_main.configure(bg="black", fg="#CFD2D1", bd=8)
    show_cmd_scrolled_main.insert(END, finalcommand.replace('""', '"'))
    show_cmd_scrolled_main.see(END)
    show_cmd_scrolled_main.configure(state=DISABLED)

    def print_command_line_updater():
        try:
            if show_cmd_scrolled_main.winfo_viewable():
                if (
                    show_cmd_scrolled_main.get(1.0, END).strip()
                    != finalcommand.replace('""', '"').strip()
                ):
                    audio_filter_function()
                    collect_final_job_commands()
                    show_cmd_scrolled_main.configure(state=NORMAL)
                    show_cmd_scrolled_main.delete(1.0, END)
                    show_cmd_scrolled_main.insert(END, finalcommand.replace('""', '"'))
                    show_cmd_scrolled_main.see(END)
                    show_cmd_scrolled_main.configure(state=DISABLED)
            root.after(50, print_command_line_updater)
        except (NameError, AttributeError, TclError):
            return

    print_command_line_updater()

    def right_click_menu_func(
        x_y_pos,
    ):  # Function for mouse button 3 (right click) to pop up menu
        right_click_menu.tk_popup(
            x_y_pos.x_root, x_y_pos.y_root
        )  # This gets the position of cursor

    def copy_selected_text():  # Function to copy only selected text
        pya_hotkey("ctrl", "c")
        sleep(0.01)  # Slow program incase ctrl+c is slower

    right_click_menu = Menu(
        cmd_line_window, tearoff=False
    )  # This is the right click menu
    right_click_menu.add_command(label="Copy Selected Text", command=copy_selected_text)
    right_click_menu.add_command(
        label="Copy All Text",
        command=lambda: pyperclip.copy(show_cmd_scrolled_main.get(1.0, END).strip()),
    )
    cmd_line_window.bind(
        "<Button-3>", right_click_menu_func
    )  # Uses mouse button 3 (right click) to pop up menu
    Hovertip(
        cmd_line_window, "Right click to copy", hover_delay=1200
    )  # Hover tip tool-tip


# ---------------------------------------------------------------------------------------- Print Command Line from ROOT


def collect_final_job_commands():
    global finalcommand, last_used_command, batch_command, batch_mode
    if batch_mode == "no":
        file_output_quoted = '"' + str(pathlib.Path(file_output)) + '"'
    # AC3 Start Job ---------------------------------------------------------------------------------------------------
    if encoder.get() == "AC3":
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + ac3_custom_cmd_input
                + file_output_quoted
                + " -v error -hide_banner -stats"
            )
            last_used_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + ac3_custom_cmd_input
            )
        elif batch_mode == "yes":
            batch_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + ac3_custom_cmd_input
            )

    # --------------------------------------------------------------------------------------------------------- AC3 Job
    # AAC Start Job ---------------------------------------------------------------------------------------------------
    elif encoder.get() == "AAC":
        if aac_vbr_toggle.get() == "-c:a ":
            bitrate_or_quality = f"-b:a {aac_bitrate_spinbox.get()}k "
        elif aac_vbr_toggle.get() == "-q:a ":
            bitrate_or_quality = f"-q:a {aac_quality_spinbox.get()} "
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + encoder_dropdownmenu_choices[encoder.get()]
                + bitrate_or_quality
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + aac_custom_cmd_input
                + aac_title_input
                + file_output_quoted
                + " -v error -hide_banner -stats"
            )
            last_used_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + bitrate_or_quality
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + aac_custom_cmd_input
                + aac_title_input
            )
        elif batch_mode == "yes":
            batch_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + bitrate_or_quality
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + aac_custom_cmd_input
                + aac_title_input
            )
        # ------------------------------------------------------------------------------------------------- AAC Job
    # DTS Start Job ---------------------------------------------------------------------------------------------------
    elif encoder.get() == "DTS":
        if dts_settings.get() == "DTS Encoder":
            if batch_mode == "no":
                finalcommand = str(
                    '"'
                    + ffmpeg
                    + " -y -analyzeduration 100M -probesize 50M -i "
                    + file_input_quoted
                    + acodec_stream_choices[acodec_stream.get()]
                    + dts_settings_choices[dts_settings.get()]
                    + "-b:a "
                    + dts_bitrate_spinbox.get()
                    + "k "
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + dts_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + file_output_quoted
                    + " -v error -hide_banner -stats"
                )
                last_used_command = str(
                    dts_settings_choices[dts_settings.get()]
                    + "-b:a "
                    + dts_bitrate_spinbox.get()
                    + "k "
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + dts_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                )
            elif batch_mode == "yes":
                batch_command = str(
                    dts_settings_choices[dts_settings.get()]
                    + "-b:a "
                    + dts_bitrate_spinbox.get()
                    + "k "
                    + acodec_channel_choices[acodec_channel.get()]
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + audio_filter_setting
                    + dts_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                )
        elif dts_settings.get() != "DTS Encoder":
            if batch_mode == "no":
                finalcommand = str(
                    '"'
                    + ffmpeg
                    + " -y -analyzeduration 100M -probesize 50M -i "
                    + file_input_quoted
                    + acodec_stream_choices[acodec_stream.get()]
                    + dts_settings_choices[dts_settings.get()]
                    + dts_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + file_output_quoted
                    + " -v error -hide_banner -stats"
                )
                last_used_command = str(
                    dts_settings_choices[dts_settings.get()]
                    + dts_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                )
            elif batch_mode == "yes":
                batch_command = str(
                    dts_settings_choices[dts_settings.get()]
                    + dts_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                )
    # ------------------------------------------------------------------------------------------------------------- DTS
    # Opus Start Job --------------------------------------------------------------------------------------------------
    elif encoder.get() == "Opus":
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + encoder_dropdownmenu_choices[encoder.get()]
                + acodec_vbr_choices[acodec_vbr.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_application_choices[acodec_application.get()]
                + opus_mapping_family_choices[opus_mapping_family.get()]
                + "-packet_loss "
                + packet_loss.get()
                + " -frame_duration "
                + frame_duration.get()
                + " "
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + opus_custom_cmd_input
                + file_output_quoted
                + " -v error -hide_banner -stats"
            )
            last_used_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_vbr_choices[acodec_vbr.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_application_choices[acodec_application.get()]
                + opus_mapping_family_choices[opus_mapping_family.get()]
                + "-packet_loss "
                + packet_loss.get()
                + " -frame_duration "
                + frame_duration.get()
                + " "
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
            )
        elif batch_mode == "yes":
            batch_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_vbr_choices[acodec_vbr.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_application_choices[acodec_application.get()]
                + opus_mapping_family_choices[opus_mapping_family.get()]
                + "-packet_loss "
                + packet_loss.get()
                + " -frame_duration "
                + frame_duration.get()
                + " "
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
            )
    # ------------------------------------------------------------------------------------------------------------ Opus
    # MP3 Start Job ---------------------------------------------------------------------------------------------------
    elif encoder.get() == "MP3":
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + mp3_abr.get()
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + mp3_custom_cmd_input
                + file_output_quoted
                + " -v error -hide_banner -stats"
            )
            last_used_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + mp3_abr.get()
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + mp3_custom_cmd_input
            )
        elif batch_mode == "yes":
            batch_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + mp3_abr.get()
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + mp3_custom_cmd_input
            )
    # ------------------------------------------------------------------------------------------------------------- MP3
    # E-AC3 Start Job -------------------------------------------------------------------------------------------------
    elif encoder.get() == "E-AC3":
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + encoder_dropdownmenu_choices[encoder.get()]
                + "-b:a "
                + eac3_spinbox.get()
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + eac3_custom_cmd_input
                + per_frame_metadata_choices[per_frame_metadata.get()]
                + "-mixing_level "
                + eac3_mixing_level.get()
                + " "
                + room_type_choices[room_type.get()]
                + "-copyright "
                + copyright_bit.get()
                + " "
                + "-dialnorm "
                + dialogue_level.get()
                + " "
                + dolby_surround_mode_choices[dolby_surround_mode.get()]
                + "-original "
                + original_bit_stream.get()
                + " "
                + downmix_mode_choices[downmix_mode.get()]
                + "-ltrt_cmixlev "
                + lt_rt_center_mix.get()
                + " "
                + "-ltrt_surmixlev "
                + lt_rt_surround_mix.get()
                + " "
                + "-loro_cmixlev "
                + lo_ro_center_mix.get()
                + " "
                + "-loro_surmixlev "
                + lo_ro_surround_mix.get()
                + " "
                + dolby_surround_ex_mode_choices[dolby_surround_ex_mode.get()]
                + dolby_headphone_mode_choices[dolby_headphone_mode.get()]
                + a_d_converter_type_choices[a_d_converter_type.get()]
                + stereo_rematrixing_choices[stereo_rematrixing.get()]
                + "-channel_coupling "
                + channel_coupling.get()
                + " "
                + "-cpl_start_band "
                + cpl_start_band.get()
                + " "
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + file_output_quoted
                + " -v error -hide_banner -stats"
            )
            last_used_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + "-b:a "
                + eac3_spinbox.get()
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + eac3_custom_cmd_input
                + per_frame_metadata_choices[per_frame_metadata.get()]
                + "-mixing_level "
                + eac3_mixing_level.get()
                + " "
                + room_type_choices[room_type.get()]
                + "-copyright "
                + copyright_bit.get()
                + " "
                + "-dialnorm "
                + dialogue_level.get()
                + " "
                + dolby_surround_mode_choices[dolby_surround_mode.get()]
                + "-original "
                + original_bit_stream.get()
                + " "
                + downmix_mode_choices[downmix_mode.get()]
                + "-ltrt_cmixlev "
                + lt_rt_center_mix.get()
                + " "
                + "-ltrt_surmixlev "
                + lt_rt_surround_mix.get()
                + " "
                + "-loro_cmixlev "
                + lo_ro_center_mix.get()
                + " "
                + "-loro_surmixlev "
                + lo_ro_surround_mix.get()
                + " "
                + dolby_surround_ex_mode_choices[dolby_surround_ex_mode.get()]
                + dolby_headphone_mode_choices[dolby_headphone_mode.get()]
                + a_d_converter_type_choices[a_d_converter_type.get()]
                + stereo_rematrixing_choices[stereo_rematrixing.get()]
                + "-channel_coupling "
                + channel_coupling.get()
                + " "
                + "-cpl_start_band "
                + cpl_start_band.get()
                + " "
                + "-sn -vn -map_chapters -1 "
            )
        elif batch_mode == "yes":
            batch_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + "-b:a "
                + eac3_spinbox.get()
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + eac3_custom_cmd_input
                + per_frame_metadata_choices[per_frame_metadata.get()]
                + "-mixing_level "
                + eac3_mixing_level.get()
                + " "
                + room_type_choices[room_type.get()]
                + "-copyright "
                + copyright_bit.get()
                + " "
                + "-dialnorm "
                + dialogue_level.get()
                + " "
                + dolby_surround_mode_choices[dolby_surround_mode.get()]
                + "-original "
                + original_bit_stream.get()
                + " "
                + downmix_mode_choices[downmix_mode.get()]
                + "-ltrt_cmixlev "
                + lt_rt_center_mix.get()
                + " "
                + "-ltrt_surmixlev "
                + lt_rt_surround_mix.get()
                + " "
                + "-loro_cmixlev "
                + lo_ro_center_mix.get()
                + " "
                + "-loro_surmixlev "
                + lo_ro_surround_mix.get()
                + " "
                + dolby_surround_ex_mode_choices[dolby_surround_ex_mode.get()]
                + dolby_headphone_mode_choices[dolby_headphone_mode.get()]
                + a_d_converter_type_choices[a_d_converter_type.get()]
                + stereo_rematrixing_choices[stereo_rematrixing.get()]
                + "-channel_coupling "
                + channel_coupling.get()
                + " "
                + "-cpl_start_band "
                + cpl_start_band.get()
                + " "
                + "-sn -vn -map_chapters -1 "
            )
    # ----------------------------------------------------------------------------------------------------------- E-AC3
    # FDK_AAC Start Job -----------------------------------------------------------------------------------------------
    elif encoder.get() == "FDK-AAC":
        if progress_output_view.get() == "Default":
            silent = "--silent "
        else:
            silent = " "
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + ffmpeg_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + "-f caf - -v error -hide_banner -stats | "
                + fdkaac
                + " "
                + acodec_profile_choices[acodec_profile.get()]
                + fdkaac_title_input
                + fdkaac_custom_cmd_input
                + acodec_gapless_mode_choices[acodec_gapless_mode.get()]
                + afterburnervar.get()
                + crccheck.get()
                + moovbox.get()
                + sbrdelay.get()
                + headerperiod.get()
                + acodec_lowdelay_choices[acodec_lowdelay.get()]
                + acodec_sbr_ratio_choices[acodec_sbr_ratio.get()]
                + acodec_transport_format_choices[acodec_transport_format.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + silent
                + "- -o "
                + file_output_quoted
            )
            last_used_command = str(
                acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + ffmpeg_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + "-f caf - -v error -hide_banner -stats | "
                + fdkaac
                + " "
                + acodec_profile_choices[acodec_profile.get()]
                + fdkaac_title_input
                + fdkaac_custom_cmd_input
                + acodec_gapless_mode_choices[acodec_gapless_mode.get()]
                + afterburnervar.get()
                + crccheck.get()
                + moovbox.get()
                + sbrdelay.get()
                + headerperiod.get()
                + acodec_lowdelay_choices[acodec_lowdelay.get()]
                + acodec_sbr_ratio_choices[acodec_sbr_ratio.get()]
                + acodec_transport_format_choices[acodec_transport_format.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + silent
                + "- -o "
            )
        elif batch_mode == "yes":
            batch_command = str(
                acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + ffmpeg_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + "-f caf - -v error -hide_banner -stats | "
                + fdkaac
                + " "
                + acodec_profile_choices[acodec_profile.get()]
                + fdkaac_title_input
                + fdkaac_custom_cmd_input
                + acodec_gapless_mode_choices[acodec_gapless_mode.get()]
                + afterburnervar.get()
                + crccheck.get()
                + moovbox.get()
                + sbrdelay.get()
                + headerperiod.get()
                + acodec_lowdelay_choices[acodec_lowdelay.get()]
                + acodec_sbr_ratio_choices[acodec_sbr_ratio.get()]
                + acodec_transport_format_choices[acodec_transport_format.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + silent
                + "- -o "
            )
    # ------------------------------------------------------------------------------------------------------------- FDK
    # QAAC Start Job --------------------------------------------------------------------------------------------------
    elif encoder.get() == "QAAC":
        if progress_output_view.get() == "Default":
            silent = "--silent "
        else:
            silent = " "
        if q_acodec_profile.get() == "True VBR":
            if batch_mode == "no":
                finalcommand = str(
                    '"'
                    + ffmpeg
                    + " -y -analyzeduration 100M -probesize 50M -i "
                    + file_input_quoted
                    + acodec_stream_choices[acodec_stream.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + audio_filter_setting
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + ffmpeg_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + "-f wav - -v error -hide_banner -stats | "
                    + qaac
                    + " --ignorelength "
                    + q_acodec_profile_choices[q_acodec_profile.get()]
                    + q_acodec_quality_amnt.get()
                    + " "
                    + qaac_high_efficiency.get()
                    + qaac_normalize.get()
                    + qaac_nodither.get()
                    + "--gain "
                    + q_acodec_gain.get()
                    + " "
                    + q_acodec_quality_choices[q_acodec_quality.get()]
                    + qaac_nodelay.get()
                    + q_gapless_mode_choices[q_gapless_mode.get()]
                    + qaac_nooptimize.get()
                    + qaac_threading.get()
                    + qaac_limiter.get()
                    + qaac_title_input
                    + qaac_custom_cmd_input
                    + silent
                    + "- -o "
                    + file_output_quoted
                )
                last_used_command = str(
                    acodec_channel_choices[acodec_channel.get()]
                    + audio_filter_setting
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + ffmpeg_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + "-f wav - -v error -hide_banner -stats | "
                    + qaac
                    + " --ignorelength "
                    + q_acodec_profile_choices[q_acodec_profile.get()]
                    + q_acodec_quality_amnt.get()
                    + " "
                    + qaac_high_efficiency.get()
                    + qaac_normalize.get()
                    + qaac_nodither.get()
                    + "--gain "
                    + q_acodec_gain.get()
                    + " "
                    + q_acodec_quality_choices[q_acodec_quality.get()]
                    + qaac_nodelay.get()
                    + q_gapless_mode_choices[q_gapless_mode.get()]
                    + qaac_nooptimize.get()
                    + qaac_threading.get()
                    + qaac_limiter.get()
                    + qaac_title_input
                    + qaac_custom_cmd_input
                    + silent
                    + "- -o "
                )
            elif batch_mode == "yes":
                batch_command = str(
                    acodec_channel_choices[acodec_channel.get()]
                    + audio_filter_setting
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + ffmpeg_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + "-f wav - -v error -hide_banner -stats | "
                    + qaac
                    + " --ignorelength "
                    + q_acodec_profile_choices[q_acodec_profile.get()]
                    + q_acodec_quality_amnt.get()
                    + " "
                    + qaac_high_efficiency.get()
                    + qaac_normalize.get()
                    + qaac_nodither.get()
                    + "--gain "
                    + q_acodec_gain.get()
                    + " "
                    + q_acodec_quality_choices[q_acodec_quality.get()]
                    + qaac_nodelay.get()
                    + q_gapless_mode_choices[q_gapless_mode.get()]
                    + qaac_nooptimize.get()
                    + qaac_threading.get()
                    + qaac_limiter.get()
                    + qaac_title_input
                    + qaac_custom_cmd_input
                    + silent
                    + "- -o "
                )
        else:
            if batch_mode == "no":
                finalcommand = str(
                    '"'
                    + ffmpeg
                    + " -analyzeduration 100M -probesize 50M -i "
                    + file_input_quoted
                    + acodec_stream_choices[acodec_stream.get()]
                    + acodec_channel_choices[acodec_channel.get()]
                    + audio_filter_setting
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + ffmpeg_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + "-f wav - -v error -hide_banner -stats | "
                    + qaac
                    + " --ignorelength "
                    + q_acodec_profile_choices[q_acodec_profile.get()]
                    + q_acodec_bitrate.get()
                    + qaac_high_efficiency.get()
                    + qaac_normalize.get()
                    + qaac_nodither.get()
                    + "--gain "
                    + q_acodec_gain.get()
                    + " "
                    + q_acodec_quality_choices[q_acodec_quality.get()]
                    + qaac_nodelay.get()
                    + q_gapless_mode_choices[q_gapless_mode.get()]
                    + qaac_nooptimize.get()
                    + qaac_threading.get()
                    + qaac_limiter.get()
                    + qaac_title_input
                    + qaac_custom_cmd_input
                    + silent
                    + "- -o "
                    + file_output_quoted
                )
                last_used_command = str(
                    acodec_channel_choices[acodec_channel.get()]
                    + audio_filter_setting
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + ffmpeg_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + "-f wav - -v error -hide_banner -stats | "
                    + qaac
                    + " --ignorelength "
                    + q_acodec_profile_choices[q_acodec_profile.get()]
                    + q_acodec_bitrate.get()
                    + qaac_high_efficiency.get()
                    + qaac_normalize.get()
                    + qaac_nodither.get()
                    + "--gain "
                    + q_acodec_gain.get()
                    + " "
                    + q_acodec_quality_choices[q_acodec_quality.get()]
                    + qaac_nodelay.get()
                    + q_gapless_mode_choices[q_gapless_mode.get()]
                    + qaac_nooptimize.get()
                    + qaac_threading.get()
                    + qaac_limiter.get()
                    + qaac_title_input
                    + qaac_custom_cmd_input
                    + silent
                    + "- -o "
                )
            elif batch_mode == "yes":
                batch_command = str(
                    acodec_channel_choices[acodec_channel.get()]
                    + audio_filter_setting
                    + acodec_samplerate_choices[acodec_samplerate.get()]
                    + ffmpeg_custom_cmd_input
                    + "-sn -vn -map_chapters -1 -map_metadata -1 "
                    + "-f wav - -v error -hide_banner -stats | "
                    + qaac
                    + " --ignorelength "
                    + q_acodec_profile_choices[q_acodec_profile.get()]
                    + q_acodec_bitrate.get()
                    + qaac_high_efficiency.get()
                    + qaac_normalize.get()
                    + qaac_nodither.get()
                    + "--gain "
                    + q_acodec_gain.get()
                    + " "
                    + q_acodec_quality_choices[q_acodec_quality.get()]
                    + qaac_nodelay.get()
                    + q_gapless_mode_choices[q_gapless_mode.get()]
                    + qaac_nooptimize.get()
                    + qaac_threading.get()
                    + qaac_limiter.get()
                    + qaac_title_input
                    + qaac_custom_cmd_input
                    + silent
                    + "- -o "
                )
    # ------------------------------------------------------------------------------------------------------------ QAAC
    # FLAC Start Job --------------------------------------------------------------------------------------------------
    elif encoder.get() == "FLAC":
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + set_flac_acodec_coefficient
                + acodec_flac_lpc_type_choices[acodec_flac_lpc_type.get()]
                + acodec_flac_lpc_passes_choices[acodec_flac_lpc_passes.get()]
                + flac_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + file_output_quoted
                + " -v error -hide_banner -stats"
                + '"'
            )
            last_used_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + set_flac_acodec_coefficient
                + acodec_flac_lpc_type_choices[acodec_flac_lpc_type.get()]
                + acodec_flac_lpc_passes_choices[acodec_flac_lpc_passes.get()]
                + flac_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
            )
        elif batch_mode == "yes":
            batch_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_bitrate_choices[acodec_bitrate.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + set_flac_acodec_coefficient
                + acodec_flac_lpc_type_choices[acodec_flac_lpc_type.get()]
                + acodec_flac_lpc_passes_choices[acodec_flac_lpc_passes.get()]
                + flac_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
            )
    # ------------------------------------------------------------------------------------------------------------ FLAC
    # ALAC Start Job --------------------------------------------------------------------------------------------------
    elif encoder.get() == "ALAC":
        if batch_mode == "no":
            finalcommand = str(
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + acodec_stream_choices[acodec_stream.get()]
                + encoder_dropdownmenu_choices[encoder.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + min_pre_order
                + max_pre_order
                + alac_custom_cmd_input
                + " "
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
                + file_output_quoted
                + " -v error -hide_banner -stats"
                + '"'
            )
            last_used_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + min_pre_order
                + max_pre_order
                + alac_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
            )
        elif batch_mode == "yes":
            batch_command = str(
                encoder_dropdownmenu_choices[encoder.get()]
                + acodec_channel_choices[acodec_channel.get()]
                + acodec_samplerate_choices[acodec_samplerate.get()]
                + audio_filter_setting
                + min_pre_order
                + max_pre_order
                + alac_custom_cmd_input
                + "-sn -vn -map_chapters -1 -map_metadata -1 "
            )
    # ------------------------------------------------------------------------------------------------------------ ALAC


# Start Audio Job -----------------------------------------------------------------------------------------------------
def startaudiojob():
    global example_cmd_output, ac3_job, aac_job, dts_job, opus_job, mp3_job, eac3_job, fdkaac_job, qaac_job, flac_job, alac_job, encoding_job_type, auto_track_input, acodec_stream, acodec_stream_choices
    # Quote File Input/Output Paths------------
    file_input_quoted = '"' + file_input + '"'
    file_output_quoted = '"' + file_output + '"'
    # -------------------------- Quote File Paths
    # Combine audio filters for FFMPEG
    audio_filter_function()
    # ------------------------- Filters

    # Start job ConfigParser
    single_progress_win_parser = ConfigParser()
    single_progress_win_parser.read(config_file)

    complete_or_not = ""  # Set empty placeholder variable for complete_or_not

    if progress_output_view.get() == "Default":  # Default progress bars
        global total_duration
        media_info = MediaInfo.parse(pathlib.Path(file_input))  # Parse input file
        track_selection_mediainfo = media_info.audio_tracks[
            int(acodec_stream_choices[acodec_stream.get()].strip()[-1])
        ]
        # track_selection_mediainfo uses the -map 0:a:x code to get the track input, the code grabs only the last number
        if (
            track_selection_mediainfo.duration is not None
        ):  # If track input HAS a duration
            total_duration = float(track_selection_mediainfo.duration)
        elif (
            track_selection_mediainfo.duration is None
        ):  # If track input DOES NOT have a duration
            messagebox.showinfo(
                title="Info",
                message="Input file has no duration, consider muxing elementary "
                "stream into mka/mkv/etc...\n\nProgress bar is "
                "temporarily disabled",
            )
            total_duration = track_selection_mediainfo.duration

        def save_close_position():  # Function to save size/position upon exit
            func_parser = ConfigParser()
            func_parser.read(config_file)
            if (
                func_parser["save_window_locations"]["progress window"] == "yes"
            ):  # If checkbutton is checked
                try:
                    if (
                        func_parser["save_window_locations"]["progress window position"]
                        != progress_window.geometry()
                    ):
                        func_parser.set(
                            "save_window_locations",
                            "progress window position",
                            progress_window.geometry(),
                        )
                        with open(config_file, "w") as configfile:
                            func_parser.write(configfile)
                except (Exception,):
                    pass

        def close_encode():
            if complete_or_not == "complete":
                save_close_position()
                progress_window.destroy()
                advanced_root_deiconify()
                open_all_toplevels()
                if encoder.get() == "Set Codec":
                    output_entry.configure(state=NORMAL)  # Enable output_entry
                    output_entry.delete(0, END)  # Clear contents of output entry
                    output_entry.configure(state=DISABLED)  # Disable output entry

            else:
                confirm_exit = messagebox.askyesno(
                    title="Prompt",
                    parent=progress_window,
                    message="Are you sure you want to stop the encode?",
                )
                if confirm_exit:
                    try:
                        parent = psutil.Process(job.pid)  # Set psutil parent ID
                        for child in parent.children(recursive=True):
                            child.kill()  # Loop through all the children processes and kill them with psutil module
                            child.wait()
                        if pathlib.Path(
                            str(file_output_quoted).replace('"', "")
                        ).is_file():  # Delete file if forced
                            file_del = pathlib.Path(
                                str(file_output_quoted).replace('"', "")
                            )
                            file_del.unlink(missing_ok=True)
                    except psutil.NoSuchProcess:
                        pass
                    save_close_position()  # Save position
                    progress_window.destroy()  # Destroy progress window
                    advanced_root_deiconify()  # Re-Open root
                    open_all_toplevels()  # Re-open top levels if there was any
                    if encoder.get() == "Set Codec":
                        output_entry.configure(state=NORMAL)  # Enable output_entry
                        output_entry.delete(0, END)  # Clear contents of output entry
                        output_entry.configure(state=DISABLED)  # Disable output entry

        def close_window():
            thread = threading.Thread(target=close_encode)
            thread.start()

        hide_all_toplevels()  # Hide all top levels
        root.withdraw()  # Hide root

        progress_window = Toplevel(root)
        progress_window.title(
            "Codec : " + encoder.get() + "  |  " + str(pathlib.Path(file_input).stem)
        )
        progress_window.configure(background="#434547")
        if (
            single_progress_win_parser["save_window_locations"][
                "progress window position"
            ]
            != ""
            and single_progress_win_parser["save_window_locations"]["progress window"]
            == "yes"
        ):
            progress_window.geometry(
                single_progress_win_parser["save_window_locations"][
                    "progress window position"
                ]
            )
        progress_window.protocol("WM_DELETE_WINDOW", close_window)
        progress_window.grid_rowconfigure(0, weight=1)
        progress_window.grid_rowconfigure(1, weight=1)
        progress_window.grid_columnconfigure(0, weight=1)

        progress_window_frame = LabelFrame(
            progress_window, text=" Encoding Progress ", labelanchor="nw"
        )
        progress_window_frame.grid(
            column=0, row=0, columnspan=1, padx=5, pady=(0, 3), sticky=N + S + E + W
        )
        progress_window_frame.configure(
            fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold")
        )
        progress_window_frame.grid_rowconfigure(0, weight=1)
        progress_window_frame.grid_columnconfigure(0, weight=1)

        progress_button_frame = LabelFrame(
            progress_window, text=" Options ", labelanchor="nw"
        )
        progress_button_frame.grid(
            column=0, row=1, columnspan=1, padx=5, pady=(0, 3), sticky=N + S + E + W
        )
        progress_button_frame.configure(
            fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold")
        )
        progress_button_frame.grid_rowconfigure(0, weight=1)
        progress_button_frame.grid_rowconfigure(1, weight=1)
        for pbf_n in range(5):
            progress_button_frame.grid_columnconfigure(pbf_n, weight=1)

        encode_window_progress = scrolledtextwidget.ScrolledText(
            progress_window_frame,
            tabs=10,
            spacing2=3,
            spacing1=2,
            spacing3=3,
            height=10,
        )
        encode_window_progress.grid(
            row=0, column=0, pady=(0, 6), padx=10, sticky=E + W + N + S
        )
        encode_window_progress.config(bg="black", fg="#CFD2D1", bd=8)
        encode_window_progress.insert(
            END, " -" * 16 + " Encode Started " + "- " * 16 + "\n\n"
        )

        def right_click_menu_func(
            x_y_pos,
        ):  # Function for mouse button 3 (right click) to pop up menu
            right_click_menu.tk_popup(
                x_y_pos.x_root, x_y_pos.y_root
            )  # This gets the position of cursor

        right_click_menu = Menu(
            encode_window_progress, tearoff=False
        )  # This is the right click menu
        right_click_menu.add_command(
            label="Copy",
            command=lambda: pyperclip.copy(
                encode_window_progress.get(1.0, END).strip()
            ),
        )
        encode_window_progress.bind(
            "<Button-3>", right_click_menu_func
        )  # Uses right click to pop up menu

        def auto_close_window_toggle():  # Function to save input from the checkbox below to config.ini
            try:
                config.set(
                    "auto_close_progress_window", "option", auto_close_window.get()
                )
                with open(config_file, "w") as configfile:
                    config.write(configfile)
            except (Exception,):
                pass

        auto_close_window_checkbox = Checkbutton(
            progress_button_frame,
            text="Automatically Close",
            variable=auto_close_window,
            takefocus=False,
            width="10",
            onvalue="on",
            offvalue="off",
            command=auto_close_window_toggle,
        )
        auto_close_window_checkbox.grid(
            row=0,
            column=0,
            columnspan=1,
            rowspan=1,
            padx=5,
            pady=(10, 5),
            sticky=S + E + W + N,
        )
        auto_close_window_checkbox.configure(
            background="#434547",
            foreground="white",
            activebackground="#434547",
            activeforeground="white",
            selectcolor="#434547",
            font=("Helvetica", 12),
        )
        auto_close_window.set(config["auto_close_progress_window"]["option"])

        def copy_to_clipboard():  # Function to allow copying full command to clipboard via pyperclip module
            pyperclip.copy(encode_window_progress.get(1.0, END))

        copy_text = HoverButton(
            progress_button_frame,
            text="Copy to clipboard",
            command=copy_to_clipboard,
            foreground="white",
            background="#23272A",
            borderwidth="3",
            activebackground="grey",
        )
        copy_text.grid(
            row=0, column=1, columnspan=1, padx=10, pady=(5, 4), sticky=S + E + W + N
        )

        if total_duration is not None:
            app_progress_bar = ttk.Progressbar(
                progress_window_frame,
                orient=HORIZONTAL,
                mode="determinate",
                style="custom.Horizontal.TProgressbar",
            )
            app_progress_bar.grid(column=0, row=1, sticky=W + E, pady=(0, 2), padx=3)
        if total_duration is None:
            temp_label = Label(
                progress_window_frame,
                text="Input has no duration - progress bar is temporarily disabled",
                bd=4,
                relief=SUNKEN,
                anchor=E,
                background="#717171",
                foreground="white",
            )
            temp_label.grid(column=0, row=1, pady=(0, 2), padx=3, sticky=E + W)

        def update_last_codec_command():  # Updates 'profiles.ini' last used codec/commands
            config_profile.set("Auto Encode", "codec", encoder.get())
            config_profile.set("Auto Encode", "command", str(last_used_command))
            with open(config_profile_ini, "w") as configfile_two:
                config_profile.write(configfile_two)

        def reset_main_gui():  # This resets the Main Gui back to default settings
            encoder.set("Set Codec")
            audiosettings_button.configure(state=DISABLED)

    collect_final_job_commands()

    if progress_output_view.get() == "Default":  # If program is set to progress bars
        # If variable encoding_job_type is set to 'manual', the command = final command
        if encoding_job_type == "manual":
            command = finalcommand
            update_last_codec_command()  # Calls a function that set's the auto encode information to ini file
        # If variable encoding_job_type is set to 'auto' it uses the info in the
        elif encoding_job_type == "auto":
            # Start job ConfigParser
            auto_parser = ConfigParser()
            auto_parser.read(config_profile_ini)
            # ini file to encode with the command below
            if (
                auto_parser["Auto Encode"]["codec"] == "QAAC"
                or auto_parser["Auto Encode"]["codec"] == "FDK-AAC"
            ):
                hide_banner_verbose = ""
            else:
                hide_banner_verbose = ' -v error -hide_banner -stats"'
            command = (
                '"'
                + ffmpeg
                + " -y -analyzeduration 100M -probesize 50M -i "
                + file_input_quoted
                + f" -map 0:a:{str(auto_track_input)} "
                + config_profile["Auto Encode"]["command"].lstrip().rstrip()
                + " "
                + file_output_quoted
                + hide_banner_verbose
            )

        # Use subprocess.Popen to feed the command to the terminal and handle the stder/stdout output
        job = subprocess.Popen(
            "cmd /c " + command + '"',
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        def cancel_job():  # Cancel job code
            if complete_or_not != "complete":
                confirm_exit = messagebox.askyesno(
                    title="Prompt",
                    parent=progress_window,
                    message="Are you sure you want to stop the encode?",
                )
                if confirm_exit:  # If user selects yes
                    try:
                        job_id = psutil.Process(job.pid)
                        for job_ids in job_id.children(recursive=True):
                            job_ids.kill()
                            job_ids.wait()
                        if pathlib.Path(
                            str(file_output_quoted).replace('"', "")
                        ).is_file():
                            file_del = pathlib.Path(
                                str(file_output_quoted).replace('"', "")
                            )
                            file_del.unlink(missing_ok=True)
                    except psutil.NoSuchProcess:
                        pass
                    save_close_position()  # Save position
                    progress_window.destroy()  # Destroy progress window
                    advanced_root_deiconify()  # Re-Open root
                    if encoder.get() == "Set Codec":
                        output_entry.configure(state=NORMAL)  # Enable output_entry
                        output_entry.delete(0, END)  # Clear contents of output entry
                        output_entry.configure(state=DISABLED)  # Disable output entry
                    open_all_toplevels()  # Re-open top levels if there was any

        # Cancel button
        cancel_encode_job = HoverButton(
            progress_button_frame,
            text="Cancel",
            command=cancel_job,
            foreground="white",
            background="#23272A",
            borderwidth="3",
            activebackground="grey",
        )
        cancel_encode_job.grid(
            row=0, column=4, columnspan=1, padx=10, pady=(5, 4), sticky=S + E + W + N
        )

        def pause_job():  # Pause function/button
            pause_current_job = psutil.Process(job.pid)
            for p_current_job in pause_current_job.children(recursive=True):
                p_current_job.suspend()
            pause_encode_job.config(state=DISABLED)
            resume_encode_job.config(state=NORMAL)

        pause_encode_job = HoverButton(
            progress_button_frame,
            text="Pause",
            command=pause_job,
            foreground="white",
            background="#23272A",
            borderwidth="3",
            activebackground="grey",
        )
        pause_encode_job.grid(
            row=0, column=2, columnspan=1, padx=10, pady=(5, 4), sticky=S + E + W + N
        )

        def resume_job():  # Resume function/button
            resume_current_job = psutil.Process(job.pid)
            for r_current_job in resume_current_job.children(recursive=True):
                r_current_job.resume()
            pause_encode_job.config(state=NORMAL)
            resume_encode_job.config(state=DISABLED)

        resume_encode_job = HoverButton(
            progress_button_frame,
            text="Resume",
            command=resume_job,
            foreground="white",
            background="#23272A",
            borderwidth="3",
            activebackground="grey",
            state=DISABLED,
        )
        resume_encode_job.grid(
            row=0, column=3, columnspan=1, padx=10, pady=(5, 4), sticky=S + E + W + N
        )

        # Open Save Directory
        def open_save_directory():
            webbrowser.open(pathlib.Path(file_output).parent)

        open_output_dir = HoverButton(
            progress_button_frame,
            text="Open Output Directory",
            command=open_save_directory,
            foreground="white",
            background="#23272A",
            borderwidth="3",
            activebackground="grey",
        )
        open_output_dir.grid(
            row=1, column=0, columnspan=1, padx=10, pady=(5, 4), sticky=S + E + W + N
        )

        if encoding_job_type == "auto":
            codec_selection = config_profile["Auto Encode"]["codec"]
        else:
            codec_selection = str(encoder.get())

        if (
            encoder.get() == "QAAC" or encoder.get() == "FDK-AAC"
        ):  # String to output for fdk/qaac encoder
            insert_info_string = (
                f'Encoding {str(file_input_quoted)} via "FFMPEG" by piping to external encoder: '
                f'"{codec_selection}"'
            )
        elif (
            encoder.get() != "QAAC" or encoder.get() != "FDK-AAC"
        ):  # String to output for all internal encoders
            insert_info_string = (
                f'Encoding {str(file_input_quoted)} via "FFMPEG" with internal encoder: '
                f'"{codec_selection}"'
            )

        if (
            encoding_job_type == "auto"
        ):  # If encoding_job_type is set to 'auto', once the user encodes it resets
            # main gui back to default settings
            reset_main_gui()

        encode_window_progress.configure(state=NORMAL)
        encode_window_progress.insert(END, str("\n" + "-" * 62 + "\n"))
        encode_window_progress.insert(
            END, insert_info_string
        )  # Insert string for internal/external encoders
        encode_window_progress.insert(END, str("\n" + "-" * 62 + "\n\n\n"))
        encode_window_progress.configure(state=DISABLED)
        progress_error = ""  # Set an empty variable to be changed in the job code

        for line in job.stdout:  # Using subprocess.Popen, read stdout lines
            try:
                encode_window_progress.configure(state=NORMAL)
                # Code removes any/all double or white space from string to keep it looking nice (ffmpeg is messy)
                encode_window_progress.insert(
                    END, str("\n".join(" ".join(x.split()) for x in line.split("\n")))
                )
                encode_window_progress.see(
                    END
                )  # Scrolls the textbox to bottom every single pass
                encode_window_progress.configure(state=DISABLED)
            except TclError:
                return

            if (
                total_duration is None
            ):  # Set's the percent to 100% if input has no duration
                percent = 100  # this way the job code can complete without error
                if (
                    line.split()[0] == "size=" and progress_error != "no"
                ):  # Find string 'size=',
                    # if found program is running correctly, also only check if progress error isn't == 'no'
                    progress_error = (
                        "no"  # Once 'size=' is found update progress_error to 'no'
                    )
                else:
                    progress_error = "yes"

            if total_duration is not None:  # If input file has duration metadata
                if (
                    line.split()[0] == "size="
                ):  # Find string 'size=' to start work with progress bar
                    progress_error = (
                        "no"  # Once 'size=' is found set progress_error to 'no'
                    )
                    try:  # Block of code to turn 00:00:00 frmt to milliseconds (same as duration) for progress bar
                        time = line.split()[2].rsplit("=", 1)[1]
                        try:
                            progress = (
                                sum(
                                    x * float(t)
                                    for x, t in zip(
                                        [1, 60, 3600], reversed(time.split(":"))
                                    )
                                )
                                * 1000
                            )
                            percent = float(
                                str(
                                    "{:.1%}".format(
                                        float(progress) / float(total_duration)
                                    )
                                ).replace("%", "")
                            )
                        except (ValueError, TypeError):
                            continue
                        try:
                            app_progress_bar["value"] = int(
                                percent
                            )  # Input progress into progress bar
                        except (Exception,):
                            pass
                    except (
                        Exception
                    ) as e:  # If progress window errors out for what ever reason
                        progress_error = "yes"  # Set error to 'yes'
                        progress_window.destroy()  # Close progress window
                        subprocess.Popen(
                            f"TASKKILL /F /PID {job.pid} /T",  # Force close job.pid/children
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        msg_error = messagebox.askokcancel(
                            title="Error!",
                            message=f"There was an error:"
                            f'\n\n"{str(line).rstrip()}"\n\n'
                            f"Additional info: {e}\n\n"
                            f"Would you like to report the "
                            f"error on the github tracker?",
                        )
                        if msg_error:  # If user wants to post bug on the github tracker
                            webbrowser.open(
                                "https://github.com/jlw4049/FFMPEG-Audio-Encoder/issues"
                            )
                else:
                    progress_error = "yes"
        try:
            encode_window_progress.configure(
                state=NORMAL
            )  # Enable progress window editing
            encode_window_progress.insert(END, str("\n" + "-" * 62 + "\n"))

            if (
                progress_error == "no" and int(percent) >= 99
            ):  # If no error and percent reached 99%, job is complete
                if pathlib.Path(
                    str(file_output_quoted).replace('"', "")
                ).is_file():  # Check if file exists
                    encode_window_progress.insert(
                        END, str("Job Completed!\n\n")
                    )  # Insert into text window
                    encode_window_progress.insert(
                        END, f"Output file is: \n{str(file_output_quoted)}"
                    )
                    complete_or_not = str(
                        "complete"
                    )  # Set variable to complete, for closing window without prompt
                else:  # If job does not complete, string to show the user there was an error
                    messagebox.showerror(
                        title="Error!",
                        message="There was an error in job:\n\n"
                        + '"Codec : '
                        + encoder.get()
                        + "  |  "
                        + str(pathlib.Path(file_input).stem)
                        + '"\n\n Please run job with program in debug mode',
                    )
                    progress_window.destroy()  # Close window and kill job.pid/children
                    subprocess.Popen(
                        f"TASKKILL /F /PID {job.pid} /T",
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )

            elif (
                progress_error != "no" or int(percent) <= 98
            ):  # If there is an error OR percent is less than 98%
                encode_window_progress.insert(
                    END,
                    "\nThere was an error, run the job in debug mode to troubleshoot\n",
                )
                complete_or_not = "complete"

            encode_window_progress.insert(END, str("\n" + "-" * 62 + "\n"))
            encode_window_progress.see(END)  # Scroll to bottom of text window
            encode_window_progress.configure(
                state=DISABLED
            )  # Disable progress window editing
        except TclError:
            return

        # Log Files ---------------------------------------------------------------------------------------------------
        try:
            log_folder = pathlib.Path("Runtime/logs/manual_auto/").resolve()
            pathlib.Path(log_folder).mkdir(parents=False, exist_ok=True)
            if len(str(pathlib.Path(file_input).name).strip()) > 50:
                file_name = str(pathlib.Path(file_input).name)[:50].strip()
            else:
                file_name = str(pathlib.Path(file_input).name).strip()
            log_txt = pathlib.Path(
                f"{str(log_folder)}/{datetime.now().strftime('%m-%d-%y - %I.%M.%S')}-[{file_name}]-log.txt"
            )
            logfile = open(log_txt, "w", encoding="utf-8")
            logfile.write(encode_window_progress.get(1.0, END))
            logfile.flush()
            logfile.close()
        except TclError:
            return
        # --------------------------------------------------------------------------------------------------- Log Files

        if (
            config["auto_close_progress_window"]["option"] == "on"
            and progress_error == "no"
        ):
            close_window()  # If program is set to auto close encoding window when complete, close

        advanced_root_deiconify()  # Re-Open Root
        open_all_toplevels()  # Re-Open all toplevels if there was any open

    elif (
        progress_output_view.get() == "Debug"
    ):  # Debug mode, only opens a cmd.exe terminal for raw output
        subprocess.Popen("cmd /k " + finalcommand + '"')


# Buttons Main Gui ----------------------------------------------------------------------------------------------------
# Encoder Menu Enter/Leave Binds ----------------------------------------------------------------
encoder_menu.bind("<Enter>", encoder_menu_hover)
encoder_menu.bind("<Leave>", encoder_menu_hover_leave)


def encoder_menu_on_enter(e):
    status_label.configure(text="Select Audio Codec...")


def encoder_menu_on_leave(e):
    status_label.configure(text="")


encoder_menu.bind("<Enter>", encoder_menu_on_enter)
encoder_menu.bind("<Leave>", encoder_menu_on_leave)
# ---------------------------------------------------------------- # Encoder Menu Enter/Leave Binds

# codec settings Button --------------------------------------------------------------------------
audiosettings_button = HoverButton(
    audio_setting_frame,
    text="Codec Settings",
    command=openaudiowindow,
    foreground="white",
    background="#23272A",
    state=DISABLED,
    borderwidth="3",
    activebackground="grey",
)
audiosettings_button.grid(
    row=0, column=2, columnspan=1, padx=5, pady=(5, 4), sticky=N + S + E + W
)


# --------------------------------------------------------------------------- # codec settings Button


# File input check ----------------------------------------------------------------------------------------------------
def file_input_check(file_input):
    global track_count, file_input_quoted, autosavefilename
    check_dependencies()  # check for app dependencies
    exit_cmd_window()  # Close cmd window upon opening a new file
    file_input_quoted = f'"{file_input}"'  # Quote VideInput for use in the code
    media_info = MediaInfo.parse(
        pathlib.Path(file_input)
    )  # Parse with media_info module
    total_audio_streams_in_input = media_info.general_tracks[
        0
    ].count_of_audio_streams  # Check input for audio
    if (
        total_audio_streams_in_input is not None
    ):  # If audio is not None (1 or more audio tracks)
        track_count = total_audio_streams_in_input  # Get track count from input
        input_entry.configure(state=NORMAL)  # Enable input entry box
        input_entry.delete(0, END)  # Remove text from input entry box if there is any
        input_entry.insert(
            0, str(pathlib.Path(str(file_input)))
        )  # Insert file_input into the input entrybox
        input_entry.configure(state=DISABLED)  # Disable input entry
        output_entry.configure(state=NORMAL)  # Enable output entry
        output_entry.delete(
            0, END
        )  # Delete anything in output entry if there is anything
        output_entry.configure(state=DISABLED)  # Disable output entry
        encoder.set("Set Codec")  # Reset encoder selection menu to default
        audiosettings_button.configure(state=DISABLED)  # Disable button
        start_audio_button.configure(state=DISABLED)  # Disable button
        encoder_menu.configure(state=NORMAL)
        output_button.config(state=DISABLED)  # Disable button
        command_line_button.config(state=DISABLED)  # Disable button
        start_audio_button.config(state=DISABLED)
        add_job_button.config(state=DISABLED)
        if (
            config_profile["Auto Encode"]["codec"] == ""
        ):  # If auto-encode profile has no information keep disabled
            auto_encode_last_options.configure(state=DISABLED)
        elif (
            config_profile["Auto Encode"]["codec"] != ""
        ):  # If it has information, define auto_file_out save location
            auto_encode_last_options.configure(state=NORMAL)  # for what ever codec
            if config_profile["Auto Encode"]["codec"] == "AAC":
                auto_file_out = (
                    str(pathlib.Path(file_input).with_suffix("")) + "._new_.mp4"
                )
            elif (
                config_profile["Auto Encode"]["codec"] == "AC3"
                or config_profile["Auto Encode"]["codec"] == "E-AC3"
            ):
                auto_file_out = (
                    str(pathlib.Path(file_input).with_suffix("")) + "._new_.ac3"
                )
            elif config_profile["Auto Encode"]["codec"] == "DTS":
                auto_file_out = (
                    str(pathlib.Path(file_input).with_suffix("")) + "._new_.dts"
                )
            elif config_profile["Auto Encode"]["codec"] == "Opus":
                auto_file_out = (
                    str(pathlib.Path(file_input).with_suffix("")) + "._new_.opus"
                )
            elif config_profile["Auto Encode"]["codec"] == "MP3":
                auto_file_out = (
                    str(pathlib.Path(file_input).with_suffix("")) + "._new_.mp3"
                )
            elif (
                config_profile["Auto Encode"]["codec"] == "FDK-AAC"
                or config_profile["Auto Encode"]["codec"] == "QAAC"
                or config_profile["Auto Encode"]["codec"] == "ALAC"
            ):
                auto_file_out = (
                    str(pathlib.Path(file_input).with_suffix("")) + "._new_.m4a"
                )
            elif config_profile["Auto Encode"]["codec"] == "FLAC":
                auto_file_out = (
                    str(pathlib.Path(file_input).with_suffix("")) + "._new_.flac"
                )
            autosavefilename = pathlib.Path(
                auto_file_out
            ).name  # Set autosavefilename var
    elif total_audio_streams_in_input is None:  # If input has 0 audio tracks
        input_entry.config(state=DISABLED)  # Disable input entry-box
        messagebox.showinfo(
            title="No Audio Streams",
            message=f"{file_input_quoted}:\n\nDoes not " f"contain any audio streams!",
        )  # Display error msg


# ---------------------------------------------------------------------------------------------------- File input check


# Drag and drop code for file input -----------------------------------------------------------------------------------
def drop_input(event):
    global file_input
    input_list = []  # Creates an empty list
    for filenames in root.splitlist(event.data):
        input_list.append(filenames)  # Appends all data to the list
    file_input = str(
        input_list[0]
    )  # For main gui, it takes in the item at index 0 as input (only 1 item)

    # if file input is a directory exit this function
    if pathlib.Path(file_input).is_dir():
        return

    input_entry.configure(state=NORMAL)
    input_entry.delete(0, END)
    file_input_check(file_input)  # Run file_input_check() with file_input


# ----------------------------------------------------------------------------------- Drag and drop code for file input


# Select "Open File" code ---------------------------------------------------------------------------------------------
def input_button_commands():
    global file_input, track_count
    encoder.set("Set Codec")
    audiosettings_button.configure(state=DISABLED)
    output_entry.configure(state=NORMAL)
    output_entry.delete(0, END)
    output_entry.configure(state=DISABLED)
    input_entry.configure(state=NORMAL)
    input_entry.delete(0, END)
    input_entry.configure(state=DISABLED)
    encoder_menu.configure(state=DISABLED)
    command_line_button.configure(state=DISABLED)
    output_button.config(state=DISABLED)
    command_line_button.config(state=DISABLED)
    start_audio_button.config(state=DISABLED)
    add_job_button.config(state=DISABLED)

    file_input = filedialog.askopenfilename(
        initialdir="/", title="Select A File", filetypes=[("All Files", "*.*")]
    )

    if file_input:  # If user selects a file to open
        file_input_check(file_input)

    elif not file_input:  # If user presses cancel
        input_entry.configure(state=NORMAL)
        input_entry.delete(0, END)
        input_entry.configure(state=DISABLED)
        output_button.config(state=DISABLED)
        encoder_menu.config(state=DISABLED)
        audiosettings_button.configure(state=DISABLED)
        auto_encode_last_options.configure(state=DISABLED)


# --------------------------------------------------------------------------------------------- Select "Open File" code


# Batch Processing ----------------------------------------------------------------------------------------------------
def batch_processing_input():
    global batch_listbox, encoder, batch_input_window, batch_encoder_menu

    try:  # If the window is already open do nothing when the button is hit
        if batch_input_window.winfo_exists():
            return
    except NameError:
        pass

    # Config Parser
    config_file = "Runtime/config.ini"
    batch_func_parser = ConfigParser()
    batch_func_parser.read(config_file)

    def batch_window_exit_function():  # function that is called when the user closes the window
        def save_batch_position():  # save batch window position
            func_parser = ConfigParser()
            func_parser.read(config_file)
            if func_parser["save_window_locations"]["batch window"] == "yes":
                if (
                    func_parser["save_window_locations"]["batch window position"]
                    != batch_input_window.geometry()
                ):
                    func_parser.set(
                        "save_window_locations",
                        "batch window position",
                        batch_input_window.geometry(),
                    )
                    with open(config_file, "w") as configfile:
                        func_parser.write(configfile)
            batch_input_window.destroy()  # close batch window
            advanced_root_deiconify()  # restore root

        if batch_listbox.size() >= 1:
            msg = messagebox.askyesno(
                message="Are you sure you want to close the window?\nThis will clear all "
                "inputs.",
                title="Prompt",
                parent=batch_input_window,
            )
            if msg:
                save_batch_position()
        else:
            save_batch_position()

    batch_input_window = Toplevel()
    batch_input_window.configure(background="#434547")  # Set's the background color
    batch_input_window.title("Batch File Input")  # Toplevel Title
    if (
        batch_func_parser["save_window_locations"]["batch window position"] == ""
        or batch_func_parser["save_window_locations"]["batch window"] == "no"
    ):
        window_height = 400
        window_width = 1000
        screen_width = batch_input_window.winfo_screenwidth()
        screen_height = batch_input_window.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        batch_input_window.geometry(
            f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}"
        )
    elif (
        batch_func_parser["save_window_locations"]["batch window position"] != ""
        and batch_func_parser["save_window_locations"]["batch window"] == "yes"
    ):
        batch_input_window.geometry(
            batch_func_parser["save_window_locations"]["batch window position"]
        )
    batch_input_window.protocol("WM_DELETE_WINDOW", batch_window_exit_function)

    # Row/Grid configures
    batch_input_window.grid_columnconfigure(0, weight=20)
    batch_input_window.grid_columnconfigure(1, weight=1)
    batch_input_window.grid_rowconfigure(0, weight=1)
    # Row/Grid configures

    listbox_frame = Frame(batch_input_window)  # Set dynamic listbox frame
    listbox_frame.grid(column=0, row=0, padx=5, pady=5, sticky=N + S + E + W)
    listbox_frame.grid_rowconfigure(0, weight=200)
    listbox_frame.grid_rowconfigure(1, weight=0)
    listbox_frame.grid_columnconfigure(0, weight=200)
    listbox_frame.grid_columnconfigure(1, weight=0)

    right_scrollbar = Scrollbar(listbox_frame, orient=VERTICAL)  # Scrollbars
    bottom_scrollbar = Scrollbar(listbox_frame, orient=HORIZONTAL)

    # Create listbox
    batch_listbox = Listbox(
        listbox_frame,
        xscrollcommand=bottom_scrollbar.set,
        activestyle="none",
        yscrollcommand=right_scrollbar.set,
        bd=2,
        bg="black",
        fg="#3498db",
        selectbackground="#272727",
        selectforeground="light green",
        selectmode=EXTENDED,
        font=(set_font, set_font_size + 2),
    )
    batch_listbox.grid(row=0, column=0, sticky=N + E + S + W)

    # add scrollbars to the listbox
    right_scrollbar.config(command=batch_listbox.yview)
    right_scrollbar.grid(row=0, column=1, sticky=N + W + S)
    bottom_scrollbar.config(command=batch_listbox.xview)
    bottom_scrollbar.grid(row=1, column=0, sticky=W + E + N)

    # button frame
    button_frame = LabelFrame(batch_input_window, bd=3, bg="#434547", fg="#3498db")
    button_frame.grid(column=1, row=0, rowspan=2, pady=2, padx=2, sticky=N + S + E + W)
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_rowconfigure(0, weight=1)
    button_frame.grid_rowconfigure(1, weight=1)
    button_frame.grid_rowconfigure(2, weight=1)
    button_frame.grid_rowconfigure(3, weight=10000)
    button_frame.grid_rowconfigure(4, weight=300)
    button_frame.grid_rowconfigure(5, weight=1)
    button_frame.grid_rowconfigure(6, weight=1)

    # batch output selection code
    batch_frame = LabelFrame(
        batch_input_window, text=" Batch Processing Path ", labelanchor="nw"
    )
    batch_frame.grid(column=0, row=1, columnspan=1, padx=2, pady=2, sticky=E + W)
    batch_frame.configure(
        fg="#3498db", bg="#434547", bd=3, font=(set_font, 9, "italic")
    )
    batch_frame.grid_rowconfigure(0, weight=1)
    batch_frame.grid_columnconfigure(0, weight=2)
    batch_frame.grid_columnconfigure(1, weight=20)
    batch_frame.grid_columnconfigure(3, weight=1)

    # extension var
    extension_var = StringVar()
    non_filtered_list = []

    def set_batch_path():  # set batch files output path, default uses file input as output
        path = filedialog.askdirectory(
            title="Output Path Manual/Auto", parent=batch_input_window
        )
        if path:
            func_parser = ConfigParser()
            func_parser.read(config_file)
            path = str(pathlib.Path(path))
            func_parser.set("batch_path", "path", path)
            with open(config_file, "w") as configfile:
                func_parser.write(configfile)
            batch_entry_box.config(state=NORMAL)
            batch_entry_box.delete(0, END)
            batch_entry_box.insert(
                0, str(pathlib.Path(str(func_parser["batch_path"]["path"])))
            )
            batch_entry_box.config(state=DISABLED)

    set_batch_path_button = HoverButton(
        batch_frame,
        text="Set Path",
        command=set_batch_path,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    set_batch_path_button.grid(
        row=0, column=0, columnspan=1, padx=5, pady=5, sticky=N + S + E + W
    )

    saved_batch_path = None  # define an empty variable
    if batch_func_parser["batch_path"]["path"] == "file input directory":
        saved_batch_path = str(batch_func_parser["batch_path"]["path"]).title()
    elif batch_func_parser["batch_path"]["path"] != "file input directory":
        saved_batch_path = str(
            pathlib.Path(batch_func_parser["batch_path"]["path"]).resolve()
        )
    batch_entry_box = Entry(batch_frame, borderwidth=4, background="#CACACA")
    batch_entry_box.grid(
        row=0, column=1, columnspan=2, padx=5, pady=5, sticky=N + S + E + W
    )
    batch_entry_box.insert(0, saved_batch_path)
    batch_entry_box.config(state=DISABLED)

    def reset_batch_path():  # reset batch path to default
        msg = messagebox.askyesno(
            title="Prompt",
            message="Reset path to directory of input file?",
            parent=batch_input_window,
        )
        if msg:
            func_parser = ConfigParser()
            func_parser.read(config_file)
            func_parser.set("batch_path", "path", "file input directory")
            with open(config_file, "w") as configfile:
                func_parser.write(configfile)
            batch_entry_box.config(state=NORMAL)
            batch_entry_box.delete(0, END)
            batch_entry_box.insert(0, str(func_parser["batch_path"]["path"]).title())
            batch_entry_box.config(state=DISABLED)

    reset_batch_path_button = HoverButton(
        batch_frame,
        text="X",
        command=reset_batch_path,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    reset_batch_path_button.grid(
        row=0, column=3, columnspan=1, padx=5, pady=5, sticky=N + S + E + W
    )

    # function to update track counter, for track list
    def create_track_count():
        global acodec_stream_track_counter
        # create empty list
        max_common_audio_track = []
        audio_track_info = {}

        # common var
        all_common = True

        # get total of files in the list box
        total_tracks_to_parse = batch_listbox.size()

        # loop through listbox to check all audio streams
        for count, batch_file in enumerate(batch_listbox.get(0, END), start=1):
            try:
                batch_input_window.title(
                    f"Generating track information - {str(count)} of {str(total_tracks_to_parse)}"
                )
            except TclError:
                return  # exit the function
            media_info = MediaInfo.parse(pathlib.Path(batch_file))
            audio_track_count = media_info.general_tracks[0].count_of_audio_streams
            max_common_audio_track.append(audio_track_count)

            # let's try to update languages
            # let's parse all tracks for each file
            for num, x in enumerate(range(int(audio_track_count))):
                # get data
                same_language_string = media_info.audio_tracks[num].language
                same_format_string = media_info.audio_tracks[num].format
                same_channel_string = media_info.audio_tracks[num].channel_s
                compiled_audio_track_info = [
                    same_language_string,
                    same_format_string,
                    same_channel_string,
                ]

                # check for all common files
                if not audio_track_info:
                    audio_track_info.update({str(num): compiled_audio_track_info})
                else:
                    try:
                        if audio_track_info[str(num)] != compiled_audio_track_info:
                            all_common = False
                        audio_track_info.update({str(num): compiled_audio_track_info})
                    except KeyError:
                        audio_track_info.update({str(num): compiled_audio_track_info})

        max_common_audio_track.sort()  # sort from least to greatest
        max_total_tracks = Counter(
            max_common_audio_track
        )  # use counter module to check most used lowest track

        # update track counter for codec settings window based off of max_total_tracks
        acodec_stream_track_counter = {}
        for i in range(int(max_total_tracks.most_common(1)[0][0])):
            if all_common:
                additional_audio_info_string = (
                    f"   ({str(audio_track_info[str(i)][0])}, "
                    f"{str(audio_track_info[str(i)][1])}, "
                    f"chnl {str(audio_track_info[str(i)][2])})"
                )
            elif not all_common:
                additional_audio_info_string = ""

            acodec_stream_track_counter[
                f"Track #{i + 1}{additional_audio_info_string}"
            ] = f" -map 0:a:{i} "

    def enable_disable_batch_win_btns(mode):
        """function to enable/disable buttons while batch window is loading the files"""
        if mode == "disable":
            select_files.config(state=DISABLED)
            delete_job_button.config(state=DISABLED)
            delete_all_button.config(state=DISABLED)
            set_batch_path_button.config(state=DISABLED)
            reset_batch_path_button.config(state=DISABLED)
            batch_listbox.config(state=DISABLED)
            encoder.set("Set Codec")
            batch_encoder_menu.config(state=DISABLED)
        elif mode == "enable":
            select_files.config(state=NORMAL)
            delete_job_button.config(state=NORMAL)
            delete_all_button.config(state=NORMAL)
            set_batch_path_button.config(state=NORMAL)
            reset_batch_path_button.config(state=NORMAL)
            batch_encoder_menu.config(state=NORMAL)  # enable the encoder menu

    def process_batch_file_input_information(*args):
        nonlocal non_filtered_list
        # if input is a directory convert args into a list with a recursive search
        list_of_batch_files = []

        # update empty lists
        for input_args in args:
            if pathlib.Path(input_args).is_dir():
                for x in pathlib.Path(input_args).rglob("*.*"):
                    if x.is_file():
                        list_of_batch_files.append(x)
            elif pathlib.Path(input_args).is_file():
                list_of_batch_files.append(input_args)

        # sort list
        list_of_batch_files.sort()

        check_dependencies()  # check for dependencies
        files_without_audio = []  # define an empty list for files without audio
        files_with_audio = []  # define an empty list for files with audio
        batch_listbox.delete(0, END)  # clear list box
        # insert simple string
        batch_listbox.insert(END, "Please wait, checking all files for audio...")
        total_number_of_input = len(list_of_batch_files)
        enable_disable_batch_win_btns("disable")  # disable all batch listbox buttons
        batch_input_window.grab_set()  # force attention to batch list box window
        for count, f in enumerate(
            list(list_of_batch_files), start=1
        ):  # loop through file selection tuple by converting it to list
            batch_input_window.title(
                f"Checking file {str(count)} of {str(total_number_of_input)}"
            )
            media_info = MediaInfo.parse(pathlib.Path(f))  # use media info on each file
            general_info = media_info.general_tracks[0]  #
            if (
                general_info.count_of_audio_streams is not None
            ):  # if file has audio streams
                try:
                    if f not in list(
                        batch_listbox.get(0, END)
                    ):  # if file not already in list
                        files_with_audio.append(f)  # add file to list with audio
                except TclError:  # if user closes the window while it's loading files
                    return  # exit this function
            elif (
                general_info.count_of_audio_streams is None
            ):  # if file does not have any audio streams
                files_without_audio.append(f)  # add files to list without audio
        # add files with audio to list box
        batch_listbox.config(state=NORMAL)  # re-enable list box
        batch_listbox.delete(0, END)  # clear list box
        files_with_audio.sort()  # sort the list alphabetically

        # copy list for ext filtering
        non_filtered_list = files_with_audio.copy()

        # get all the loaded extensions
        loaded_ext = []
        for (
            file_w_aud
        ) in files_with_audio:  # loop through the list and add it to the list box
            batch_listbox.insert(END, file_w_aud)  # insert file into the batch_listbox
            if pathlib.Path(file_w_aud).suffix not in loaded_ext:
                loaded_ext.append(pathlib.Path(file_w_aud).suffix)

        # disable list box until audio parsing is complete
        batch_listbox.config(state=DISABLED)

        # create new menu
        # rebuild_ext_menu(loaded_ext)
        update_ext_menu(loaded_ext)

        if len(files_without_audio) >= 1:  # if files without audio is 1 or more
            no_audio = str(
                len(files_without_audio)
            )  # count amount of files without audio
            if int(no_audio) == 1:  # set string to file or files depending on amount
                files_string = "file"
            elif int(no_audio) >= 2:
                files_string = "files"
            # show message showing how many files wasn't added without audio
            messagebox.showinfo(
                parent=batch_input_window,
                title=f"No Audio Tracks [{no_audio}]",
                message=f"{no_audio} {files_string} not added to batch list\n\nReason:\n{no_audio} "
                f"{files_string} did not contain any audio tracks",
            )
        if len(files_with_audio) >= 1:  # if files with audio is 1 or more
            encoder.set("Set Codec")  # set menu to 'Set Codec'
            audio_settings.config(state=DISABLED)  # disable codec settings button
            apply_and_send.config(state=DISABLED)  # disable the apply_and_send button
            create_track_count()  # run create track count function
            try:
                batch_listbox.config(state=NORMAL)  # re-enable list box
            except TclError:
                return  # exit the function
            enable_disable_batch_win_btns("enable")
            batch_input_window.grab_release()  # release attention to batch list box window
            batch_input_window.title("Batch File input")

    # function for add files button
    def select_files_batch():
        file_selection = filedialog.askopenfilenames(
            parent=batch_input_window,
            title="Select File(s)",
            initialdir="/",
            filetypes=[("Media Files", "*.*")],
        )
        if file_selection:  # if user opens file(s)
            threading.Thread(
                target=process_batch_file_input_information,
                args=list(file_selection),
                daemon=True,
            ).start()

    select_files = HoverButton(
        button_frame,
        text="Add Files",
        command=select_files_batch,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    select_files.grid(row=0, column=0, columnspan=1, padx=5, pady=5, sticky=N + E + W)

    # drag and drop code for batch file window
    def batch_drop_input(event):
        input_list_batch = []  # creates an empty list
        for filenames in root.splitlist(event.data):
            input_list_batch.append(filenames)  # appends all drop data to the list

        # process_batch_file_input_information(input_list_batch)  # call function with input_list_batch
        threading.Thread(
            target=process_batch_file_input_information,
            args=input_list_batch,
            daemon=True,
        ).start()

    batch_input_window.drop_target_register(DND_FILES)
    batch_input_window.dnd_bind("<<Drop>>", batch_drop_input)

    def delete():  # define delete for selected items
        if batch_listbox.curselection():
            msg = messagebox.askyesno(
                parent=batch_input_window,
                title="Prompt!",
                message="Delete selected item(s)?",
            )
            if msg:
                for selected_items in reversed(batch_listbox.curselection()):
                    batch_listbox.delete(selected_items)
                if batch_listbox.size() == 0:
                    return
                create_track_count()  # run track count code to update track selection based off of list box

    delete_job_button = HoverButton(
        button_frame,
        text="Delete Selected\nItem(s)",
        command=delete,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    delete_job_button.grid(
        row=1, column=0, columnspan=1, padx=5, pady=5, sticky=N + E + W
    )

    def delete_all():  # Define delete for all items code
        if batch_listbox.size() > 0:
            msg = messagebox.askyesno(
                parent=batch_input_window, title="Prompt!", message="Delete all items?"
            )
            if msg:
                batch_listbox.delete(0, END)

    delete_all_button = HoverButton(
        button_frame,
        text="Delete All",
        command=delete_all,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    delete_all_button.grid(
        row=2, column=0, columnspan=1, padx=5, pady=(5, 5), sticky=N + E + W
    )

    def update_ext_menu(ext_list):
        update_menu = extension_filter_menu.children["menu"]
        update_menu.delete(0, END)
        update_menu.add_command(
            label="Filter: All",
            command=lambda v="Filter: All": [extension_var.set(v), ext_changed(v)],
        )
        extension_filter_menu.config(state=NORMAL)
        for value in ext_list:
            update_menu.add_command(
                label=value,
                command=lambda v=value: [extension_var.set(v), ext_changed(v)],
            )

    def ext_changed(_):
        batch_listbox.delete(0, END)
        for x in non_filtered_list:
            if extension_var.get() == "Filter: All":
                batch_listbox.insert(END, x)
            else:
                if (
                    str(pathlib.Path(x).suffix).lower()
                    == str(extension_var.get()).lower()
                ):
                    batch_listbox.insert(END, x)

    extension_var.set("Filter: All")
    extension_filter_menu = OptionMenu(
        button_frame,
        extension_var,
        extension_var.get(),
    )
    extension_filter_menu.grid(
        row=3, column=0, columnspan=1, padx=5, pady=5, sticky=S + W + E
    )
    extension_filter_menu.config(
        state=DISABLED,
        background="#23272A",
        foreground="white",
        highlightthickness=1,
        width=7,
    )
    extension_filter_menu["menu"].configure(activebackground="dim grey")

    def batch_encoder_changed(*args):  # batch encoder menu function
        global batch_mode  # set global variable batch_mode
        audio_settings.config(state=NORMAL)  # audio_settings enable button
        apply_and_send.config(state=DISABLED)  # disable add to job manager button
        batch_mode = "yes"  # set variable batch_mode to 'yes'

    encoder.set("Set Codec")  # set encoder string var to 'Set Codec'
    batch_encoder_menu = OptionMenu(
        button_frame,
        encoder,
        *encoder_dropdownmenu_choices.keys(),
        command=batch_encoder_changed,
    )
    batch_encoder_menu.grid(
        row=4, column=0, columnspan=1, padx=5, pady=5, sticky=S + W + E
    )
    batch_encoder_menu.config(
        state=DISABLED,
        background="#23272A",
        foreground="white",
        highlightthickness=1,
        width=7,
    )
    batch_encoder_menu["menu"].configure(activebackground="dim grey")

    def set_audio_settings():  # audio_settings button function
        openaudiowindow()  # open codec settings window
        audio_window.wait_window()  # wait for codec settings window to close
        apply_and_send.config(state=NORMAL)  # enable apply_and_send button

    audio_settings = HoverButton(
        button_frame,
        text="Codec Settings",
        command=set_audio_settings,
        state=DISABLED,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    audio_settings.grid(
        row=5, column=0, columnspan=1, padx=5, pady=(5, 5), sticky=N + W + E + S
    )

    def thread_adding_to_manager():
        """multi-thread files being loaded to the job manager window"""
        func_parser = ConfigParser()  # define local ConfigParser()
        func_parser.read(config_file)  # open config_file

        # get total number of files
        total_number_of_files = batch_listbox.size()

        # loop through listbox for all files
        for count, batch_file in enumerate(batch_listbox.get(0, END), start=1):
            jobs_window.title(f"Parsing - {str(count)} of {str(total_number_of_files)}")
            autofilesave_file_path = pathlib.Path(
                batch_file
            )  # command to get file input location

            # check for saved directory
            saved_dir = func_parser["batch_path"]["path"]
            if saved_dir != "file input directory" and pathlib.Path(saved_dir).is_dir():
                autofilesave_dir_path = saved_dir
            elif saved_dir == "file input directory":
                autofilesave_dir_path = autofilesave_file_path.parents[
                    0
                ]  # final command to get only the directory

            convert_filename = (
                f"{str(autofilesave_dir_path)}/{str(pathlib.Path(batch_file).name)}"
            )
            if encoder.get() == "AAC":
                batch_file_out = pathlib.Path(convert_filename).with_suffix(
                    "._new_.mp4"
                )
            elif encoder.get() == "AC3" or encoder.get() == "E-AC3":
                batch_file_out = pathlib.Path(convert_filename).with_suffix(
                    "._new_.ac3"
                )
            elif encoder.get() == "DTS":
                batch_file_out = pathlib.Path(convert_filename).with_suffix(
                    "._new_.dts"
                )
            elif encoder.get() == "Opus":
                batch_file_out = pathlib.Path(convert_filename).with_suffix(
                    "._new_.opus"
                )
            elif encoder.get() == "MP3":
                batch_file_out = pathlib.Path(convert_filename).with_suffix(
                    "._new_.mp3"
                )
            elif (
                encoder.get() == "FDK-AAC"
                or encoder.get() == "QAAC"
                or encoder.get() == "ALAC"
            ):
                batch_file_out = pathlib.Path(convert_filename).with_suffix(
                    "._new_.m4a"
                )
            elif encoder.get() == "FLAC":
                batch_file_out = pathlib.Path(convert_filename).with_suffix(
                    "._new_.flac"
                )

            file_output = str(batch_file_out)  # define file output

            language_string = None  # place holder variable
            delay_string = None  # place holder variable
            channel_string = None  # place holder variable

            media_info = MediaInfo.parse(batch_file)  # Parse file_input
            general_track = media_info.general_tracks[0]
            # track_selection_mediainfo uses the -map 0:a:x code to get the track input
            track_selection_mediainfo = media_info.audio_tracks[
                int(acodec_stream_choices[acodec_stream.get()].strip()[-1])
            ]
            total_streams = 0  # Empty variable to add up all the tracks
            if general_track.count_of_video_streams is not None:
                total_streams += int(
                    general_track.count_of_video_streams
                )  # check for video track(s)
            if general_track.count_of_audio_streams is not None:
                total_streams += int(
                    general_track.count_of_audio_streams
                )  # check for audio track(s)
            if general_track.count_of_subtitle_streams is not None:
                total_streams += int(
                    general_track.count_of_subtitle_streams
                )  # check for subtitle track(s)
            if general_track.count_of_menu_streams is not None:
                total_streams += int(
                    general_track.count_of_menu_streams
                )  # check for menu track(s)

            try:
                if "mp4" in str(pathlib.Path(batch_file).suffix):
                    if track_selection_mediainfo.source_delay:
                        delay_string = (
                            f"[delay {str(track_selection_mediainfo.source_delay)}ms]"
                        )
                    else:
                        delay_string = str("[delay 0ms]")
                else:
                    if track_selection_mediainfo.delay_relative_to_video is not None:
                        delay_string = f"[delay {str(track_selection_mediainfo.delay_relative_to_video)}ms]"
                    else:
                        delay_string = str("[delay 0ms]")
            except UnboundLocalError:
                pass

            try:
                if track_selection_mediainfo.channel_s:
                    channel_string = (
                        f"[chnl {str(track_selection_mediainfo.channel_s)}]"
                    )
            except UnboundLocalError:
                pass

            try:  # set language string for file output name
                # Obtain language string from file_input's parsed track
                if (
                    track_selection_mediainfo.other_language is not None
                ):  # If language is not None
                    l_lengths = [
                        len(i) for i in track_selection_mediainfo.other_language
                    ]  # List of language codes
                    if (
                        3 in l_lengths
                    ):  # Find strings in l_lengths that only are equal to 3 characters
                        l_index = l_lengths.index(
                            3
                        )  # Save the index of the 3 character string to variable
                    language_string = (
                        f"[{str(track_selection_mediainfo.other_language[l_index])}]"
                    )
                else:
                    language_string = "[und]"
            except UnboundLocalError:
                pass

            audio_track_number_string = f"[Audio#{acodec_stream.get().split()[1][-1]}]"
            if total_streams == 1:  # If total_streams equals 1
                file_output = str(file_output).replace(
                    "_new_", audio_track_number_string + channel_string
                )  # Replace _new_ with Audio #
            elif total_streams >= 2:  # If total_streams is 2 or greater
                file_output = str(file_output).replace(
                    "_new_",
                    audio_track_number_string
                    + language_string
                    + delay_string
                    + channel_string,
                )  # Replace '_new_'

            # add total duration as argument to pass
            if (
                track_selection_mediainfo.duration is not None
            ):  # if track input HAS a duration
                track_duration = float(track_selection_mediainfo.duration)
            elif (
                track_selection_mediainfo.duration is None
            ):  # if track input DOES NOT have a duration
                track_duration = "None"

            # if encoder is fdk-aac or qaac set banner and verbose string
            if encoder.get() == "FDK-AAC" or encoder.get() == "QAAC":
                hide_banner_and_verbose = ""
            elif encoder.get() != "FDK-AAC" or encoder.get() != "QAAC":
                hide_banner_and_verbose = " -v error -hide_banner -stats"

            # batch final command to add to job manager dictionary
            batch_final_command = " ".join(
                str(
                    f'"{ffmpeg} -y -analyzeduration 100M -probesize 50M -i '
                    f'"{autofilesave_file_path}" '
                    f"{acodec_stream_choices[acodec_stream.get()]} {batch_command} "
                    f'"{file_output}"{hide_banner_and_verbose}'
                ).split()
            )

            # create dictionary based off of all the above information to send to job manager window
            temp_dictionary = {
                f'Codec: {encoder.get()}  >>>>  "{pathlib.Path(autofilesave_file_path).name}"': batch_final_command,
                "Duration = ": str(track_duration),
                "Output Filename = ": f"[{file_output}]",
            }
            jobs_window.deiconify()  # bring jobs window to the front of other windows
            job_listbox.insert(
                END,
                str(
                    f"{list(temp_dictionary.keys())[0]}  >>>>  "
                    f"Command: {list(temp_dictionary.values())[0]}  >>>>  "
                    f"{list(temp_dictionary.keys())[1]}{list(temp_dictionary.values())[1]}  >>>>  "
                    f"{list(temp_dictionary.keys())[2]}{list(temp_dictionary.values())[2]}"
                ),
            )

            with open("Runtime/jobs.dat", "wb") as pickle_file:
                pickle.dump(
                    job_listbox.get(0, END), pickle_file, pickle.HIGHEST_PROTOCOL
                )
        jobs_window.title("Job Manager")
        batch_input_window.grab_release()
        open_all_toplevels()

    def add_to_job_manager():
        """function to add all files in listbox to job manager with the commands"""
        open_jobs_manager()  # open jobs manager window
        batch_input_window.grab_set()  # force attention of program to hidden batch input window that will be hidden
        batch_input_window.wm_withdraw()  # hide this window
        threading.Thread(
            target=thread_adding_to_manager, daemon=True
        ).start()  # start job manager code in a thread

    apply_and_send = HoverButton(
        button_frame,
        text="Add Jobs to\nJob Manager",
        command=add_to_job_manager,
        state=DISABLED,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    apply_and_send.grid(
        row=6, column=0, columnspan=1, padx=5, pady=(5, 5), sticky=N + W + E + S
    )


# ---------------------------------------------------------------------------------------------------- Batch Processing


# Input Button/Entry Box ----------------------------------------------------------------------
def input_popup_menu(*args):  # Menu for input button
    input_menu = Menu(
        input_frame,
        tearoff=False,
        font=(set_font, set_font_size + 1),
        background="#23272A",
        foreground="white",
        activebackground="grey",
    )  # Menu
    input_menu.add_command(label="Open File", command=input_button_commands)
    input_menu.add_separator()
    input_menu.add_command(label="Batch Process", command=batch_processing_input)
    input_menu.tk_popup(input_button.winfo_rootx(), input_button.winfo_rooty() + 5)


input_button = HoverButton(
    input_frame,
    text="Input",
    command=input_popup_menu,
    foreground="white",
    background="#23272A",
    borderwidth="3",
    activebackground="grey",
)
input_button.grid(row=0, column=0, columnspan=1, padx=5, pady=5, sticky=N + S + E + W)
input_button.bind("<Button-3>", input_popup_menu)  # Right click to pop up menu in frame

input_entry = Entry(input_frame, borderwidth=4, background="#CACACA", state=DISABLED)
input_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=S + E + W)

root.drop_target_register(DND_FILES)
root.dnd_bind("<<Drop>>", drop_input)

# ------------------------------------------------------------------------- Input Button/Entry Box

# Output Button/Entry Box ------------------------------------------------------------------------
output_button = HoverButton(
    output_frame,
    text="Save File",
    command=file_save,
    state=DISABLED,
    foreground="white",
    background="#23272A",
    borderwidth="3",
    activebackground="grey",
)
output_button.grid(row=0, column=0, columnspan=1, padx=5, pady=5, sticky=N + S + E + W)
output_entry = Entry(output_frame, borderwidth=4, background="#CACACA", state=DISABLED)
output_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=S + E + W)
# ---------------------------------------------------------------------- # Output Button/Entry Box

# Print Final Command Line ---------------------------------------------------------------------
command_line_button = HoverButton(
    root,
    text="Display\nCommand",
    command=print_command_line,
    state=DISABLED,
    foreground="white",
    background="#23272A",
    borderwidth="3",
    activebackground="grey",
)
command_line_button.grid(
    row=1, column=0, columnspan=1, padx=10, pady=15, sticky=N + S + E + W
)


# ----------------------------------------------------------------------- Print Final Command Line


def open_jobs_manager():  # Opens the job manager window --------------------------------------------------------------
    global file_input, jobs_window, job_listbox, job_number, jobs_dat_file, jobs_window_progress_frame, jobs_window_button_frame, jobs_window_progress, job_jw

    top_level_width = (
        1068  # This top level, needs dynamic resizing, so adjust height/width here
    )
    top_level_height = 276

    try:  # If the job manager window is already open do nothing when the button is hit
        if jobs_window.winfo_exists():
            return
    except NameError:
        pass

    def jobs_window_exit_function():  # Job Manager exit function
        # If either frame that has to do with progress is viewable, prompt user
        if (
            jobs_window_progress_frame.winfo_viewable()
            and jobs_window_button_frame.winfo_viewable()
        ):
            msg = messagebox.askyesno(
                message="Are you sure you want to close the Jobs Manager window?\nNote: "
                "This will end current tasks",
                title="Prompt",
            )
            if (
                msg
            ):  # If user selects yes, recursively stop all processes that has to do with encode
                try:
                    job_id = psutil.Process(job_jw.pid)
                    for job_ids in job_id.children(recursive=True):
                        job_ids.kill()
                except psutil.NoSuchProcess:
                    pass

            close_jobs_progress_drawer()  # Close progress drawer
        # Set custom geometry variables for this window to save to config ini
        jobs_window_geometry = f"+{jobs_window.geometry().split('+')[1]}+{jobs_window.geometry().split('+')[2]}"
        func_parser = ConfigParser()
        func_parser.read(config_file)
        if func_parser["save_window_locations"]["job window"] == "yes":
            if (
                func_parser["save_window_locations"]["job window position"]
                != jobs_window_geometry
            ):
                func_parser.set(
                    "save_window_locations", "job window position", jobs_window_geometry
                )
                with open(config_file, "w") as configfile:
                    func_parser.write(configfile)
        open_all_toplevels()  # Re-open all hidden toplevels if they exist
        advanced_root_deiconify()  # Re-open main gui
        jobs_window.destroy()  # Destroy the jobs window

    hide_all_toplevels()  # Hide any/all top levels if they exist upon launching this

    jobs_window_parser = ConfigParser()  # Parser for jobs_window function
    jobs_window_parser.read(config_file)

    jobs_window = Toplevel()  # Toplevel loop
    jobs_window.configure(background="#434547")  # Set's the background color
    jobs_window.title("Job Manager")  # Toplevel Title
    jobs_window.resizable(False, False)  # Disables resizing window
    # Code to check window position and set geometry
    if (
        jobs_window_parser["save_window_locations"]["job window position"] == ""
        or jobs_window_parser["save_window_locations"]["job window"] == "no"
    ):
        x_coordinate = int(
            (jobs_window.winfo_screenwidth() / 2) - (top_level_width / 2)
        )
        y_coordinate = int(
            (jobs_window.winfo_screenheight() / 3) - (top_level_height / 2)
        )
        jobs_window.geometry(f"+{x_coordinate}+{y_coordinate}")
    if (
        jobs_window_parser["save_window_locations"]["job window position"] != ""
        and jobs_window_parser["save_window_locations"]["job window"] == "yes"
    ):
        jobs_window.geometry(
            jobs_window_parser["save_window_locations"]["job window position"]
        )
    jobs_window.protocol(
        "WM_DELETE_WINDOW", jobs_window_exit_function
    )  # Define exit function

    # Row/Grid configures
    jobs_window.grid_columnconfigure(0, weight=20)
    jobs_window.grid_columnconfigure(1, weight=1)
    jobs_window.grid_rowconfigure(0, weight=1)
    jobs_window.grid_rowconfigure(1, weight=1)
    # Row/Grid configures

    listbox_frame = Frame(jobs_window)  # Set dynamic listbox frame
    listbox_frame.grid(column=0, row=0, padx=5, pady=5, sticky=N + S + E + W)

    right_scrollbar = Scrollbar(listbox_frame, orient=VERTICAL)  # Scrollbars
    bottom_scrollbar = Scrollbar(listbox_frame, orient=HORIZONTAL)

    # Create listbox
    job_listbox = Listbox(
        listbox_frame,
        width=100,
        height=10,
        xscrollcommand=bottom_scrollbar.set,
        activestyle="none",
        yscrollcommand=right_scrollbar.set,
        bd=2,
        bg="black",
        fg="#3498db",
        selectbackground="#272727",
        selectforeground="light green",
        font=(set_font, set_font_size + 2),
    )
    job_listbox.grid(row=0, column=0)

    # Add scrollbars to the listbox
    right_scrollbar.config(command=job_listbox.yview)
    right_scrollbar.grid(row=0, column=1, sticky=N + E + S)
    bottom_scrollbar.config(command=job_listbox.xview)
    bottom_scrollbar.grid(row=1, column=0, sticky=W + E + S)

    # Create drawer frames/widgets
    button_frame = Frame(jobs_window)
    button_frame.grid(column=1, row=0, sticky=N + S + E + W)
    button_frame.config(bg="#434547")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_rowconfigure(0, weight=1)
    button_frame.grid_rowconfigure(1, weight=300)
    button_frame.grid_rowconfigure(2, weight=300)
    button_frame.grid_rowconfigure(3, weight=1)

    jobs_window_progress_frame = LabelFrame(
        jobs_window, text=" Encoding Progress ", labelanchor="nw"
    )
    jobs_window_progress_frame.grid(
        column=0, row=1, columnspan=1, padx=5, pady=(0, 3), sticky=N + S + E + W
    )
    jobs_window_progress_frame.configure(
        fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold")
    )
    jobs_window_progress_frame.grid_rowconfigure(0, weight=1)
    jobs_window_progress_frame.grid_columnconfigure(0, weight=1)

    jobs_window_button_frame = LabelFrame(
        jobs_window, text=" Options ", labelanchor="n"
    )
    jobs_window_button_frame.grid(
        column=1, row=1, columnspan=1, padx=5, pady=(0, 3), sticky=N + S + E + W
    )
    jobs_window_button_frame.configure(
        fg="#3498db", bg="#434547", bd=3, font=(set_font, 10, "bold")
    )
    jobs_window_button_frame.grid_rowconfigure(0, weight=1)
    jobs_window_button_frame.grid_columnconfigure(0, weight=1)

    jobs_window_progress = scrolledtextwidget.ScrolledText(
        jobs_window_progress_frame,
        width=90,
        height=0,
        tabs=10,
        spacing2=3,
        spacing1=2,
        spacing3=3,
    )
    jobs_window_progress.grid(
        row=0, column=0, columnspan=2, pady=(0, 6), padx=10, sticky=E + W
    )
    jobs_window_progress.config(bg="black", fg="#CFD2D1", bd=8)

    app_progress_bar = ttk.Progressbar(
        jobs_window_progress_frame,
        orient=HORIZONTAL,
        mode="determinate",
        style="custom.Horizontal.TProgressbar",
    )
    app_progress_bar.grid(
        column=0, row=1, columnspan=4, sticky=W + E, pady=(0, 2), padx=3
    )
    temp_label = Label(
        jobs_window_progress_frame,
        text="Input has no duration - progress bar is temporarily disabled",
        bd=4,
        relief=SUNKEN,
        anchor=E,
        background="#717171",
        foreground="white",
    )
    temp_label.grid(column=0, row=1, columnspan=4, pady=(0, 2), padx=3, sticky=E + W)

    jobs_window_progress_frame.grid_remove()  # Hide widgets after creation
    jobs_window_button_frame.grid_remove()
    app_progress_bar.grid_remove()
    temp_label.grid_remove()

    def delete():  # Define delete for single items code and button
        if job_listbox.curselection():
            msg = messagebox.askyesno(
                parent=jobs_window, title="Prompt!", message="Delete selected item?"
            )
            if msg:
                for selected_items in reversed(job_listbox.curselection()):
                    job_listbox.delete(selected_items)
                with open("Runtime/jobs.dat", "wb") as pickle_file:
                    pickle.dump(
                        job_listbox.get(0, END), pickle_file, pickle.HIGHEST_PROTOCOL
                    )

    delete_job_button = HoverButton(
        button_frame,
        text="Delete Selected",
        command=delete,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    delete_job_button.grid(
        row=0, column=0, columnspan=1, padx=5, pady=5, sticky=N + E + W
    )

    def delete_all():  # Define delete for all items code and button
        if job_listbox.size() > 0:
            msg = messagebox.askyesno(
                parent=jobs_window, title="Prompt!", message="Delete all items?"
            )
            if msg:
                job_listbox.delete(0, END)
                with open("Runtime/jobs.dat", "wb") as pickle_file:
                    pickle.dump(
                        job_listbox.get(0, END), pickle_file, pickle.HIGHEST_PROTOCOL
                    )

    delete_all_button = HoverButton(
        button_frame,
        text="Delete All",
        command=delete_all,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    delete_all_button.grid(
        row=1, column=0, columnspan=1, padx=5, pady=(5, 5), sticky=N + E + W
    )

    def open_jobs_progress_drawer():  # Code to "animate" progress drawer opening
        jobs_window_progress_frame.grid()
        jobs_window_button_frame.grid()
        start_selected_button.config(state=DISABLED)
        start_all_jobs_button.config(state=DISABLED)
        root.withdraw()
        for x_open in range(10):
            jobs_window_progress.config(height=x_open + 1)
            sleep(0.0167)  # Open drawer at 60fps

    def close_jobs_progress_drawer():  # Code to "animate" progress drawer closing
        for x_close in reversed(range(10)):
            jobs_window_progress.config(height=x_close - 1)
            sleep(0.0167)  # Close drawer at 60fps
        jobs_window_progress.config(state=NORMAL)
        jobs_window_progress.delete(1.0, END)
        jobs_window_progress.config(state=DISABLED)
        jobs_window_progress_frame.grid_remove()
        jobs_window_button_frame.grid_remove()
        start_selected_button.config(state=NORMAL)
        start_all_jobs_button.config(state=NORMAL)
        advanced_root_deiconify()  # call advanced root deiconify to avoid white root window upon reloading
        jobs_window.deiconify()

    def start_job_window_encode_single():  # Code for single file selection encoding
        global jobs_window_progress_frame, jobs_window_progress, jobs_window_button_frame

        try:
            selected_job = [
                job_listbox.selection_get()
            ]  # Get selected job index from listbox
            current_selection = job_listbox.curselection()
        except TclError:  # If user hits the button and there is nothing selected
            messagebox.showerror(
                title="Error",
                message="Please select a job before continuing",
                parent=jobs_window_progress,
            )
            return  # Exit function if no job is selected

        def start_single_file_encode():
            global job_jw
            job_duration = (
                str(selected_job[0])
                .split("Command:")[1]
                .split(">>>>  Duration =")[1]
                .split(">>>>")[0]
                .strip()
            )  # Used to extract duration from listbox string
            if job_duration != "None":  # If track input HAS a duration
                total_duration = float(job_duration)
                app_progress_bar.grid()
            elif job_duration == "None":
                total_duration = job_duration
                temp_label.grid()

            if (
                not jobs_window_progress_frame.winfo_viewable()
                and not jobs_window_button_frame.winfo_viewable()
            ):
                open_jobs_progress_drawer()  # If the drawer is already opened, do not attempt to re-open it

            def check_for_existing_output():  # Function to check if output exists, if it does change older file name
                check_output_file = pathlib.Path(
                    str(job_listbox.get(0)).split("Output Filename =")[1].strip()[1:-1]
                )
                if check_output_file.is_file():
                    replace_name = (
                        check_output_file.stem + "[old_file]" + check_output_file.suffix
                    )
                    try:
                        pathlib.Path(check_output_file).rename(
                            pathlib.Path(check_output_file.parent, replace_name)
                        )
                    except FileExistsError:
                        replace_name = (
                            check_output_file.stem
                            + f"[old_file({str(randint(0, 99))})]"
                            + check_output_file.suffix
                        )
                        pathlib.Path(check_output_file).rename(
                            pathlib.Path(check_output_file.parent, replace_name)
                        )
                    jobs_window_progress.config(state=NORMAL)
                    jobs_window_progress.insert(END, "## RENAME OLD FILE ##\n")
                    jobs_window_progress.insert(END, "Output already exists!!\n")
                    jobs_window_progress.insert(
                        END,
                        f'Renaming older file "{check_output_file.name}" to "{replace_name}"\n',
                    )
                    jobs_window_progress.insert(END, "## RENAME OLD FILE ##\n\n")
                    jobs_window_progress.config(state=DISABLED)

            check_for_existing_output()

            command = (
                str(selected_job[0])
                .split("Command:")[1]
                .split(">>>>  Duration =")[0]
                .strip()
            )  # Command
            job_jw = subprocess.Popen(
                "cmd /c " + command + '"',
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.CREATE_NO_WINDOW,
                encoding="utf-8",
                shell=False,
            )  # Run the job with subprocess module

            def cancel_job(*args):  # Cancel job code
                confirm_exit = messagebox.askyesno(
                    title="Prompt",
                    parent=jobs_window,
                    message="Are you sure you want to stop the encode(s)?",
                )
                if confirm_exit:  # If user selects yes
                    if args[0] == "exit":
                        try:
                            job_id = psutil.Process(job_jw.pid)
                            for job_ids in job_id.children(recursive=True):
                                job_ids.kill()
                                job_ids.wait()
                            if pathlib.Path(output_file).is_file():
                                pathlib.Path(output_file).unlink(missing_ok=True)
                        except psutil.NoSuchProcess:
                            pass

            # Cancel buttons
            cancel_encode_job = HoverButton(
                jobs_window_button_frame,
                text="Cancel",
                command=lambda: cancel_job("exit"),
                foreground="white",
                background="#23272A",
                borderwidth="3",
                activebackground="grey",
            )
            cancel_encode_job.grid(
                row=1, column=1, columnspan=1, padx=5, pady=(5, 4), sticky=E + W + S
            )

            def pause_job():  # Pause function/button
                pause_current_job = psutil.Process(job_jw.pid)
                for p_current_job in pause_current_job.children(recursive=True):
                    p_current_job.suspend()
                pause_encode_job.config(state=DISABLED)
                resume_encode_job.config(state=NORMAL)

            pause_encode_job = HoverButton(
                jobs_window_button_frame,
                text="Pause",
                command=pause_job,
                foreground="white",
                background="#23272A",
                borderwidth="3",
                activebackground="grey",
            )
            pause_encode_job.grid(
                row=0, column=0, columnspan=1, padx=5, pady=(5, 4), sticky=E + W + N
            )

            def resume_job():  # Resume function/button
                resume_current_job = psutil.Process(job_jw.pid)
                for r_current_job in resume_current_job.children(recursive=True):
                    r_current_job.resume()
                pause_encode_job.config(state=NORMAL)
                resume_encode_job.config(state=DISABLED)

            resume_encode_job = HoverButton(
                jobs_window_button_frame,
                text="Resume",
                command=resume_job,
                foreground="white",
                background="#23272A",
                borderwidth="3",
                activebackground="grey",
                state=DISABLED,
            )
            resume_encode_job.grid(
                row=0, column=1, columnspan=1, padx=5, pady=(5, 4), sticky=E + W + N
            )

            job_input = str(selected_job[0]).split(">>>>")[1].strip()  # file input
            job_codec = (
                str(selected_job[0])
                .split("Codec: ")[1]
                .split("  >>>>")[0]
                .strip()
                .upper()
            )  # codec
            jobs_window_progress.configure(state=NORMAL)
            jobs_window_progress.insert(
                END, "- " * 18 + "Encode Started" + " -" * 18 + "\n\n"
            )
            jobs_window_progress.insert(
                END, f"Encoding: {job_input} with codec [{job_codec}]\n\n"
            )
            jobs_window_progress.see(END)
            jobs_window_progress.configure(state=DISABLED)

            new_file = True  # Set's a temporary variable to True, this is set to false, so it only deletes 1
            size_string_multiplier = (
                0  # Set's a string to 0, to be added to, to error check
            )
            progress_error = "yes"

            for line in job_jw.stdout:  # Getting output from Popen for job_jw progress
                try:
                    jobs_window_progress.configure(state=NORMAL)
                    # Code removes all extra white space from string to keep it looking nice (ffmpeg is messy)
                    jobs_window_progress.insert(
                        END,
                        str("\n".join(" ".join(x.split()) for x in line.split("\n"))),
                    )
                    jobs_window_progress.see(
                        END
                    )  # Scrolls the textbox to bottom every single pass
                    jobs_window_progress.configure(state=DISABLED)
                except TclError:
                    return

                if total_duration != "None":  # If input file has duration metadata
                    if line.split()[0] == "size=":  # Find string 'size='
                        size_string_multiplier += 1  # Add 1 to the variable
                        if size_string_multiplier >= 1:
                            progress_error = "no"  # Once 'size=' is found 3 times, set progress_error to 'no'
                        try:  # Block of code to turn 00:00:00 frmt to ms (same as duration) for progress bar
                            time = line.split()[2].rsplit("=", 1)[1]
                            try:
                                progress = (
                                    sum(
                                        x * float(t)
                                        for x, t in zip(
                                            [1, 60, 3600], reversed(time.split(":"))
                                        )
                                    )
                                    * 1000
                                )
                                percent = float(
                                    str(
                                        "{:.1%}".format(
                                            float(progress) / float(total_duration)
                                        )
                                    ).replace("%", "")
                                )
                            except (ValueError, TypeError):
                                continue
                            app_progress_bar["value"] = int(
                                percent
                            )  # Input progress into progress bar
                        except (Exception,):
                            pass

                elif total_duration == "None":  # If input file has duration metadata
                    if (
                        line.split()[0] == "size=" and size_string_multiplier < 1
                    ):  # Find string 'size='
                        size_string_multiplier += 1  # Add 1 to the variable
                        if size_string_multiplier == 1:  # Once variable hits 1
                            progress_error = "no"  # Once 'size=' is found 1 times, set progress_error to 'no'

                if (
                    new_file is True and progress_error == "no"
                ):  # If new file is True and no error
                    new_file = False  # Set new file to False
                    output_file = (
                        str(selected_job[0]).split("Output Filename =")[1].strip()[1:-1]
                    )
                    job_listbox.delete(
                        current_selection
                    )  # Deletes selected item in list
                    with open(
                        "Runtime/jobs.dat", "wb"
                    ) as pickle_file:  # Updates dat file
                        pickle.dump(
                            job_listbox.get(0, END),
                            pickle_file,
                            pickle.HIGHEST_PROTOCOL,
                        )
                    job_listbox.xview_moveto(0)
                    job_listbox.yview_moveto(0)

            if pathlib.Path(output_file).is_file() and progress_error == "no":
                # This block of code will show FILE OUTPUT ETC
                jobs_window_progress.configure(state=NORMAL)
                jobs_window_progress.insert(END, f'\nSaved Output to:\n"{output_file}"')
                jobs_window_progress.insert(
                    END, "\n" + "- " * 18 + "Encode Completed" + " -" * 18 + "\n\n"
                )
                jobs_window_progress.see(END)
                jobs_window_progress.configure(state=DISABLED)

            # Log Files -----------------------------------------------------------------------------------
            log_folder = pathlib.Path("Runtime/logs/job_manager_single/").resolve()
            pathlib.Path(log_folder).mkdir(parents=False, exist_ok=True)
            log_txt = pathlib.Path(
                f"{str(log_folder)}/{datetime.now().strftime('%m-%d-%y - %I.%M.%S')}-log.txt"
            )
            logfile = open(log_txt, "w", encoding="utf-8")
            logfile.write(jobs_window_progress.get(1.0, END))
            logfile.flush()
            logfile.close()
            # ----------------------------------------------------------------------------------- Log Files

            start_all_jobs_button.config(state=NORMAL)
            start_selected_button.config(state=NORMAL)
            job_listbox.config(state=NORMAL)
            close_jobs_progress_drawer()

        threading.Thread(
            target=start_single_file_encode
        ).start()  # Use threading module to start job in a new thread

    start_selected_button = HoverButton(
        button_frame,
        text="Start Selected Job",
        command=start_job_window_encode_single,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    start_selected_button.grid(
        row=2, column=0, columnspan=1, padx=5, pady=5, sticky=S + E + W
    )

    def start_job_window_encode_list():  # Start encoding entire list
        global job_listbox, continue_multiprocess_job

        def update_job_list():  # Takes the items in the lisbox and converts them to a python list
            for all_items in job_listbox.get(0, END):
                job_list.append(all_items)

        job_list = []  # Creates an empty list
        if not job_list:  # If no data is inside the list, run the update_job_list()
            update_job_list()

        continue_multiprocess_job = True

        if job_listbox.size() > 0:  # If the listbox has 1 or more elements inside

            def start_multi_file_processing():
                global jobs_window_progress_frame, jobs_window_progress, jobs_window_button_frame, job_jw
                job_duration = (
                    str(job_listbox.get(0))
                    .split("Command:")[1]
                    .split(">>>>  Duration =")[1]
                    .split(">>>>")[0]
                    .strip()
                )  # Used to extract duration from listbox string
                if job_duration != "None":  # If track input HAS a duration
                    total_duration = float(job_duration)
                    app_progress_bar.grid()  # Put progress bar on the app
                elif job_duration == "None":  # IF track input does not have a duration
                    total_duration = job_duration
                    temp_label.grid()  # But temp label on the app

                if (
                    not jobs_window_progress_frame.winfo_viewable()
                    and not jobs_window_button_frame.winfo_viewable()
                ):
                    open_jobs_progress_drawer()  # If the drawer is already opened, do not attempt to re-open it

                def check_for_existing_output():
                    check_output_file = pathlib.Path(
                        str(job_listbox.get(0))
                        .split("Output Filename =")[1]
                        .strip()[1:-1]
                    )
                    if check_output_file.is_file():
                        replace_name = (
                            check_output_file.stem
                            + "[old_file]"
                            + check_output_file.suffix
                        )
                        try:
                            pathlib.Path(check_output_file).rename(
                                pathlib.Path(check_output_file.parent, replace_name)
                            )
                        except FileExistsError:
                            replace_name = (
                                check_output_file.stem
                                + f"[old_file({str(randint(0, 99))})]"
                                + check_output_file.suffix
                            )
                            pathlib.Path(check_output_file).rename(
                                pathlib.Path(check_output_file.parent, replace_name)
                            )
                        jobs_window_progress.config(state=NORMAL)
                        jobs_window_progress.insert(END, "## RENAME OLD FILE ##\n")
                        jobs_window_progress.insert(END, "Output already exists!!\n")
                        jobs_window_progress.insert(
                            END,
                            f'Renaming older file "{check_output_file.name}" to "{replace_name}"\n',
                        )
                        jobs_window_progress.insert(END, "## RENAME OLD FILE ##\n\n")
                        jobs_window_progress.config(state=DISABLED)

                check_for_existing_output()

                command = (
                    str(job_listbox.get(0))
                    .split("Command:")[1]
                    .split(">>>>  Duration =")[0]
                    .strip()
                )
                job_jw = subprocess.Popen(
                    "cmd /c " + command + '"',
                    universal_newlines=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.CREATE_NO_WINDOW,
                    encoding="utf-8",
                    shell=False,
                )

                def cancel_job(*args):
                    global continue_multiprocess_job
                    confirm_exit = messagebox.askyesno(
                        title="Prompt",
                        parent=jobs_window,
                        message="Are you sure you want to stop the encode(s)?",
                    )
                    if confirm_exit:
                        if args[0] == "exit":
                            try:
                                job_id = psutil.Process(job_jw.pid)
                                for job_ids in job_id.children(recursive=True):
                                    job_ids.kill()
                                    job_ids.wait()
                                if pathlib.Path(output_file).is_file():
                                    pathlib.Path(output_file).unlink(missing_ok=True)
                            except psutil.NoSuchProcess:
                                pass
                        elif (
                            args[0] == "exit all"
                        ):  # If exit function is ran by cancel all jobs button
                            try:
                                job_id = psutil.Process(job_jw.pid)
                                for job_ids in job_id.children(recursive=True):
                                    job_ids.kill()
                                    job_ids.wait()
                                if pathlib.Path(output_file).is_file():
                                    pathlib.Path(output_file).unlink(missing_ok=True)
                            except psutil.NoSuchProcess:
                                pass
                            continue_multiprocess_job = False

                cancel_encode_job = HoverButton(
                    jobs_window_button_frame,
                    text="Cancel",
                    command=lambda: cancel_job("exit"),
                    foreground="white",
                    background="#23272A",
                    borderwidth="3",
                    activebackground="grey",
                )
                cancel_encode_job.grid(
                    row=1, column=1, columnspan=1, padx=5, pady=(5, 4), sticky=E + W + S
                )

                cancel_all_jobs = HoverButton(
                    jobs_window_button_frame,
                    text="Cancel\nAll Jobs",
                    command=lambda: cancel_job("exit all"),
                    foreground="white",
                    background="#23272A",
                    borderwidth="3",
                    activebackground="grey",
                )
                cancel_all_jobs.grid(
                    row=1, column=0, columnspan=1, padx=5, pady=(5, 4), sticky=E + W + S
                )

                def pause_job():  # Pause function/button
                    pause_current_job = psutil.Process(job_jw.pid)
                    for p_current_job in pause_current_job.children(recursive=True):
                        p_current_job.suspend()
                    pause_encode_job.config(state=DISABLED)
                    resume_encode_job.config(state=NORMAL)

                pause_encode_job = HoverButton(
                    jobs_window_button_frame,
                    text="Pause",
                    command=pause_job,
                    foreground="white",
                    background="#23272A",
                    borderwidth="3",
                    activebackground="grey",
                )
                pause_encode_job.grid(
                    row=0, column=0, columnspan=1, padx=5, pady=(5, 4), sticky=E + W + N
                )

                def resume_job():  # Resume function/button
                    resume_current_job = psutil.Process(job_jw.pid)
                    for r_current_job in resume_current_job.children(recursive=True):
                        r_current_job.resume()
                    pause_encode_job.config(state=NORMAL)
                    resume_encode_job.config(state=DISABLED)

                resume_encode_job = HoverButton(
                    jobs_window_button_frame,
                    text="Resume",
                    command=resume_job,
                    foreground="white",
                    background="#23272A",
                    borderwidth="3",
                    activebackground="grey",
                    state=DISABLED,
                )
                resume_encode_job.grid(
                    row=0, column=1, columnspan=1, padx=5, pady=(5, 4), sticky=E + W + N
                )

                job_input = (
                    str(job_listbox.get(0)).split(">>>>")[1].strip()
                )  # file input
                job_codec = (
                    str(job_listbox.get(0))
                    .split("Codec: ")[1]
                    .split("  >>>>")[0]
                    .strip()
                    .upper()
                )  # codec
                jobs_window_progress.configure(state=NORMAL)
                jobs_window_progress.insert(
                    END, "- " * 18 + "Encode Started" + " -" * 18 + "\n\n"
                )
                jobs_window_progress.insert(
                    END, f"Encoding: {job_input} with codec [{job_codec}]\n\n"
                )
                jobs_window_progress.see(END)
                jobs_window_progress.configure(state=DISABLED)

                new_file = True  # Set's a temporary variable to True, this is set to false, so it only deletes 1
                size_string_multiplier = (
                    0  # Set's a variable to 0, to be added to, for error checking
                )
                progress_error = (
                    "yes"  # Set's variable with error mode automatically set to 'yes'
                )

                for (
                    line
                ) in job_jw.stdout:  # Getting output from Popen for job_jw progress
                    try:
                        jobs_window_progress.configure(state=NORMAL)
                        # Code removes all extra white space from string to keep it looking nice (ffmpeg is messy)
                        jobs_window_progress.insert(
                            END,
                            str(
                                "\n".join(" ".join(x.split()) for x in line.split("\n"))
                            ),
                        )
                        jobs_window_progress.see(
                            END
                        )  # Scrolls the textbox to bottom every single pass
                        jobs_window_progress.configure(state=DISABLED)
                    except TclError:
                        return

                    if total_duration != "None":  # If input file has duration metadata
                        if line.split()[0] == "size=":  # Find string 'size='
                            size_string_multiplier += 1  # Add 1 to the variable
                            if size_string_multiplier >= 1:
                                progress_error = "no"  # Once 'size=' is found 3 times, set progress_error to 'no'
                            try:  # Block of code to turn 00:00:00 frmt to ms (same as duration) for progress bar
                                time = line.split()[2].rsplit("=", 1)[1]
                                try:
                                    progress = (
                                        sum(
                                            x * float(t)
                                            for x, t in zip(
                                                [1, 60, 3600], reversed(time.split(":"))
                                            )
                                        )
                                        * 1000
                                    )
                                    percent = float(
                                        str(
                                            "{:.1%}".format(
                                                float(progress) / float(total_duration)
                                            )
                                        ).replace("%", "")
                                    )
                                except (ValueError, TypeError):
                                    continue
                                app_progress_bar["value"] = int(
                                    percent
                                )  # Input progress into progress bar
                            except (Exception,):
                                pass

                    elif (
                        total_duration == "None"
                    ):  # If input file has duration metadata
                        if (
                            line.split()[0] == "size=" and size_string_multiplier < 1
                        ):  # Find string 'size='
                            size_string_multiplier += 1  # Add 1 to the variable
                            if size_string_multiplier == 1:  # Once variable hits 1
                                progress_error = "no"  # Once 'size=' is found 1 times, set progress_error to 'no'

                    if (
                        new_file is True and progress_error == "no"
                    ):  # If new file is True and no error
                        new_file = False  # Set new file to False
                        output_file = (
                            job_listbox.get(0)
                            .split("Output Filename =")[1]
                            .strip()[1:-1]
                        )
                        job_listbox.delete(0)  # Deletes top item from listbox
                        with open(
                            "Runtime/jobs.dat", "wb"
                        ) as pickle_file:  # Updates dat file
                            pickle.dump(
                                job_listbox.get(0, END),
                                pickle_file,
                                pickle.HIGHEST_PROTOCOL,
                            )
                        job_listbox.xview_moveto(0)
                        job_listbox.yview_moveto(0)

                if pathlib.Path(output_file).is_file() and progress_error == "no":
                    # This block of code will show FILE OUTPUT ETC
                    jobs_window_progress.configure(state=NORMAL)
                    jobs_window_progress.insert(
                        END, f'\nSaved Output to:\n"{output_file}"'
                    )
                    if job_listbox.size() == 0:
                        jobs_window_progress.insert(
                            END, "\n" + "- " * 18 + "Encode Completed" + " -" * 18
                        )
                    elif job_listbox.size() > 0:
                        jobs_window_progress.insert(
                            END,
                            "\n"
                            + "- " * 18
                            + "Encode Completed"
                            + " -" * 18
                            + "\n\n\n",
                        )
                        # jobs_window_progress.insert(END, '- ' * 18 + 'Encode Started' + ' -' * 18 + '\n')
                    jobs_window_progress.see(END)
                    jobs_window_progress.configure(state=DISABLED)

                if continue_multiprocess_job:
                    if job_listbox.size() > 0:  # If listbox has more than 0 items in it
                        threading.Thread(
                            target=start_multi_file_processing
                        ).start()  # Start job again
                    elif job_listbox.size() == 0:  # If listbox has 0 items
                        # Log Files -----------------------------------------------------------------------------------
                        log_folder = pathlib.Path(
                            "Runtime/logs/job_manager_multi"
                        ).resolve()
                        pathlib.Path(log_folder).mkdir(parents=False, exist_ok=True)
                        log_txt = pathlib.Path(
                            f"{str(log_folder)}/{datetime.now().strftime('%m-%d-%y - %I.%M.%S')}-log.txt"
                        )
                        logfile = open(log_txt, "w", encoding="utf-8")
                        logfile.write(jobs_window_progress.get(1.0, END))
                        logfile.flush()
                        logfile.close()
                        # ----------------------------------------------------------------------------------- Log Files
                        close_jobs_progress_drawer()  # Close processing drawer

                if not continue_multiprocess_job:
                    close_jobs_progress_drawer()

            threading.Thread(
                target=start_multi_file_processing
            ).start()  # Start multi-file job work

    start_all_jobs_button = HoverButton(
        button_frame,
        text="Start All Jobs",
        command=start_job_window_encode_list,
        foreground="white",
        background="#23272A",
        borderwidth="3",
        activebackground="grey",
    )
    start_all_jobs_button.grid(
        row=6, column=0, columnspan=1, padx=5, pady=5, sticky=S + E + W
    )

    def popup_menu(e):  # Right click menu inside the listbox
        option_menu = Menu(listbox_frame, tearoff=False)  # Menu
        option_menu.add_command(label="Delete Selection", command=delete)
        option_menu.add_command(label="Delete All", command=delete_all)
        option_menu.add_separator()
        option_menu.add_command(
            label="Start Selected Job", command=start_job_window_encode_single
        )
        option_menu.add_command(
            label="Start All Jobs", command=start_job_window_encode_list
        )
        option_menu.tk_popup(
            e.x_root, e.y_root
        )  # This gets the position of 'e' on the root widget

    job_listbox.bind("<Button-3>", popup_menu)  # Right click to pop up menu in frame

    def update_listbox_with_saved_jobs():
        try:
            with open("Runtime/jobs.dat", "rb") as pickle_file:
                saved_jobs = pickle.load(pickle_file)
        except FileNotFoundError:
            return

        for (
            jobs
        ) in (
            saved_jobs
        ):  # Go through jobs.dat file to load all the jobs into the listbox window
            job_listbox.insert(END, jobs)

        def updater():  # Updater to update files between multiple processes
            try:
                with open("Runtime/jobs.dat", "rb") as pickle_file:
                    saved_jobs = pickle.load(pickle_file)
                job_tuple = job_listbox.get(0, END)  # Check listbox window
                if (
                    saved_jobs != job_tuple
                ):  # If saved jobs does not equal the same as listbox window
                    job_listbox.delete(0, END)  # Delete listbox window contents fully
                    for (
                        jobs
                    ) in (
                        saved_jobs
                    ):  # Update listbox window with list of saved jobs in dat file
                        job_listbox.insert(END, jobs)
            except EOFError:
                pass
            job_listbox.after(
                100, updater
            )  # Check ever .1 of a second for updates on the dat file

        job_listbox.after(500, updater)

    update_listbox_with_saved_jobs()

    def update_total_jobs():
        """function to update job manager window with total jobs"""
        if jobs_window.wm_title().split()[0].strip() != "Parsing":
            jobs_window.title(f"Job Manager - ({str(job_listbox.size())})")
        jobs_window.after(100, update_total_jobs)

    update_total_jobs()


file_menu.add_command(
    label="Open File         [CTRL + O]", command=input_button_commands
)
root.bind("<Control-o>", lambda event: input_button_commands())
file_menu.add_command(
    label="File Batch         [CTRL + B]", command=batch_processing_input
)
root.bind("<Control-b>", lambda event: batch_processing_input())
file_menu.add_command(label="Job Manager    [CTRL + J]", command=open_jobs_manager)
root.bind("<Control-j>", lambda event: open_jobs_manager())
file_menu.add_separator()


# Reset GUI -----------------------------------------------------------------------------------------------------------
def set_fresh_launch_for_auto_encode():
    encoder.set("Set Codec")
    audiosettings_button.config(state=DISABLED)
    add_job_button.config(state=DISABLED)
    start_audio_button.config(state=DISABLED)
    command_line_button.config(state=DISABLED)
    output_button.config(state=DISABLED)


def set_fresh_launch():
    set_fresh_launch_for_auto_encode()
    check_dependencies()
    encoder_menu.config(state=DISABLED)
    input_entry.config(state=NORMAL)
    input_entry.delete(0, END)
    input_entry.config(state=DISABLED)
    output_entry.config(state=NORMAL)
    output_entry.delete(0, END)
    output_entry.config(state=DISABLED)
    auto_encode_last_options.config(state=DISABLED)
    for widget in root.winfo_children():
        if isinstance(widget, Toplevel):
            widget.destroy()


file_menu.add_command(label="Reset GUI         [CTRL + R]", command=set_fresh_launch)
root.bind("<Control-r>", lambda event: set_fresh_launch())
# ----------------------------------------------------------------------------------------------------------- Reset GUI
file_menu.add_command(
    label="Exit                   [ALT + F4]", command=root_exit_function
)


# Add to jobs list ------------------------------------------------------------------------------
def add_to_jobs():
    global file_input, jobs_window, job_listbox, job_number, file_output
    open_jobs_manager()
    audio_filter_function()
    collect_final_job_commands()

    # add total duration as argument to pass
    media_info = MediaInfo.parse(pathlib.Path(file_input))  # Parse input file
    track_selection_mediainfo = media_info.audio_tracks[
        int(acodec_stream_choices[acodec_stream.get()].strip()[-1])
    ]
    # track_selection_mediainfo uses the -map 0:a:x code to get the track input, the code grabs only the last number
    if track_selection_mediainfo.duration is not None:  # If track input HAS a duration
        track_duration = float(track_selection_mediainfo.duration)
    elif (
        track_selection_mediainfo.duration is None
    ):  # If track input DOES NOT have a duration
        track_duration = "None"

    temp_dictionary = {
        f'Codec: {encoder.get()}  >>>>  "{pathlib.Path(file_input).name}"': finalcommand,
        "Duration = ": str(track_duration),
        "Output Filename = ": f"[{file_output}]",
    }
    jobs_window.deiconify()  # Bring jobs window to the front of other windows
    job_listbox.insert(
        END,
        str(
            f"{list(temp_dictionary.keys())[0]}  >>>>  "
            f"Command: {list(temp_dictionary.values())[0]}  >>>>  "
            f"{list(temp_dictionary.keys())[1]}{list(temp_dictionary.values())[1]}  >>>>  "
            f"{list(temp_dictionary.keys())[2]}{list(temp_dictionary.values())[2]}"
        ),
    )

    with open("Runtime/jobs.dat", "wb") as pickle_file:
        pickle.dump(job_listbox.get(0, END), pickle_file, pickle.HIGHEST_PROTOCOL)


add_job_button = HoverButton(
    start_buttons_frame,
    text="Add to Jobs List",
    command=add_to_jobs,
    state=DISABLED,
    foreground="white",
    background="#23272A",
    borderwidth="3",
    activebackground="grey",
)
add_job_button.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=N + S + E + W)


# ------------------------------------------------------------------------------ Add to jobs list


# Start Audio Job: Manual -----------------------------------------------------------------------
def start_audio_job_manual():
    global encoding_job_type
    if pathlib.Path(
        file_output
    ).is_file():  # Checks if 'output' variable/file already exists
        overwrite_output = messagebox.askyesno(
            title="Overwrite?",  # If exists would you like to over-write?
            message=f"Would you like to overwrite {str(file_output)}?",
        )
        if overwrite_output:  # If "yes"
            encoding_job_type = "manual"
            threading.Thread(target=startaudiojob).start()
        if not overwrite_output:  # If "no"
            file_save()  # Open Output button function to set a new output file location
    else:  # If output doesn't exist go on and run the start job code
        encoding_job_type = "manual"
        threading.Thread(target=startaudiojob).start()


start_audio_button = HoverButton(
    start_buttons_frame,
    text="Start Job",
    command=start_audio_job_manual,
    state=DISABLED,
    foreground="white",
    background="#23272A",
    borderwidth="3",
    activebackground="grey",
)
start_audio_button.grid(
    row=0, column=3, columnspan=1, padx=5, pady=5, sticky=N + S + E + W
)


# --------------------------------------------------------------------------- Start Audio Job: Manual


# Start Audio Job: Auto -----------------------------------------------------------------------------
def encode_last_used_setting():
    global encoding_job_type, audio_window, acodec_stream_track_counter, gotosavefile, track_counter, file_output, batch_mode
    batch_mode = "no"
    encoding_job_type = "auto"
    track_counter()
    encoder.set(config_profile["Auto Encode"]["codec"])
    encoder_changed()
    openaudiowindow()
    gotosavefile()
    command_line_button.config(state=DISABLED)
    output_button.config(state=DISABLED)
    if encoder.get() != "None":
        if pathlib.Path(
            file_output
        ).is_file():  # Checks if 'output' variable/file already exists
            overwrite_output = messagebox.askyesno(
                title="Overwrite?",  # If exists would you like to over-write?
                message=f"Would you like to overwrite {str(file_output)}?",
            )
            if overwrite_output:  # If "yes"
                threading.Thread(target=startaudiojob).start()
            if not overwrite_output:  # If "no"
                file_input_extension = str(
                    pathlib.Path(file_output).suffix
                )  # Get output extension
                # Open save dialog box to define new path
                change_name = filedialog.asksaveasfilename(
                    defaultextension=file_input_extension,
                    initialdir=pathlib.Path(file_output).parent,
                    title="Select New Save Location",
                    initialfile=pathlib.Path(file_output).name,
                    filetypes=[(file_input_extension, file_input_extension)],
                )
                if change_name:  # If path is defined (user presses save)
                    file_output = change_name
                    threading.Thread(target=startaudiojob).start()
                if not change_name:  # If path is not defined (user presses cancel or X)
                    advanced_root_deiconify()  # Re-Open root
                    open_all_toplevels()  # Re-Open any top levels that might have been closed
                    set_fresh_launch()  # Reset the GUI to fresh launch
                    return  # Return None and exit
        else:  # If output doesn't exist go on and run the start job code
            threading.Thread(target=startaudiojob).start()


auto_encode_last_options = HoverButton(
    start_buttons_frame,
    text="Auto Encode:\nLast Used Options",
    command=encode_last_used_setting,
    foreground="white",
    background="#23272A",
    borderwidth="3",
    state=DISABLED,
    activebackground="grey",
)
auto_encode_last_options.grid(
    row=0, column=0, columnspan=1, padx=5, pady=5, sticky=N + S + E + W
)


def popup_auto_e_b_menu(e):  # Function for mouse button 3 (right click) to pop up menu
    global rightclick_on_off
    try:
        if rightclick_on_off == 1:
            auto_encode_button_menu.tk_popup(
                e.x_root, e.y_root
            )  # This gets the position of 'e' on the root widget
    except NameError:
        pass


def show_auto_encode_command(*args):  # Opens a new window with 'Auto Encode' command
    try:
        global show_auto_command_window
        show_auto_command_window.destroy()  # Destroys existing auto command window before continuing to make a new one
    except (Exception,):
        pass

    show_auto_command_window = Toplevel(
        root
    )  # auto command window (shows auto encoding command)
    show_auto_command_window.title("Auto Encode Command")
    show_auto_command_window.configure(background="#434547")
    text_area = scrolledtextwidget.ScrolledText(
        show_auto_command_window,
        width=60,
        height=7,
        tabs=10,
        spacing2=3,
        spacing1=2,
        spacing3=3,
    )
    text_area.grid(column=0, pady=10, padx=10)
    text_area.configure(state=NORMAL, bg="black", fg="#CFD2D1", bd=8)
    text_area.insert(INSERT, config_profile["Auto Encode"]["command"])
    text_area.see(END)
    text_area.configure(state=DISABLED)
    show_auto_command_window.grid_columnconfigure(0, weight=1)


auto_encode_button_menu = Menu(
    root, tearoff=False
)  # This is the right click menu for the auto_encode_button
auto_encode_button_menu.add_command(
    label="Show Command", command=show_auto_encode_command
)
root.bind(
    "<Button-3>", popup_auto_e_b_menu
)  # Uses mouse button 3 (right click) to pop up menu
# --------------------------------------------------------------------------- Start Audio Job: Auto

# Status Label at bottom of main GUI -----------------------------------------------------------------
status_label = Label(
    root,
    text="",
    bd=4,
    relief=SUNKEN,
    anchor=E,
    background="#717171",
    foreground="white",
)
status_label.grid(column=0, row=4, columnspan=4, sticky=W + E)


# ----------------------------------------------------------------- Status Label at bottom of main GUI


# dependency check ----------------------------------------------------------------------------------------------------
def check_dependencies():
    global batch_encoder_menu, ffmpeg, mpv_player, mediainfo
    # ffmpeg ---------------------------------------------------------------------------------------------
    if not pathlib.Path(config["ffmpeg_path"]["path"].replace('"', "")).is_file():
        # if ffmpeg found on system PATH
        if shutil.which("ffmpeg"):
            ffmpeg = '"' + str(pathlib.Path(shutil.which("ffmpeg"))).lower() + '"'
            messagebox.showinfo(
                title="Prompt!",
                message="ffmpeg.exe found on system PATH, "
                "automatically setting path to location.\n\n"
                "Note: This can be changed in the config.ini file"
                " or in the General Settings window",
            )

            # if ffmpeg found on path, ask the user if they'd like to delete the included ffmpeg.exe
            if pathlib.Path("Apps/ffmpeg/ffmpeg.exe").exists():
                remove_ffmpeg = messagebox.askyesno(
                    title="Delete Included ffmpeg?",
                    message="Would you like to delete the included FFMPEG?",
                )
                if remove_ffmpeg:
                    pathlib.Path("Apps/ffmpeg.exe").unlink(missing_ok=True)

            # define the path to ffmpeg.exe in the config.ini
            config.set("ffmpeg_path", "path", ffmpeg)
            with open(config_file, "w") as configfile:
                config.write(configfile)

        # if ffmpeg is '' in the .ini and not on system path
        elif ffmpeg == "" and not shutil.which("ffmpeg"):
            messagebox.showinfo(
                title="Info",
                message="Program will use the included "
                '"ffmpeg.exe" located in the "Apps" folder',
            )
            ffmpeg = '"' + str(pathlib.Path("Apps/ffmpeg/ffmpeg.exe")) + '"'
            config.set("ffmpeg_path", "path", ffmpeg)
            with open(config_file, "w") as configfile:
                config.write(configfile)

        # if ffmpeg.exe is missing all together (it shouldn't be as it gets packed with the program)
        if (
            not pathlib.Path("Apps/ffmpeg/ffmpeg.exe").exists()
            and not shutil.which("ffmpeg")
            and not pathlib.Path(
                config["ffmpeg_path"]["path"].replace('"', "")
            ).is_file()
        ):
            # clear path to ffmpeg in config.ini
            config.set("ffmpeg_path", "path", "")
            with open(config_file, "w") as configfile:
                config.write(configfile)

            # prompt user that ffmpeg is missing
            ffmpeg_prompt = messagebox.askyesno(
                parent=root,
                title="FFMPEG Not Found",
                message='FFMPEG is missing!\n\nDownload "ffmpeg.exe" and define '
                'the path to it in the "General Settings" window or place it '
                "in:\n"
                f'"{pathlib.Path(pathlib.Path.cwd() / "Apps" / "FFMPEG")}"\n '
                "and restart the program.\n\n"
                "Would you like to download ffmpeg now?",
            )

            # if user selects 'yes' in the prompt, download ffmpeg from gyans build
            if ffmpeg_prompt:
                webbrowser.open(
                    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z"
                )

    # mpv player -----------------------------------------------------------------------------------------
    if not pathlib.Path(config["mpv_player_path"]["path"].replace('"', "")).is_file():
        if mpv_player == "" or not pathlib.Path(mpv_player.replace('"', "")).exists():
            mpv_player = '"' + str(pathlib.Path("Apps/mpv/mpv.exe")) + '"'
            config.set("mpv_player_path", "path", mpv_player)
            with open(config_file, "w") as configfile:
                config.write(configfile)

    # mediainfo GUI ---------------------------------------------------------------------------------------
    if not pathlib.Path(config["mediainfogui_path"]["path"].replace('"', "")).is_file():
        if mediainfo == "" or not pathlib.Path(mediainfo.replace('"', "")).exists():
            mediainfo = '"' + str(pathlib.Path("Apps/MediaInfo/MediaInfo.exe")) + '"'
            config.set("mediainfogui_path", "path", mediainfo)
            with open(config_file, "w") as configfile:
                config.write(configfile)

    # fdk-aac ----------------------------------------------------------------------------------------------
    if not pathlib.Path(str(config["fdkaac_path"]["path"]).replace('"', "")).is_file():
        encoder_menu["menu"].entryconfigure(
            "FDK-AAC", state=DISABLED
        )  # disables fdk-aac in codec menu
        try:  # update batch encoder menu
            batch_encoder_menu["menu"].entryconfigure(
                "FDK-AAC", state=DISABLED
            )  # disables fdk-aac in batch menu
        except (NameError, AttributeError):  # if batch_encoder menu doesn't exist
            pass
    elif pathlib.Path(str(config["fdkaac_path"]["path"]).replace('"', "")).is_file():
        encoder_menu["menu"].entryconfigure(
            "FDK-AAC", state=NORMAL
        )  # enables fdk-aac in codec menu
        try:  # update batch encoder menu
            batch_encoder_menu["menu"].entryconfigure(
                "FDK-AAC", state=NORMAL
            )  # enables fdk-aac in batch menu
        except (NameError, AttributeError):  # if batch_encoder menu doesn't exist
            pass

    # qaac64 -------------------------------------------------------------------------------------------------
    if not pathlib.Path(str(config["qaac_path"]["path"]).replace('"', "")).is_file():
        encoder_menu["menu"].entryconfigure(
            "QAAC", state=DISABLED
        )  # disables qaac in codec menu
        try:  # update batch encoder menu
            batch_encoder_menu["menu"].entryconfigure(
                "QAAC", state=DISABLED
            )  # disables qaac in batch menu
        except (NameError, AttributeError):  # if batch_encoder menu doesn't exist
            pass
    elif pathlib.Path(str(config["qaac_path"]["path"]).replace('"', "")).is_file():
        qt_folder = pathlib.Path(
            pathlib.Path(str(config["qaac_path"]["path"]).replace('"', ""))
            .resolve()
            .parent
            / "QTfiles64"
        )

        # list of needed qaac files to run
        list_of_qaac_files = [
            pathlib.Path(qt_folder / "ASL.dll"),
            pathlib.Path(qt_folder / "CoreAudioToolbox.dll"),
            pathlib.Path(qt_folder / "CoreFoundation.dll"),
            pathlib.Path(qt_folder / "icudt62.dll"),
            pathlib.Path(qt_folder / "libdispatch.dll"),
            pathlib.Path(qt_folder / "libicuin.dll"),
            pathlib.Path(qt_folder / "libicuuc.dll"),
            pathlib.Path(qt_folder / "objc.dll"),
        ]

        checked_qaac_files = []  # check if all the files in the list above are present
        for (
            files
        ) in list_of_qaac_files:  # return true or false if they are/are not present
            checked_qaac_files.append(pathlib.Path(files).is_file())

        if all(checked_qaac_files):  # if all files are present
            encoder_menu["menu"].entryconfigure(
                "QAAC", state=NORMAL
            )  # enables qaac in codec menu
            try:  # update batch encoder menu
                batch_encoder_menu["menu"].entryconfigure(
                    "QAAC", state=NORMAL
                )  # enables qaac in batch menu
            except (NameError, AttributeError):  # if batch_encoder menu doesn't exist
                pass
        else:  # if 1 or more files are missing
            encoder_menu["menu"].entryconfigure(
                "QAAC", state=DISABLED
            )  # disables qaac in codec menu
            try:  # update batch encoder menu
                batch_encoder_menu["menu"].entryconfigure(
                    "QAAC", state=DISABLED
                )  # disables qaac in batch menu
            except (NameError, AttributeError):  # if batch_encoder menu doesn't exist
                pass


check_dependencies()
# dependency check ----------------------------------------------------------------------------------------------------
root.mainloop()  # bottom of mainloop
