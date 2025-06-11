import unittest
from unittest.mock import patch, MagicMock
from vive.modules.untis.client import UntisClient

class TestUntisClient(unittest.TestCase):

    @patch('vive.untis.client.requests.Session')
    def test_login_success(self, mock_session_class):
        mock_session = mock_session_class.return_value
        mock_session.post.return_value.json.return_value = {
            "result": {"personId": 12345}
        }

        client = UntisClient()
        client.login()

        self.assertTrue(client.logged_in)
        self.assertEqual(client.person_id, 12345)

    @patch('vive.untis.client.requests.Session')
    def test_login_failure(self, mock_session_class):
        mock_session = mock_session_class.return_value
        mock_session.post.return_value.json.return_value = {
            "error": {"message": "Invalid credentials"}
        }

        client = UntisClient()

        with self.assertRaises(Exception) as context:
            client.login()

        self.assertIn("Login failed", str(context.exception))

    @patch('vive.untis.client.requests.Session')
    def test_get_timetable_no_login(self, mock_session_class):
        client = UntisClient()
        with self.assertRaises(Exception) as context:
            client.get_timetable()

        self.assertIn("Not logged in", str(context.exception))

    @patch('vive.untis.client.requests.Session')
    def test_logout_without_login(self, mock_session_class):
        client = UntisClient()
        # Should not raise error
        client.logout()

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUntisClient))

