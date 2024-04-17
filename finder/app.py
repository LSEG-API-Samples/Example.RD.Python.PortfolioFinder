#=============================================================================
#   This source code is provided under the Apache 2.0 license
#   and is provided AS IS with no warranty or guarantee of fit for purpose.
#   Copyright (C) 2024 LSEG. All rights reserved.
#=============================================================================
import refinitiv.data as rd

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtGui import QIcon

from .PAM import PAM
from .Frames import DataFrame, InputFrame, StatusFrame
from .waitingspinnerwidget import QtWaitingSpinner

import traceback, os

# Window
# root display window and controller class
class Window(QMainWindow):
    def __init__(self, loop, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.loop = loop

        # Create our main window
        self.setWindowIcon(QIcon('assets/LSEG.ico'))
        self.setWindowTitle("Portfolio Finder")
        self.resize(1100, 600)
        self.setMinimumSize(400, 200)

        self.pam = PAM(self)
        self.err = None
        self.session = None

        # Define the layout within our main container.
        layout = QVBoxLayout()

        # Our container will contain 3 main frames:
        # 1. Input Frame - captures request details
        # 2. Data Frame - displays results
        # 3. Status Frame - general status details
        self.data = DataFrame(self)
        self.status = StatusFrame(self)
        self.input = InputFrame(self)

        # Add frames to layout
        layout.addWidget(self.input)
        layout.addWidget(self.data)
        layout.addWidget(self.status)

        # Set layout on a QWidget and set as central widget
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Register interest in grid changes
        self.data.gridChanged.dataChanged.connect(self.setStatusMsg)

    # initialize
    # Upon startup, this method attempts to connect and load an initial list of user-defined portfolios
    def initialize(self):
        self.input.on_submit()

    def check_event(self, event, message, session):
        if event == rd.session.EventCode.SessionAuthenticationFailed:
            self.err = f"Session authentication failed: {message} Refer to the refinitiv-data.config.json config for setting credentials."

    def open_session(self):
        self.session = rd.session.Definition().get_session()
        self.session.on_event(self.check_event)
        self.session.open()		# Note: open_async blocks for some reason, so I'm using open()

    async def connect(self):
        # Ensure we can connect into our data environment
        try:
            self.setStatusMsg("Connecting...")			
            await self.loop.run_in_executor(None, self.open_session)
            if self.err is None:
                rd.session.set_default(self.session)
            else:
                self.setStatusMsg(self.err, True)

            return self.err is None
        except Exception as e:
            self.setStatusMsg(f"Failed to connect. {e}", True)
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

    async def processSubmit(self, typeIndex, query, maxCount):
        # Enable submit button
        self.input.setSubmitState(False)

        # Provide some user feedback
        spinner = QtWaitingSpinner(self)
        spinner.start()

        # Connect, if not already
        if self.session is None:
            if not await self.connect():
                spinner.stop()
                return
            
        # Retrieve the data...
        ptype = self.mapTypeToPortfolioTypes(typeIndex)

        try:
            self.setStatusMsg("Submitted request...")
            df = await self.pam.requestPortfolios(ptype, query, maxCount)
            self.data.displayPortfolios(df)
        except Exception as e:
            tb = traceback.TracebackException.from_exception(e)
            err = f'Exception {type(e).__name__} - {e}'
            for stack in reversed(tb.stack):
                if 'finder' in stack.filename:
                    err = f'{err}. File: {os.path.basename(stack.filename)}, line: {stack.lineno}, function: {stack.name}'
                    break
            self.setStatusMsg(err, True)
            traceback.print_exc()   # Dump entire trace to the console
        finally:
            # Enable submit button
            self.input.setSubmitState(True)
            spinner.stop()