from django.core.management.base import BaseCommand
from confeitaria.repos_insumos import InsumosRepo


class Command(BaseCommand):
    help = 'Lista TODOS os insumos do Firestore com detalhes'

    def handle(self, *args, **options):
        repo = InsumosRepo()
        
        # Buscar com limite alto para garantir que pega tudo
        insumos = repo.list(limit=50)  # Limite bem alto
        
        self.stdout.write(f"🔥 Total de insumos no Firestore: {len(insumos)}")
        self.stdout.write("\n📋 Lista completa:")
        
        for insumo in sorted(insumos, key=lambda x: int(x['id'])):
            self.stdout.write(
                f"   🔸 ID {insumo['id']}: {insumo.get('nome', 'N/A')} - "
                f"{insumo.get('quantidade_total', 'N/A')} {insumo.get('unidade_base', 'N/A')}"
            )