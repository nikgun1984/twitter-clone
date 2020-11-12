"""User View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.testuser1 = User.signup(username="testuser1",
                                    email="test@test.com",
                                    password="testuser1")
        uid1 = 1111
        self.testuser1.id = uid1

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2")

        uid2 = 2222
        self.testuser2.id = uid2

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_show_following(self):
        follower = Follows(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id)
        """Test if testuser1 follows testuser2"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.get(f"/users/{self.testuser1.id}/following")

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))

    def test_users_followers(self):
        """Test followers"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.get(f"/users/{self.testuser1.id}/followers")

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code,200)
            self.assertIn("@testuser1", str(resp.data))

    def test_unauthorised_access_to_see_following(self):
        """Test if access denied to the users user following"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser1.id}/following",follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    
    def test_unauthorised_access_to_see_followers(self):
        """Test if access denied to the followers"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser1.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))


    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser1.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))


            
