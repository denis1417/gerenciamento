from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Colaborador
from confeitaria.repos_colaboradores import ColaboradoresRepo

class Command(BaseCommand):
    help = "Exporta todos os Colaboradores do SQLite para o Firestore (não apaga nada no SQL)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limite de itens (0 = todos).")

    def handle(self, *args, **opts):
        qs = Colaborador.objects.all().select_related("usuario").order_by("id")
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        repo = ColaboradoresRepo()
        total = 0
        for c in qs.iterator():
            data = {
                "rc": c.rc,
                "nome": c.nome,
                "data_nascimento": c.data_nascimento,
                "sexo": c.sexo,
                "funcao": c.funcao,
                "CPF_RG": c.CPF_RG,
                "foto": getattr(c.foto, "name", None),
                "email": c.email,
                "celular": c.celular,
                "cep": c.cep,
                "logradouro": c.logradouro,
                "numero": c.numero,
                "bairro": c.bairro,
                "cidade": c.cidade,
                "estado": c.estado,
                "complemento": c.complemento,
                "usuario_id": c.usuario.id if c.usuario_id else None,
                "usuario_username": c.usuario.username if c.usuario_id else None,
            }
            repo.upsert_by_rc(c.rc, data)
            total += 1

        self.stdout.write(self.style.SUCCESS(f"Exportação concluída. Registros criados: {total}"))
