from database import db 
from flask_login import UserMixin
from datetime import datetime

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




class ParkingLotSearch(db.Model):
    __tablename__ = 'parking_lot_search'
    __table_args__ = {'extend_existing': True}

    rowid = db.Column(db.Integer, primary_key=True)
    lot_name = db.Column(db.Text)
    lot_address = db.Column(db.Text)

class Bookings(db.Model):
    __tablename__ = 'bookings'

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.lot_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_number = db.Column(db.String(20),  db.ForeignKey('user.vehicle_number'), nullable=False)
    start_time = db.Column(db.String, default=datetime.utcnow)
    end_time = db.Column(db.String)
    current_status=db.Column(db.Text)
    # Relationships (optional, for convenience)
    spot = db.relationship('Parking_spot', backref='bookings')
    lot = db.relationship('Parking_lot', backref='bookings')
    user = db.relationship('User', foreign_keys=[user_id], backref='bookings')

class ReleaseHistory(db.Model):
      __tablename__ = 'release_history'

      release_id = db.Column(db.Integer, primary_key=True)
      spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
      lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.lot_id'), nullable=False)
      vehicle_number = db.Column(db.String(20), nullable=False)
      released_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
      release_time = db.Column(db.String)
      charge_paid=db.Column(db.Float())

#     # Resolve ambiguity
      released_by_user = db.relationship('User', foreign_keys=[released_by_user_id], backref='release_history')