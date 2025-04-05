# main.py

import tkinter as tk
from gui import MemoryVisualizerGUI

def main():
    """
    Main entry point for the memory visualization application.
    Initializes the Tkinter root window and creates the GUI.
    """
    root = tk.Tk()
    app = MemoryVisualizerGUI(root)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

def on_close():
    """
    Handle the window close event.
    """
    # Clean up resources
    import matplotlib.pyplot as plt
    
    plt.close('all')
    
    # Exit the application
    import sys
    sys.exit(0)

if __name__ == "__main__":
    main()