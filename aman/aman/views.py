
import sys
from os import environ
import random, string
from datetime import datetime
from flask import Flask,render_template, Request, url_for, redirect, flash, jsonify, Session, session, request, make_response
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from database_setup import Base, Restaurant, MenuItem, User
from flask import session as login_session
from aman import app
from oauth2client.client import flow_from_clientsecrets, AccessTokenCredentials
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests


with open("client_secret.json") as json_file:
    CLIENT_ID = json.load(json_file)['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

engine=create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.create_all(engine)

DBSession=sessionmaker(bind=engine)
session=DBSession()

@app.route('/')
@app.route('/login1')
def showLogin1():
    state=''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state']=state
    return render_template("index1.html",STATE=state )

@app.route('/restaurant')
def showRestaurants():
    restaurant=session.query(Restaurant).all()
    if 'username' not in login_session:
        return render_template('publicrestaurants.html',restaurant=restaurant)
    else:
        return render_template("restaurants.html",restaurant=restaurant)


#@app.route('/login')
#def showLogin():
#    state=''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
#    login_session['state']=state
#    #return "The current session state is %s" %login_session['state']
#    return render_template("login.html", STATE=state)



@app.route('/aboutme')
def showResume():
    return render_template("resume.html")

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    #print login_session['state']
    #print request.args.get('state')
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    #print app_id
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    #print app_secret
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    #print result

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token=result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    #print "url sent for API access:%s"% url
    #print "API JSON result: %s" % result
    data = json.loads(result)
    #data=json.loads(h.request(url, 'GET')[1])
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token=token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    
    if request.args.get('state')!= login_session['state']:
        response=make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code=request.data
    try:
        oauth_flow=flow_from_clientsecrets('client_secret.json',scope='')
        oauth_flow.redirect_uri= 'postmessage'
        credentials= oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response=make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type']='application/json'
        return response
    access_token=credentials.access_token
    url=('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %access_token)
    h=httplib2.Http() 
    result=json.loads((h.request(url, 'GET')[1]))
    
    if result.get('error') is not None:
        response=make_response(json.dumps(result.get('error')),500)
        response.headers['Content-Type']='application/json'
    gplus_id=credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response=make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type']='application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        reponse=make_response(json.dumps("Token's client ID does not match app's."),401)
        print ("Token's client ID does not match app's")
        response.headers['Content-Type']= 'application/json'
        return response
    stored_credentials=login_session.get('credentials')
    stored_gplus_id=login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id==stored_gplus_id:
        response=make_response(json.dumps('You are already connected.'),200)
        response.headers['Content-Type']='application/json'
        return response
    login_session['credentials']=credentials.access_token
    login_session['gplus_id']=gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    #data=json.loads(answer.text)
    data = answer.json()
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id=getUserId(login_session['email'])
    if not user_id:
        user_id=createUser(login_session)
    login_session['user_id']= user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    #print ("done!")
    
    return output
#    #return redirect( url_for('showRestaurants'))



##user helper function

def createUser(login_session):
    newUser=User(name=login_session['username'], email=login_session['email'],
                  picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user=session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user=session.query(User).filter_by(id=user_id).one()
    return user

def getUserId(email):
    try:
        user=session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None
def getCreatorInfo(name):
    restaurant = session.query(Restaurant).filter_by(name=name).one()
    return restaurant.user_id

app.jinja_env.globals.update(getCreatorInfo=getCreatorInfo)
app.jinja_env.globals.update(getUserInfo=getUserInfo)


@app.route('/gdisconnect')
def gdisconnect():
    #access_token = login_session['access_token']
    access_token = login_session['credentials']
    #credentials=login_session.get('credentials')
    #print ("In gdisconnect access token is %s", access_token)
    #print ("User name is: " )
    #print (login_session['username'])
    if access_token is None:
        #print ("Access Token is None")
    	response = make_response(json.dumps('Current user not connected.'), 401)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    #access_token=credentials.access_token
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    #print 'result is '
    #print result
    #if result['status'] == '200':
    #    #del login_session['access_token'] 
    #    del access_token
    #    del login_session['gplus_id']
    #    del login_session['username']
    #    del login_session['email']
    #    del login_session['picture']
    #    response = make_response(json.dumps('Successfully disconnected.'), 200)
    #    response.headers['Content-Type'] = 'application/json'
    #    return response
    #else:
    #    response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    #    response.headers['Content-Type'] = 'application/json'
    #    return response
    if result['status'] != '200':
         response = make_response(json.dumps('Failed to revoke token for given user.', 400))
         response.headers['Content-Type'] = 'application/json'
         return response



@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id'] 
            del login_session['credentials'] 
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showLogin1'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showRestaurants'))



#@app.route('/restaurant')
#def showRestaurants():
#    restaurant=session.query(Restaurant).all()
#    #return "This Page will show all my restaurants"
#    return render_template("restaurants.html",restaurant=restaurant)

@app.route('/restaurant/new',methods=['GET','POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect('/login')
    #return "This page will be for making new restaurant"
    if request.method=='POST':
        newrestaurant=Restaurant(name=request.form['name'],user_id=getUserId(login_session['email']))
        session.add(newrestaurant)
        session.commit()
        flash("New Restaurant created!")
        return redirect( url_for('showRestaurants'))
    else:
        return render_template("newRestaurant.html")


@app.route('/restaurant/<restaurant_id>/edit',methods=['GET','POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    edititem=session.query(Restaurant).filter_by(id=restaurant_id).one()
    if getUserId(login_session['email'])==edititem.user_id:
        if request.method=='POST':
            if request.form['name']:
                edititem.name=request.form['name']
            session.add(edititem)
            session.commit()
            flash(" Restaurant edited!")
            return redirect( url_for('showRestaurants'))
        else:
            #return "<Script>alert('Sorry!! Cannot edit other user's restaurant.')</Script>"
    #else:       
            return render_template('editRestaurant.html',i=edititem)



    #return ("This page will be for editing restaurant"+restaurant_id)
    return render_template("editRestaurant.html")
    
@app.route('/restaurant/<restaurant_id>/delete',methods=['GET','POST'])
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemtodelete=session.query(Restaurant).filter_by(id=restaurant_id).one()
    if itemtodelete.user_id != login_session['user_id']:
      return "<sript>function myFunction() {alert(YOU ARE NOT AUTHORIZED TO DELETE THIS RESTAURANT.);}</script><body onload='myFunction()''>"
    if request.method=='POST':
        session.delete(itemtodelete)
        session.commit()
        flash("Restaurant deleted!")
        return redirect( url_for('showRestaurants'))
    else:
    #return ("This page will be for deleting restaurant"+restaurant_id)
        return render_template("deleteRestaurant.html",i=itemtodelete)

@app.route('/restaurant/<restaurant_id>/menu',methods=['GET','POST'])
def showMenu(restaurant_id):
    
    restaurant=session.query(Restaurant).filter_by(id=restaurant_id).one()
    creator=getUserInfo(restaurant.user_id)
    items=session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    if 'username' not in login_session or creator.id!=login_session['user_id']:
        return render_template('publicmenu.html', items = items, restaurant = restaurant,creator=creator)
    else:
        return render_template('menu.html',restaurantfetched=restaurant,i=items,creator=creator)
    
    

@app.route('/restaurant/<restaurant_id>/menu/new',methods=['GET','POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method=='POST':
        newitem=MenuItem(name=request.form['name'],course=request.form['course'],description=request.form['description'],price=request.form['price'],restaurant_id=restaurant_id)
        session.add(newitem)
        session.commit()
        flash("New Menu Item created!")
        return redirect(url_for('showMenu',restaurant_id=restaurant_id))
    else:
        return render_template('newMenuItem.html',restaurant_id=restaurant_id)
    #return "This page is for making new menu item for restaurant"+ restaurant_id
    
@app.route('/restaurant/<restaurant_id>/menu/<menu_id>/edit',methods=['GET','POST'])
def editMenuItem(restaurant_id,menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    edititem=session.query(MenuItem).filter_by(restaurant_id=restaurant_id,id=menu_id).one()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method=='POST':
        
        if request.form['name']:
            edititem.name = request.form['name']
        if request.form['description']:
            edititem.description = request.form['description']
        if request.form['price']:
            edititem.price = request.form['price']
        if request.form['course']:
            edititem.course = request.form['course']
        session.add(edititem)
        session.commit() 
        flash(" Menu Item edited!")
        return redirect( url_for('showMenu',restaurant_id=restaurant_id))
    else:
    #return "This page is for editing menu item "+menu_id
        return render_template("editMenuItem.html",i=edititem)

@app.route('/restaurant/<restaurant_id>/menu/<menu_id>/delete',methods=['GET','POST'])
def deleteMenuItem(restaurant_id,menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemtodelete=session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method=='POST':
        session.delete(itemtodelete)
        session.commit()
        flash("Menu Item deleted!")
        return redirect( url_for('showMenu',restaurant_id=restaurant_id))
    else:
    #return "This page is for deleting menu item"+menu_id
        return render_template("deleteMenuItem.html",p=itemtodelete)

@app.route('/restaurants/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
    restaurant=session.query(Restaurant).filter_by(id=restaurant_id).one()
    items=session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return jsonify(MenuItem=[item.serialize for item in items])



@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def menuItemJSON(restaurant_id, menu_id):
    menuItem=session.query(MenuItem).filter_by(id=menu_id).one()
    
    return jsonify(MenuItem=menuItem.serialize)




#@app.route('/fbconnect', methods=['POST'])
#def fbconnect():
#    if request.args.get('state') != login_session['state']:
#        response = make_response(json.dumps('Invalid state parameter.'), 401)
#        response.headers['Content-Type'] = 'application/json'
#        return response
#    access_token = request.data
#    #print ("access token received %s ") % access_token

#    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
#        'web']['app_id']
#    app_secret = json.loads(
#        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
#    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
#        app_id, app_secret, access_token)
#    h = httplib2.Http()
#    result = (h.request(url, 'GET')[1])

#    # Use token to get user info from API
#    userinfo_url = "https://graph.facebook.com/v2.4/me"
#    # strip expire tag from access token
#    #token = result.split("&")[0]
#    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % result
#    h = httplib2.Http()
#    result = (h.request(url, 'GET')[1])
#    print ("url sent for API access:%s", url)
#    print ("API JSON result: %s", result)
#    data = json.loads(result.read())
#    #data = json.loads((h.request(url, 'GET')[1]).decode('utf-8'))
#    login_session['provider'] = 'facebook'
#    login_session['username'] = data["name"]
#    login_session['email'] = data["email"]
#    login_session['facebook_id'] = data["id"]

#    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
#    stored_token = token.split("=")[1]
#    login_session['access_token'] = stored_token

#    # Get user picture
#    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
#    h = httplib2.Http()
#    result = h.request(url, 'GET')[1]
#    data = json.loads(result)

#    login_session['picture'] = data["data"]["url"]

#    # see if user exists
#    user_id = getUserID(login_session['email'])
#    if not user_id:
#        user_id = createUser(login_session)
#    login_session['user_id'] = user_id

#    output = ''
#    output += '<h1>Welcome, '
#    output += login_session['username']

#    output += '!</h1>'
#    output += '<img src="'
#    output += login_session['picture']
#    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

#    flash("Now logged in as %s" % login_session['username'])
#    return output

#@app.route('/fbdisconnect')
#def fbdisconnect():
#    facebook_id = login_session['facebook_id']
#    # The access token must me included to successfully logout
#    access_token = login_session['access_token']
#    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
#    h = httplib2.Http()
#    result = h.request(url, 'DELETE')[1]
#    return "you have been logged out"


