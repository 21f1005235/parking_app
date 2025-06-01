from database import db 
from flask_login import UserMixin

class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.Text, nullable=False)
    vehicle_number = db.Column(db.Text,nullable=True)
    is_admin=db.Column(db.Text,default="user")

class Parking_lot(db.Model):
    __tablename__='parking_lot'
    lot_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    lot_name= db.Column(db.Text,nullable=False,unique=True)
    lot_address=db.Column(db.Text,nullable=False)
    lot_spot_count=db.Column(db.Integer,nullable=False)
    lot_price_per_hour=db.Column(db.Integer,nullable=False)
    owner = db.relationship('User', backref=db.backref('parking_lots', passive_deletes=True))
    spots = db.relationship('Parking_spot', backref='lot', cascade="all, delete", passive_deletes=True)



class Parking_spot(db.Model):
    __tablename__ = 'parking_spot'

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.lot_id', ondelete="CASCADE"), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.String, default="Yes",nullable=False)