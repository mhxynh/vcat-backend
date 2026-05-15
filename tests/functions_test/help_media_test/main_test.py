import os
from unittest import TestCase
from unittest.mock import patch

from functions.help_media import main as help_media


class TestHelpMedia(TestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {
                "HELP_MEDIA_BUCKET_NAME": "vcat-help-videos",
                "HELP_MEDIA_PRESIGNED_URL_TTL_SECONDS": "900",
            },
            clear=False,
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()

    @patch("functions.help_media.main.S3Utils.generate_presigned_get_url")
    def test_get_help_media_returns_signed_url(self, mock_generate_url):
        mock_generate_url.return_value = "https://signed.example/quickstart.mp4"

        response = help_media.lambda_handler(
            {
                "httpMethod": "GET",
                "queryStringParameters": {"key": "/help-assets/quickstart.mp4"},
            },
            None,
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("quickstart.mp4", response["body"])
        self.assertIn("https://signed.example/quickstart.mp4", response["body"])
        mock_generate_url.assert_called_once_with(
            bucket_name="vcat-help-videos",
            object_key="quickstart.mp4",
            expires_in=900,
        )

    @patch("functions.help_media.main.S3Utils.generate_presigned_get_url")
    def test_get_help_media_rejects_parent_directory_key(self, mock_generate_url):
        response = help_media.lambda_handler(
            {
                "httpMethod": "GET",
                "queryStringParameters": {"key": "../secret.mp4"},
            },
            None,
        )

        self.assertEqual(response["statusCode"], 400)
        mock_generate_url.assert_not_called()

    @patch("functions.help_media.main.S3Utils.generate_presigned_get_url")
    def test_get_help_media_rejects_unapproved_extension(self, mock_generate_url):
        response = help_media.lambda_handler(
            {
                "httpMethod": "GET",
                "queryStringParameters": {"key": "secret.txt"},
            },
            None,
        )

        self.assertEqual(response["statusCode"], 400)
        mock_generate_url.assert_not_called()

    @patch("functions.help_media.main.S3Utils.generate_presigned_get_url")
    def test_get_help_media_requires_bucket_config(self, mock_generate_url):
        with patch.dict(os.environ, {"HELP_MEDIA_BUCKET_NAME": ""}, clear=False):
            response = help_media.lambda_handler(
                {
                    "httpMethod": "GET",
                    "queryStringParameters": {"key": "quickstart.mp4"},
                },
                None,
            )

        self.assertEqual(response["statusCode"], 500)
        mock_generate_url.assert_not_called()
