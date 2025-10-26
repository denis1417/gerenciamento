from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, date
from google.cloud import firestore
from core.services.firestore_repo import FirestoreRepo
from google.cloud.firestore_v1.base_query import FieldFilter

class ColaboradoresRepo(FirestoreRepo):
    collection_name = "colaboradores"

    def _coerce_date(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, (datetime, )):
            return value.astimezone(timezone.utc)
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            return None

    def normalize_in(self, data: Dict[str, Any]) -> Dict[str, Any]:
        def s(key): 
            return str(data.get(key, "") or "").strip()

        usuario_id = data.get("usuario_id")
        usuario_username = data.get("usuario_username")

        foto = data.get("foto")
        if hasattr(foto, "name"):
            foto = foto.name

        payload = {
            "rc": s("rc"),
            "nome": s("nome"),
            "data_nascimento": self._coerce_date(data.get("data_nascimento")),
            "sexo": s("sexo"),
            "funcao": s("funcao"),
            "CPF_RG": s("CPF_RG"),
            "foto": foto if foto else None,
            "email": s("email") or None,
            "celular": s("celular") or None,
            "cep": s("cep") or None,
            "logradouro": s("logradouro") or None,
            "numero": s("numero") or None,
            "bairro": s("bairro") or None,
            "cidade": s("cidade") or None,
            "estado": s("estado") or None,
            "complemento": s("complemento") or None,
            "usuario": {
                "id": int(usuario_id) if str(usuario_id).isdigit() else None,
                "username": s("usuario_username") or None,
            },
        }
        return payload

    def create_colab(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = self.normalize_in(data)
        if not payload["rc"]:
            raise ValueError("Campo 'rc' é obrigatório.")
        if not payload["nome"]:
            raise ValueError("Campo 'nome' é obrigatório.")
        if not payload["CPF_RG"]:
            raise ValueError("Campo 'CPF_RG' é obrigatório.")
        return self.create(payload)

    def update_colab(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = self.normalize_in(data)
        return self.set(doc_id, payload)

    def get_by_rc(self, rc: str):
        q = self.col.where(filter=FieldFilter("rc", "==", rc)).limit(1).stream()
        for s in q:
            return {"id": s.id, **(s.to_dict() or {})}
        return None

    def list_by_nome(self, termo: str, limit: int = 50) -> List[Dict[str, Any]]:
        termo = (termo or "").strip().lower()
        if not termo:
            return self.list(limit=limit)
        q = self.col.where("nome", ">=", termo).where("nome", "<=", termo + u"\uf8ff").limit(limit)
        return [{"id": s.id, **(s.to_dict() or {})} for s in q.stream()]

    def upsert_by_rc(self, rc: str, data: Dict[str, Any]) -> Dict[str, Any]:
        found = self.get_by_rc(rc)
        payload = self.normalize_in({**data, "rc": rc})
        if found:
            return self.set(found["id"], payload)
        return self.create(payload)