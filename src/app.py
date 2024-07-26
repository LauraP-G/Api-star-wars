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
from models import db, User, Favourites, Planets, Starships, Characters
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


#ENDPOINT USER
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
            return jsonify ({'msg':'Parece que ya te conocemos, intenta logearte'}),400
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

#---------------------------------------------------------------------------------------------------
#ENDPOINT FAVORITOS
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

    # Compruebo que solo un tipo de favorito se puede añadir, esto es importante para cuando quiero eliminar
    # un favorito, ya que cada favorito debe tener su propio id si genero dos o tres favoritos al mismo tiempo
    # ocurrirá que al momento de eliminar uno estaré elimando los que se crearon al mismo tiempo
    favourites_count = sum([character_id is not None, planet_id is not None, starship_id is not None])
    if favourites_count != 1:
        return jsonify({'msg': 'Debes añadir tus favoritos de uno en uno'}), 400

    # Comprobar si el favorito ya existe
    favourite = Favourites.query.filter_by(
        user_id=user_id,
        character_id=character_id if character_id else None,
        planet_id=planet_id if planet_id else None,
        starship_id=starship_id if starship_id else None
    ).first()
    if favourite:
        return jsonify({'msg': 'Este elemento ya está en tus favoritos'}), 200
    
    # Creo el nuevo favorito
    new_favourite = Favourites(
        user_id=user_id,
        character_id=character_id if character_id else None,
        planet_id=planet_id if planet_id else None,
        starship_id=starship_id if starship_id else None
    )
    db.session.add(new_favourite)
    db.session.commit()
    return jsonify({'msg': 'Favorito creado', 'favourite': new_favourite.serialize()}), 200



@app.route('/user/<int:user_id>/favourites/<int:favourite_id>', methods=['DELETE'])
def delete_favourites(user_id, favourite_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    favourite = Favourites.query.filter_by(id=favourite_id, user_id=user_id).first()
    
    if favourite:
         db.session.delete(favourite)
         db.session.commit()
         return jsonify({'msg':'Favorito eliminado'}),204
    return jsonify({'msg':'no se encontró favorito a eliminar'}), 404

#--------------------------------------------------------------------------------------------------
#ENDPOINT MOSTRAR PLANETAS, PERSONAJES Y NAVES
@app.route('/planets', methods=['GET'])
def show_planets():
    planets=Planets.query.all()
    planets = [planet.serialize() for planet in planets]

    if not planets:
        return jsonify({'msg': 'No hay planetas que mostrar'}),404
    
    return jsonify({'msg': 'mostrando planetas', 'planets':planets}),200

@app.route('/starships', methods=['GET'])
def show_starships():
    starships=Starships.query.all()
    starships = [starship.serialize() for starship in starships]

    if not starships:
        return jsonify({'msg': 'No hay naves que mostrar'}),404
    
    return jsonify({'msg': 'mostrando naves', 'starships': starships}),200

@app.route('/characters', methods=['GET'])
def show_characters():
    characters=Characters.query.all()
    characters = [character.serialize() for character in characters]

    if not characters:
        return jsonify({'msg': 'No hay personajes que mostrar'}),404
    
    return jsonify({'msg': 'mostrando personajes', 'characters':characters}),200


#--------------------------------------------------------------------------------------------------
#ENDPOINT AÑADIR PLANETAS, PERSONAJES Y NAVES
@app.route('/add_datas', methods=['POST'])
#/add_datas?type=characters
#/add_datas?type=planets
#/add_datas?type=starships
def add_datas():
    data_type = request.args.get('type')

    if data_type == 'characters':
        data = request.json
        new_data = Characters(
            name=data['name'],
            height=data['height'],
            mass=data['mass'],
            hair_color=data['hair_color'],
            skin_color=data['skin_color'],
            birth_year=data['birth_year'],
            gender=data['gender']
        )
        db.session.add(new_data)
        db.session.commit()
        return jsonify({'msg': 'Character creado', 'character': new_data.serialize()}), 201

    elif data_type == 'planets':
        data = request.json
        new_data = Planets(
            name=data['name'],
            diameter=data['diameter'],
            rotation_period=data['rotation_period'],
            orbital_period=data['orbital_period'],
            gravity=data['gravity'],
            population=data['population'],
            climate=data['climate'],
            terrain=data['terrain']
        )
        db.session.add(new_data)
        db.session.commit()
        return jsonify({'msg': 'Planet creado', 'planet': new_data.serialize()}), 201

    elif data_type == 'starships':
        data = request.json
        new_data = Starships(
            name=data['name'],
            model=data['model'],
            starship_class=data['starship_class'],
            manufacturer=data['manufacturer'],
            cost_in_credits=data['cost_in_credits'],
            length=data['length'],
            crew=data['crew'],
            passengers=data['passengers'],
            max_atmosphering_speed=data['max_atmosphering_speed'],
            cargo_capacity=data['cargo_capacity']
        )
        db.session.add(new_data)
        db.session.commit()
        return jsonify({'msg': 'Starship creado', 'starship': new_data.serialize()}), 201

    else:
        return jsonify({'msg': 'Tipo de dato no valido'}), 400




# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
