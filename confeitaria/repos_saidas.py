from typing import Any, Dict
from core.services.firestore_repo import FirestoreRepo, _coerce_dt

class SaidasRepo(FirestoreRepo):
    collection_name = "saidas_insumo"

    def normalize_in(self, data: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in (data or {}).items():
            if k.lower().endswith(("_data", "_dt", "_at")):
                out[k] = _coerce_dt(v)
            else:
                out[k] = v
        return out

    def create_saida(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.create(self.normalize_in(data))

    def update_saida(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.set(doc_id, self.normalize_in(data))
