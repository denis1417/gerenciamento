from typing import Any, Dict, List, Optional
from core.services.firestore_repo import FirestoreRepo, _coerce_dt

class FichasRepo(FirestoreRepo):
    collection_name = "fichas_producao"

    def normalize_in(self, data: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in (data or {}).items():
            if k.lower().endswith(("_data", "_dt", "_at", "_em", "_assinatura")):
                out[k] = _coerce_dt(v)
            else:
                out[k] = v
        return out

    def create_ficha(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma nova ficha de produção no Firestore"""
        return self.create(self.normalize_in(data))

    def update_ficha(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza uma ficha existente"""
        return self.set(doc_id, self.normalize_in(data))
    
    def list_by_produto(self, produto_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Lista fichas de um produto específico"""
        from google.cloud import firestore
        
        produto_id_str = str(produto_id)
        
        try:
            # Tenta buscar com ordenação (requer índice composto)
            q = self.col.where("produto_id", "==", produto_id_str).order_by("criado_em", direction=firestore.Query.DESCENDING).limit(limit)
            results = [{"id": s.id, **(s.to_dict() or {})} for s in q.stream()]
            return results
        except Exception:
            # Se falhar (índice não criado), busca sem ordenação
            q = self.col.where(filter=firestore.FieldFilter("produto_id", "==", produto_id_str)).limit(limit)
            results = [{"id": s.id, **(s.to_dict() or {})} for s in q.stream()]
            
            # Ordena em memória
            results.sort(key=lambda x: x.get('criado_em', ''), reverse=True)
            return results
    
    def add_insumo(self, ficha_id: str, insumo_data: Dict[str, Any]) -> None:
        """Adiciona insumo à lista de insumos da ficha"""
        try:
            ficha = self.get(ficha_id)
            if not ficha:
                raise ValueError(f"Ficha {ficha_id} não encontrada")
            
            insumos = ficha.get("insumos", [])
            insumos.append(insumo_data)
            
            self.set(ficha_id, {"insumos": insumos})
        except Exception as e:
            print(f"Erro ao adicionar insumo à ficha {ficha_id}: {e}")
            raise
    
    def get_insumos(self, ficha_id: str) -> List[Dict[str, Any]]:
        """Retorna a lista de insumos de uma ficha"""
        ficha = self.get(ficha_id)
        if not ficha:
            return []
        return ficha.get("insumos", [])
