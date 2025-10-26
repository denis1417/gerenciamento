from django.core.management.base import BaseCommand
from django.conf import settings
from confeitaria.repos_colaboradores import ColaboradoresRepo


class Command(BaseCommand):
    help = 'Testa o sistema híbrido SQLite/Firestore'

    def handle(self, *args, **options):
        self.stdout.write("🧪 TESTE DO SISTEMA HÍBRIDO\n")
        
        # Verifica configuração
        use_fs = getattr(settings, "USE_FIRESTORE", False)
        self.stdout.write(f"⚙️  USE_FIRESTORE = {use_fs}")
        
        if use_fs:
            self.stdout.write("🔥 Sistema configurado para usar FIRESTORE")
        else:
            self.stdout.write("🗃️  Sistema configurado para usar SQLITE")
        
        # Testa repositório Firestore
        self.stdout.write("\n📊 TESTE REPOSITÓRIO FIRESTORE:")
        try:
            repo = ColaboradoresRepo()
            colaboradores = repo.list(limit=5)
            self.stdout.write(f"✅ Firestore OK - {len(colaboradores)} colaboradores encontrados")
            
            for colab in colaboradores:
                self.stdout.write(f"   ID: {colab['id']} | Nome: {colab.get('nome', 'N/A')}")
                
        except Exception as e:
            self.stdout.write(f"❌ Erro Firestore: {str(e)}")
        
        # Testa importação das views
        self.stdout.write("\n🌐 TESTE IMPORTAÇÃO DAS VIEWS:")
        try:
            from core.views import colaboradores_list
            self.stdout.write("✅ Views do core importadas com sucesso")
        except Exception as e:
            self.stdout.write(f"❌ Erro importação views: {str(e)}")
        
        # Verifica se _FS_COLAB está disponível
        try:
            from core.views import _FS_COLAB
            if _FS_COLAB:
                self.stdout.write("✅ _FS_COLAB disponível na view")
            else:
                self.stdout.write("⚠️  _FS_COLAB é None")
        except Exception as e:
            self.stdout.write(f"❌ Erro _FS_COLAB: {str(e)}")
        
        self.stdout.write("\n✨ Teste concluído!")