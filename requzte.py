from django.db.models import (
    OuterRef, Subquery, IntegerField, BooleanField, Value, Case, When
)
import json


def get_installations_with_lots_json():

    # Sous-requête = version de lot correspondant au Mantis du ticket
    lot_version_qs = SuiviLotVersion.objects.filter(
        si_lot=OuterRef('su_lots__id'),
        si_installation_mantis=OuterRef('su_mantis')   # <--- lien MANTIS INSTALLATION
    ).order_by('-id')

    qs = (
        SuiviInstall.objects
        .order_by('-su_reception_date')  # <--- tri récent comme demandé
        .values(
            'id',
            'su_mantis',
            'su_description',
            'su_priorite',
            'su_type_installation',
            'su_total_coeff',
            'su_contexte',

            # Tous tes champs visibles sur la photo
            'su_reception_date',
            'su_taken_date',
            'su_statut',
            'su_analyse_date',
            'su_is_lisa_smi',
            'su_standby_date',
            'su_test_date',
            'su_desired_delivery_date',
            'su_delivery_date',
            'su_main_penv_user',
            'su_other_penv_user',
            'su_commentary',
            'su_nb_known_lot',
            'su_nb_new_version',
            'su_nb_new_lot',
            'su_is_manually_modified',
            'su_nb_artefacts',
            'su_nb_artefact_maj',

            # Champs LOTS depuis ton values()
            'su_lots__id',
            'su_lots__l_name',
            'su_lots__l_version',
        )
        .annotate(
            version_id=Subquery(
                lot_version_qs.values('id')[:1],
                output_field=IntegerField()
            ),
            is_new_lot=Subquery(
                lot_version_qs.values('si_is_new_lot')[:1],
                output_field=BooleanField()
            ),

            # Nouvelle version = pas un nouveau lot
            is_new_version=Case(
                When(is_new_lot=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),

            artefact_number=Subquery(
                lot_version_qs.values('si_updated_artefact_number')[:1]
            ),
            previous_lot_id=Subquery(
                lot_version_qs.values('si_precedent')[:1]
            ),
        )
    )

    # Regroupement JSON propre
    installations = {}

    for r in qs:
        inst_id = r['id']

        if inst_id not in installations:
            installations[inst_id] = {
                "id": r['id'],
                "mantis": r['su_mantis'],
                "description": r['su_description'],
                "priorite": r['su_priorite'],
                "type_installation": r['su_type_installation'],
                "total_coeff": r['su_total_coeff'],
                "contexte": r['su_contexte'],

                # Dates
                "reception_date": r['su_reception_date'],
                "taken_date": r['su_taken_date'],
                "statut": r['su_statut'],
                "analyse_date": r['su_analyse_date'],
                "is_lisa_smi": r['su_is_lisa_smi'],
                "standby_date": r['su_standby_date'],
                "test_date": r['su_test_date'],
                "desired_delivery_date": r['su_desired_delivery_date'],
                "delivery_date": r['su_delivery_date'],

                # Users + commentaires
                "main_penv_user": r['su_main_penv_user'],
                "other_penv_user": r['su_other_penv_user'],
                "commentary": r['su_commentary'],

                # Compteurs
                "nb_known_lot": r['su_nb_known_lot'],
                "nb_new_version": r['su_nb_new_version'],
                "nb_new_lot": r['su_nb_new_lot'],
                "is_manually_modified": r['su_is_manually_modified'],
                "nb_artefacts": r['su_nb_artefacts'],
                "nb_artefact_maj": r['su_nb_artefact_maj'],

                # Liste des lots
                "lots": []
            }

        installations[inst_id]["lots"].append({
            "id": r['su_lots__id'],
            "name": r['su_lots__l_name'],
            "version": r['su_lots__l_version'],
            "version_id": r['version_id'],
            "is_new_lot": r['is_new_lot'],
            "is_new_version": r['is_new_version'],
            "artefact_number": r['artefact_number'],
            "previous_lot_id": r['previous_lot_id'],
        })

    return json.dumps(list(installations.values()), default=str, indent=2)

########
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_modify.html"
    success_url = reverse_lazy("app_index")

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        return response