import os

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm
from models import db, connect_db, User, Message, Follows, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler'))
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
# toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.context_processor
def context_processor():
    """Now form will be available globally across all jinja templates"""
    form = MessageForm()
    return dict(form=form)

def not_signed_in():
    """If user not signed in"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
                header_image_url = form.header_image_url.data,
                location = form.location.data,
                bio = form.bio.data
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', user_form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', user_form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()
    flash("See you later, alligator!!!","success")
    return redirect('/login')


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>', methods=["GET","POST"])
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)
    
    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())

    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    not_signed_in()

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    not_signed_in()

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    not_signed_in()

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    not_signed_in()

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    not_signed_in()
    form = UserAddForm(obj=g.user)

    if form.validate_on_submit():

        user = User.authenticate(form.username.data,form.password.data)
        """update all fields, correct password needs to be entered to update"""
        if user:
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data,
            g.user.location = form.location.data,
            g.user.bio = form.bio.data
            db.session.commit()
            return redirect(f'/users/{g.user.id}')

        flash("Invalid password", 'danger')
        return redirect('/')

    return render_template('users/login.html', user_form=form)

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    not_signed_in()
    
    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET","POST"])
def messages_add():
    """Create a message on the front end(modal window) and save it in the database"""
    not_signed_in()
    text = request.json["text"]
    msg = Message(text=text)
    g.user.messages.append(msg)
    db.session.commit()

    return (jsonify(message=msg.serialize()), 201)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    not_signed_in()

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages

@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        following = [user.id for user in g.user.following]
        messages = (Message
                   .query
                   .filter(Message.user_id.in_(following))
                   .order_by(Message.timestamp.desc())
                   .limit(100)
                   .all())
        
        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')

@app.route('/users/add_like/<int:message_id>', methods=["POST","DELETE"])
def like_unlike_post(message_id):
    """Add/Delete liked messages"""
    not_signed_in()
    
    message = Message.query.get(message_id)
    if message not in g.user.likes:
        like = Likes(user_id=message.user_id,message_id=message_id)
        g.user.likes.append(message)
        db.session.commit()
        serialized = like.serialize()
        like = Likes.query.filter(Likes.message_id == message_id).first()
        return jsonify(like=serialized), 201
    else:
        like = Likes.query.filter(Likes.message_id == message_id).first()
        db.session.delete(like)
        db.session.commit()
        return jsonify(message="Deleted")
    return render_template('home.html')

@app.route('/messages/liked')
def liked_posts():
    """Will diplay only liked messages of the users the authorized user follows"""
    not_signed_in()
    return render_template('home.html',messages=g.user.likes)


    




##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
