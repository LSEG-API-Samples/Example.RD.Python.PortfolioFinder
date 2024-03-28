#=============================================================================
#   This source code is provided under the Apache 2.0 license
#   and is provided AS IS with no warranty or guarantee of fit for purpose.
#   Copyright (C) 2024 LSEG. All rights reserved.
#=============================================================================

import tkinter as tk
from tkinter import messagebox
import asyncio
import threading
import Frames
from WaitingIndicator import WaitingIndicator
from PAM import PAM
import refinitiv.data as rd
import pandas as pd

# Used when starting from generated executable to control splash screen
try:
    import pyi_splash
except ImportError:
    pass


# ----------------------------
# root display window and controller class
class Window(tk.Tk):
# ----------------------------
	def __init__(self, *args, **kwargs):
		tk.Tk.__init__(self, *args, **kwargs)

		# Create our main window
		self.iconbitmap('LSEG.ico')
		self.title("Portfolio Finder")
		self.geometry("1100x600")
		self.minsize(800, 500)

		self.pam = PAM(self)
		self.err = None	

		# For more flexibility and possible future enhancements, let's create a container for our window
		self.container = tk.Frame(self)
		self.container.pack(fill=tk.BOTH, expand=True)

		# Define the layout within our main container.  Our container will contain 3 main frames:
		#  
		# 1. Input Frame - captures request details
		# 2. Data Frame - displays results
		# 3. Status Frame - general status details
		#
		self.data = Frames.DataFrame(self.container, self)
		self.status = Frames.StatusFrame(self.container, self)
		self.input = Frames.InputFrame(self.container, self)

        # Pack frames
		self.input.pack(side=tk.TOP, fill=tk.X)
		self.data.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # Create an instance of WaitingIndicator and pack it into the main window
		self.circles = WaitingIndicator(self)

		# Perform our initialization after main window has been rendered...
		self.update_idletasks()		
		self.after_idle(self.initialize)


	def check_event(self, event, message, session):
		if event == rd.session.EventCode.SessionAuthenticationFailed:
			self.err = f"Session authentication failed: {message} Refer to the refinitiv-data.config.json config for setting credentials."

	def initialize(self):
		self.update_idletasks()	

		# Ensure we can connect into our data environment
		try:
			session = rd.session.Definition().get_session()
			session.on_event(self.check_event)
			session.open()
			if self.err is None:
				rd.session.set_default(session)
				self.input.submitRequest()		# Pre-populate some data
			else:
				self.setStatusMsg(self.err, True)

		except Exception as e:
			pass

	# set the message in the bottom status bar
	def setStatusMsg(self, message, error=False):
		self.status.set_status(message, error)

	def mapTypeToPortfolioTypes(self, typeIndex):
		if typeIndex == 1:
			return ['MarketIndex']
		elif typeIndex == 2:
			return ['PeerList', 'MonitorList']
		else:
			return ['FundedPortfolio', 'CompositeFundedPortfolio', 'CarveOutPortfolio', 'ModelPortfolio', 'WatchList']

	def processSubmit(self, typeIndex, query, maxCount):
		self.setStatusMsg("Submitted request...")

		# Display the waiting indicator...
		self.circles.place(relx=0.5, rely=0.5, anchor='center')
		self.circles.displayIndicator()

		# Retrieve the data...
		ptype = self.mapTypeToPortfolioTypes(typeIndex)
		threading.Thread(target=self.run_async_func, args=(self.pam.requestPortfolios, ptype, query, maxCount)).start()

	def run_async_func(self, func, *args):
        # Create a new event loop
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)

		try:
			# During request, disable the submit button...
			self.input.setSubmitState(False)

			# Run the async function on the event loop and get the result
			data = loop.run_until_complete(func(*args))
		except Exception as e:
			print(e)
			self.setStatusMsg(str(e), True)
			return
		finally:
			# Close the event loop
			loop.close()

			# Hide the indicator
			self.circles.hideIndicator()

			# Enable submit button
			self.input.setSubmitState(True)						

        # The data request has been fulfilled and the following displays the results in another Frame 
		#self.data.displayPortfolios(pd.DataFrame.from_records(data))	
		self.data.displayPortfolios(data)
		
if __name__ == "__main__":
	# Kill the splash screen (start via pyinstaller)
	try:
		pyi_splash.close()
	except NameError:
		pass

	# Create and launch the main window...
	window = Window()
	window.mainloop()
