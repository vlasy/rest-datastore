# -*- coding: utf-8 -*-
"""
    test_datastore
    ~~~~~~~~~~~~~~

    REST Datastore tests
"""

import requests
from pytest import fixture
from flask import Flask
from flask_security import Security
from flask_security.utils import encrypt_password
from rest_datastore import RESTUserDatastore


@fixture()
def datastore():
    return RESTUserDatastore("http://localhost:5000")


def create_roles(ds):
    for role in ('admin', 'editor', 'author'):
        ds.create_role(name=role)


def create_users(ds, count=None):
    users = [('matt@lp.com', 'matt', 'password', ['admin'], True),
             ('joe@lp.com', 'joe', 'password', ['editor'], True),
             ('dave@lp.com', 'dave', 'password', ['admin', 'editor'], True),
             ('jill@lp.com', 'jill', 'password', ['author'], True),
             ('tiya@lp.com', 'tiya', 'password', [], False),
             ('jess@lp.com', 'jess', None, [], True)]
    count = count or len(users)

    for u in users[:count]:
        pw = u[2]
        if pw is not None:
            pw = encrypt_password(pw)
        roles = [ds.find_or_create_role(rn) for rn in u[3]]
        ds.commit()
        user = \
            ds.create_user(email=u[0], username=u[1], password=pw, active=u[4])
        ds.commit()
        for role in roles:
            ds.add_role_to_user(user, role)
        ds.commit()


def populate_data(app, user_count=None):
    ds = app.security.datastore
    with app.app_context():
        create_roles(ds)
        create_users(ds, user_count)


def purge_data(app):
    requests.delete('http://localhost:5000/role')
    requests.delete('http://localhost:5000/user')


@fixture()
def app(request):
    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = 'secret'
    app.config['TESTING'] = True
    app.config['LOGIN_DISABLED'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    for opt in ['changeable', 'recoverable', 'registerable',
                'trackable', 'passwordless', 'confirmable']:
        app.config['SECURITY_' + opt.upper()] = opt in request.keywords

    if 'settings' in request.keywords:
        for key, value in request.keywords['settings'].kwargs.items():
            app.config['SECURITY_' + key.upper()] = value
    return app


def init_app_with_options(app, datastore, **options):
    security_args = options.pop('security_args', {})
    app.config.update(**options)
    app.security = Security(app, datastore=datastore, **security_args)
    purge_data(app)
    populate_data(app)


def test_get_user(app, datastore):
    init_app_with_options(app, datastore, **{
        'SECURITY_USER_IDENTITY_ATTRIBUTES': ('email', 'username')
    })

    with app.app_context():
        user_id = datastore.find_user(email='matt@lp.com').id

        user = datastore.get_user(user_id)
        assert user is not None

        user = datastore.get_user('matt@lp.com')
        assert user is not None

        user = datastore.get_user('matt')
        assert user is not None


def test_find_role(app, datastore):
    init_app_with_options(app, datastore)

    role = datastore.find_role('admin')
    assert role is not None

    role = datastore.find_role('bogus')
    assert role is None


def test_add_role_to_user(app, datastore):
    init_app_with_options(app, datastore)

    # Test with user object
    user = datastore.find_user(email='matt@lp.com')
    assert user.has_role('editor') is False
    assert datastore.add_role_to_user(user, 'editor') is True
    assert datastore.add_role_to_user(user, 'editor') is False
    assert user.has_role('editor') is True

    # Test with email
    assert datastore.add_role_to_user('jill@lp.com', 'editor') is True
    user = datastore.find_user(email='jill@lp.com')
    assert user.has_role('editor') is True

    # Test remove role
    assert datastore.remove_role_from_user(user, 'editor') is True
    assert datastore.remove_role_from_user(user, 'editor') is False


def test_create_user_with_roles(app, datastore):
    init_app_with_options(app, datastore)

    role = datastore.find_role('admin')
    datastore.commit()

    user = datastore.create_user(email='dude@lp.com', username='dude',
                                 password='password', roles=[role])
    datastore.commit()
    user = datastore.find_user(email='dude@lp.com')
    assert user.has_role('admin') is True


def test_delete_user(app, datastore):
    init_app_with_options(app, datastore)

    user = datastore.find_user(email='matt@lp.com')
    datastore.delete_user(user)
    datastore.commit()
    user = datastore.find_user(email='matt@lp.com')
    assert user is None


def test_find_or_create_user(app, datastore):
    init_app_with_options(app, datastore)

    role = datastore.find_role('admin')
    datastore.commit()

    user = datastore.create_user(email='dude@lp.com', username='dude',
                                 password='password', roles=[role])

    found = datastore.find_or_create_user(email="dude@lp.com")
    assert found['id'] is user['id']
    assert found['roles'][0]['name'] == role['name']

    userB = datastore.find_or_create_user(email="johndoe@lp.com")
    foundB = datastore.find_or_create_user(email="johndoe@lp.com")
    assert userB['id'] is foundB['id']
