from django.core.management.base import BaseCommand
from django.db.models.fields.files import FieldFile
from datetime import datetime, timezone, date
from decimal import Decimal

try:
    from core.models import FichaProducao, FichaInsumo
except Exception:
    from confeitaria.models import FichaProducao, FichaInsumo

from confeitaria.repos_fichas import FichasRepo


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

def _first_attr(obj, candidates):
    for name in candidates:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


class Command(BaseCommand):
    help = "Exporta Fichas de Produção do SQLite para Firestore (denormalizadas, tolerantes a esquema)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limite de itens (0 = todos).")

    def handle(self, *args, **opts):
        qs = FichaProducao.objects.all().order_by("id")
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        repo = FichasRepo()
        total = 0

        for ficha in qs.iterator():
            doc_id = f"sql-{ficha.pk}"

            payload = _model_to_dict_safe(ficha)

            itens = []
            rel_qs = FichaInsumo.objects.filter(ficha=ficha)

            for fi in rel_qs:
                fi_dict = _model_to_dict_safe(fi)

                insumo_id = getattr(fi, "insumo_id", None)
                insumo_nome = str(getattr(fi, "insumo", "")) if insumo_id else None

                quantidade_val = _first_attr(fi, [
                    "quantidade", "qtd", "qtde", "quant", "quantidade_usada", "qtd_usada", "qtd_saida"
                ])
                unidade_val = _first_attr(fi, ["unidade", "un", "u"])

                item = {
                    "insumo_id": insumo_id,
                    "insumo_nome": insumo_nome,
                    "quantidade": str(quantidade_val) if quantidade_val is not None else None,
                    "unidade": unidade_val if unidade_val is not None else fi_dict.get("unidade"),
                    "raw": fi_dict,
                }
                itens.append(item)

            payload["insumos"] = itens

            repo.create_with_id(doc_id, payload)
            total += 1

        self.stdout.write(self.style.SUCCESS(f"Exportação concluída. Registros processados: {total}"))
