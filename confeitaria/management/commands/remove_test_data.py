from django.core.management.base import BaseCommand
from confeitaria.repos_colaboradores import ColaboradoresRepo


class Command(BaseCommand):
    help = 'Remove colaborador de teste (ID 5) do Firestore'

    def handle(self, *args, **options):
        repo = ColaboradoresRepo()
        
        # Verificar se existe
        colab = repo.get("5")
        if colab:
            self.stdout.write(f"Removendo colaborador ID 5: {colab.get('nome', 'N/A')}")
            repo.delete("5")
            self.stdout.write(self.style.SUCCESS("✅ Colaborador removido com sucesso!"))
        else:
            self.stdout.write("ℹ️  Colaborador ID 5 não encontrado")