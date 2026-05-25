"""
Notification Manager: Gère le stockage et la diffusion temps réel (SSE)
des notifications pour le candidat et l'équipe RH.
Conforme RGPD – Audit trail de suppression et traitement.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Service de notifications temps réel utilisant Server-Sent Events (SSE).
    Permet de notifier les candidats et les recruteurs des événements clés.
    """

    def __init__(self):
        # Liste des files d'attente actives pour les clients SSE connectés
        self.listeners: List[asyncio.Queue] = []

    async def create_notification(
        self,
        recipient: str,  # 'hr' ou candidate_id spécifique
        type_key: str,  # 'cv_upload', 'consent_accepted', 'analysis_started', 'analysis_completed', 'shortlisted', 'data_deleted'
        title: str,
        message: str,
        score: Optional[float] = None,
        candidate_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Crée une notification, l'enregistre en base et la diffuse aux écouteurs SSE."""
        from backend.database.mongo import MongoDB

        notification = {
            "id": f"notif_{datetime.now(timezone.utc).timestamp()}",
            "recipient": recipient,
            "type": type_key,
            "title": title,
            "message": message,
            "score": score,
            "candidate_id": candidate_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_read": False,
        }

        try:
            # Sauvegarder dans MongoDB
            col = MongoDB.get_collection("notifications")
            await col.insert_one(notification)
            logger.info(f"🔔 Notification created: {title} (recipient: {recipient})")
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")

        # Diffuser en temps réel aux clients connectés
        await self.broadcast(notification)
        return notification

    async def broadcast(self, notification: Dict[str, Any]) -> None:
        """Envoie la notification à tous les écouteurs SSE actifs."""
        for queue in list(self.listeners):
            try:
                await queue.put(notification)
            except Exception as e:
                logger.debug(f"Failed to push notification to queue: {e}")
                # Retirer la queue si elle est déconnectée ou erronée
                if queue in self.listeners:
                    self.listeners.remove(queue)

    async def get_notifications(
        self, recipient: str, limit: int = 20, unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Récupère l'historique des notifications pour un destinataire."""
        from backend.database.mongo import MongoDB
        try:
            col = MongoDB.get_collection("notifications")
            query = {"recipient": recipient}
            if unread_only:
                query["is_read"] = False

            cursor = col.find(query).sort("timestamp", -1).limit(limit)
            from backend.database.mongo import MOTOR_AVAILABLE
            if MOTOR_AVAILABLE:
                return await cursor.to_list(length=limit)
            else:
                return await cursor
        except Exception as e:
            logger.error(f"Failed to list notifications: {e}")
            return []

    async def mark_as_read(self, notification_id: str) -> bool:
        """Marque une notification comme lue."""
        from backend.database.mongo import MongoDB
        try:
            col = MongoDB.get_collection("notifications")
            await col.update_one({"id": notification_id}, {"$set": {"is_read": True}})
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification {notification_id} as read: {e}")
            return False

    async def mark_all_as_read(self, recipient: str) -> bool:
        """Marque toutes les notifications d'un utilisateur comme lues."""
        from backend.database.mongo import MongoDB
        try:
            col = MongoDB.get_collection("notifications")
            await col.update_many({"recipient": recipient, "is_read": False}, {"$set": {"is_read": True}})
            return True
        except Exception as e:
            logger.error(f"Failed to mark all as read for {recipient}: {e}")
            return False

    async def stream_notifications(self, recipient: str):
        """Générateur asynchrone SSE pour diffuser les notifications."""
        queue = asyncio.Queue()
        self.listeners.append(queue)
        logger.info(f"SSE Client connected for notifications (recipient: {recipient})")

        try:
            while True:
                notification = await queue.get()
                # Filtrer par destinataire
                # 'hr' reçoit toutes les notifications de type RH et globales.
                # Un candidat reçoit uniquement les siennes.
                if recipient == "hr" or notification["recipient"] == recipient:
                    yield f"data: {import_json_dumps(notification)}\n\n"
        except asyncio.CancelledError:
            logger.info(f"SSE Client disconnected for notifications (recipient: {recipient})")
        finally:
            if queue in self.listeners:
                self.listeners.remove(queue)


def import_json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj)


# Singleton
notification_manager = NotificationManager()
