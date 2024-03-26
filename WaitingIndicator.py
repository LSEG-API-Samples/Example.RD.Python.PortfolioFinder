import tkinter as tk

class WaitingIndicator(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bg='white')

        self.canvas = tk.Canvas(self, width=100, height=100, bg='white', highlightthickness=0)
        self.canvas.pack()

        self.circles = [self.canvas.create_oval(10 + 30*i, 10, 30 + 30*i, 30, fill='white') for i in range(3)]

        self.current_circle = 0
        
        # Flag to control animation
        self.is_animating = False
        

    def animate(self):
        if not self.is_animating:
            return
        
        # Make all circles white
        for circle in self.circles:
            self.canvas.itemconfig(circle, fill='white')

        # Make the current circle red
        self.canvas.itemconfig(self.circles[self.current_circle], fill='blue')

        # Move to the next circle
        self.current_circle = (self.current_circle + 1) % 3

        # Schedule the next animation frame
        self.after(500, self.animate)

    def displayIndicator(self):
        self.is_animating = True
        self.animate()
        self.canvas.pack()

    def hideIndicator(self):
        self.is_animating = False
        self.canvas.pack_forget()
        