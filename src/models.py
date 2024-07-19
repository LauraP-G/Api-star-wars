from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)

    favourite=db.relationship('Favourites', back_populetes="user")

    def __repr__(self):
        return f'<User {self.email}>' 

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            'is_active':self.is_active
            # do not serialize the password, its a security breach
        }
    
class Favourites(db.Model):
    __tablename__ = 'favourites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    
    user = db.relationship('User', back_populates='favourite')
    character = db.relatioship('Characters', back_populates='favourite')
     

    def serialize(self):
        return {
            "id":self.id,
            "user_id": self.user_id
            
        }
    
class Characters(db.Model):
     __tablename__ = 'starships'

     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.String(250), nullable=False)
     model = db.Column(db.String(150))
     starship_class = db.Column(db.String(150))
     manufacturer =  db.Column(db.String(150))
     cost_in_credits = db.Column(db.Integer)
     length = db.Column(db.Integer)
     crew = db.Column(db.Integer)
     passengers = db.Column(db.Integer)
     max_atmosphering_speed = db.Column(db.Integer)
     cargo_capacity = db.Column(db.Integer)

     favourite = db.relationship('Favourites', back_populates='charater')

     def serialize(self):
         return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "starship_class": self.starship_class,
            "manufacturer": self.manufacturer,
            "cost_in_credits": self.cost_in_credits,
            "length": self.length,
            "crew": self.crew,
            "passengers": self.passengers,
            "max_atmosphering_speed": self.max_atmosphering_speed,
            "cargo_capacity": self.cargo_capacity
        }
       
         
      
    
    

