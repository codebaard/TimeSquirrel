import functools
import os

from flask import(
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash
from app.databaseHandler import get_db 

bp = Blueprint('login', __name__, url_prefix='/login')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST': #means that the user submitted data
        username = request.form['username'].lower()
        password = request.form['password']
        email = request.form['email'].lower()
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username, )
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)
        elif db.execute(
            'SELECT id FROM user WHERE email = ?', (email, )
        ).fetchone() is not None:
            error = 'The email you entered is alreay being used.'  

        if error is None:
            db.execute(
                'INSERT INTO user (username, password_hash, email) VALUES (?,?,?)',
                (username, generate_password_hash(password), email) 
            )
            db.commit()
            return redirect(url_for('landing.dashboard'))        
        
        flash(error)

    return render_template('login/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * from user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'User does not exist.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'

        if error == None:
            session.clear()
            session['user_id'] = user['id']

            return redirect(url_for('index'))

        flash(error)            

    return render_template('login/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login.login'))

        return view(**kwargs)
    return wrapped_view