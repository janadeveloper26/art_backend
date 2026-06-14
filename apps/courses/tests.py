from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.conf import settings

from .api import _get_cf_signer, _cloudfront_signed_url, _get_s3
from . import api as courses_api


def _reset_cf_cache():
    courses_api._cf_signer = None
    courses_api._cf_signer_expires = 0


class CloudFrontSignerTests(TestCase):
    def test_get_cf_signer_returns_none_when_no_keys(self):
        with override_settings(CLOUDFRONT_KEY_ID=None, CLOUDFRONT_PRIVATE_KEY=None):
            _reset_cf_cache()
            self.assertIsNone(_get_cf_signer())

    def test_get_cf_signer_returns_signer_with_file_key(self):
        _reset_cf_cache()
        signer = _get_cf_signer()
        self.assertIsNotNone(signer)
        self.assertEqual(signer.key_id, settings.CLOUDFRONT_KEY_ID)

    def test_get_cf_signer_returns_signer_with_inline_pem(self):
        pem = Path(settings.CLOUDFRONT_PRIVATE_KEY).read_bytes().decode()
        with override_settings(CLOUDFRONT_PRIVATE_KEY=pem):
            _reset_cf_cache()
            signer = _get_cf_signer()
            self.assertIsNotNone(signer)

    def test_cloudfront_signed_url_returns_cf_url_when_signer_available(self):
        url = _cloudfront_signed_url('lessons/videos/test.mp4', expires_in=3600)
        self.assertTrue(url.startswith(f'https://{settings.CLOUDFRONT_DOMAIN}/'))
        self.assertIn('Expires=', url)
        self.assertIn('Signature=', url)
        self.assertIn('Key-Pair-Id=', url)

    @override_settings(CLOUDFRONT_DOMAIN=None)
    def test_cloudfront_signed_url_falls_back_to_s3_when_no_cf_domain(self):
        url = _cloudfront_signed_url('lessons/videos/test.mp4', expires_in=3600)
        self.assertTrue(url.startswith('https://'))
        self.assertIn('X-Amz-Signature=', url)
        self.assertIn('X-Amz-Credential=', url)
        self.assertIn('X-Amz-Expires=', url)

    @override_settings(CLOUDFRONT_KEY_ID=None, CLOUDFRONT_PRIVATE_KEY=None)
    def test_cloudfront_signed_url_falls_back_to_s3_when_no_signer(self):
        url = _cloudfront_signed_url('lessons/videos/test.mp4', expires_in=3600)
        self.assertTrue(url.startswith('https://'))
        self.assertIn('X-Amz-Signature=', url)
