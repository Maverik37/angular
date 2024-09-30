import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Menu
from MainApp.classes.consultation import *
from MainApp.classes.ajouts import *

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestionnaire de courses")
        self.geometry("600x600")
        #paramétrage de la page d'acceuil
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        #Liste des frames
        self.frames = {}

        for f in (Prix,Magasin,Produit,AddMagasins):
            name = f.__name__
            frame = f(parent=self.container,controller=self)
            self.frames[name] = frame
            frame.grid(row=0,column=0,sticky="nsew")

        #le menu
        self.menubar = Menu(self)
        #Menu pour la consultation
        menu_consult = Menu(self.menubar,tearoff=0)
        menu_consult.add_command(label="Prix",command=lambda: self.show_frame(page_name="Prix"))
        menu_consult.add_command(label="Magasins",command=lambda:self.show_frame(page_name="Magasin"))
        menu_consult.add_command(label="Produits",command=lambda:self.show_frame(page_name="Produit"))
        #Menu pour l'ajout
        menu_ajout = Menu(self.menubar,tearoff=0)
        menu_ajout.add_command(label="Magasins",command=lambda:self.show_frame(page_name="AddMagasins"))
        menu_ajout.add_command(label="Produits")
        #Ajout dans la barre de menu
        self.menubar.add_cascade(label="Consultation",menu=menu_consult)
        self.menubar.add_cascade(label="Ajouts",menu=menu_ajout)
        #On ajoute le menu dans l'app principale
        self.config(menu=self.menubar)

        #On affiche au démarra=ge la liste des prix
        self.show_frame("Prix")

        print (self.frames)

    def show_frame(self,page_name):

        frame = self.frames[page_name]
        print(page_name)
        frame.tkraise()

MainApp().mainloop()
