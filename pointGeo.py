# -*- coding:Utf-8 -*-
'''
Created on 2014-07-17

@author: Simon T-L
'''
#Importer les modules
import utilitaires as UTIL
import math

# Classe: PointGeo
#
# Repr�sente un point defini par ses coordonees geographiques x et y

class PointGeo:
    """Point geographique"""
        
    # constructeur a partir de x et y
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y
        
    # retourne la distance entre ce point et un autre
    def distance(self, point):
        if (self.x == 0 or self.y == 0):
            raise UTIL.ScriptError("Erreur: calcul de distance sur un point non initialisé")
    
        return ((point.x - self.x)**2 + (point.y - self.y)**2)**0.5
    
    # retourne un bool qui dit si le point est valide
    def valide(self):
        if (self.x == 0 or self.y == 0):
            return False
        else:
            return True
        
    # retourne un point qui represente ce point deplace d'un offset donne en coordonnees
    # cartesiennes (x, y)
    def depl_cart(self, x, y):
        if not self.valide():
            raise UTIL.ScriptError("Erreur: calcul de deplacement sur un point non initialisé")
        
        return PointGeo(self.x + x, self.y + y)
    
    # retourne un point qui represente ce point deplace d'un offset donne en coordonnees
    # polaires (r, tetha)
    def depl_pol(self, r, theta):
        if not self.valide():
            raise UTIL.ScriptError("Erreur: calcul de deplacement sur un point non initialisé")
        
        return PointGeo(self.x + (r * math.cos(theta)), self.y + (r * math.sin(theta)))
    
        