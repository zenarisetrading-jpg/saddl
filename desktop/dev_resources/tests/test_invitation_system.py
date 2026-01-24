#!/usr/bin/env python3
"""
Standalone Test Script for SADDL AdPulse Invitation System
============================================================

This script tests the invitation system in isolation without requiring
the full application to be running. Use this to verify the system works
before integration.

Usage:
    # From project root:
    python dev_resources/tests/test_invitation_system.py

    # Or with specific tests:
    python dev_resources/tests/test_invitation_system.py --test token
    python dev_resources/tests/test_invitation_system.py --test email
    python dev_resources/tests/test_invitation_system.py --test database
    python dev_resources/tests/test_invitation_system.py --test full

Requirements:
    - Python 3.9+
    - PostgreSQL database running with migration 005 applied
    - Environment variables configured (.env file)

Environment Variables Required:
    - DATABASE_URL or SUPABASE_DB_URL
    - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (for email tests)
    - APP_URL (optional, defaults to http://localhost:8501)
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from multiple locations (matching main app pattern)
from dotenv import load_dotenv
load_dotenv(project_root / ".env")           # desktop/.env
load_dotenv(project_root.parent / ".env")    # saddle/.env (parent directory)


# ============================================================================
# TEST UTILITIES
# ============================================================================

class TestColors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{TestColors.HEADER}{TestColors.BOLD}{'='*60}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{text}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{'='*60}{TestColors.ENDC}")


def print_section(text: str):
    print(f"\n{TestColors.OKCYAN}{TestColors.BOLD}--- {text} ---{TestColors.ENDC}")


def print_success(text: str):
    print(f"{TestColors.OKGREEN}✓ {text}{TestColors.ENDC}")


def print_fail(text: str):
    print(f"{TestColors.FAIL}✗ {text}{TestColors.ENDC}")


def print_warning(text: str):
    print(f"{TestColors.WARNING}⚠ {text}{TestColors.ENDC}")


def print_info(text: str):
    print(f"{TestColors.OKBLUE}ℹ {text}{TestColors.ENDC}")


# ============================================================================
# ENVIRONMENT CHECKS
# ============================================================================

def check_environment() -> dict:
    """Check required environment variables."""
    print_section("Environment Check")

    results = {
        'database': False,
        'smtp': False,
        'app_url': False
    }

    # Database
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if db_url:
        print_success(f"Database URL configured: {db_url[:30]}...")
        results['database'] = True
    else:
        print_fail("DATABASE_URL not configured")

    # SMTP
    smtp_vars = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD']
    smtp_status = all(os.environ.get(var) for var in smtp_vars)
    if smtp_status:
        print_success(f"SMTP configured: {os.environ.get('SMTP_HOST')}")
        results['smtp'] = True
    else:
        missing = [v for v in smtp_vars if not os.environ.get(v)]
        print_warning(f"SMTP partially configured. Missing: {missing}")

    # App URL
    app_url = os.environ.get("APP_URL", "http://localhost:8501")
    print_success(f"App URL: {app_url}")
    results['app_url'] = True

    return results


# ============================================================================
# TOKEN GENERATION TESTS
# ============================================================================

def test_token_generation():
    """Test secure token generation."""
    print_section("Token Generation Tests")

    from core.auth.invitation_service import InvitationService

    service = InvitationService()

    # Test 1: Token length and format
    token = service._generate_token()
    print_info(f"Generated token: {token}")

    assert len(token) == 43, f"Token length should be 43, got {len(token)}"
    print_success("Token has correct length (43 chars)")

    # Test 2: Tokens are unique
    tokens = [service._generate_token() for _ in range(100)]
    unique_tokens = set(tokens)
    assert len(unique_tokens) == 100, "Tokens should be unique"
    print_success("100 generated tokens are all unique")

    # Test 3: Token is URL-safe
    import re
    url_safe_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
    assert url_safe_pattern.match(token), "Token should be URL-safe"
    print_success("Token is URL-safe (base64url encoding)")

    # Test 4: Expiry calculation
    expiry = service._get_expiry_date()
    now = datetime.now(timezone.utc)
    days_diff = (expiry - now).days
    expected_days = int(os.environ.get("INVITATION_EXPIRY_DAYS", 7))
    assert days_diff >= expected_days - 1 and days_diff <= expected_days, \
        f"Expiry should be ~{expected_days} days, got {days_diff}"
    print_success(f"Expiry date calculation correct ({days_diff} days)")

    return True


# ============================================================================
# EMAIL TEMPLATE TESTS
# ============================================================================

def test_email_templates():
    """Test email template generation."""
    print_section("Email Template Tests")

    from core.auth.email_templates import (
        get_invitation_email_template,
        get_password_reset_email_template,
        get_welcome_email_template
    )

    # Test 1: Invitation template
    html = get_invitation_email_template(
        inviter_name="Test Admin",
        org_name="Test Organization",
        role="OPERATOR",
        invitation_url="http://localhost:8501/accept-invite?token=test123",
        expiry_days=7
    )
    assert len(html) > 1000, "Invitation template should be substantial"
    assert "Test Admin" in html, "Template should contain inviter name"
    assert "Test Organization" in html, "Template should contain org name"
    assert "OPERATOR" in html, "Template should contain role"
    assert "token=test123" in html, "Template should contain token"
    print_success("Invitation email template generated correctly")

    # Test 2: Password reset template
    html = get_password_reset_email_template(
        temp_password="PPC-abc123!",
        user_name="John Doe"
    )
    assert "PPC-abc123!" in html, "Template should contain password"
    assert "John Doe" in html, "Template should contain user name"
    print_success("Password reset email template generated correctly")

    # Test 3: Welcome template
    html = get_welcome_email_template(
        user_name="Jane Doe",
        org_name="Acme Corp",
        login_url="http://localhost:8501"
    )
    assert "Jane Doe" in html, "Template should contain user name"
    assert "Acme Corp" in html, "Template should contain org name"
    print_success("Welcome email template generated correctly")

    # Save preview for manual inspection
    preview_path = "/tmp/invitation_email_preview.html"
    with open(preview_path, "w") as f:
        f.write(get_invitation_email_template(
            inviter_name="John Admin",
            org_name="SADDL Demo",
            role="ADMIN",
            invitation_url="http://localhost:8501/accept-invite?token=demo123abc",
            expiry_days=7
        ))
    print_info(f"Preview saved to: {preview_path}")

    return True


# ============================================================================
# DATABASE CONNECTION TESTS
# ============================================================================

def test_database_connection():
    """Test database connectivity."""
    print_section("Database Connection Tests")

    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        print_fail("No DATABASE_URL configured - skipping database tests")
        return False

    from core.auth.invitation_service import InvitationService

    service = InvitationService()

    # Test 1: Connection
    try:
        conn = service._get_connection()
        print_success("Database connection successful")
        conn.close()
    except Exception as e:
        print_fail(f"Database connection failed: {e}")
        return False

    # Test 2: Check if table exists
    try:
        conn = service._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'user_invitations'
            );
        """)
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()

        if exists:
            print_success("user_invitations table exists")
        else:
            print_warning("user_invitations table does not exist - run migration 005")
            print_info("Run: psql -d your_database -f dev_resources/migrations/005_user_invitations.sql")
            return False

    except Exception as e:
        print_fail(f"Table check failed: {e}")
        return False

    # Test 3: Check table schema
    try:
        conn = service._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'user_invitations'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        cur.close()
        conn.close()

        expected_columns = [
            'id', 'email', 'token', 'organization_id', 'invited_by_user_id',
            'role', 'status', 'expires_at', 'created_at', 'accepted_at', 'created_user_id'
        ]
        actual_columns = [col[0] for col in columns]

        missing = set(expected_columns) - set(actual_columns)
        if missing:
            print_warning(f"Missing columns: {missing}")
        else:
            print_success(f"Table schema correct ({len(columns)} columns)")

    except Exception as e:
        print_fail(f"Schema check failed: {e}")
        return False

    return True


# ============================================================================
# EMAIL SENDING TESTS
# ============================================================================

def test_email_sending(test_email: str = None):
    """Test actual email sending (optional)."""
    print_section("Email Sending Tests")

    smtp_configured = all([
        os.environ.get("SMTP_HOST"),
        os.environ.get("SMTP_USER"),
        os.environ.get("SMTP_PASSWORD")
    ])

    if not smtp_configured:
        print_warning("SMTP not fully configured - skipping email send test")
        return None

    if not test_email:
        print_warning("No test email provided - skipping actual send")
        print_info("Use --email your@email.com to test sending")
        return None

    from utils.email_sender import EmailSender
    from core.auth.email_templates import get_invitation_email_template

    print_info(f"Sending test email to: {test_email}")

    sender = EmailSender()

    html = get_invitation_email_template(
        inviter_name="Test Script",
        org_name="SADDL AdPulse Test",
        role="OPERATOR",
        invitation_url="http://localhost:8501/accept-invite?token=TEST_TOKEN_123",
        expiry_days=7
    )

    success = sender.send_email(
        to_email=test_email,
        subject="[TEST] SADDL AdPulse Invitation System Test",
        html_content=html
    )

    if success:
        print_success(f"Test email sent successfully to {test_email}")
        print_info("Check your inbox (and spam folder)")
        return True
    else:
        print_fail("Email sending failed")
        return False


# ============================================================================
# FULL INTEGRATION TEST
# ============================================================================

def test_full_flow(cleanup: bool = True):
    """Test the complete invitation flow (requires database and valid UUIDs)."""
    print_section("Full Integration Test")

    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        print_warning("No database - skipping full flow test")
        return None

    from core.auth.invitation_service import InvitationService

    service = InvitationService()

    # First, check if we have any organizations to use
    try:
        conn = service._get_connection()
        cur = conn.cursor()

        # Get a test organization
        cur.execute("SELECT id, name FROM organizations LIMIT 1")
        org_row = cur.fetchone()

        if not org_row:
            print_warning("No organizations in database - cannot run full test")
            print_info("Create an organization first, then re-run")
            conn.close()
            return None

        org_id, org_name = str(org_row[0]), org_row[1]
        print_info(f"Using organization: {org_name} ({org_id[:8]}...)")

        # Get a test user (admin)
        cur.execute("SELECT id, email FROM users WHERE organization_id = %s LIMIT 1", (org_id,))
        user_row = cur.fetchone()

        if not user_row:
            print_warning("No users in organization - cannot run full test")
            conn.close()
            return None

        admin_id, admin_email = str(user_row[0]), user_row[1]
        print_info(f"Using admin: {admin_email} ({admin_id[:8]}...)")

        cur.close()
        conn.close()

    except Exception as e:
        print_fail(f"Setup failed: {e}")
        return False

    # Test email for invitation
    test_email = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"

    # Step 1: Create invitation
    print_info(f"Creating invitation for: {test_email}")
    result = service.create_invitation(
        email=test_email,
        organization_id=org_id,
        invited_by_user_id=admin_id,
        role="VIEWER",
        inviter_name="Test Admin",
        org_name=org_name
    )

    if result.success:
        print_success(f"Invitation created: {result.message}")
        token = result.invitation.token
        print_info(f"Token: {token[:20]}...")
    else:
        print_fail(f"Failed to create invitation: {result.message}")
        return False

    # Step 2: Validate token
    print_info("Validating token...")
    invitation = service.validate_token(token)

    if invitation:
        print_success(f"Token valid for: {invitation.email}")
        assert invitation.role == "VIEWER"
        assert invitation.status == "pending"
    else:
        print_fail("Token validation failed")
        return False

    # Step 3: Test resend
    print_info("Testing resend...")
    result2 = service.create_invitation(
        email=test_email,
        organization_id=org_id,
        invited_by_user_id=admin_id,
        role="VIEWER",
        inviter_name="Test Admin",
        org_name=org_name
    )

    if "resent" in result2.message.lower() or result2.success:
        print_success("Resend handled correctly")
    else:
        print_warning(f"Unexpected resend result: {result2.message}")

    # Step 4: List invitations
    print_info("Listing invitations...")
    invitations = service.list_invitations(org_id, status_filter="pending")
    found = any(inv.email == test_email for inv in invitations)

    if found:
        print_success(f"Found invitation in list ({len(invitations)} pending)")
    else:
        print_warning("Invitation not found in list")

    # Step 5: Accept invitation (simulate)
    print_info("Simulating acceptance...")
    # In real flow, a new user would be created first
    # For test, we'll just mark it accepted with a dummy user ID
    import uuid
    dummy_user_id = str(uuid.uuid4())

    accept_result = service.accept_invitation(token, dummy_user_id)

    if accept_result.success:
        print_success("Invitation accepted")
    else:
        print_fail(f"Accept failed: {accept_result.message}")

    # Step 6: Verify accepted status
    print_info("Verifying status...")
    invalid = service.validate_token(token)

    if invalid is None:
        print_success("Token correctly invalidated after acceptance")
    else:
        print_warning("Token should be invalid after acceptance")

    # Cleanup
    if cleanup:
        print_info("Cleaning up test data...")
        try:
            conn = service._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM user_invitations WHERE email = %s", (test_email,))
            conn.commit()
            cur.close()
            conn.close()
            print_success("Test data cleaned up")
        except Exception as e:
            print_warning(f"Cleanup failed: {e}")

    return True


# ============================================================================
# FEATURE FLAGS TESTS
# ============================================================================

def test_feature_flags():
    """Test feature flag system."""
    print_section("Feature Flags Tests")

    from config.features import (
        FeatureFlags,
        FEATURE_EMAIL_INVITATIONS,
        FEATURE_ONBOARDING_WIZARD,
        FEATURE_ENHANCED_EMPTY_STATES,
        get_app_url,
        get_invitation_expiry_days,
        get_password_requirements
    )

    # Test 1: Flag reading
    flags = FeatureFlags.get_all_flags()
    print_info(f"Current flags: {flags}")
    print_success("Feature flags loaded successfully")

    # Test 2: Convenience constants
    print_info(f"FEATURE_EMAIL_INVITATIONS: {FEATURE_EMAIL_INVITATIONS}")
    print_info(f"FEATURE_ONBOARDING_WIZARD: {FEATURE_ONBOARDING_WIZARD}")
    print_info(f"FEATURE_ENHANCED_EMPTY_STATES: {FEATURE_ENHANCED_EMPTY_STATES}")
    print_success("Convenience constants accessible")

    # Test 3: App settings
    print_info(f"App URL: {get_app_url()}")
    print_info(f"Invitation Expiry: {get_invitation_expiry_days()} days")
    print_info(f"Password Requirements: {get_password_requirements()}")
    print_success("Application settings accessible")

    # Test 4: Flag info
    info = FeatureFlags.get_flag_info()
    assert 'ENABLE_EMAIL_INVITATIONS' in info
    assert 'value' in info['ENABLE_EMAIL_INVITATIONS']
    print_success("Flag info retrieval works")

    # Test 5: Log output
    log = FeatureFlags.log_current_state()
    assert "Feature Flags Status:" in log
    print_success("Log output generation works")

    return True


# ============================================================================
# DESIGN SYSTEM TESTS
# ============================================================================

def test_design_system():
    """Test design system configuration."""
    print_section("Design System Tests")

    from config.design_system import (
        COLORS,
        TYPOGRAPHY,
        SPACING,
        GLASSMORPHIC,
        ComponentStyles,
        STREAMLIT_CUSTOM_CSS
    )

    # Test 1: Colors
    assert 'primary' in COLORS
    assert 'background' in COLORS
    assert COLORS['primary'].startswith('#')
    print_success(f"Colors loaded ({len(COLORS)} values)")

    # Test 2: Typography
    assert 'font_family' in TYPOGRAPHY
    assert 'heading_lg' in TYPOGRAPHY
    print_success(f"Typography loaded ({len(TYPOGRAPHY)} values)")

    # Test 3: Spacing
    assert 'md' in SPACING
    assert SPACING['md'] == '16px'
    print_success(f"Spacing loaded ({len(SPACING)} values)")

    # Test 4: Glassmorphic
    assert 'backdrop_filter' in GLASSMORPHIC
    assert 'blur' in GLASSMORPHIC['backdrop_filter']
    print_success(f"Glassmorphic effects loaded ({len(GLASSMORPHIC)} values)")

    # Test 5: Component styles
    card_style = ComponentStyles.card()
    assert 'background' in card_style
    assert 'border-radius' in card_style
    print_success("Component style generators work")

    # Test 6: Streamlit CSS
    assert len(STREAMLIT_CUSTOM_CSS) > 500
    assert '.stApp' in STREAMLIT_CUSTOM_CSS
    print_success("Streamlit custom CSS generated")

    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Test SADDL AdPulse Invitation System"
    )
    parser.add_argument(
        '--test',
        choices=['all', 'token', 'email', 'database', 'full', 'flags', 'design'],
        default='all',
        help='Which tests to run'
    )
    parser.add_argument(
        '--email',
        type=str,
        help='Email address for sending test email'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Do not clean up test data after full test'
    )

    args = parser.parse_args()

    print_header("SADDL AdPulse - Invitation System Tests")
    print(f"Project root: {project_root}")
    print(f"Test mode: {args.test}")

    # Environment check
    env = check_environment()

    # Track results
    results = {}

    # Run selected tests
    if args.test in ['all', 'flags']:
        try:
            results['feature_flags'] = test_feature_flags()
        except Exception as e:
            print_fail(f"Feature flags test error: {e}")
            results['feature_flags'] = False

    if args.test in ['all', 'design']:
        try:
            results['design_system'] = test_design_system()
        except Exception as e:
            print_fail(f"Design system test error: {e}")
            results['design_system'] = False

    if args.test in ['all', 'token']:
        try:
            results['token'] = test_token_generation()
        except Exception as e:
            print_fail(f"Token test error: {e}")
            results['token'] = False

    if args.test in ['all', 'email']:
        try:
            results['templates'] = test_email_templates()
        except Exception as e:
            print_fail(f"Template test error: {e}")
            results['templates'] = False

        if args.email:
            try:
                results['email_send'] = test_email_sending(args.email)
            except Exception as e:
                print_fail(f"Email send test error: {e}")
                results['email_send'] = False

    if args.test in ['all', 'database']:
        try:
            results['database'] = test_database_connection()
        except Exception as e:
            print_fail(f"Database test error: {e}")
            results['database'] = False

    if args.test in ['all', 'full']:
        if env['database']:
            try:
                results['full_flow'] = test_full_flow(cleanup=not args.no_cleanup)
            except Exception as e:
                print_fail(f"Full flow test error: {e}")
                import traceback
                traceback.print_exc()
                results['full_flow'] = False
        else:
            print_warning("Skipping full flow test - database not configured")

    # Summary
    print_header("Test Summary")

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results.items():
        if result is True:
            print_success(f"{test_name}: PASSED")
            passed += 1
        elif result is False:
            print_fail(f"{test_name}: FAILED")
            failed += 1
        else:
            print_warning(f"{test_name}: SKIPPED")
            skipped += 1

    print(f"\n{TestColors.BOLD}Total: {passed} passed, {failed} failed, {skipped} skipped{TestColors.ENDC}")

    if failed > 0:
        sys.exit(1)
    else:
        print_success("\nAll tests passed! The invitation system is ready.")
        sys.exit(0)


if __name__ == "__main__":
    main()
