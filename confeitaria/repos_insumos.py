from typing import Any, Dict
from core.services.firestore_repo import FirestoreRepo, _coerce_dt

class InsumosRepo(FirestoreRepo):
    collection_name = "insumos"

    def normalize_in(self, data: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in (data or {}).items():
            if k.lower().endswith(("_data", "_dt", "_at")):
                out[k] = _coerce_dt(v)
            else:
                out[k] = v
        return out

    def create_insumo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.create(self.normalize_in(data))

    def update_insumo(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.set(doc_id, self.normalize_in(data))
