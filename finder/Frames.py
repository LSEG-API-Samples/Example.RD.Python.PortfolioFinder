#=============================================================================
#   This source code is provided under the Apache 2.0 license
#   and is provided AS IS with no warranty or guarantee of fit for purpose.
#   Copyright (C) 2024 LSEG. All rights reserved.
#=============================================================================

from PySide6.QtWidgets import QWidget, QLabel, QComboBox, QLineEdit, QPushButton, \
							  QGridLayout, QVBoxLayout, QHBoxLayout, QDialog, QSpinBox, \
                              QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QIcon, QPixmap
import asyncio

from .TreeComponents import PortfolioTreeView, DataFrameModel, FilterHeaderView

# ----------------------------
# Settings
# Presents a simple dialog defining the application settings used within this application.
class Settings(QDialog):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)

        # Global setting values
        self.maxPortfolioCnt = 1000         # Default

        # Set the dialog properties
        self.setWindowIcon(QIcon('assets/LSEG.ico'))
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 140)

        # Create the label and QSpinBox
        self.label = QLabel("Maximum Count:", self)
        self.maxPortfolioWdgt = QSpinBox(self)
        self.maxPortfolioWdgt.setRange(1, 999999)  # Set the minimum and maximum values
        self.maxPortfolioWdgt.setValue(self.maxPortfolioCnt)  # Set the initial value

        # Create OK and Cancel buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(lambda:self.accepted())
        self.cancel_button.clicked.connect(lambda:self.rejected())

        # Create a horizontal layout for the label and the QSpinBox
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.label)
        h_layout.addWidget(self.maxPortfolioWdgt)

        # Layout for buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)             

        # Set up the layout
        layout = QVBoxLayout(self)
        layout.addLayout(h_layout)
        layout.addStretch(1)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def accepted(self):
        # Save the current state to the actual variable when "Ok" is pressed
        self.maxPortfolioCnt = self.maxPortfolioWdgt.value()
        super().accept()
        
    def rejected(self):
        # Save the current state to the actual variable when "Ok" is pressed
        self.maxPortfolioWdgt.setValue(self.maxPortfolioCnt)
        super().reject()

    def closeEvent(self, event):
        self.rejected()

# ----------------------------
# InputFrame
# Represents the controls providing the query parameters to search for portfolios
class InputFrame(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)

        self.controller = controller

        portfolio_types = ['My Portfolios & Lists', 'All Indices', 'Peer & Monitor Lists']
        self.settings = Settings(self)

        # Define the controls
        lbl1 = QLabel('Portfolio Type:', self)
        self.types = QComboBox(self)
        self.types.addItems(portfolio_types)
        lbl2 = QLabel('Search:', self)
        self.query = QLineEdit(self)
        self.submit_btn = QPushButton('Submit', self)
        self.submit_btn.clicked.connect(self.on_submit)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        settings_btn = QLabel("...", self)
        settings_btn.setCursor(Qt.PointingHandCursor)
        pixmap = QPixmap("assets/settings.png")
        settings_btn.setPixmap(pixmap.scaled(16, 16, Qt.KeepAspectRatio))
        settings_btn.mousePressEvent = self.open_settings

        # Layout the controls
        layout = QGridLayout(self)
        layout.addWidget(lbl1, 0, 0)
        layout.addWidget(self.types, 0, 1)
        layout.addWidget(lbl2, 0, 2)
        layout.addWidget(self.query, 0, 3)
        self.query.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.submit_btn, 0, 4)
        layout.addItem(spacer, 0, 5)
        layout.addWidget(settings_btn, 0, 6, 1, 2, Qt.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)        
        self.setLayout(layout)

        # Bind <Return> to the query field
        self.query.returnPressed.connect(self.on_submit)

        # Disable submit initially upon startup - main controller will enable if properly initialized
        self.setSubmitState(False)

    # Determine the input state for controls based on the status of the application or whether an outstanding request.
    def setSubmitState(self, enabled):
        self.submit_btn.setEnabled(enabled)
        self.query.setEnabled(enabled)

    def on_submit(self):
        asyncio.ensure_future(self.submitRequest())

    async def submitRequest(self):
        # Process the values selected and pass onto our controller for processing
        query = self.query.text().strip()

        # Fetch and display the data
        await self.controller.processSubmit(self.types.currentIndex(), 
                                            query if query else None, 
                                            int(self.settings.maxPortfolioCnt))

    def open_settings(self, event):
        self.settings.show()

# ----------------------------
# DataFrame
# Represents the main control that presents our portfolios retrieved from the service
class DataFrame(QWidget):
    class DataChanged(QObject):
        dataChanged = Signal(str)

    def __init__(self, parent=None, controller=None):
        super(DataFrame, self).__init__(parent)

        # Create the QTreeView and its associated header view
        self.tree = PortfolioTreeView(self)
        self.header = FilterHeaderView()

        # Create the layout and add the widgets
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)        
        layout.addWidget(self.tree)
        self.setLayout(layout)

        # Monitor grid change
        self.gridChanged = DataFrame.DataChanged()       

    def displayPortfolios(self, data):
        # Create the DataFrameModel and assign
        model = DataFrameModel(data, self.gridChanged, self)
        self.tree.setModel(model)

        # Assign the header view
        self.tree.setHeader(self.header)

        self.tree.setColumnWidth(0, 60)

        # Enable sorting
        if not self.tree.isSortingEnabled():
            self.tree.setSortingEnabled(True)

        self.tree.setHeaderHidden(False)


# ----------------------------
# StatusFrame
# Represents a simple area providing application feedback.
class StatusFrame(QWidget):
    def __init__(self, parent=None, controller=None):
        super(StatusFrame, self).__init__(parent)

        # General information style
        self.generalColor = QColor(26, 67, 191)
        self.errorColor = QColor(128, 0, 0)

        self.statusMsg = "Initializing..."
        self.lbl1 = QLabel(self.statusMsg)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lbl1)
        self.setLayout(layout)

    def set_status(self, message, error):
        self.statusMsg = message
        self.lbl1.setText(self.statusMsg)
        if error:
            self.lbl1.setStyleSheet("color: rgb({}, {}, {});".format(self.errorColor.red(), self.errorColor.green(), self.errorColor.blue()))
            p = self.palette()
            p.setColor(self.backgroundRole(), QColor(255, 204, 204))
            self.setPalette(p)
        else:
            self.lbl1.setStyleSheet("color: rgb({}, {}, {});".format(self.generalColor.red(), self.generalColor.green(), self.generalColor.blue()))
            p = self.palette()
            p.setColor(self.backgroundRole(), QColor(217, 217, 217))
            self.setPalette(p)


