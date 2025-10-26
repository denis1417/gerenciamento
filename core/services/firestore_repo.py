from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, date
from decimal import Decimal
from google.cloud import firestore
from .firestore_client import get_db

def _ts_now():
    return datetime.now(timezone.utc)

def _coerce_dt(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day, tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        return None

def _coerce_value(v):
    if isinstance(v, Decimal):
        # evite float surprises: salve como string ou float. Aqui, string.
        return str(v)
    if isinstance(v, (datetime, date)):
        return _coerce_dt(v)
    return v

class FirestoreRepo:
    """Repo base com operações comuns."""
    collection_name: str = ""

    @property
    def col(self) -> firestore.CollectionReference:
        return get_db().collection(self.collection_name)
    
    def _get_next_numeric_id(self) -> str:
        """Gera próximo ID numérico sequencial para compatibilidade com SQLite"""
        db = get_db()
        counter_ref = db.collection("_counters").document(self.collection_name)
        
        # Transação para garantir atomicidade
        @firestore.transactional
        def update_counter(transaction, counter_ref):
            counter_doc = counter_ref.get(transaction=transaction)
            if counter_doc.exists:
                current_value = counter_doc.get("value") or 0
            else:
                # Busca o maior ID existente para inicializar o contador
                existing_docs = list(self.col.stream())
                max_id = 0
                for doc in existing_docs:
                    try:
                        doc_id_num = int(doc.id)
                        if doc_id_num > max_id:
                            max_id = doc_id_num
                    except ValueError:
                        # Se encontrar IDs não numéricos, ignora
                        pass
                current_value = max_id
            
            new_value = current_value + 1
            transaction.set(counter_ref, {"value": new_value})
            return str(new_value)
        
        transaction = db.transaction()
        return update_counter(transaction, counter_ref)

    def list(self, limit: int = 50, start_after_id: Optional[str] = None) -> List[Dict[str, Any]]:
        q = self.col.order_by("criado_em", direction=firestore.Query.DESCENDING).limit(limit)
        if start_after_id:
            ref = self.col.document(start_after_id).get()
            if ref.exists:
                q = q.start_after(ref)
        return [{"id": s.id, **(s.to_dict() or {})} for s in q.stream()]

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        snap = self.col.document(doc_id).get()
        if not snap.exists:
            return None
        return {"id": snap.id, **(snap.to_dict() or {})}

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {k: _coerce_value(v) for k, v in data.items()}
        payload.setdefault("criado_em", _ts_now())
        payload.setdefault("atualizado_em", None)
        
        # Gera ID numérico sequencial
        numeric_id = self._get_next_numeric_id()
        doc_ref = self.col.document(numeric_id)
        doc_ref.set(payload)
        return {"id": doc_ref.id, **payload}

    def create_with_id(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria documento com ID específico (útil para migração do SQLite)"""
        payload = {k: _coerce_value(v) for k, v in data.items()}
        payload.setdefault("criado_em", _ts_now())
        payload.setdefault("atualizado_em", None)
        doc_ref = self.col.document(str(doc_id))  # Garante que ID seja string
        doc_ref.set(payload, merge=True)
        
        # Atualiza o contador se necessário
        try:
            numeric_id = int(doc_id)
            db = get_db()
            counter_ref = db.collection("_counters").document(self.collection_name)
            counter_doc = counter_ref.get()
            current_max = counter_doc.get("value") if counter_doc.exists else 0
            if numeric_id > current_max:
                counter_ref.set({"value": numeric_id})
        except ValueError:
            # ID não é numérico, não atualiza contador
            pass
        
        snap = doc_ref.get()
        return {"id": snap.id, **(snap.to_dict() or {})}

    def set(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {k: _coerce_value(v) for k, v in data.items()}
        payload["atualizado_em"] = _ts_now()
        doc_ref = self.col.document(str(doc_id))  # Garante que ID seja string
        doc_ref.set(payload, merge=True)
        snap = doc_ref.get()
        return {"id": snap.id, **(snap.to_dict() or {})}

    def delete(self, doc_id: str) -> None:
        self.col.document(str(doc_id)).delete()
    
    def migrate_from_sqlite_model(self, sqlite_objects, id_field="id"):
        """
        Migra dados do SQLite para Firestore mantendo os mesmos IDs numéricos
        
        Args:
            sqlite_objects: QuerySet ou lista de objetos do Django ORM
            id_field: nome do campo ID no modelo SQLite (padrão: 'id')
        """
        migrated_count = 0
        for obj in sqlite_objects:
            # Converte objeto Django para dict
            if hasattr(obj, '__dict__'):
                data = {}
                for field in obj._meta.fields:
                    if field.related_model:  # Pula campos de relacionamento
                        continue
                        
                    value = getattr(obj, field.name)
                    if field.name == id_field:
                        continue  # Não inclui o ID nos dados, usa como doc_id
                    
                    # Trata campos especiais do Django
                    if field.get_internal_type() in ['FileField', 'ImageField']:
                        # Campos de arquivo: salva o nome se existir, senão None
                        if value and hasattr(value, 'name') and value.name:
                            data[field.name] = value.name
                        else:
                            data[field.name] = None
                    else:
                        data[field.name] = value
                
                # Adiciona relacionamentos OneToOne se existir
                for field in obj._meta.fields:
                    if field.related_model and hasattr(obj, field.name):
                        related_obj = getattr(obj, field.name)
                        if related_obj:
                            data[f"{field.name}_id"] = related_obj.id
                            if hasattr(related_obj, 'username'):
                                data[f"{field.name}_username"] = related_obj.username
                
                # Usa o ID do SQLite como ID do documento Firestore
                doc_id = str(getattr(obj, id_field))
                self.create_with_id(doc_id, data)
                migrated_count += 1
        
        return migrated_count
