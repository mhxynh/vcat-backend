from unittest import TestCase
from unittest.mock import MagicMock, patch

from utils.s3_utils import S3Utils


class TestS3Utils(TestCase):
	# is_s3_event

	def test_is_s3_event_returns_false_for_non_dict(self):
		self.assertFalse(S3Utils.is_s3_event("not-a-dict"))

	def test_is_s3_event_returns_false_for_missing_records(self):
		self.assertFalse(S3Utils.is_s3_event({}))

	def test_is_s3_event_returns_false_for_non_s3_source(self):
		event = {"Records": [{"eventSource": "aws:sns"}]}
		self.assertFalse(S3Utils.is_s3_event(event))

	def test_is_s3_event_returns_true_for_s3_source(self):
		event = {"Records": [{"eventSource": "aws:s3"}]}
		self.assertTrue(S3Utils.is_s3_event(event))

	# get_client

	@patch("utils.s3_utils.boto3.client")
	def test_get_client_uses_s3_sigv4(self, mock_boto_client):
		mock_client = MagicMock()
		mock_boto_client.return_value = mock_client

		client = S3Utils.get_client()

		self.assertEqual(client, mock_client)
		args, kwargs = mock_boto_client.call_args
		self.assertEqual(args[0], "s3")
		self.assertEqual(kwargs["config"].signature_version, "s3v4")

	# get_object_bytes

	@patch("utils.s3_utils.S3Utils.get_client")
	def test_get_object_bytes_returns_body_content_type_and_length(self, mock_get_client):
		body = MagicMock()
		body.read.return_value = b"abc"
		client = MagicMock()
		client.get_object.return_value = {
			"Body": body,
			"ContentType": "text/csv",
			"ContentLength": 10,
		}
		mock_get_client.return_value = client

		body_bytes, content_type, content_length = S3Utils.get_object_bytes(
			"bucket", "key"
		)

		self.assertEqual(body_bytes, b"abc")
		self.assertEqual(content_type, "text/csv")
		self.assertEqual(content_length, 10)
		client.get_object.assert_called_once_with(Bucket="bucket", Key="key")

	@patch("utils.s3_utils.S3Utils.get_client")
	def test_get_object_bytes_uses_body_len_when_length_missing(self, mock_get_client):
		body = MagicMock()
		body.read.return_value = b"abcd"
		client = MagicMock()
		client.get_object.return_value = {
			"Body": body,
			"ContentType": "text/plain",
		}
		mock_get_client.return_value = client

		body_bytes, content_type, content_length = S3Utils.get_object_bytes(
			"bucket", "key"
		)

		self.assertEqual(body_bytes, b"abcd")
		self.assertEqual(content_type, "text/plain")
		self.assertEqual(content_length, 4)

	# get_file_from_s3

	@patch("utils.s3_utils.S3Utils.get_object_bytes")
	def test_get_file_from_s3_returns_body_and_content_type(self, mock_get_object_bytes):
		mock_get_object_bytes.return_value = (b"file-bytes", "text/csv", 10)

		body_bytes, content_type = S3Utils.get_file_from_s3("bucket", "key")

		self.assertEqual(body_bytes, b"file-bytes")
		self.assertEqual(content_type, "text/csv")

	@patch("utils.s3_utils.S3Utils.get_object_bytes")
	def test_get_file_from_s3_raises_when_content_length_exceeds_limit(
		self, mock_get_object_bytes
	):
		mock_get_object_bytes.return_value = (
			b"small-body",
			"text/csv",
			(2 * 1024 * 1024),
		)

		with self.assertRaises(ValueError):
			S3Utils.get_file_from_s3("bucket", "key", max_file_size_mb=1)

	@patch("utils.s3_utils.S3Utils.get_object_bytes")
	def test_get_file_from_s3_with_limit_returns_when_under_limit(
		self, mock_get_object_bytes
	):
		body_bytes = b"x" * 1024
		mock_get_object_bytes.return_value = (body_bytes, "text/csv", len(body_bytes))

		returned_body, content_type = S3Utils.get_file_from_s3(
			"bucket", "key", max_file_size_mb=1
		)

		self.assertEqual(returned_body, body_bytes)
		self.assertEqual(content_type, "text/csv")

	@patch("utils.s3_utils.S3Utils.get_object_bytes")
	def test_get_file_from_s3_raises_when_body_size_exceeds_limit(
		self, mock_get_object_bytes
	):
		oversized_body = b"x" * ((1 * 1024 * 1024) + 1)
		mock_get_object_bytes.return_value = (oversized_body, "text/csv", 1)

		with self.assertRaises(ValueError):
			S3Utils.get_file_from_s3("bucket", "key", max_file_size_mb=1)

	# generate_presigned_put_url

	@patch("utils.s3_utils.S3Utils.get_client")
	def test_generate_presigned_put_url_uses_expected_params(self, mock_get_client):
		client = MagicMock()
		client.generate_presigned_url.return_value = "https://example.com/upload"
		mock_get_client.return_value = client

		url = S3Utils.generate_presigned_put_url(
			bucket_name="uploads-bucket",
			object_key="control-metadata/file.csv",
			content_type="text/csv",
			expires_in=900,
		)

		self.assertEqual(url, "https://example.com/upload")
		client.generate_presigned_url.assert_called_once_with(
			"put_object",
			Params={
				"Bucket": "uploads-bucket",
				"Key": "control-metadata/file.csv",
				"ContentType": "text/csv",
			},
			ExpiresIn=900,
		)
