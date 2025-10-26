from django.core.management.base import BaseCommand
from django.db.models.fields.files import FieldFile
from datetime import datetime, timezone, date
from decimal import Decimal

# Ajuste o import do modelo SaidaInsumo conforme seu projeto:
try:
    from core.models import SaidaInsumo
except Exception:
    from confeitaria.models import SaidaInsumo

from confeitaria.repos_saidas import SaidasRepo

def _coerce_dt(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day, tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def _coerce_value(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (datetime, date)):
        return _coerce_dt(v)
    return v

def _model_to_dict_safe(instance):
    """
    Serializa apenas campos concretos e M2M forward (sem reversos).
    FK vira <campo>_id e <campo>_str. File/Image vira .name.
    """
    data = {}
    for f in instance._meta.fields:
        if not hasattr(instance, f.name):
            continue
        val = getattr(instance, f.name)
        if getattr(f, "many_to_one", False) and getattr(f, "remote_field", None):
            rel = getattr(instance, f.name)
            data[f"{f.name}_id"] = getattr(rel, "pk", None)
            data[f"{f.name}_str"] = str(rel) if rel else None
            continue
        if isinstance(val, FieldFile):
            data[f.name] = val.name or None
        else:
            data[f.name] = _coerce_value(val)

    for m2m in instance._meta.many_to_many:
        if not hasattr(instance, m2m.name):
            continue
        try:
            qs = getattr(instance, m2m.name).all()
        except Exception:
            continue
        data[f"{m2m.name}_ids"]  = [obj.pk for obj in qs]
        data[f"{m2m.name}_strs"] = [str(obj) for obj in qs]

    return data

class Command(BaseCommand):
    help = "Exporta Saídas de Insumo do SQLite para Firestore (idempotente por PK, doc_id = 'sql-<pk>')."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limite de itens (0 = todos).")

    def handle(self, *args, **opts):
        qs = SaidaInsumo.objects.all().order_by("id")
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        repo = SaidasRepo()
        total = 0

        for saida in qs.iterator():
            doc_id = f"sql-{saida.pk}"
            payload = _model_to_dict_safe(saida)

            # Campos denormalizados úteis (se existirem no seu modelo):
            # - insumo (FK)
            insumo_id = getattr(saida, "insumo_id", None)
            insumo_nome = str(getattr(saida, "insumo", "")) if insumo_id else None
            payload.setdefault("insumo_id", insumo_id)
            payload.setdefault("insumo_nome", insumo_nome)

            # - colaborador/usuario que efetuou a saída (se houver)
            colaborador_id = getattr(saida, "colaborador_id", None)
            colaborador_nome = str(getattr(saida, "colaborador", "")) if colaborador_id else None
            payload.setdefault("colaborador_id", colaborador_id)
            payload.setdefault("colaborador_nome", colaborador_nome)

            # Upsert determinístico (merge=True)
            repo.create_with_id(doc_id, payload)
            total += 1

        self.stdout.write(self.style.SUCCESS(f"Exportação concluída. Registros processados: {total}"))
