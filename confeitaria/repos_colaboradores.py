# confeitaria/repos_colaboradores.py
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, date
from google.cloud import firestore
from core.services.firestore_repo import FirestoreRepo
from google.cloud.firestore_v1.base_query import FieldFilter

class ColaboradoresRepo(FirestoreRepo):
    collection_name = "colaboradores"

    # ⚠️ Campos do seu Django:
    # rc, nome, data_nascimento, sexo, funcao, CPF_RG, foto, email, celular,
    # cep, logradouro, numero, bairro, cidade, estado, complemento, usuario (OneToOne User)

    def _coerce_date(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, (datetime, )):
            return value.astimezone(timezone.utc)
        if isinstance(value, date):
            # salva como datetime UTC 00:00 pra manter consistência nas queries
            return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        # tenta parse básico ISO
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            return None

    def normalize_in(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Strings “limpas”
        def s(key): 
            return str(data.get(key, "") or "").strip()

        # mapeia usuário associado (OneToOne): guardamos apenas o id e o username, se vier
        usuario_id = data.get("usuario_id")
        usuario_username = data.get("usuario_username")

        # imagem/foto: no Firestore vamos guardar o caminho relativo (ou URL se você enviar)
        foto = data.get("foto")
        if hasattr(foto, "name"):
            foto = foto.name  # ex.: "colaboradores/arquivo.jpg"

        payload = {
            "rc": s("rc"),
            "nome": s("nome"),
            "data_nascimento": self._coerce_date(data.get("data_nascimento")),
            "sexo": s("sexo"),            # "M" ou "F"
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
            "estado": s("estado") or None,   # “MG”, “SP”, etc.
            "complemento": s("complemento") or None,
            "usuario": {
                "id": int(usuario_id) if str(usuario_id).isdigit() else None,
                "username": s("usuario_username") or None,
            },
        }
        return payload

    # CRUD conveniência
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

    # Filtros úteis (exemplos)
    def get_by_rc(self, rc: str):
        q = self.col.where(filter=FieldFilter("rc", "==", rc)).limit(1).stream()
        for s in q:
            return {"id": s.id, **(s.to_dict() or {})}
        return None

    def list_by_nome(self, termo: str, limit: int = 50) -> List[Dict[str, Any]]:
        # Firestore não faz LIKE, então sugerido: indexar nome_lower p/ prefix search (opcional)
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