"""
Repositórios Firestore para Vistorias
"""
from core.services.firestore_repo import FirestoreRepo


class VistoriasRepo(FirestoreRepo):
    """Repositório para gerenciar vistorias de insumos no Firestore"""
    collection_name = "vistorias"
    
    def get_by_data(self, data_vistoria):
        """Buscar todas as vistorias de uma data específica"""
        try:
            docs = (
                self.col
                .where("data_vistoria", "==", str(data_vistoria))
                .stream()
            )
            return {doc.id: doc.to_dict() for doc in docs}
        except Exception as e:
            print(f"Erro ao buscar vistorias por data: {e}")
            return {}
    
    def get_datas_vistoria(self):
        """Buscar todas as datas de vistoria únicas, ordenadas por data decrescente"""
        try:
            docs = self.col.stream()  # Usar self.col em vez de self.db.collection
            datas = set()
            for doc in docs:
                data = doc.to_dict()
                if data.get('data_vistoria'):
                    datas.add(data['data_vistoria'])
            
            # Converter para lista e ordenar (decrescente)
            return sorted(list(datas), reverse=True)
        except Exception as e:
            print(f"Erro ao buscar datas de vistoria: {e}")
            return []
    
    def delete_by_data(self, data_vistoria):
        """Deletar todas as vistorias de uma data específica"""
        try:
            docs = (
                self.col
                .where("data_vistoria", "==", str(data_vistoria))
                .stream()
            )
            
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            return deleted_count
        except Exception as e:
            print(f"Erro ao deletar vistorias por data: {e}")
            return 0