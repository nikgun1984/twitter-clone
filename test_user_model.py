"""User model tests."""

# run these tests like:
#
# python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        self.u1 = User(
            email='test2@test.com',
            username="testuser2",
            password="HASHED_PASSWORD"
        )

    def test_user_model(self):
        """Does basic model work?"""

        db.session.add(self.u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(self.u.messages), 0)
        self.assertEqual(len(self.u.followers), 0)

    def test_repr(self):
        """Will test __repr__ method"""
        self.assertEqual(str(self.u),self.u.__repr__())

    def test_is_following(self):
        self.u.following.append(self.u1)
        self.assertEqual(self.u.is_following(self.u1), True)

    def test_is_not_following(self):
        self.assertNotEqual(self.u.is_following(self.u1), True)

    def test_is_followed_by(self):
        self.u.followers.append(self.u1)
        self.assertEqual(self.u.is_followed_by(self.u1), True)

    def test_is_not_followed(self):
        self.assertNotEqual(self.u.is_followed_by(self.u1), True)

    def test_signup(self):

        self.assertEqual(User.signup('testuser','test@test.com','HASHED_PASSWORD'),self.u)


    


