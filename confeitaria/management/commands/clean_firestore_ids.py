from django.core.management.base import BaseCommand
from confeitaria.repos_colaboradores import ColaboradoresRepo
from confeitaria.repos_insumos import InsumosRepo
from confeitaria.repos_produtos import ProdutosRepo
from confeitaria.repos_fichas import FichasRepo
from confeitaria.repos_saidas import SaidasRepo
from core.services.firestore_client import get_db


class Command(BaseCommand):
    help = 'Limpa IDs não-numéricos do Firestore (formato sql-*) e mantém apenas IDs numéricos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quais registros seriam deletados sem executar'
        )
        parser.add_argument(
            '--collection',
            type=str,
            choices=['colaboradores', 'insumos', 'produtos', 'fichas_producao', 'saidas_insumo', 'all'],
            default='all',
            help='Coleção específica para limpar ou "all" para todas'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        collection = options['collection']

        self.stdout.write(f"🔍 Análise de IDs inconsistentes no Firestore...")
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODO DRY-RUN - Nenhum registro será deletado"))
        
        repos = {
            'colaboradores': ColaboradoresRepo(),
            'insumos': InsumosRepo(),
            'produtos': ProdutosRepo(),
            'fichas_producao': FichasRepo(),
            'saidas_insumo': SaidasRepo(),
        }

        collections_to_clean = [collection] if collection != 'all' else repos.keys()
        
        total_found = 0
        total_deleted = 0

        for collection_name in collections_to_clean:
            if collection_name not in repos:
                continue
                
            repo = repos[collection_name]
            self.stdout.write(f"\n📋 Verificando coleção: {collection_name}")
            
            # Lista todos os documentos
            docs = repo.list(limit=1000)
            non_numeric_ids = []
            
            for doc in docs:
                doc_id = doc['id']
                # Converte para string e verifica se não é numérico
                doc_id_str = str(doc_id)
                if not doc_id_str.isdigit():
                    non_numeric_ids.append(doc_id_str)
                    total_found += 1
            
            if non_numeric_ids:
                self.stdout.write(f"❌ Encontrados {len(non_numeric_ids)} IDs não-numéricos:")
                for doc_id in non_numeric_ids:
                    self.stdout.write(f"   - {doc_id}")
                
                if not dry_run:
                    # Deleta os registros com IDs não-numéricos
                    for doc_id in non_numeric_ids:
                        repo.delete(doc_id)
                        total_deleted += 1
                    self.stdout.write(self.style.SUCCESS(f"✅ {len(non_numeric_ids)} registros deletados"))
                else:
                    self.stdout.write(self.style.WARNING(f"🔄 {len(non_numeric_ids)} registros seriam deletados"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Nenhum ID inconsistente encontrado"))

        # Relatório final
        self.stdout.write(f"\n📊 RELATÓRIO FINAL:")
        self.stdout.write(f"   IDs inconsistentes encontrados: {total_found}")
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"   Registros deletados: {total_deleted}"))
            self.stdout.write(f"\n🎯 Agora todos os IDs estão no formato numérico padrão!")
        else:
            self.stdout.write(self.style.WARNING(f"   Registros que seriam deletados: {total_found}"))
            self.stdout.write(f"\n💡 Execute sem --dry-run para aplicar as mudanças")