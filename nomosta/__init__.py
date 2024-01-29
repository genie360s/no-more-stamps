import os
from flask import Flask

def create_app(test_config=None):
    """Creates and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path,'nomosta.sqlite'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py',silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass    

    #importing and calling the function init_app from db.py
    from . import db
    db.init_app(app)

    #importing and registering the blueprint from auth.py
    from . import auth
    app.register_blueprint(auth.bp)


    #importing and registering the blueprint from dashboard.py
    from . import dashboard
    app.register_blueprint(dashboard.bp)
    # app.add_url_rule('/',endpoint='dashboard')
    
    return app
