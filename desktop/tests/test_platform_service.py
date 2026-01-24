import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import uuid
from datetime import datetime

# Add desktop to path
desktop_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if desktop_path not in sys.path:
    sys.path.insert(0, desktop_path)

from core.platform_service import PlatformService, OrganizationResult

class TestPlatformService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        
        self.mock_db._get_connection.return_value.__enter__.return_value = self.mock_conn
        self.mock_conn.cursor.return_value.__enter__.return_value = self.mock_cursor
        
        self.mock_invite_service = MagicMock()
        
        with patch('core.platform_service.PostgresManager', return_value=self.mock_db), \
             patch('core.platform_service.InvitationService', return_value=self.mock_invite_service):
            self.service = PlatformService()

    def test_list_organizations(self):
        # Setup mock return data
        self.mock_cursor.fetchall.return_value = [
            (uuid.uuid4(), 'Org A', datetime.now(), 'ACTIVE', 5, 1),
            (uuid.uuid4(), 'Org B', datetime.now(), 'ACTIVE', 3, 1)
        ]
        
        orgs = self.service.list_organizations()
        
        self.assertEqual(len(orgs), 2)
        self.assertEqual(orgs[0].name, 'Org A')
        self.assertEqual(orgs[0].user_count, 5)

    def test_create_organization_success(self):
        # Setup mocks
        self.mock_cursor.fetchone.return_value = None # No existing org
        
        mock_invite_result = MagicMock()
        mock_invite_result.success = True
        self.mock_invite_service.create_invitation.return_value = mock_invite_result
        
        # Execute
        result = self.service.create_organization("New Org", "admin@new.com", "creator-uuid")
        
        # Verify
        self.assertTrue(result.success)
        self.assertIn("Created organization", result.message)
        
        # Verify DB calls
        self.assertTrue(self.mock_cursor.execute.called)
        # Verify invite call
        self.mock_invite_service.create_invitation.assert_called_once()
        args = self.mock_invite_service.create_invitation.call_args[1]
        self.assertEqual(args['email'], "admin@new.com")
        self.assertEqual(args['role'], "OWNER")

    def test_create_organization_duplicate(self):
        # Setup mock to return existing org
        self.mock_cursor.fetchone.return_value = ("existing-id",)
        
        result = self.service.create_organization("Existing Org", "admin@new.com")
        
        self.assertFalse(result.success)
        self.assertIn("already exists", result.message)
        
    def test_create_organization_invalid_input(self):
        result = self.service.create_organization("", "admin@new.com")
        self.assertFalse(result.success)
        
        result = self.service.create_organization("Org", "invalid-email")
        self.assertFalse(result.success)

if __name__ == '__main__':
    unittest.main()
