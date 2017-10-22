# -*- coding:Utf-8 -*-
'''
Created on 2014-07-18

@author: Simon T-L
'''
#Importer les modules
import utilitaires as UTIL
import math

PI = 3.14159

# Classe: VecteurGeo
#
# Represente un vecteur  qui est une ligne dirigee du point a au point b
class VecteurGeo:
    """Vecteur geographique"""
        
    # constructeur a partir du point de depart et du point d'arrivee
    def __init__(self, a, b):
        self.a = a    # de type PointGeo
        self.b = b    # de type PointGeo
        
    # re-initialise le vecteur a partir de coordonnees polaires
    # Input:
    #    a - point de depart
    #    r - (rayon) la longueur du vecteur
    #    t - (theta) l'angle de deplacement (en radians)
    def init_pol(self, a, r, t):
        self.a = a
        self.b = a.depl_pol(r, t)
    
    # retourne un bool qui dit si le vecteur est valide
    def valide(self):
        if (self.a.valide() and self.b.valide()):
            return True
        else:
            return False
        
    # retourne la longueur du vecteur    
    def longueur(self):
        if not self.valide():
            raise UTIL.ScriptError("Erreur: calcul de longueur sur un vecteur non initialis�")
        
        return self.a.distance(self.b)
    
    # retourne l'angle entre AB et l'axe positif des x (angle conventionel en trigonometrie)
    # l'angle est en radians et est compris entre -PI/2 et PI/2
    def angl_hor(self):
        if not self.valide():
            raise UTIL.ScriptError("Erreur: calcul d'angle sur un vecteur non initialis�")
        
        return math.atan2((self.b.y - self.a.y), (self.b.x - self.a.x))
    
    # retourne l'angle entre 2 vecteurs
    # Input:
    #    cd  - vecteur C � D 
    #
    # Pour trouver l'angle, on d�place CD en C'D', tel que C'=A . On retourne l'angle BAD'.
    # La valeur est comprise entre -PI/2 et PI/2
    def angl_vects(self, cd):
        
        if not self.valide():
            raise UTIL.ScriptError("Erreur: calcul d'angle sur un vecteur non initialis�")
        
        anglHorizAB = self.angl_hor()
        anglHorizCD = cd.angl_hor()
        
        anglBADprime = anglHorizCD - anglHorizAB
        
        # Ramener a une valeur d'angle entre -180 et +180 degres si necessaire
        if anglBADprime > PI:
            anglBADprime = anglBADprime - (2 * PI)
        elif anglBADprime < -1 * PI:
            anglBADprime = anglBADprime + (2 * PI)
            
        return anglBADprime
    
    # Retourne la perpendiculaire qui va de ce vecteur vers le point c fourni
    # retourne aussi un bool qui est vrai si la perpendiculaire debute sur le vecteur
    # et faux si la perpendiculaire debute sur la prolongation du vecteur.
    def perpend(self, c):
        
        if not self.valide():
            raise UTIL.ScriptError("Erreur: calcul de perpendiculaire sur un vecteur non initialis�")
        
        # La perpendiculaire est le cote oppose du triangle rectangle dont AC est l'hypothenuse
        # et AD est le cote adjacent. D est la base de la perpendiculaire, soit la projection 
        # du point C sur la ligne AB ou sa prolongation.
        ac = VecteurGeo(self.a, c)
        angle_DAC = self.angl_vects(ac)  # C'est a dire l'angle BAC
        d = self.a.depl_pol(math.fabs(ac.longueur() * math.cos(angle_DAC)), self.angl_hor())
        ad = VecteurGeo(self.a, d)
        
        # Determiner si D se trouve sur la ligne AB, ou au dela
        if ((angle_DAC > -1 * PI / 2 ) and (angle_DAC < PI / 2 ) and (ad.longueur() < self.longueur())):
            surVecteur = True
        else:
            surVecteur = False
        
        return VecteurGeo(d, c), surVecteur
    
    # Determine si les points C et D sont du meme cote du vecteur
    # Retourne un boolean vrai si du meme cote.
    def du_meme_cote(self, c, d):
        
        if not self.valide():
            raise UTIL.ScriptError("Erreur: calcul de perpendiculaire sur un vecteur non initialis�")
        
        # Creer 2 vecteurs a partir du point A vers C et vers D
        ac = VecteurGeo(self.a, c)
        ad = VecteurGeo(self.a, d)
        angleBAC = self.angl_vects(ac)
        angleBAD = self.angl_vects(ad)
        
        # Si les point sont du meme cote de AB, leur angles auront le meme signe (positif
        # ou negatif). Donc leur multiplication donnera un nombre positif.
        memeCote = angleBAC * angleBAD >= 0
        return memeCote
    
    