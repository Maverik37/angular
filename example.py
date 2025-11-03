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

def get_installations_stats():
    """
    Retourne les statistiques mensuelles des installations :
      - ok : livrées dans les délais
      - ko : livrées hors délais
      - tickets_ko : liste des N° mantis hors délai
    """
    from .models import SuiviInstallation  # adapte le nom du modèle

    # Filtrage des statuts concernés
    queryset = SuiviInstallation.objects.filter(
        su_statut__in=["Terminé", "Validation à cartographier"],
        su_delivery_date__isnull=False,
        su_desired_delivery_date__isnull=False
    )

    # Regroupement par mois de livraison
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

    # Construction des résultats avec liste des tickets hors délai
    results = []
    for s in stats:
        month = s["month"]

        # Récupération des mantis hors délai du mois
        hors_delais = list(
            queryset.filter(
                su_delivery_date__month=month.month,
                su_delivery_date__year=month.year,
                su_delivery_date__gt=F("su_desired_delivery_date")
            ).values_list("su_mantis", flat=True)
        )

        results.append({
            "month": month.strftime("%Y-%m"),
            "ok": s["ok"],
            "ko": s["ko"],
            "tickets_ko": hors_delais,
        })

    return results