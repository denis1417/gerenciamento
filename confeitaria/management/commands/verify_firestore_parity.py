from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Colaborador
from confeitaria.repos_colaboradores import ColaboradoresRepo


class Command(BaseCommand):
    help = 'Verifica de onde os dados estão vindo na rota /colaboradores/'

    def handle(self, *args, **options):
        self.stdout.write("🔍 VERIFICANDO FONTE DOS DADOS\n")
        
        # Simula exatamente o que a view faz
        use_fs = getattr(settings, "USE_FIRESTORE", False)
        
        self.stdout.write(f"⚙️  USE_FIRESTORE = {use_fs}")
        
        if use_fs:
            self.stdout.write("📊 SIMULANDO VIEW com Firestore:")
            try:
                from core.views import _FS_COLAB
                if _FS_COLAB:
                    items = _FS_COLAB.list(limit=1000)
                    self.stdout.write(f"✅ Dados vindos do FIRESTORE: {len(items)} colaboradores")
                    for item in items:
                        self.stdout.write(f"   🔥 ID: {item['id']} | Nome: {item.get('nome')}")
                else:
                    self.stdout.write("❌ _FS_COLAB não disponível")
            except Exception as e:
                self.stdout.write(f"❌ Erro Firestore: {str(e)}")
        else:
            self.stdout.write("📊 SIMULANDO VIEW com SQLite:")
            colaboradores = Colaborador.objects.all().order_by('nome')
            self.stdout.write(f"✅ Dados vindos do SQLITE: {colaboradores.count()} colaboradores")
            for colab in colaboradores:
                self.stdout.write(f"   🗃️  ID: {colab.id} | Nome: {colab.nome}")
        
        self.stdout.write(f"\n🎯 CONCLUSÃO: A rota /colaboradores/ está usando {'FIRESTORE' if use_fs else 'SQLITE'}")
        
        # Adiciona uma marca no Firestore para teste
        if use_fs:
            self.stdout.write("\n🏷️  TESTE ADICIONAL:")
            self.stdout.write("Vou adicionar um colaborador de teste no Firestore...")
            try:
                repo = ColaboradoresRepo()
                test_data = {
                    "rc": "TESTE999",
                    "nome": "TESTE FIRESTORE - Deletar depois",
                    "CPF_RG": "000.000.000-00",
                    "sexo": "M",
                    "funcao": "Teste"
                }
                resultado = repo.create(test_data)
                self.stdout.write(f"✅ Colaborador teste criado com ID: {resultado['id']}")
                self.stdout.write("🌐 Agora acesse /colaboradores/ no navegador.")
                self.stdout.write("   Se aparecer 'TESTE FIRESTORE', os dados vêm do Firestore!")
                self.stdout.write("   Para deletar: python manage.py shell -c \"from confeitaria.repos_colaboradores import ColaboradoresRepo; ColaboradoresRepo().delete('" + resultado['id'] + "')\"")
            except Exception as e:
                self.stdout.write(f"❌ Erro criando teste: {str(e)}")
