from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Colaborador, Insumo, Produto, FichaProducao, SaidaInsumo
from confeitaria.repos_colaboradores import ColaboradoresRepo
from confeitaria.repos_insumos import InsumosRepo
from confeitaria.repos_produtos import ProdutosRepo
from confeitaria.repos_fichas import FichasRepo
from confeitaria.repos_saidas import SaidasRepo


class Command(BaseCommand):
    help = 'Migra dados do SQLite para Firestore mantendo os mesmos IDs numéricos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['colaboradores', 'insumos', 'produtos', 'fichas', 'saidas', 'all'],
            default='all',
            help='Modelo específico para migrar ou "all" para todos'
        )
        parser.add_argument(
            '--clear-firestore',
            action='store_true',
            help='Limpa dados do Firestore antes da migração'
        )

    def handle(self, *args, **options):
        model = options['model']
        clear_firestore = options['clear_firestore']

        self.stdout.write(f"Iniciando migração do SQLite para Firestore...")
        
        if model in ['colaboradores', 'all']:
            self._migrate_colaboradores(clear_firestore)
        
        if model in ['insumos', 'all']:
            self._migrate_insumos(clear_firestore)
        
        if model in ['produtos', 'all']:
            self._migrate_produtos(clear_firestore)
        
        if model in ['fichas', 'all']:
            self._migrate_fichas(clear_firestore)
        
        if model in ['saidas', 'all']:
            self._migrate_saidas(clear_firestore)

        self.stdout.write(
            self.style.SUCCESS(f'Migração concluída!')
        )

    def _migrate_colaboradores(self, clear_firestore):
        self.stdout.write("Migrando Colaboradores...")
        
        repo = ColaboradoresRepo()
        
        if clear_firestore:
            self._clear_collection(repo)
        
        colaboradores = Colaborador.objects.all()
        count = repo.migrate_from_sqlite_model(colaboradores)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} colaboradores migrados')
        )

    def _migrate_insumos(self, clear_firestore):
        self.stdout.write("Migrando Insumos...")
        
        repo = InsumosRepo()
        
        if clear_firestore:
            self._clear_collection(repo)
        
        insumos = Insumo.objects.all()
        count = repo.migrate_from_sqlite_model(insumos)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} insumos migrados')
        )

    def _migrate_produtos(self, clear_firestore):
        self.stdout.write("Migrando Produtos...")
        
        repo = ProdutosRepo()
        
        if clear_firestore:
            self._clear_collection(repo)
        
        produtos = Produto.objects.all()
        count = repo.migrate_from_sqlite_model(produtos)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} produtos migrados')
        )

    def _migrate_fichas(self, clear_firestore):
        self.stdout.write("Migrando Fichas...")
        
        repo = FichasRepo()
        
        if clear_firestore:
            self._clear_collection(repo)
        
        fichas = FichaProducao.objects.all()
        count = repo.migrate_from_sqlite_model(fichas)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} fichas migradas')
        )

    def _migrate_saidas(self, clear_firestore):
        self.stdout.write("Migrando Saídas de Insumos...")
        
        repo = SaidasRepo()
        
        if clear_firestore:
            self._clear_collection(repo)
        
        saidas = SaidaInsumo.objects.all()
        count = repo.migrate_from_sqlite_model(saidas)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} saídas migradas')
        )

    def _clear_collection(self, repo):
        """Limpa todos os documentos de uma coleção"""
        self.stdout.write(f"Limpando coleção {repo.collection_name}...")
        
        docs = repo.list(limit=1000)  # Pega todos os documentos
        for doc in docs:
            repo.delete(doc['id'])
        
        # Limpa também o contador
        from core.services.firestore_client import get_db
        db = get_db()
        counter_ref = db.collection("_counters").document(repo.collection_name)
        counter_ref.delete()
        
        self.stdout.write(f"✓ Coleção {repo.collection_name} limpa")