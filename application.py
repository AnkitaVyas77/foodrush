from flask import Flask,flash, render_template,session, request, redirect, url_for, jsonify, Response, send_from_directory
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime,timedelta
import os

from authlib.integrations.flask_client import OAuth




ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


application = Flask(__name__,static_folder='static')
@application.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(application.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

api=Api(application)
db = SQLAlchemy(application)

global client_id
global client_secret

client_id = "your-client-id"
client_secret = "your-secret-key"




# Sessionconfig
application.secret_key = "password"
application.config['SESSION_COOKIE_NAME'] = 'google-login-session'
application.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
# ======================================================================


# oAuth Setup
oauth = OAuth(application)
google = oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
    prompt='consent'
)


def isLoggedIN():
    try:
        user = dict(session).get('profile', None)
        if user:
            username=user.get("name")
            
            return True, username
        else:
            
            return False,{}
    except Exception as e:
        return False,{}

@application.route('/')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@application.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    session['profile'] = user_info
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    return redirect('/post')


@application.route('/logout')
def logout():
    
    for key in list(session.keys()):
        session.pop(key)
        
    return redirect('/')



@application.before_first_request
def create_tables():
    db.create_all()

class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    usermail=db.Column(db.String(50))
    caption = db.Column(db.String(50))
    url = db.Column(db.Text)
    userimg=db.Column(db.Text)
    date_posted = db.Column(db.DateTime)
    
    

    
    


@application.route('/post')
def index():
    
    posts = Blogpost.query.order_by(Blogpost.date_posted.desc())
    flag,user = isLoggedIN()
    return render_template("index.html", flag=flag, user=user,posts=posts)

    

@application.route('/updatepost')
def updatepos():
    
    user = dict(session).get('profile', None)
    if user:
        flag=True
        usermail=user.get("email")
        username=user.get("name")
        
        posts = Blogpost.query.filter_by(usermail=usermail).order_by(Blogpost.date_posted.desc())
    else:
        flag=False
    
    return render_template("updatepost.html", flag=flag, user=username,posts=posts)




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/food', methods=['GET','POST'])

def addpost():
    user = dict(session).get('profile', None)
    if user:   
        if request.method == 'POST':
            usermail=user.get("email")
            username=user.get("name")
            userpic=user["picture"]
            
                
            if request.headers['Content-Type'] == 'application/json':
                json_data = request.get_json(force=True)
                name = username
                userimg=userpic
                caption = json_data['caption']
                            
                url = json_data['url']
            else:
                name = username
                caption = request.form['caption']
                userimg=userpic
                            
                url = request.form['url']
                        
                posts=db.session.query(Blogpost)
                        
                post = Blogpost(name=name,usermail=usermail,caption=caption, url=url,userimg=userimg,date_posted=datetime.now())

                db.session.add(post)
                db.session.commit()
                return redirect("/post")
        else:
            return jsonify([
                {'id': post.id, 'name': post.name, 'caption': post.caption,'url':post.url,'userimg':post.userimg,'date':post.date_posted}
                    for post in Blogpost.query.order_by(Blogpost.date_posted.desc())
                      ])
          
    else:
        flash("Please LogIn to Continue")
            

                
        return redirect("/post")
    
         

@application.route('/food/<id>', methods=['GET'])
def get_post(id):
    #id=request.args['id']
    post=Blogpost.query.get_or_404(id)
    return jsonify([
                {'id': post.id, 'name': post.name, 'caption': post.caption,'url':post.url,'date':post.date_posted} 
                      ])
@application.route('/food/delete', methods=['DELETE','GET'])
def deletepost():
    
    id=request.args['id']
    
    post=Blogpost.query.get_or_404(id)
    
    db.session.delete(post)
    db.session.commit()
    if request.method == 'GET':
        return redirect('/updatepost')
        
    else:
        return jsonify([
                {'id': post.id, 'name': post.name, 'caption': post.caption,'url':post.image,'date':post.date_posted}
                    for post in Blogpost.query.order_by(Blogpost.date_posted.desc())
                      ])
@application.route('/food/update', methods=['PUT','GET'])
def updatepost():
    user = dict(session).get('profile', None)
    username=user.get("name")
    userpic=user["picture"]
    usermail=user.get("email")
    
        
    
    id = request.args['id']
            
    post=Blogpost.query.get_or_404(id)
            
    if request.args.get('caption'):
        post.caption = request.args['caption']
    if request.args.get('url'):    
        post.url = request.args['url']
            
            
                
            
                    
            
    db.session.commit()
    if request.method == 'GET':
        #posts = Blogpost.query.filter_by(name=user).order_by(Blogpost.date_posted.desc())
        return redirect("/updatepost")
    else:
        return jsonify([{'id': post.id, 'name': post.name, 'caption': post.caption,'url':post.url,'userimg':post.userimg, 'date':post.date_posted}
                            for post in Blogpost.query.filter_by(usermail=usermail).order_by(Blogpost.date_posted.desc())
                              ])



    

if __name__ == '__main__':
    application.run(debug=True, port=5000)
    
