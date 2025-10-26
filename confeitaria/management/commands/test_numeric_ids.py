from django.core.management.base import BaseCommand
from confeitaria.repos_colaboradores import ColaboradoresRepo
from core.services.firestore_client import get_db


class Command(BaseCommand):
    help = 'Testa a criação de IDs numéricos no Firestore'

    def handle(self, *args, **options):
        self.stdout.write("Testando sistema de IDs numéricos...")
        
        try:
            repo = ColaboradoresRepo()
            
            # Teste básico - cria um colaborador com ID numérico
            test_data = {
                "rc": "TEST001",
                "nome": "Teste ID Numérico",
                "CPF_RG": "123.456.789-00",
                "sexo": "M",
                "funcao": "Teste"
            }
            
            resultado = repo.create(test_data)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Colaborador criado com ID: {resultado["id"]}')
            )
            
            # Verifica se o ID é numérico
            try:
                int(resultado["id"])
                self.stdout.write(
                    self.style.SUCCESS(f'✓ ID é numérico: {resultado["id"]}')
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'❌ ID não é numérico: {resultado["id"]}')
                )
            
            # Lista para ver todos os IDs
            todos = repo.list(limit=10)
            self.stdout.write(f"IDs existentes: {[doc['id'] for doc in todos]}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro: {str(e)}')
            )