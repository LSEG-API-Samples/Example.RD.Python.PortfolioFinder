#=============================================================================
#   This source code is provided under the Apache 2.0 license
#   and is provided AS IS with no warranty or guarantee of fit for purpose.
#   Copyright (C) 2024 LSEG. All rights reserved.
#=============================================================================

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

# ----------------------------
# Settings
# Presents a simple dialog defining the application settings used within this application.
class Settings(tk.Toplevel):
	def __init__(self, parent):
		super().__init__(parent)		

		self.iconbitmap('LSEG.ico')
		self.title("Settings")
		self.geometry("300x200")
		self.resizable(False, False)
		tk.Label(self, text="Maximum Count:", anchor='w').grid(row=0, sticky='w', padx=5, pady=5)
		self.maxCountEntry = tk.Entry(self)
		self.maxCountEntry.grid(row=0, column=1, sticky='w')
		self.maxCountEntry.insert(0, 1000)

        # Make the middle row expandable
		self.grid_rowconfigure(1, weight=1)

		# Create a frame for the buttons
		button_frame = tk.Frame(self)
		button_frame.grid(row=2, column=0, columnspan=2, sticky='we')

		# Add an empty label to push the buttons to the right
		tk.Label(button_frame).grid(row=0, column=0, sticky='we')		

		# Add OK and Cancel buttons
		ok_button = tk.Button(self, text="OK", command=self.ok)
		ok_button.place(relx=0.7, rely=0.97, anchor='sw')
		cancel_button = tk.Button(self, text="Cancel", command=self.cancel)
		cancel_button.place(relx=0.8, rely=0.97, anchor='sw')

		# Make the empty label expandable
		button_frame.grid_columnconfigure(0, weight=1)		

		self.protocol("WM_DELETE_WINDOW", self.hide)  # Override close button
		self.hide()   # Hide the display

		
	def ok(self):
		# Validate the inputs and close the window
		try:
			numVal = int(self.maxCountEntry.get())
			if numVal < 1:
				messagebox.showerror("Error", "Max Count must be greater than 0", parent=self)
				return
		except ValueError:
			messagebox.showerror("Error", "Invalid number", parent=self)
			return

		self.hide()  # Hide the window

	def cancel(self):
		self.hide()

	def show(self):
		# Center the window on the screen
		window_width = self.winfo_reqwidth()
		window_height = self.winfo_reqheight()
		position_right = int(self.winfo_screenwidth()/2 - window_width/2)
		position_down = int(self.winfo_screenheight()/2 - window_height/2)
		self.geometry("+{}+{}".format(position_right, position_down))		
		self.deiconify()

	def hide(self):
		self.withdraw()

# ----------------------------
# InputFrame
# Represents the controls providing the query parameters to search for portfolios
class InputFrame(ttk.Frame):
# ----------------------------
	def __init__(self, parent, controller):

		ttk.Frame.__init__(self, parent, relief=tk.GROOVE)

		portfolio_types = ['My Portfolios & Lists', 'All Indices', 'Peer & Monitor Lists']
		self.settings = Settings(self)

		# ----------------------------------------
		# Define the controls
		# ----------------------------------------
		lbl1 = ttk.Label(self, text='Portfolio Type:', font=(None, 10, 'bold'))
		types = ttk.Combobox(self, width=25, state="readonly")
		types['values'] = portfolio_types		
		types.current(0)  # Set the initial value to the first item in the list
		lbl2 = ttk.Label(self, text='Search:', font=(None, 10, 'bold'))
		query = ttk.Entry(self, width=40)
		submit_btn = ttk.Button(self, text="Submit", style='Dload.TButton', command=self.submitRequest)
		spacer = ttk.Label(self)
		settings_btn = ttk.Label(self, text="...", cursor="hand2", font=("Helvetica", 16, 'bold'))
		settings_btn.bind("<Button-1>", self.open_settings)

		# -----------------------------------------
		# Layout the controls
		# All controls will be layed out in a grid within a single row
		# -----------------------------------------
		lbl1.grid(row=0, column=0, sticky=tk.W, padx=5)
		types.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
		lbl2.grid(row=0, column=2, sticky=tk.W, padx=5)
		query.grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
		submit_btn.grid(row=0, column=4, sticky=(tk.W), pady=5, padx=5)
		spacer.grid(row=0, column=5, sticky='we')
		settings_btn.grid(row=0, column=6, sticky=(tk.E), pady=(5,20), padx=(5, 20))

		# Force the settings to the right side
		self.grid_columnconfigure(5, weight=1)

		# Bind <Return> to the query field
		query.bind('<Return>', self.on_enter)

		self.types = types
		self.query = query
		self.submit = submit_btn
		self.controller = controller

		# Disable submit initialally upon startup - main controller will enable if properly initialized
		self.setSubmitState(False)

	def setSubmitState(self, enabled):
		self.submit['state'] = 'normal' if enabled else 'disabled'

	def on_enter(self, v1):
		state = str(self.submit['state'])
		if state == 'normal':
			self.submitRequest()

	def submitRequest(self):
		# Process the values selected and pass onto our controller for processing
		query = self.query.get().strip()

		# Fetch and display the data
		self.controller.processSubmit(self.types.current(), 
									query if query else None, 
									int(self.settings.maxCountEntry.get()))

	def open_settings(self, event):
		self.settings.show()

# ----------------------------
# DataFrame
# Represents the main control that presents our portfolios retrieved from the service
class DataFrame(ttk.Frame):
# ----------------------------
	def __init__(self, parent, controller):
		# Set the frames background color to gray
		style = ttk.Style()
		style.configure('Status.TFrame', background='gray')
		style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

		ttk.Frame.__init__(self, parent, style='Status.TFrame')

		# ----------------------------------------
		# Define the controls
		# ----------------------------------------
		tree = ttk.Treeview(self, selectmode='browse', style="Treeview")
		vsb = ttk.Scrollbar(self, orient="vertical", command=tree.yview)

		# Attach scrollbars to Treeview
		tree.configure(yscrollcommand=vsb.set)

        # Configure the DataFrame to expand and fill both directions
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)
			
		# -----------------------------------------
		# Layout the controls
		# All controls will be layed out in a grid
		# -----------------------------------------		
		tree.grid(row=0, column=0, sticky='nsew')
		vsb.grid(row=0, column=1, sticky='ns')		

		self.tree = tree
		self.controller = controller

	def displayPortfolios(self, data):
		# Clear the treeview
		self.tree.delete(*self.tree.get_children())

		# Update the status
		self.controller.setStatusMsg(f"Found a total of {len(data)} portfolios")

		if data:
			# Get the keys from the first row in the data list, but skip keys whose values are dictionaries
			columns = [key for key, value in data[0].items() if not isinstance(value, dict)]
			self.tree['columns'] = columns

			# Set the heading and width of the #0 column
			self.tree.heading("#0", text="#")
			self.tree.column('#0', minwidth=0, width=50, stretch='no')

			for column in columns:
				self.tree.heading(column, text=column, anchor="w")
				self.tree.column(column, anchor="w", width=50)

			# Add rows
			for i, row_data in enumerate(data, start=1):
				# Get the values from the dictionary, but only for keys that are in the columns list
				row_values = [value for key, value in row_data.items() if key in columns]
				self.tree.insert('', 'end', text=str(i), values=row_values)				


# ----------------------------
# StatusFrame
# Represents a simple area providing application feedback.
class StatusFrame(ttk.Frame):
# ----------------------------
	def __init__(self, parent, controller):
		# Set the frames background color to dark gray
		style = ttk.Style()

		# General information style
		style.configure('General.TFrame', background='#d9d9d9')
		style.configure('General.TLabel', background='#d9d9d9', foreground='#1A43BF', font=(None, 10))

        # Error information style
		style.configure('Error.TFrame', background='#ffcccc')
		style.configure('Error.TLabel', background='#ffcccc', foreground='#800000', font=(None, 10))

		ttk.Frame.__init__(self, parent, style='General.TFrame')

		self.statusMsg = tk.StringVar(value="Initializing...")
		self.lbl1 = ttk.Label(self, textvariable=self.statusMsg, anchor='w', style='General.TLabel')

		self.lbl1.grid(row=0, column=0, sticky='nsew')

		self.style = style
		self.controller = controller

	def set_status(self, message, error):
		self.statusMsg.set(message)
		if error:
			self.lbl1.config(style='Error.TLabel')
			self.config(style='Error.TFrame')
		else:
			self.lbl1.config(style='General.TLabel')
			self.config(style='General.TFrame')


