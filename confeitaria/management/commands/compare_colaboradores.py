from django.core.management.base import BaseCommand
from core.models import Colaborador
from confeitaria.repos_colaboradores import ColaboradoresRepo


class Command(BaseCommand):
    help = 'Lista e compara colaboradores do SQLite vs Firestore'

    def handle(self, *args, **options):
        self.stdout.write("=== COMPARAÇÃO SQLITE vs FIRESTORE ===\n")
        
        # SQLite
        self.stdout.write("📊 COLABORADORES NO SQLITE:")
        sqlite_colaboradores = Colaborador.objects.all().order_by('id')
        if sqlite_colaboradores:
            for colab in sqlite_colaboradores:
                self.stdout.write(f"  ID: {colab.id} | RC: {colab.rc} | Nome: {colab.nome}")
        else:
            self.stdout.write("  ❌ Nenhum colaborador encontrado no SQLite")
        
        self.stdout.write(f"Total SQLite: {sqlite_colaboradores.count()}\n")
        
        # Firestore
        self.stdout.write("🔥 COLABORADORES NO FIRESTORE:")
        try:
            repo = ColaboradoresRepo()
            firestore_colaboradores = repo.list(limit=100)
            if firestore_colaboradores:
                for colab in firestore_colaboradores:
                    rc = colab.get('rc', 'N/A')
                    nome = colab.get('nome', 'N/A')
                    self.stdout.write(f"  ID: {colab['id']} | RC: {rc} | Nome: {nome}")
            else:
                self.stdout.write("  ❌ Nenhum colaborador encontrado no Firestore")
            
            self.stdout.write(f"Total Firestore: {len(firestore_colaboradores)}\n")
            
        except Exception as e:
            self.stdout.write(f"  ❌ Erro ao acessar Firestore: {str(e)}\n")
            firestore_colaboradores = []
        
        # Comparação
        self.stdout.write("🔍 COMPARAÇÃO:")
        sqlite_ids = set(str(c.id) for c in sqlite_colaboradores)
        firestore_ids = set(c['id'] for c in firestore_colaboradores)
        
        # IDs que existem apenas no SQLite
        apenas_sqlite = sqlite_ids - firestore_ids
        if apenas_sqlite:
            self.stdout.write(f"  ⚠️  Apenas no SQLite: {sorted(apenas_sqlite)}")
        
        # IDs que existem apenas no Firestore  
        apenas_firestore = firestore_ids - sqlite_ids
        if apenas_firestore:
            self.stdout.write(f"  ⚠️  Apenas no Firestore: {sorted(apenas_firestore)}")
        
        # IDs que existem em ambos
        em_ambos = sqlite_ids & firestore_ids
        if em_ambos:
            self.stdout.write(f"  ✅ Em ambos: {sorted(em_ambos)}")
        
        if sqlite_ids == firestore_ids:
            self.stdout.write("  🎉 SQLite e Firestore estão sincronizados!")
        else:
            self.stdout.write("  ⚠️  SQLite e Firestore NÃO estão sincronizados")