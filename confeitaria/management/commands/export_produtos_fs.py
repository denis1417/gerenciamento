from django.core.management.base import BaseCommand
from django.db.models.fields.files import FieldFile

try:
    from core.models import ProdutoPronto as Produto
except Exception:
    from confeitaria.models import ProdutoPronto as Produto

from confeitaria.repos_produtos import ProdutosRepo

def _model_to_dict(instance):
    """Serializa modelo Django em dict plano."""
    data = {}
    opts = instance._meta
    for f in opts.get_fields():
        if f.many_to_many:
            if hasattr(instance, f.name):
                qs = getattr(instance, f.name).all()
                data[f"{f.name}_ids"]  = [obj.pk for obj in qs]
                data[f"{f.name}_strs"] = [str(obj) for obj in qs]
            continue
        if f.many_to_one:
            rel = getattr(instance, f.name, None)
            data[f"{f.name}_id"]  = getattr(rel, "pk", None)
            data[f"{f.name}_str"] = str(rel) if rel else None
            continue
        if hasattr(instance, f.name):
            val = getattr(instance, f.name)
            if isinstance(val, FieldFile):
                data[f.name] = val.name or None
            else:
                data[f.name] = val
    return data

class Command(BaseCommand):
    help = "Exporta Produtos do SQLite para Firestore (idempotente por PK, doc_id = 'sql-<pk>')."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limite de itens (0 = todos).")

    def handle(self, *args, **opts):
        qs = Produto.objects.all().order_by("id")
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        repo = ProdutosRepo()
        total = 0
        for obj in qs.iterator():
            doc_id = f"sql-{obj.pk}"
            payload = _model_to_dict(obj)
            repo.create_with_id(doc_id, payload)
            total += 1

        self.stdout.write(self.style.SUCCESS(f"Exportação concluída. Registros processados: {total}"))
