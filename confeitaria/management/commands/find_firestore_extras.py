from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Colaborador, Insumo
from confeitaria.repos_colaboradores import ColaboradoresRepo
from confeitaria.repos_insumos import InsumosRepo


class Command(BaseCommand):
    help = 'Mostra registros que existem apenas no Firestore (não no SQLite)'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Identificando registros extras no Firestore...")
        
        self._find_extra_colaboradores()
        self._find_extra_insumos()

    def _find_extra_colaboradores(self):
        self.stdout.write("\n" + "="*50)
        self.stdout.write("👥 COLABORADORES EXTRAS NO FIRESTORE")
        self.stdout.write("="*50)
        
        # SQLite IDs
        sqlite_ids = set(str(colab.id) for colab in Colaborador.objects.all())
        self.stdout.write(f"📊 SQLite IDs: {sorted(sqlite_ids)}")
        
        # Firestore IDs
        fs_repo = ColaboradoresRepo()
        fs_colaboradores = fs_repo.list(limit=1000)
        fs_ids = set(str(item['id']) for item in fs_colaboradores)
        self.stdout.write(f"🔥 Firestore IDs: {sorted(fs_ids)}")
        
        # Encontrar extras
        extras = fs_ids - sqlite_ids
        if extras:
            self.stdout.write(f"\n❌ IDs EXTRAS NO FIRESTORE: {sorted(extras)}")
            for extra_id in sorted(extras):
                extra_colab = next(item for item in fs_colaboradores if str(item['id']) == extra_id)
                self.stdout.write(f"   🔸 ID {extra_id}: {extra_colab.get('nome', 'N/A')}")
        else:
            self.stdout.write("✅ Nenhum colaborador extra no Firestore")

    def _find_extra_insumos(self):
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🥄 INSUMOS EXTRAS NO FIRESTORE")
        self.stdout.write("="*50)
        
        # SQLite IDs
        sqlite_ids = set(str(insumo.id) for insumo in Insumo.objects.all())
        self.stdout.write(f"📊 SQLite IDs: {sorted(sqlite_ids)}")
        
        # Firestore IDs
        fs_repo = InsumosRepo()
        fs_insumos = fs_repo.list(limit=1000)
        fs_ids = set(str(item['id']) for item in fs_insumos)
        self.stdout.write(f"🔥 Firestore IDs: {sorted(fs_ids)}")
        
        # Encontrar extras
        extras = fs_ids - sqlite_ids
        if extras:
            self.stdout.write(f"\n❌ IDs EXTRAS NO FIRESTORE: {sorted(extras)}")
            for extra_id in sorted(extras):
                extra_insumo = next(item for item in fs_insumos if str(item['id']) == extra_id)
                quantidade = extra_insumo.get('quantidade_total', 'N/A')
                unidade = extra_insumo.get('unidade_base', 'N/A')
                self.stdout.write(f"   🔸 ID {extra_id}: {extra_insumo.get('nome', 'N/A')} - {quantidade} {unidade}")
        else:
            self.stdout.write("✅ Nenhum insumo extra no Firestore")