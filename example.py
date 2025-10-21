# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET

def update_logger_levels(element, new_level):
    """
    Fonction récursive pour modifier les attributs 'level' des balises <Logger>.

    :param element: Élément XML courant (racine ou enfant)
    :param new_level: Niveau de log à appliquer (ex: 'INFO', 'DEBUG', etc.)
    """
    # Si c'est une balise <Logger>, on modifie son attribut 'level'
    if element.tag == 'Logger':
        element.set('level', new_level)

    # Appel récursif sur les sous-éléments
    for child in element:
        update_logger_levels(child, new_level)

def modify_log4j_levels(xml_path, new_level, output_path=None):
    """
    Modifie récursivement les niveaux de log dans un fichier log4j2.xml

    :param xml_path: Chemin du fichier XML d'entrée
    :param new_level: Nouveau niveau de log à définir
    :param output_path: (Optionnel) Chemin du fichier de sortie
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    update_logger_levels(root, new_level)

    # Sauvegarde (dans le même fichier si output_path est None)
    if not output_path:
        output_path = xml_path

    tree.write(output_path, encoding='utf-8', xml_declaration=True)

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    modify_log4j_levels("log4j2.xml", "WARN")
    print("✅ Tous les niveaux de logger ont été changés en 'WARN'")