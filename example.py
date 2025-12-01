8# -*- coding: utf-8 -*-
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

from collections import OrderedDict
from django.db.models import OuterRef, Subquery, Max
from .models import Contexte, SuiviInstall

def get_cartographie():
    cartographie = OrderedDict()

    # 🔁 Parcours de toutes les catégories définies dans le modèle Contexte
    for code, label in Contexte.CATEGORY:
        latest_version = (
            SuiviInstall.objects.filter(
                su_contexte__c_category=code,
                su_contexte=OuterRef('su_contexte_id'),
                su_statut__in=[14, 12, 2, 11],
                su_lots=OuterRef('su_lots'),
            )
            .values('su_lots')
            .annotate(max_version=Max('su_lots__l_version'))
            .values('max_version')[:1]
        )

        queryset = (
            SuiviInstall.su_lots.through.objects.filter(
                suiviinstall__su_statut__in=[14, 12, 2, 11]
            )
            .annotate(last_version=Subquery(latest_version))
            .filter(suiviinstall__su_contexte__c_category=code)
            .select_related(
                'suiviinstall__su_contexte',
                'suiviinstall__su_lots',
                'suiviinstall__su_statut',
                'suiviinstall__su_mantis',
            )
            .values(
                'suiviinstall__su_contexte__c_name',
                'lot__l_name',
                'lot_version',
                'suiviinstall__su_delivery_date',
                'suiviinstall__su_mantis',
                'suiviinstall__su_statut__s_name',
            )
            .order_by('suiviinstall__su_contexte__c_name', 'lot__l_name')
        )

        # 📦 Construction de la cartographie pour cette catégorie
        for key in queryset:
            contexte_name = key["suiviinstall__su_contexte__c_name"]
            lot_name = key["lot__l_name"]
            version = key["lot_version"]

            # On initialise le contexte s’il n’existe pas encore
            if contexte_name not in cartographie:
                cartographie[contexte_name] = OrderedDict()

            # On garde la version la plus haute
            if (
                lot_name not in cartographie[contexte_name]
                or version > cartographie[contexte_name][lot_name]["Version"]
            ):
                cartographie[contexte_name][lot_name] = {
                    "Version": version,
                    "Categorie": label,
                    "Statut": key["suiviinstall__su_statut__s_name"],
                    "Date_install": key["suiviinstall__su_delivery_date"],
                    "Mantis": key["suiviinstall__su_mantis"],
                }

    return cartographie



№########

from django.db import models
from datetime import datetime
import locale

# Force la locale française pour les noms de mois
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    # Sur Windows ou serveurs sans locale FR, on peut gérer manuellement
    pass

class MonthYearField(models.CharField):
    """
    Champ personnalisé pour stocker YYYY-MM
    et afficher Mois Année en français (ex: 'Novembre 2025')
    """
    description = "Champ mois-année au format texte (YYYY-MM)"

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 7  # ex: "2025-11"
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """Convertit la valeur DB en texte affichable"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m")
        # Si c’est une chaîne '2025-11' → 'Novembre 2025'
        try:
            date_obj = datetime.strptime(value, "%Y-%m")
            return date_obj.strftime("%B %Y").capitalize()
        except ValueError:
            return value

    def get_prep_value(self, value):
        """Avant d’enregistrer, on convertit 'Novembre 2025' en '2025-11'"""
        if not value:
            return None
        # Si déjà au bon format, on laisse
        if isinstance(value, str) and len(value) == 7 and "-" in value:
            return value
        # Conversion du texte français → format YYYY-MM
        try:
            date_obj = datetime.strptime(value, "%B %Y")
            return date_obj.strftime("%Y-%m")
        except ValueError:
            return value


####
qs = (
    SuiviInstall.objects.filter(
        su_statut__s_name__in=["Terminé", "Validation à cadrer"],
        su_delivery_date__isnull=False,
        su_desired_delivery_date__isnull=False,
    )
    .annotate(
        mois=TruncMonth("su_delivery_date"),
        desired_date=TruncDate("su_desired_delivery_date"),
        real_date=TruncDate("su_delivery_date"),
    )
    .annotate(
        dans_delai=Count(
            Case(When(desired_date__gte=F("real_date"), then=1)),
            output_field=IntegerField(),
        ),
        hors_delai=Count(
            Case(When(real_date__gt=F("desired_date"), then=1)),
            output_field=IntegerField(),
        ),
        tickets_hors_delai=ArrayAgg(
            "su_mantis",
            filter=Q(real_date__gt=F("desired_date"))
        )
    )
    .values("mois", "dans_delai", "hors_delai", "tickets_hors_delai")
    .order_by("mois")
)


#######
from django.db.models import Count, Q, F
from django.db.models.functions import TruncMonth

from django.db.models import Count, Q, F
from django.db.models.functions import TruncMonth

def get_installations_stats():
    """
    Retourne un dictionnaire des installations par mois :
    {
        '2025-01': {'ok': 12, 'ko': 3, 'tickets_ko': [1234, 1237, 1240]},
        '2025-02': {'ok': 9,  'ko': 1, 'tickets_ko': [1302]},
        ...
    }
    """
    from .models import SuiviInstallation  # adapte selon ton modèle

    # Filtrage principal : statuts terminés ou à cartographier
    queryset = SuiviInstallation.objects.filter(
        su_statut__in=["Terminé", "Validation à cartographier"],
        su_delivery_date__isnull=False,
        su_desired_delivery_date__isnull=False
    )

    # Agrégation mensuelle de base
    stats = (
        queryset
        .annotate(month=TruncMonth("su_delivery_date"))
        .values("month")
        .annotate(
            ok=Count("id", filter=Q(su_delivery_date__lte=F("su_desired_delivery_date"))),
            ko=Count("id", filter=Q(su_delivery_date__gt=F("su_desired_delivery_date"))),
        )
        .order_by("month")
    )

    # Transformation en dictionnaire
    results = {}

    for s in stats:
        month = s["month"]
        month_key = month.strftime("%Y-%m")

        # Récupération des tickets hors délai pour ce mois
        hors_delais = list(
            queryset.filter(
                su_delivery_date__year=month.year,
                su_delivery_date__month=month.month,
                su_delivery_date__gt=F("su_desired_delivery_date")
            ).values_list("su_mantis", flat=True)
        )

        results[month_key] = {
            "ok": s["ok"],
            "ko": s["ko"],
            "tickets_ko": hors_delais
        }

    return results


###########
from django.db.models import Prefetch

# Prefetch des lots pour éviter 1000 requêtes
qs = (
    Installation.objects
    .prefetch_related(
        Prefetch(
            "su_lots",
            queryset=Lot.objects.only("lot_name", "version")
        )
    )
)

result = []

for inst in qs:
    # Construction LOT@VERSION
    lots_version = [
        f"{lot.lot_name}@{lot.version}"
        for lot in inst.su_lots.all()
    ]

    result.append({
        "mantis": inst.su_mantis,
        "type": inst.su_type,
        "context": inst.su_contexte.c_name if inst.su_contexte else None,
        "statut": inst.su_statut.s_name if inst.su_statut else None,
        "date_livraison_souhaitee": inst.su_delivery_date.date() if inst.su_delivery_date else None,
        "date_livraison_reelle": inst.su_real_delivery_date.date() if inst.su_real_delivery_date else None,
        "nb_lots_connus": inst.su_nb_known_lot,
        "nb_nouvelle_version": inst.su_nb_new_version,
        "nb_nouveau_lot": inst.su_nb_new_lot,

        # ✔ Liste LOT@VERSION
        "lots_version": ", ".join(lots_version),
    })




from openpyxl import Workbook

def creer_fichier_mantis(filepath="donnees_mantis.xlsx"):
    # Données extraites de la photo
    data = [
        {
            "mantis": 31492,
            "type": "",
            "coefforth": 0.0,
            "contexte": "EQUAL2",
            "statut_livraison": "OK",
            "etat_livraison": 0,
            "date_livraison_souhaite": "20/10/2022 00:00:00",
            "date_prise_en_compte": None,
            "date_installation": None,
            "date_fin_installation": "19/10/2022 10:44:00",
            "nb_lots_connus": 40.0,
            "nb_nouvelles_versions": 0.0,
            "lots_version": (
                "Fusion Carrières; Schéma XCAR001.0.1|Habilitation9.3.1|MVC - Masse9.2.2|"
                "MVC - Unitaire9.2.1|Momenclature9.2.0|1000 - Extraction9.0.1|"
                "Service de Calcul du Quotient RCI - Schéma XCAR001.0.1|Synchronisation EC969.0.2"
            )
        },
        {
            "mantis": 34447,
            "type": "",
            "coefforth": 0.0,
            "contexte": "EQUAL2",
            "statut_livraison": "OK",
            "etat_livraison": 0,
            "date_livraison_souhaite": "25/11/2022 00:00:00",
            "date_prise_en_compte": None,
            "date_installation": None,
            "date_fin_installation": "25/11/2022 12:40:00",
            "nb_lots_connus": 11.0,
            "nb_nouvelles_versions": 1.0,
            "lots_version": "Synchronisation EC969.0.2"
        },
        {
            "mantis": 35520,
            "type": "",
            "coefforth": 0.0,
            "contexte": "EQUAL2",
            "statut_livraison": "OK",
            "etat_livraison": 0,
            "date_livraison_souhaite": "09/12/2022 00:00:00",
            "date_prise_en_compte": None,
            "date_installation": None,
            "date_fin_installation": "19/12/2022 08:30:00",
            "nb_lots_connus": 13.0,
            "nb_nouvelles_versions": 0.0,
            "lots_version": "..."
        }
    ]

    # Création du fichier
    wb = Workbook()
    ws = wb.active

    # En-têtes
    headers = list(data[0].keys())
    ws.append(headers)

    # Lignes
    for row in data:
        ws.append([row[h] for h in headers])

    # Sauvegarde
    wb.save(filepath)
    print(f"Fichier créé : {filepath}")