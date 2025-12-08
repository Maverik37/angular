from django.db.models import (
    OuterRef, Subquery, IntegerField, BooleanField, Value, Case, When
)
from django.db.models.functions import Coalesce
from django.db import connection
import json


def get_installations_with_lots_json():
    # Sous-requête récupérant la version du lot correspondant au mantis du ticket
    lot_version_qs = SuiviLotVersion.objects.filter(
        si_lot=OuterRef('su_lots__id'),
        si_installation_mantis=OuterRef('su_mantis')
    ).order_by('-id')

    # Query ORM : inst × lot avec annotations
    qs = (
        SuiviInstall.objects
        .values(
            'id',
            'su_mantis',
            'su_description',
            'su_user',
            'su_start_date',
            'su_end_date',
            'su_status',
            'su_lots__id',
            'su_lots__l_name',
            'su_lots__l_version',
        )
        .annotate(
            version_id=Subquery(lot_version_qs.values('id')[:1], output_field=IntegerField()),
            is_new_lot=Subquery(lot_version_qs.values('si_is_new_lot')[:1], output_field=BooleanField()),

            # Nouvelle version = si_is_new_lot == False
            is_new_version=Case(
                When(is_new_lot=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),

            artefact_number=Subquery(lot_version_qs.values('si_updated_artefact_number')[:1]),
            previous_lot_id=Subquery(lot_version_qs.values('si_precedent')[:1]),
        )
    )

    # Regroupement Python (aucune requête SQL supplémentaire)
    installations = {}

    for row in qs:
        inst_id = row['id']

        if inst_id not in installations:
            installations[inst_id] = {
                "id": row['id'],
                "mantis": row['su_mantis'],
                "description": row['su_description'],
                "user": row['su_user'],
                "start_date": row['su_start_date'],
                "end_date": row['su_end_date'],
                "status": row['su_status'],
                "lots": []
            }

        installations[inst_id]["lots"].append({
            "id": row['su_lots__id'],
            "name": row['su_lots__l_name'],
            "version": row['su_lots__l_version'],
            "version_id": row['version_id'],
            "is_new_lot": row['is_new_lot'],
            "is_new_version": row['is_new_version'],
            "artefact_number": row['artefact_number'],
            "previous_lot_id": row['previous_lot_id'],
        })

    return json.dumps(list(installations.values()), default=str, indent=2)