from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Colaborador, Insumo
from confeitaria.repos_colaboradores import ColaboradoresRepo
from confeitaria.repos_insumos import InsumosRepo
from types import SimpleNamespace


class Command(BaseCommand):
    help = 'Compara dados entre SQLite e Firestore para identificar diferenças'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['colaboradores', 'insumos', 'all'],
            default='all',
            help='Modelo específico para comparar ou "all" para todos'
        )

    def handle(self, *args, **options):
        model = options['model']

        self.stdout.write(f"🔍 Comparando dados entre SQLite e Firestore...")
        
        if model in ['colaboradores', 'all']:
            self._compare_colaboradores()
        
        if model in ['insumos', 'all']:
            self._compare_insumos()

    def _compare_colaboradores(self):
        self.stdout.write("\n" + "="*50)
        self.stdout.write("👥 COMPARANDO COLABORADORES")
        self.stdout.write("="*50)
        
        # SQLite
        sqlite_colaboradores = list(Colaborador.objects.all().order_by('id'))
        self.stdout.write(f"📊 SQLite: {len(sqlite_colaboradores)} colaboradores")
        
        # Firestore
        fs_repo = ColaboradoresRepo()
        fs_colaboradores = fs_repo.list(limit=1000)
        self.stdout.write(f"🔥 Firestore: {len(fs_colaboradores)} colaboradores")
        
        # Comparar contagem
        if len(sqlite_colaboradores) != len(fs_colaboradores):
            self.stdout.write(
                self.style.WARNING(f"⚠️  DIFERENÇA NA QUANTIDADE: SQLite={len(sqlite_colaboradores)}, Firestore={len(fs_colaboradores)}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Quantidade igual: {len(sqlite_colaboradores)} registros")
            )
        
        # Comparar registros individuais
        self.stdout.write("\n📋 Detalhes dos registros:")
        
        # Criar dicionário do Firestore por ID
        fs_dict = {str(item['id']): item for item in fs_colaboradores}
        
        for sqlite_colab in sqlite_colaboradores:
            sqlite_id = str(sqlite_colab.id)
            fs_colab = fs_dict.get(sqlite_id)
            
            self.stdout.write(f"\n🔸 ID {sqlite_id}:")
            self.stdout.write(f"   SQLite: {sqlite_colab.nome}")
            
            if fs_colab:
                self.stdout.write(f"   Firestore: {fs_colab.get('nome', 'N/A')}")
                
                # Comparar campos importantes
                if sqlite_colab.nome != fs_colab.get('nome'):
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ NOME DIFERENTE!")
                    )
                else:
                    self.stdout.write(f"   ✅ Nome igual")
            else:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ NÃO ENCONTRADO NO FIRESTORE")
                )

    def _compare_insumos(self):
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🥄 COMPARANDO INSUMOS")
        self.stdout.write("="*50)
        
        # SQLite
        sqlite_insumos = list(Insumo.objects.all().order_by('id'))
        self.stdout.write(f"📊 SQLite: {len(sqlite_insumos)} insumos")
        
        # Firestore
        fs_repo = InsumosRepo()
        fs_insumos = fs_repo.list(limit=1000)
        self.stdout.write(f"🔥 Firestore: {len(fs_insumos)} insumos")
        
        # Comparar contagem
        if len(sqlite_insumos) != len(fs_insumos):
            self.stdout.write(
                self.style.WARNING(f"⚠️  DIFERENÇA NA QUANTIDADE: SQLite={len(sqlite_insumos)}, Firestore={len(fs_insumos)}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Quantidade igual: {len(sqlite_insumos)} registros")
            )
        
        # Comparar registros individuais
        self.stdout.write("\n📋 Detalhes dos registros:")
        
        # Criar dicionário do Firestore por ID
        fs_dict = {str(item['id']): item for item in fs_insumos}
        
        for sqlite_insumo in sqlite_insumos:
            sqlite_id = str(sqlite_insumo.id)
            fs_insumo = fs_dict.get(sqlite_id)
            
            self.stdout.write(f"\n🔸 ID {sqlite_id}:")
            self.stdout.write(f"   SQLite: {sqlite_insumo.nome}")
            self.stdout.write(f"   SQLite Quantidade: {sqlite_insumo.quantidade_total} {sqlite_insumo.unidade_base}")
            
            if fs_insumo:
                self.stdout.write(f"   Firestore: {fs_insumo.get('nome', 'N/A')}")
                fs_quantidade = fs_insumo.get('quantidade_total', 'N/A')
                fs_unidade = fs_insumo.get('unidade_base', 'N/A')
                self.stdout.write(f"   Firestore Quantidade: {fs_quantidade} {fs_unidade}")
                
                # Comparar campos importantes
                nome_ok = sqlite_insumo.nome == fs_insumo.get('nome')
                quantidade_ok = str(sqlite_insumo.quantidade_total) == str(fs_quantidade)
                
                if nome_ok and quantidade_ok:
                    self.stdout.write(f"   ✅ Dados iguais")
                else:
                    if not nome_ok:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ NOME DIFERENTE!")
                        )
                    if not quantidade_ok:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ QUANTIDADE DIFERENTE! SQLite: {sqlite_insumo.quantidade_total}, Firestore: {fs_quantidade}")
                        )
            else:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ NÃO ENCONTRADO NO FIRESTORE")
                )
        
        # Verificar se há registros no Firestore que não estão no SQLite
        sqlite_ids = {str(insumo.id) for insumo in sqlite_insumos}
        fs_only = [item for item in fs_insumos if str(item['id']) not in sqlite_ids]
        
        if fs_only:
            self.stdout.write(f"\n⚠️  REGISTROS APENAS NO FIRESTORE:")
            for item in fs_only:
                self.stdout.write(f"   🔸 ID {item['id']}: {item.get('nome', 'N/A')}")