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
from models import db, User, Favourites
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
        return jsonify({'msg': 'Usuario creado', 'user': new_user.serialize()}),200
    
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
        
        if not user:
            return jsonify({'msg':'usuario no encontrado'}),404
        
        #user.email esto es el atributo de la clase User
        #data['email'] valor del diccionario data
        # es un diccionario obtenido del cuerpo de la solicitud JSON (request.json). 
        # data['email'] accede al valor asociado con la clave 'email' en este diccionario.
        user.email=data['email'] or user.email
        user.is_active=data['is_active'] or user.is_active
        db.session.commit()
        return jsonify({'msg':'usuario editado', 'user': user.serialize()}),200
    
    return jsonify({'error': 'Todos los datos son necesarios'}),400


@app.route('/delete_user/<int:id>', methods=['DELETE'])
def delete_user(id):
     user= User.query.get(id)
     if user:
         db.session.delete(user)
         db.session.commit()
         return jsonify({'msg':'usuario eliminado'}),204
     return jsonify({'msg':'no se encontró usuario a eliminar'}), 404


@app.route('/user/<int:user_id>/favourites', methods=['GET'])
def get_favourites(user_id):
    #Recupera una instancia del modelo User desde la base de
    #datos usando el user_id proporcionado. Si el usuario con el ID especificado 
    # no existe, user será None.
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404

    # Acceder a favoritos a través de la relación
    # user.favourite se refiere a la propiedad favourite de la 
    # instancia user que se obtiene mediante User.query.get(user_id)
    # La relación se ha definido con back_populates, lo que significa que user.favourite 
    # se refiere a todos los objetos de Favourites que están relacionados con este user.
    # otra opcion 
    #favourites = user.favourite

    favourites = Favourites.query.filter_by(user_id=user_id).all()
    favourites = [favourite.serialize() for favourite in favourites]

    if favourites:
        return jsonify({'msg': 'mostrando favoritos', 'favourites': favourites}), 200
    return jsonify({'msg': 'No se encontraron favoritos'}), 404

@app.route('/user/<int:user_id>/favourites', methods=['POST'])
def add_favourites(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    data = request.json
    character_id = data.get('character_id')
    planet_id = data.get('planet_id')
    starship_id = data.get('starship_id')

    if not any([character_id, planet_id, starship_id]):
        return jsonify({'msg': 'Al menos uno de los siguientes campos es necesario: character_id, planet_id, starship_id'}), 400

    favourite = Favourites.query.filter_by(user_id=user_id, character_id=character_id, planet_id=planet_id, starship_id=starship_id).first()
    if favourite:
        return jsonify({'msg': 'Este elemento ya está en tus favoritos'}), 200
   
    new_favourite = Favourites(user_id=user_id, planet_id=planet_id, character_id=character_id, starship_id=starship_id)
    db.session.add(new_favourite)
    db.session.commit()
    return jsonify({'msg': 'Favorito creado', 'favourite': new_favourite.serialize()}), 200



@app.route('/user/<int:user_id>/favourites/<int:favourite_id', methods=['DELETE'])
def delete_favourites(user_id, favourite_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    favourite = Favourites.query.filter_by(id=favourite_id, user_id=user_id).first()
    
    if favourite:
         db.session.delete(favourite)
         db.session.commit()
         return jsonify({'msg':'Favorito eliminado'
         }),204
    return jsonify({'msg':'no se encontró favorito a eliminar'}), 404




    
   

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
