# -*- coding:Utf-8 -*-
'''
Created on 2014-07-14

@author: Simon T-L
'''


#Importer les modules
import arcgisscripting
import sys as SYS
import os as OS
import math
import string
import utilitaires as UTIL
from pointGeo import PointGeo
from vecteurGeo import VecteurGeo

#
# Constantes
#
PI = math.pi

# Methode pour trouver la pente de plage
METH_INUTILISE = 0
METH_PERP_SUR_VECTEUR = 1
METH_CENTRE_ANGL_OBTU = 2
METH_BOUT_DE_LIGNE = 3
METH_DERRIERE_LIGNE_POINTS = 4
#
# Variables globales
#

# Pour calculer des statistiques sur les methodes
comptePointsDerrierePolylignePente = int(0)
comptePointsPerpSurVecteur = int(0)
comptePointsAuBoutLignePente = int(0)
comptePointDansAngleObtu = int(0)


# ---------------------------------------------------------------------------------------------------------
# Fonctions
# ---------------------------------------------------------------------------------------------------------

# Obtenir les parametres du script
# Paramètres tirés de argv[]:
# 1 - Le fichier de points de la pente de plage
# 2 - Le fichier de points pour la position relative de l'eau
# 3 - Le fichier raster des images classifiées
# 4 - La liste des classes définies comme du pied de glace (séparées par un ":")
# 5 - l'altitude estimée de la surface supérieure du pied de glace
# 6 - l'angle de pente (vers le bas) du haut du pied de glace en s'eloignant de la cote (en degres)
#
# Résultat: un objet contenant les paramètres extraits
#
def obtenir_les_parms():
    try:
        pointsPlageFC = gp.GetParameterAsText(0)
        pointsPositionnementEauFC = gp.GetParameterAsText(1)
        rasterClassesPdgFC = gp.GetParameterAsText(2)
        listeClassesStr = gp.GetParameterAsText(3)
        altiPlafondPdg = gp.GetParameter(4)
        pentePlafondPdg = gp.GetParameter(5) 
        
    except:
        gp.AddError("Erreur: paramètres défectueux")
        raise UTIL.ScriptError()
    
    # Séparer les classes et vérifier si elles sont un nombre valide
    listeClasses = [int(cl) for cl in listeClassesStr.split(":")]
    for classe in listeClasses:
        if classe < 0 or classe > 8:
            gp.addError("Erreur: liste de classes invalide")
            raise UTIL.ScriptError()
    
    # Créer un objet générique contenant les paramètres
    try:
        obj = UTIL.Gen()
        obj.add('pointsPenteFc', pointsPlageFC)
        obj.add('pointsPositEauFC', pointsPositionnementEauFC)
        obj.add('rasterClassesFc', rasterClassesPdgFC)
        obj.add('listeClasses', listeClasses)
        obj.add('altPlafondMaxPdg', float(altiPlafondPdg))
        obj.add('pentePlafondPdg', float(pentePlafondPdg) / 180 * PI )  # convertir en radians
    except:
        gp.AddError("Erreur: problème de création de l'objet des arguments")
        raise UTIL.ScriptError()
    
    return obj

# Convertir le raster du pied de glace classifié en feature set (shapefile) de points.
# C'est n�cessaire, car on ne peut pas it�rer un raster.    
def convertir_raster_en_points():
    try:
        repertoire = OS.path.dirname(parm.rasterClassesFc)
        nomRasterFC = OS.path.basename(parm.rasterClassesFc).split('.')[0]
        pointsClassesFC = repertoire + "\\" + nomRasterFC + "_points.shp"
        
        #if OS.path.isfile(pointsClassesFC):
        #    OS.remove(pointsClassesFC)
            
        if gp.CheckExtension("spatial") == "Available":
            gp.CheckOutExtension("spatial")
        else:
            raise "LicenseError"
        
        gp.RasterToPoint_conversion(parm.rasterClassesFc, pointsClassesFC)
        gp.CheckInExtension("spatial")
        
    except arcgisscripting.ExecuteError:
        msg=gp.GetMessages(2)
        gp.AddError(msg)
     
    except:
        gp.CheckInExtension("spatial")
        gp.AddMessage("Erreur: problème de création du feature class de points à partir du raster")
        #raise ERROR.ScriptError()
        
    return pointsClassesFC

#
# ecrire des messages de resultat
#
def gen_msg_resultat():
    
    # Créer le message contenant plusieures lignes
    msg = "\n\n"
    msg = msg + "-----------------------------------------------------------------------------------------------------------\n"
    msg = msg + "\n"
    msg = msg + "   Volume total du pied de glace: " + str(volumeTotalPdg) + " (m3)\n"
    msg = msg + "\n"
    msg = msg + "      Altitude max choisie: " + str(parm.altPlafondMaxPdg) + "\n"
    msg = msg + "      Angle de pente du pdg choisi: " + str(parm.pentePlafondPdg * 180 / PI) + "\n"
    msg = msg + "-----------------------------------------------------------------------------------------------------------\n"
    msg = msg + "   Largeur cellule: " + str(largeurCellule) + ", hauteur cellule: " + str(hautCellule) + " (m)\n"
    msg = msg + "   Surface cellule: " + str(surfCellule) + " (m2)\n"
    msg = msg + "-----------------------------------------------------------------------------------------------------------\n"
    msg = msg + "   Statistiques de couverture du pied de glace:\n"
    msg = msg + "   \n"
    msg = msg + "                      nombre cell      % couverture       surface (m2)\n"
    msg = msg + "                      -----------      ------------       ------------\n"
    msg = msg + "   \n"
    for classe in parm.listeClasses:
        ncl = int(compteCellParClasse[classe])
        pcv = float(ncl) / float(nombrePointsClasse) * 100
        sfc = int(ncl * surfCellule)
        msg = msg + "     classe %d       %11d      %12.2f       %12d\n" % tuple([classe, ncl, pcv, sfc])
    ncl = compteCellPdg
    pcv = float(ncl) / float(nombrePointsClasse) * 100
    sfc = int(ncl * surfCellule)
    msg = msg + "   TOT pied de glace%11d      %12.2f       %12d\n" % tuple([ncl, pcv, sfc])
    msg = msg + "   \n"
    ncl = nombrePointsClasse
    sfc = int(ncl * surfCellule)
    msg = msg + "   MAX possible     %11d                         %12d\n" % tuple([ncl, sfc])
    msg = msg + "   \n"
    msg = msg + "-----------------------------------------------------------------------------------------------------------\n"
    msg = msg + "   \n"
    msg = msg + "   Statistiques de methode de calcul de l'altitude des cellules contenant du pied de glace:\n"
    msg = msg + "   \n"
    msg = msg + "                                     nombre cell      % des cell      \n"
    msg = msg + "                                     -----------      ------------    \n"
    msg = msg + "   \n"
    ncl = int(comptePointsPerpSurVecteur)
    pcv = float(ncl) / float(compteCellPdg) * 100
    msg = msg + "  Perpendiculaire donne sur ligne points %5d      %11.2f\n" % tuple([ncl, pcv])
    ncl = int(comptePointDansAngleObtu)
    pcv = float(ncl) / float(compteCellPdg) * 100
    msg = msg + "  Au centre d'un angle obtu sur lgn pts  %5d      %11.2f\n" % tuple([ncl, pcv])
    ncl = int(comptePointsAuBoutLignePente)
    pcv = float(ncl) / float(compteCellPdg) * 100
    msg = msg + "  Au bout d'une ligne de points          %5d      %11.2f\n" % tuple([ncl, pcv])
    ncl = int(comptePointsDerrierePolylignePente)
    pcv = float(ncl) / float(compteCellPdg) * 100
    msg = msg + "  Derriere ligne de points, selon l'eau  %5d      %11.2f\n" % tuple([ncl, pcv])
    msg = msg + "   \n"
    msg = msg + "   \n"
   
#msg = msg + "   \n"
    
    # Ecrire le message sur le service de messages de ArcGIS
    try:
        for ligne in msg.split('\n'):
            gp.AddMessage(ligne)
    except:
        pass
    
    # Ecrire le message a standard output, en cas d'execution hors de ArcGIS
    print(msg)
    
    # Et ecrire dans un fichier pour ne pas perdre les resultats
    repertoire = OS.path.dirname(parm.rasterClassesFc)
    nomRasterFC = OS.path.basename(parm.rasterClassesFc).split('.')[0]
    nomFichierOutput = repertoire + "\\" + nomRasterFC + "_resultats.txt"
    fichierOutput = open(nomFichierOutput, 'w' )
    fichierOutput.write(msg)
    fichierOutput.close()
    
    return

# Recherche dans un feature class de points les trois points les plus rapprochés
# du point de référence passé comme paramètre et les retourne.
#
# Input:
#    (str) - nom du feature class de points à rechercher
#    (PointGeo) - position du point de référence
#
# Output:
#    (PointGeo) - point le plus pres
#    (int)      - champ FID du point le plus pres
#    (PointGeo) - deuxieme point le plus pres
#    (int)      - champ FID du deuxieme point le plus pres
#    (PointGeo) - troisieme point le plus pres
#    (int)      - champ FID du troisieme point le plus pres
def trois_points_plus_proche_dans_FC(fcPoints, pointRef):
    
    ppPoint1 = PointGeo(0,0)
    distPoint1 = 999999999.0
    fidPoint1 = 0
    ppPoint2 = PointGeo(0,0)
    distPoint2 = 999999999.9
    fidPoint2 = 0
    distPoint3 = 999999999.9
    fidPoint3 = 0
   
    # Iterer sur le shapefile de points en utilidant un curseur "Search", car on lit seulement. 
    curseur = gp.SearchCursor(fcPoints)
    ligne = curseur.Next()
    while ligne :
           
        # Extraire les coordonees geometriques du point (en unitéés UTM, c. a d. en metres)
        descripteurGeo = ligne.GetValue(pointShapeFieldName)
        geoPoint = descripteurGeo.GetPart()
        point = PointGeo(geoPoint.X, geoPoint.Y)
        
        # Extraire le champ FID qui permet d'identifier le point
        fid = ligne.FID
        
        # Calculer la distance de ce point avec notre reference
        dist = pointRef.distance(point)
        
        # Si ce point bat notre point le plus proche deja trouve
        if dist < distPoint1:
            distPoint3 = distPoint2  # se fait bumper en 3eme position
            ppPoint3 = ppPoint2
            fidPoint3 = fidPoint2
            distPoint2 = distPoint1  # se fait bumper en 2eme position
            ppPoint2 = ppPoint1
            fidPoint2 = fidPoint1
            distPoint1 = dist
            ppPoint1 = point
            fidPoint1 = fid
        # Sinon, s'il bat le deuxieme point deja trouve    
        elif dist < distPoint2:
            distPoint3 = distPoint2  # se fait bumper en 3eme position
            ppPoint3 = ppPoint2
            fidPoint3 = fidPoint2
            distPoint2 = dist
            ppPoint2 = point
            fidPoint2 = fid
        # Sinon, s'il bat le troisieme point deja trouve    
        elif dist < distPoint3:
            distPoint3 = dist
            ppPoint3 = point
            fidPoint3 = fid
            
        ligne = curseur.Next()    

    del curseur
    del ligne
    
    return ppPoint1, fidPoint1, ppPoint2, fidPoint2, ppPoint3, fidPoint3

# Calcule le vecteur de pente vers le point à partir des points de pentes les plus pres.
# Le vecteur retourne represente la pente de la plage a partir d'un point de depart
# sur la polyligne des points de pentes vers le point de glace. En plus du vecteur
# la fonction retourne la pente a appliquer et l'altitude de depart du vecteur. 
#
# Input:
#    (PointGeo) - position du point a calculer
#    (PointGeo) - point de pente le plus pres
#    (int)      - champ FID du point de pente le plus pres
#    (PointGeo) - deuxieme point de pente le plus pres
#    (int)      - champ FID du deuxieme point de pente le plus pres
#    (PointGeo) - troisieme point de pente le plus pres
#    (int)      - champ FID du troisieme point de pente le plus pres
#
# Output:
#    (VecteurGeo) - Le vecteur de pente de plage menant au point a calculer
#    (float) - altitude de depart du vecteur de pente de plage
#    (float) - pente a appliquer sur le vecteur de pente de plage
#    (int)   - methode utilisee pour trouver le vecteur de pente de plage
def calcul_vecteur_de_pente_selon_pts_pente(point, pPente1, fidPente1, \
                                            pPente2, fidPente2, pPente3, fidPente3):

    try:
        # Extraire les informations des trois points en faisant une recherche à partir de leur FID
        curseur = gp.SearchCursor(parm.pointsPenteFc, '"FID" = ' + str(fidPente1))
        ligne = curseur.Next()
        altitudePoint1 = ligne.z_LR
        anglePentePoint1 = ligne.P_regressi / 360 * 2 * PI  # Pente en degre convertie en radians
        del curseur
        
        curseur = gp.SearchCursor(parm.pointsPenteFc, '"FID" = ' + str(fidPente2))
        ligne = curseur.Next()
        altitudePoint2 = ligne.z_LR
        anglePentePoint2 = ligne.P_regressi / 360 * 2 * PI
        del curseur

        curseur = gp.SearchCursor(parm.pointsPenteFc, '"FID" = ' + str(fidPente3))
        ligne = curseur.Next()
        altitudePoint3 = ligne.z_LR
        anglePentePoint3 = ligne.P_regressi / 360 * 2 * PI
        del curseur

    except:
        msg="Erreur: impossible de lire les infos de point de pente selectioné par FID. Msg gp: " + gp.GetMessages(2)
        gp.AddError(msg)
        raise UTIL.ScriptError()
    
    # Faire un vecteur avec les deux points de la polyligne de pente les plus pres et un
    # autre avec le point le plus pres et le troisieme point
    vectPointsPenteRaproches12 = VecteurGeo(pPente1, pPente2)
    vectPointsPenteRaproches13 = VecteurGeo(pPente1, pPente3)
        
    # Trouver la ou les perpendiculaire allant des deux vecteur precedents au point desire
    perpendiculaire12, perp12SurVecteur = vectPointsPenteRaproches12.perpend(point)
    perpendiculaire13, perp13SurVecteur = vectPointsPenteRaproches13.perpend(point)
    
    # Il y a quatres possibilitees, selon que les perpendiculaires partent sur les vecteurs
    # ou sur leur prolongation
    if perp12SurVecteur:
        if not perp13SurVecteur:
            # C'est le cas le plus habituel.
            # La projection du point sur la polyligne des points de pente, arrive quelque
            # part entre le point1 et le point2. On utilisera la moyenne ponderee des
            # des informations de pente des deux points.
            # Pour cela, creer un vecteur du point le plus pres vers la base de la perpendiculaire
            vecteurAdjacent = VecteurGeo(pPente1, perpendiculaire12.a)
            methode = METH_PERP_SUR_VECTEUR
        
        else:
            # Le point se trouve au centre de la rencontre de deux vecteur de points, du cote
            # de l'angle aigu. Il y a donc deux perpendiculaires, on choisit la plus courte.
            if perpendiculaire12.longueur() <= perpendiculaire13.longueur():
                vecteurAdjacent = VecteurGeo(pPente1, perpendiculaire12.a)
            else:
                vecteurAdjacent = VecteurGeo(pPente1, perpendiculaire13.a)
            methode = METH_PERP_SUR_VECTEUR

    else:
        if perp13SurVecteur:
            # Bien que le point se trouve plus pres du point2 que du 3, il est perpendiculaire 
            # avec un point sur la ligne entre le point 1 et le point 3. C'est donc
            # cette ligne que l'on choisira.
            vecteurAdjacent = VecteurGeo(pPente1, perpendiculaire13.a)
            methode = METH_PERP_SUR_VECTEUR
            
        else:
            # Aucune perpendiculaire ne touche un vecteur. Le point se trouve soit:
            # a) pres du centre, du cote obtu de l'angle forme par les deux vecteurs
            # b) a l'extremite de la polyligne de points de pente ou dans une
            #    coupure de cette polyligne; le point 3 se trouvant derriere le point 2
            # Les meillleurs resultats seront obtenus en ne tenant compte que du point
            # de pente le plus pres. On cree un vecteur adjacant de longueur nulle.
            vecteurAdjacent = VecteurGeo(pPente1, pPente1)
            
            # On tente de distinguer le cas a) du b), pour tenir des statistiques
            vect2 = VecteurGeo(point, pPente2)
            vect3 = VecteurGeo(point, pPente3)
            anglePoint2EtPoints3 = vect2.angl_vects(vect3)
            if anglePoint2EtPoints3 < (PI / 4) and anglePoint2EtPoints3 > (-1 * PI / 4):
                methode = METH_BOUT_DE_LIGNE
            else:
                methode = METH_CENTRE_ANGL_OBTU
                   
    # Si le vecteur adjacent n'a pas de longueur, alors on ne pondere pas avec un 2eme point
    if vecteurAdjacent.longueur() == 0:
        # On utilisera seulement le point1 (le plus pres) pour obtenir les informations
        # de pente.
        altDepartPlage = altitudePoint1
        anglePentePlage = anglePentePoint1
        vectPointsPenteRaproches = vectPointsPenteRaproches12 # Seulement utilise pour comparaison avec eau
        
    else:
        # La projection du point sur la polyligne des points de pente, arrive quelque
        # part sur un des vecteurs. On utilisera la moyenne ponderee des
        # des informations de pente des deux points du vecteur.
        
        # Pour savoir quel point utiliser comme point eloigne, voir dans quelle direction
        # pointe le vecteur adjacent. Comme c'Est des floats et qu'on fait une operation
        # trigonometrique pour trouver l'angle, on aloue une marge d'erreur dans la
        # comparaison.
        if math.fabs(vecteurAdjacent.angl_hor() - vectPointsPenteRaproches12.angl_hor()) < 0.01:
            vectPointsPenteRaproches = vectPointsPenteRaproches12
            altitudePointEloigne = altitudePoint2
            anglePentePointEloigne = anglePentePoint2
        else:
            vectPointsPenteRaproches = vectPointsPenteRaproches13
            altitudePointEloigne = altitudePoint3
            anglePentePointEloigne = anglePentePoint3

        # Calculons les facteurs a associer a chaque point base sur la distance
        # de la base de la perpendiculaire jusqu'au point1.
        # Noter: fact1 + fact2 = 1
        fact1 = (vectPointsPenteRaproches.longueur() - vecteurAdjacent.longueur()) / vectPointsPenteRaproches.longueur() 
        fact2 = vecteurAdjacent.longueur() / vectPointsPenteRaproches.longueur()
        
        # Et appliquons les facteurs aux altitudes et aux pentes
        altDepartPlage = (fact1 * altitudePoint1) + (fact2 * altitudePointEloigne)
        anglePentePlage = (fact1 * anglePentePoint1) + (fact2 * anglePentePointEloigne)
    
    # La pente obtenue des points de pente n'est evidemment valide que si notre point
    # se trouve du cote de l'eau, par rapport au vecteur des points de pente.
    # Pour faire cette verification on utilisera un shapefile de points de positionnement
    # de l'eau. On commence par trouver le points dans l'eau le plus pres; les deuxieme
    # et troisieme points sont ignores.
    pEau1, fidEau1, pEau2, fidEau2, pEau3, fidEau3 = trois_points_plus_proche_dans_FC(parm.pointsPositEauFC, point)
    
    # Si le point du pied de glace a calculer n'est pas du meme cote du vecteur des
    # points de pente que le point de positionnement de l'eau. Il n'est pas sur la plage pentue.
    if (not vectPointsPenteRaproches.du_meme_cote(point, pEau1)):
        # Il est acceptable d'assumer que la plage est horizontale derriere la polyligne
        # des points de pente (du haut de plage). Donc, retourner un vecteur de pente de plage
        # de longeur nulle.
        vecteurPentePlage = VecteurGeo(vecteurAdjacent.b, vecteurAdjacent.b)
        methode = METH_DERRIERE_LIGNE_POINTS
    
    else:
        # Le point se trouve du cote de l'eau; soit le cas normal
        vecteurPentePlage = VecteurGeo(vecteurAdjacent.b, point)
        
        # Une derniere exception: si le point se trouve au bout d'une
        # ligne de points de pente, soit dans une region pas couverte
        # par les profils de pente; arreter de calculer la descente de
        # pente apres huit largeurs de cellules
        if methode == METH_BOUT_DE_LIGNE and \
            vecteurPentePlage.longueur() > (largeurCellule * 8):
            vecteurPentePlage = VecteurGeo(pPente1, pPente1)
        
    return vecteurPentePlage, altDepartPlage, anglePentePlage, methode
    

# Calcule l'altitude (au sol) du point à partir des points de pentes les plus pres et la hauteur de pied de glace
#
# Input:
#    (PointGeo) - position du point a calculer
#    (bool)     - vrai si le point est classé comme du pied de glace
#    (PointGeo) - point de pente le plus pres
#    (int)      - champ FID du point de pente le plus pres
#    (PointGeo) - deuxieme point de pente le plus pres
#    (int)      - champ FID du deuxieme point de pente le plus pres
#    (PointGeo) - troisieme point de pente le plus pres
#    (int)      - champ FID du troisieme point de pente le plus pres
#
# Output:
#    (float) - altitude du sol au point
#    (float) - hauteur de la glace au point
#    (int)   - methode utilisee pour trouver le vecteur de pente de plage
def calcul_altitude_point_et_haut_glace_selon_pts_pente(point, estPdg, pPente1, fidPente1, \
                                                        pPente2, fidPente2, pPente3, fidPente3):

    global comptePointsDerrierePolylignePente
    global comptePointsPerpSurVecteur
    global comptePointsAuBoutLignePente
    global comptePointDansAngleObtu
    
    # Obtenir le vecteur qui va d'un point sur la polyligne des points de pente vers
    # notre point. Ce vecteur suit la plage. On l'apelle la perpendiculaire meme si dans 
    # certaines conditions, il n'est pas vraiment perpendiculaire a la ligne des points de pente.
    perpendiculaire, altDepartPerpend, anglePentePerpend, methode = \
        calcul_vecteur_de_pente_selon_pts_pente(point, pPente1, fidPente1, pPente2, fidPente2, pPente3, fidPente3)
    
    # On peut maintenant calculer l'altitude (au sol) du point
    altitudePoint = altDepartPerpend - (perpendiculaire.longueur() * math.tan(anglePentePerpend))
    
    # Si c'est un point contenant de la glace, calculer la hauteur du pied de glace a ce point
    if estPdg:
        # Si l'altitude du point est plus haute que le point le plus haut
        # atteint par le pied de glace
        if altitudePoint >= parm.altPlafondMaxPdg:
            hauteurPiedDeGlaceAuPoint = 0
        else:
            # Calculons la hauteur du pied de glace; en tenant compte de la
            # pente negative du plafond du pied de glace. Cette pente negative
            # ne commence qu'au point le plus haut du pied de glace (pas a la base
            # de la perpendiculaire). Cela explique la formule suivante.
            altitudePlafondPiedDeGlaceAuPoint = parm.altPlafondMaxPdg - ( perpendiculaire.longueur() - \
                (altDepartPerpend - parm.altPlafondMaxPdg) / math.tan(anglePentePerpend) ) * \
                math.tan(parm.pentePlafondPdg)
            
            hauteurPiedDeGlaceAuPoint = altitudePlafondPiedDeGlaceAuPoint - altitudePoint
    else:
        hauteurPiedDeGlaceAuPoint = 0
        methode = METH_INUTILISE
        
    # Ajustons les statistiques pour la methode utilisee
    if methode == METH_PERP_SUR_VECTEUR:
        comptePointsPerpSurVecteur += 1
    elif methode == METH_BOUT_DE_LIGNE:
        comptePointsAuBoutLignePente += 1
    elif methode == METH_CENTRE_ANGL_OBTU:
        comptePointDansAngleObtu += 1
    elif methode == METH_DERRIERE_LIGNE_POINTS:
        comptePointsDerrierePolylignePente += 1
    # On ne compte pas si ce n'est pas un point de glace
           
    return altitudePoint, hauteurPiedDeGlaceAuPoint, methode

# ---------------------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # Cr�er l'objet de g�oprocessing d'ArcGIS
    gp = arcgisscripting.create(9.3)
    
    parm = obtenir_les_parms()
    
    # Initialiser les variables globales de resultats
    compteCellParClasse = {}
    for classe in parm.listeClasses:
        compteCellParClasse[classe] = 0
    compteCellPdg = 0
    
    volumeTotalPdg = 0
    
    # Configurer le geoprocesseur
    # gp.XYResolution = resolution = 0.002  # 2 millimetres
    gp.OverwriteOutput=1    # Permet d'écrire par dessus un vieux fichier

    # Extraire des infos sur le fichier raster
    try:
        propRaster = gp.Describe(parm.rasterClassesFc)
        nombreCellHoriz = propRaster.Width 
        nombreCellVert = propRaster.Height 
        # Les deux lignes suivantes donnaient des valeurs 50 cm inférieures à la distance
        # entre les points de centre de raster mesurés avec ArcMap!
        # Donc on utilise une valeur pre-definie pour les dimensions de cellules
        largeurCellule = propRaster.MeanCellWidth
        hautCellule = propRaster.MeanCellHeight
        #largeurCellule = 8.0
        #hautCellule = 8.0
        surfCellule = largeurCellule * hautCellule 
    except:
        gp.AddError("Erreur: impossible de lire les propriétés du raster")
        raise UTIL.ScriptError()
        
    # Convertir le raster en shapefile de points, pour pouvoir l'iterer
    pointsClassesFS = convertir_raster_en_points()
    
    # Obtenir les infos du shapefile de points
    try:
        propPoints = gp.Describe(pointsClassesFS)
        pointShapeFieldName = propPoints.ShapeFieldName
        
        resultat = gp.GetCount(pointsClassesFS)
        nombrePointsClasse = int(resultat.GetOutput(0))
    except:
        gp.AddError("Erreur: impossible de lire les propriétés du shapefile point representant le raster")
        raise UTIL.ScriptError()

    # Rajouter des champs dans la table des points classifies
    try:
        gp.addfield(pointsClassesFS, "Z_sol", "FLOAT", 6, 3)       # Altitude du sol calculee
        gp.addfield(pointsClassesFS, "Epais_pdg", "FLOAT", 6, 3)   # Epaisseur (hauteur) du pied de glace        
        gp.addfield(pointsClassesFS, "Meth_cal_Z", "SHORT", 2, 0)   # Methode utilisee pour determiner l'altitude du point        
    except arcgisscripting.ExecuteError:
        msg=gp.GetMessages(2)
        gp.AddError(msg)
        raise UTIL.ScriptError(msg)
    
    # Iterer sur le shapefile de points en utilidant un curseur "Update", car on va modifier. 
    # Accompagner cette iteration d'une barre de progression (Progressor) qui apparait a l'ecran
    curseurPointsClasse = gp.UpdateCursor(pointsClassesFS)
    gp.SetProgressor("step", "Calcul de la hauteur du pied de glace pour chaque cellule du raster...", 0, nombrePointsClasse, 1)
    lignePointClasse = curseurPointsClasse.Next()
    while lignePointClasse :
        # Ceci est une nouvelle cellule du raster
        
        # Obtenir la classification du point; elle a ete mise dans le champ GRID_CODE
        classe = int(lignePointClasse.GetValue('GRID_CODE'))
        
        # Est-ce une des classes qui constituent le pied de glace
        estPdg = False
        for classePdg in parm.listeClasses:
            if classe == classePdg:
                estPdg = True
                compteCellParClasse[classe] = compteCellParClasse[classe] + 1
                compteCellPdg = compteCellPdg + 1              
           
        # Extraire les coordonees geometriques du point (en unitéés UTM, c. a d. en metres)
        descripteurGeo = lignePointClasse.GetValue(pointShapeFieldName)
        geoPoint = descripteurGeo.GetPart()
        
        # Construire un objet de notre classe PointGeo avec les coordonnées
        point = PointGeo(geoPoint.X, geoPoint.Y)
        
        # Trouver les points de reference de pente les plus proches
        pPente1, fidPente1, pPente2, fidPente2, pPente3, fidPente3 = trois_points_plus_proche_dans_FC(parm.pointsPenteFc, point)
        
        # Calculer l'altitude de la plage et la hauteur du pied de glace a cet emplacement.
        # La fonction retourne une hauteur nulle de glace si estPdg est faux.
        alt_point, hautPiedDeGlaceAuPoint, methode = \
           calcul_altitude_point_et_haut_glace_selon_pts_pente(point, estPdg, pPente1, fidPente1, pPente2, fidPente2, pPente3, fidPente3)

        # Enregistrer ces infos dans le shapefile de points, pour verification
        try:
            lignePointClasse.Z_sol = alt_point
            lignePointClasse.Epais_pdg = hautPiedDeGlaceAuPoint
            lignePointClasse.Meth_cal_Z = methode
        except arcgisscripting.ExecuteError:
            msg=gp.GetMessages(2)
            gp.AddError(msg)
            raise UTIL.ScriptError(msg)

        # Si c'est du pied de glace
        if estPdg:
            
            # Ajoutons le volume de cette glace sur toute la surface de la cellule au
            # volume total
            vCell = hautPiedDeGlaceAuPoint * surfCellule
            volumeTotalPdg += vCell
            
        # Enregistrer les changements de la ligne et passer a la suivante
        curseurPointsClasse.UpdateRow(lignePointClasse)
        lignePointClasse = curseurPointsClasse.Next()
        gp.SetProgressorPosition()
        # Fin de l'itération sur lignePointClasse
    
    del lignePointClasse
    del curseurPointsClasse

    gen_msg_resultat()