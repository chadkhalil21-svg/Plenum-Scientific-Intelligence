"""Offline regression checks for gcloud/Cloud Storage private bucket metadata."""
import unittest
from scripts.verify_browser_bucket_metadata import assert_private_bucket


class PrivateBucketMetadataTests(unittest.TestCase):
    def test_gcloud_normalized_schema(self):
        self.assertTrue(assert_private_bucket({
            "name": "bucket", "public_access_prevention": "enforced",
            "uniform_bucket_level_access": True
        }))

    def test_storage_json_api_schema(self):
        self.assertTrue(assert_private_bucket({
            "iamConfiguration": {
                "publicAccessPrevention": "enforced",
                "uniformBucketLevelAccess": {"enabled": True}
            }
        }))

    def test_normalized_dict_iam_schema(self):
        self.assertTrue(assert_private_bucket({
            "iam_config": {
                "public_access_prevention": "enforced",
                "uniform_bucket_level_access": {"enabled": True}
            }
        }))

    def test_fail_closed_when_missing_or_unsafe(self):
        for d in (
            {}, [], {"public_access_prevention": "inherited", "uniform_bucket_level_access": True},
            {"public_access_prevention": "enforced", "uniform_bucket_level_access": False},
            {"public_access_prevention": "enforced", "uniform_bucket_level_access": "true"},
        ):
            with self.subTest(d=d), self.assertRaises(ValueError):
                assert_private_bucket(d)


if __name__ == "__main__":
    unittest.main()
