#!/usr/bin/env python
from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "catalog client"


# Connect to Database and create database session
engine = create_engine('sqlite:///Category_item.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('''Current user is already
        connected.'''), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    print login_session['username']
    print login_session['picture']
    print login_session['email']

    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        flash('%s Successfully created' % login_session['username'])

    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome,'
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return False


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        flash('%s Successfully disconnect' % login_session['username'])
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'

        return redirect('/catalog')
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Category Items
@app.route('/catalog/<string:category_title>/items/JSON')
def categoryJSON(category_title):
    category = session.query(Category).filter_by(title=category_title).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    return jsonify(Item=[i.serialize for i in items])


# JSON APIs to view Category specific Item
@app.route('/catalog/<string:category_title>/<string:item_title>/JSON')
def ItemJSON(category_title, item_title):
    category = session.query(Category).filter_by(title=category_title).one()
    item = session.query(Item).filter_by(title=item_title).one()
    return jsonify(Item=item.serialize)


# JSON APIs to view Catalog categories with Items
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    list = []
    for x in categories:
        items = session.query(Item).filter_by(category_id=x.id).all()
        category = {
            "title": x.title,
            "id": x.id,
            "user_id": x.user_id,
            "items": [r.serialize for r in items]}
        list.append(category)

    return jsonify(category=list)


# Show all categories
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    category = session.query(Category).order_by(asc(Category.title))
    items = session.query(Item).order_by(Item.id.desc()).limit(10)
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    user = session.query(User).all()
    for x in user:
        print x.email
    if 'email' in login_session:
        user = getUserInfo(getUserID(login_session['email']))
        return render_template(
            'catalog.html', categories=category,
            items=items, message="Latest Items", STATE=state, USER=user
            )
    else:
        return render_template(
            'catalog.html', categories=category,
            items=items, message="Latest Items", STATE=state
        )


# Show all Items in category
@app.route('/catalog/<string:category_title>/items/')
def showCategory(category_title):
    category = session.query(Category).order_by(asc(Category.title))
    selectedCategory = category.filter_by(title=category_title).one()
    items = session.query(Item).filter_by(
        category_id=selectedCategory.id).order_by(Item.id.desc()).all()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    if 'email' in login_session:
        user = getUserInfo(getUserID(login_session['email']))
        return render_template(
            'catalog.html', categories=category,
            items=items,
            message=category_title+" Items ("+str(len(items))+" items)",
            STATE=state, USER=user
        )
    else:
        return render_template(
            'catalog.html', categories=category,
            items=items,
            message=category_title+" Items ("+str(len(items))+" items)",
            STATE=state)


# Show Item
@app.route('/catalog/<string:category_title>/<string:item_title>/')
def showItem(category_title, item_title):
    selectedCategory = session.query(Category).filter_by(
        title=category_title).one()
    item = session.query(Item).filter_by(
        category_id=selectedCategory.id, title=item_title).one()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    if 'email' in login_session:
        user = getUserInfo(getUserID(login_session['email']))
        return render_template('item.html', Item=item, USER=user, STATE=state)
    else:
        return render_template('item.html', Item=item, STATE=state)


# Create a new item
@app.route('/catalog/items/new', methods=['GET', 'POST'])
def newItem():
    if 'email' not in login_session:
        return redirect('/catalog')
    categories = session.query(Category).all()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    if request.method == 'POST':
        newItem = Item(
            title=request.form['title'],
            description=request.form['description'],
            category_id=request.form['category'],
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Item %s Item Successfully Created' % (newItem.title))
        return redirect('/catalog')
    else:
        user = getUserInfo(getUserID(login_session['email']))
        return render_template(
            'newitem.html', categories=categories,
            STATE=state, USER=user)


# Edit an item
@app.route(
    '/catalog/<string:category_title>/<string:item_title>/edit',
    methods=['GET', 'POST'])
def editItem(category_title, item_title):
    if 'email' not in login_session:
        return redirect('/catalog')
    categories = session.query(Category).all()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    editedItem = session.query(Item).filter_by(title=item_title).one()
    category = session.query(Category).filter_by(title=category_title).one()
    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_id = request.form['category']

        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect('/catalog')
    else:
        user = getUserInfo(getUserID(login_session['email']))
        return render_template(
            'edititem.html', categories=categories,
            category=category, Item=editedItem, STATE=state, USER=user)


# Delete an item
@app.route(
    '/catalog/<string:category_title>/<string:item_title>/delete',
    methods=['GET', 'POST'])
def deleteItem(category_title, item_title):
    if 'email' not in login_session:
        return redirect('/catalog')
    category = session.query(Category).filter_by(title=category_title).one()
    itemToDelete = session.query(Item).filter_by(title=item_title).one()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('item Successfully Deleted')
        return redirect('/catalog')
    else:
        user = getUserInfo(getUserID(login_session['email']))
        return render_template(
            'deleteitem.html', item=itemToDelete,
            category=category, STATE=state, USER=user)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
