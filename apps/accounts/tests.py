from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from .schemas import FirebaseAuthSchema
from .api.auth_api import firebase_auth
from .services.auth_service import AuthService

User = get_user_model()


def _fake_decoded(**overrides):
    payload = {
        'uid': 'firebase-test-uid-123',
        'email': 'original@example.com',
        'phone_number': '',
    }
    payload.update(overrides)
    return payload


@override_settings(RATELIMIT_ENABLE=False)
class FirebaseProfileDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test-user',
            firebase_uid='firebase-test-uid-123',
            first_name='',
            last_name='',
            email='',
            is_approved=True,
        )

    @patch('apps.accounts.api.auth_api.verify_firebase_token')
    def test_firebase_auth_saves_name_email_avatar(self, mock_verify):
        mock_verify.return_value = _fake_decoded(uid='firebase-test-uid-123')
        request = MagicMock()
        payload = FirebaseAuthSchema(
            firebase_token='valid-token',
            name='John Doe',
            email='google@example.com',
            avatar='https://example.com/photo.jpg',
        )
        result = firebase_auth(request, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John Doe')
        self.assertEqual(self.user.email, 'google@example.com')
        self.assertEqual(self.user.avatar, 'https://example.com/photo.jpg')
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['user']['name'], 'John Doe')
        self.assertEqual(result['data']['user']['email'], 'google@example.com')
        self.assertEqual(result['data']['user']['avatar'], 'https://example.com/photo.jpg')

    @patch('apps.accounts.api.auth_api.verify_firebase_token')
    def test_firebase_auth_does_not_overwrite_existing_name(self, mock_verify):
        self.user.first_name = 'Existing'
        self.user.email = 'existing@example.com'
        self.user.avatar = 'https://example.com/existing.jpg'
        self.user.save()
        mock_verify.return_value = _fake_decoded(uid='firebase-test-uid-123')
        request = MagicMock()
        payload = FirebaseAuthSchema(
            firebase_token='valid-token',
            name='New Name',
            email='new@example.com',
            avatar='https://example.com/new.jpg',
        )
        result = firebase_auth(request, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Existing')
        self.assertEqual(self.user.email, 'existing@example.com')
        self.assertEqual(self.user.avatar, 'https://example.com/existing.jpg')

    @patch('apps.accounts.api.auth_api.verify_firebase_token')
    def test_firebase_auth_updates_only_missing_fields(self, mock_verify):
        self.user.first_name = 'Partial'
        self.user.save()
        mock_verify.return_value = _fake_decoded(uid='firebase-test-uid-123')
        request = MagicMock()
        payload = FirebaseAuthSchema(
            firebase_token='valid-token',
            name='Partial Name',
            email='partial@example.com',
            avatar='https://example.com/partial.jpg',
        )
        result = firebase_auth(request, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Partial')
        self.assertEqual(self.user.email, 'partial@example.com')
        self.assertEqual(self.user.avatar, 'https://example.com/partial.jpg')

    def test_auth_service_includes_avatar_in_response(self):
        self.user.avatar = 'https://example.com/avatar.jpg'
        self.user.save()
        decoded = _fake_decoded(uid='firebase-test-uid-123')
        result = AuthService.authenticate(decoded, device_payload=None)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['user']['avatar'], 'https://example.com/avatar.jpg')

    def test_auth_service_returns_none_avatar_when_empty(self):
        decoded = _fake_decoded(uid='firebase-test-uid-123')
        result = AuthService.authenticate(decoded, device_payload=None)
        self.assertTrue(result['success'])
        self.assertIsNone(result['data']['user']['avatar'])
