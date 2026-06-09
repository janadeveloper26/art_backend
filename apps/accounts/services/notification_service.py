from firebase_admin import messaging


class NotificationService:
    @staticmethod
    def send_device_approved(token: str):
        message = messaging.Message(
            data={
                'type': 'device_approved',
            },
            token=token,
        )

        messaging.send(message)
