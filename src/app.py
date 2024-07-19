"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_all_users():
    users=User.query.all()
    users=[user.serialize() for user in users]

    if not users:
        return jsonify({'msg':'No hay usuarios'}),200
    return jsonify ({'data': users}),200
    #Tambien podemos pasar la respues del body así:
    # response_body ={
    #     'Users': users
    # }
    # return jsonify(response_body),200

@app.route('/add_user', methods=['POST'])
def add_usser():
    data=request.json
    if data['email'] and data['password']:
        user=User.query.filter_by(email=data['email']).first()
        if user:
            return jsonify ({'msg':'Parece que ya te conocemos, intenta logearte'}),200
        new_user=User(email=data['email'], password=data['password'], is_active=True)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'msg': 'Usuario creado', 'user': new_user.serializa()}),200
    
    return jsonify({'msg':'todos los datos son necesarios'}),400

@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user= User.query.get(id)
    if not user:
        return jsonify({'msg': '¡Oh no! No encontramos tu cuenta'}),404
    return jsonify({'msg': 'mostrando usuario', 'user': user.serialize()}),200

@app.route('/edit_user/<int:id>', methods=['PUT'])
def edit_user(id):
    data=request.json
    if data['email'] and data['is_active']:
        user=User.query.get(id)
        #user.email esto es el atributo de la clase User
        #data['email'] valor del diccionario data
        # es un diccionario obtenido del cuerpo de la solicitud JSON (request.json). 
        # data['email'] accede al valor asociado con la clave 'email' en este diccionario.
        user.email=data['email'] or user.email
        user.is_active=data['is_active'] or user.is_active
        db.session.commit()
        if not user:
            return jsonify({'msg':'usuario no encontrado'})
        return jsonify({'msg':'usuario editado', 'user': user.serialize()}),200
    return jsonify({'error': 'Todos los datos son necesarios'})


@app.route('/delete_user/<int:id>', methods=['DELETE'])
def delete_user(id):
     user= User.query.get(id)
     if user:
         db.session.delete(user)
         db.session.commit()
         return jsonify({'msg':'usuario eliminado'}),204
     return jsonify({'msg':'no se encontró usuario a eliminar'}), 404

    
    






   

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
