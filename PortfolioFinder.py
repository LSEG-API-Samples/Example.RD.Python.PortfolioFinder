import sys
import qasync, asyncio
from PySide6.QtWidgets import QApplication
from finder.app import Window

# Used when starting from generated executable to control splash screen
try:
    import pyi_splash
except ImportError:
    pass

if __name__ == "__main__":   
    app = QApplication(sys.argv)

	# Kill the splash screen (start via pyinstaller)
    try:
        pyi_splash.close()
    except NameError:
        pass    

    # In order for our application to async/await and run coroutines alongside Qt,
    # we need to create a specific QEventLoop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)  # Set the event loop for asyncio

    # Create and show the main window
    window = Window(loop)   
    window.show()

    # Populate the display with the users portfolios (default)
    window.initialize()

    with loop:
        sys.exit(loop.run_forever())
