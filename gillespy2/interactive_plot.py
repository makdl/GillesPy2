import tkinter as tk
import matplotlib
import time

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
import matplotlib.animation as animation

from matplotlib.figure import Figure
from gillespy2.gillespy2 import *
from gillespy2.gillespySolver import *


def plot_interactive(model, solver):
    results = model.run(solver=solver)
    a = Figure(figsize=(5, 4), dpi=100)
    plot_a = a.add_subplot(111)

    for key in results.keys():
        plot_a.plot(results[key])


    class InteractivePlot(tk.Tk):

        def __init__(self, *args, **kwargs):
            self._running_anim = None
            tk.Tk.__init__(self, *args, **kwargs)
            tk.Tk.wm_title(self, "{} gillespy2 Interactive Model".format(model.name))

            container = tk.Frame(self)
            container.pack(side="top", fill="both", expand=True)
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)

            self.frames = {}

            frame = GraphPage(container, self)
            self.frames[GraphPage] = frame
            frame.grid(row=0, column=0, sticky="nsew")

            self.show_frame(GraphPage)

        def show_frame(self, cont):
            frame = self.frames[cont]
            frame.tkraise()
            frame.canvas.draw_idle()

    class GraphPage(tk.Frame):

        def report_change(self, name, value):
            model.get_species(name).set_population(int(value))
            # model.get_species(name).initial_value = str(value)
            results = model.run(solver=solver)
            a.axes.clear()
            plot_a.clear()
            # a.axes.set_ylim(bottom=min(results, key=results.get), top=max(results, key=results.get))
            for key in results.keys():
                plot_a.plot(results[key])

            a.canvas.draw()
            # print("%s changed to %s" % (name, value))

        def __init__(self, parent, controller):


            tk.Frame.__init__(self, parent)

            canvas = FigureCanvasTkAgg(a, self)
            canvas.show()
            localIndex = 0
            for index, scale in enumerate(model.listOfSpecies.keys()):
                population_parameter = model.get_species(scale).initial_value
                #Ask if this is sane.
                if population_parameter < 100:
                    multiplication_parameter = 100
                else:
                    multiplication_parameter = population_parameter*10
                widget = tk.Scale(self, from_=0, to=multiplication_parameter, orient="horizontal", label=(str(scale)),
                                  command=lambda value, name=scale: self.report_change(name, value))
                widget.pack()
                widget.set(population_parameter)
                widget.grid(row=index, column=0)
                localIndex += 1

            canvas.get_tk_widget().grid(row=0, column=500, columnspan=500, pady=20, padx=10, sticky='nsew')
            self.canvas = canvas


    #
    # class PlotFrame(tk.Frame):
    #     def __init__(self, root):
    #         f = Figure(figsize=(5, 4), dpi=100)
    #         a = f.add_subplot(111)
    #         t = arange(0.0, 3.0, 0.01)
    #         s = sin(2 * pi * t)
    #
    #         a.plot(t, s)
    #
    #         # a tk.DrawingArea
    #         canvas = FigureCanvasTkAgg(f, master=root)
    #         canvas.show()
    #         canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    #
    #         toolbar = NavigationToolbar2TkAgg(canvas, root)
    #         toolbar.update()
    #         canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    #
    #         def on_key_event(event):
    #             print('you pressed %s' % event.key)
    #             key_press_handler(event, canvas, toolbar)
    #
    #         canvas.mpl_connect('key_press_event', on_key_event)
    #
    #         def _quit():
    #             root.quit()  # stops mainloop
    #             root.destroy()  # this is necessary on Windows to prevent
    #             # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    #
    #         button = tk.Button(master=root, text='Quit', command=_quit)
    #         button.pack(side=tk.BOTTOM)

    if __name__ != "__main__":
    #     root = tk.Tk()
    #     SliderFrame(root).pack(side="top", fill="both", expand=True)
    #     PlotFrame(root).pack(side="top", fill="both", expand=True)
        app = InteractivePlot()
        app.geometry("1000x1000")
        app.mainloop()