from PySide6.QtWidgets import QApplication, QTreeView, QMenu, QHeaderView, QGraphicsDropShadowEffect
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QEvent, QRect
import pandas as pd
from PySide6.QtGui import QAction, QIcon, QCursor, QMouseEvent

# PortfolioTreeView
# Used to provide the ability to copy/paste cell text
class PortfolioTreeView(QTreeView):
    def __init__(self, parent=None):
        super(PortfolioTreeView, self).__init__(parent)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        self.setGraphicsEffect(shadow)

        self.setStyleSheet("QTreeView::branch { image: none; }") # Remove expanding arrow '>' from column 1

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        # Create a QMenu
        menu = QMenu(self)

        # Create a QAction for the "Copy" option
        copyAction = QAction("Copy", self)
        copyAction.triggered.connect(lambda: self.copy_text(index))

        # Add the action to the menu
        menu.addAction(copyAction)

        # Show the menu at the event position
        menu.exec_(event.globalPos())

    def copy_text(self, index):
        text = index.data(Qt.DisplayRole)
        QApplication.clipboard().setText(text)

# FilterHeaderView
# Used to providing column filtering
class FilterHeaderView(QHeaderView):
    def __init__(self, parent=None):
        super(FilterHeaderView, self).__init__(Qt.Horizontal, parent)

        self.families = []
        self.empty_filter = QIcon("assets/filter_empty.png")
        self.full_filter = QIcon("assets/filter_full.png")
        self.icon = self.empty_filter
        self.filter_column = 1   # 'family' column
        self.filter_rec = None
        self.selected_filter = None
        self.filterCursor = False

        # Apply the font to the header view
        font = self.font()
        font.setBold(True)               
        self.setFont(font)
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)  

    def setModel(self, model):
        super(FilterHeaderView, self).setModel(model)
        if 'family' in model.df:
            self.families = model.df['family'].unique()

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super(FilterHeaderView, self).paintSection(painter, rect, logicalIndex)
        painter.restore()
        if logicalIndex == self.filter_column and len(self.families) > 1:
            icon_size = 12
            icon_rect = QRect(rect.right() - 20, rect.y() + (rect.height() - icon_size) / 2, icon_size, icon_size)
            self.filter_rec = icon_rect           
            self.icon.paint(painter, icon_rect)                       

    def mousePressEvent(self, event):
        if isinstance(event, QMouseEvent):
            index = self.logicalIndexAt(event.pos())

            # Check if we're
            if self.is_family_detected(index, event.pos()):
                menu = QMenu(self)
                for family in self.families:
                    action = QAction(family, self)
                    action.setCheckable(True)

                    # Check the action if it was previously checked
                    if family == self.selected_filter:
                        action.setChecked(True)
                    action.triggered.connect(lambda checked, family=family: self.filter_function(family, checked))
                    menu.addAction(action)

                menu.exec_(event.globalPos())
                return

        super(FilterHeaderView, self).mousePressEvent(event)

    # Used to change the cursor of the mouse when hovering over the filter icon when present
    def viewportEvent(self, event):        
        if event.type() == QEvent.MouseMove:
            pos = self.mapFromGlobal(QCursor.pos())
            if self.is_family_detected(self.logicalIndexAt(pos), pos):
                self.viewport().setCursor(Qt.PointingHandCursor)
                self.filterCursor = True
            elif self.filterCursor:
                self.viewport().setCursor(Qt.ArrowCursor)
                self.filterCursor = False

        return super(FilterHeaderView, self).viewportEvent(event)

    # is_family
    # Detects if the family filter is present based on the index and position of the cursor
    def is_family_detected(self, index, pos):
        return index == self.filter_column and len(self.families) > 1 and self.filter_rec.contains(pos)

    def filter_function(self, family, checked):
        if checked:
            self.selected_filter = family
            self.icon = self.full_filter
        else:
            self.selected_filter = None
            self.icon = self.empty_filter

        # Update our model based on the filter...
        self.model().apply_filter(self.selected_filter)

        # Repain the view (to reflect changes in the UI)
        self.viewport().update()
        

class DataFrameModel(QAbstractItemModel):
    # Some column names
    EXTENDED_PROPERTIES = 'extendedProperties'
    FAMILY = 'family'
    ACCESSIBILITY = 'accessibility'   

    def __init__(self, df, signal, parent=None):
        super(DataFrameModel, self).__init__(parent)

        self.sorting = False
        self.signal = signal

        # Enhance the data frame to include an 'row count' and 'family'
        df.insert(0, '     #', range(1, len(df) + 1))

        # Check if 'family' column exists in 'result'
        if self.EXTENDED_PROPERTIES in df.columns:
            properties=df[self.EXTENDED_PROPERTIES].apply(pd.Series)
            if self.FAMILY in properties.columns:
                # Insert 'family' column from 'result' into 'df' after the first column
                df.insert(1, self.FAMILY, properties[self.FAMILY])
            else:
                # Insert a column of empty values
                df.insert(1, self.FAMILY, pd.Series([""] * len(df), dtype='object'))

            df.drop(self.EXTENDED_PROPERTIES, axis=1, inplace=True)

        # Update the other columns
        self.rename(df, 'numberOfConstituents', '# constituents')
        self.rename(df, 'organizationCode', 'org code')
        self.rename(df, 'lastModifiedDateTime', 'modified date')
        self.rename(df, 'createdDateTime', 'create date')

        if self.ACCESSIBILITY in df:
            df.drop(self.ACCESSIBILITY, axis=1, inplace=True)

        self.df = df
        self.master_df = df
        self.indexCache = {}

        # Notify data change
        self.signal.dataChanged.emit(self.statusMsg())

    def rename(self, df, col_name1, col_name2):
        if col_name1 in df:
            df.rename(columns={col_name1: col_name2}, inplace=True)

    def rowCount(self, parent=QModelIndex()):
        return len(self.df)

    def columnCount(self, parent=QModelIndex()):
        return len(self.df.columns)

    def index(self, row, column, parent=QModelIndex()):
        if self.hasIndex(row, column, parent):
            if (row, column) not in self.indexCache:
                self.indexCache[(row, column)] = self.createIndex(row, column)
            return self.indexCache[(row, column)]
        else:
            return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self.df.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.df.columns[section]
        return None
    
    def sort(self, column, order):      
        if self.sorting:
            self.layoutAboutToBeChanged.emit()
            self.df = self.df.sort_values(self.df.columns[column], ascending=order == Qt.AscendingOrder)
            self.layoutChanged.emit()

        self.sorting = True

    def statusMsg(self, family=None):
        msg = f"Found a total of {len(self.df)} portfolios"
        if family is not None:
            msg = f'{msg} based on the filter: {family}'
        return msg

    def apply_filter(self, family):
        self.df = self.master_df if family is None else self.master_df[self.master_df[self.FAMILY] == family]

        # Notify the view that the data has changed
        self.layoutChanged.emit()

        # Signal status details of new filtered data
        self.signal.dataChanged.emit(self.statusMsg(family))