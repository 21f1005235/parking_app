from flask import Flask, request,flash,redirect, url_for
from flask import render_template
from flask_login import current_user
from functools import wraps
from flask import Blueprint, render_template, request
from models.models import User,Parking_lot,Parking_spot,ParkingLotSearch
from database import db
from flask_login import login_user, logout_user, login_required
from sqlalchemy import text
from flask import sessions


main = Blueprint('main', __name__)



@main.route('/')
def index():
    return "Welcome to the application. <a href='/login'>Login</a> | <a href='/register'>Register</a>"



def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('main.login'))
            # Change this line:
            if required_role == "admin" and current_user.is_admin != "Yes":
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator







@main.route("/login",methods=["GET","POST"])
def login():
    if request.method=="GET":
        return render_template("login.html")
    
    elif request.method=="POST":

        email=request.form.get('email')
        password=request.form.get('password')
        print(email)
        print(password)
        rec=User.query.filter(User.email==email).first()  # to match the actual column name
        
        if rec and rec.password == password:
            login_user(rec)
            if rec.is_admin == "Yes":
                return redirect("/admin/dashboard")
            else:
                return redirect(f'/dashboard/user/{rec.id}')
        else:
            if rec:
                return render_template("login.html", success=False,message=True)

            else:
                 return render_template("login.html", success=False)





@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))












@main.route('/admin_dashboard',methods=['GET','POST'])
@login_required
@role_required('admin')
def admin_dashboard():
    if current_user.is_admin == "Yes":

    
        parking_lot_list=[lot.lot_name for lot in Parking_lot.query.with_entities(Parking_lot.lot_name).all()]
        print("Parking LOt List", parking_lot_list)
        
        if parking_lot_list:
                
            
            
            parking_data={}
            for lot_name in parking_lot_list:

                print ("Lot name",lot_name)
                lot_id=Parking_lot.query.filter(Parking_lot.lot_name==lot_name).first().lot_id
                lot_price_per_hour=Parking_lot.query.filter(Parking_lot.lot_name==lot_name).first().lot_price_per_hour
                count = Parking_spot.query.filter(Parking_spot.lot_id == lot_id).count()
                if count>0:
                    occupied_spots = [spot.id for spot in Parking_spot.query.filter_by(lot_id=lot_id, is_available="No").all()]
                    spot_ids = [spot.id for spot in Parking_spot.query.filter(Parking_spot.lot_id == lot_id).all()]

                    
                    occupied_count = Parking_spot.query.filter_by(lot_id=lot_id, is_available="No").count()
                    total_count= int(Parking_spot.query.filter_by(lot_id=lot_id).count())
                    
                    parking_data[lot_name]={
                                                "occupied_spots": occupied_spots,
                                                "occupied_count": occupied_count,
                                                "total_count":total_count,
                                                "lot_price_per_hour":lot_price_per_hour,
                                                "spot_ids":spot_ids
                                            }
                else:

                    parking_data[lot_name]={}
            
            summary = {
                                "total_parking_spots": 0,
                                "available_spots": 0,
                                "occupied_spots": 0,
                                "total_revenue": 0
                            }

            for lot in parking_data:

                if parking_data[lot]:
                    total = parking_data[lot]["total_count"]
                    occupied = parking_data[lot]["occupied_count"]
                    rate = parking_data[lot]["lot_price_per_hour"]

                    summary["total_parking_spots"] += total
                    summary["occupied_spots"] += occupied
                    summary["available_spots"] += total - occupied
                    summary["total_revenue"] += occupied * rate





           
            return render_template("dashboard_admin.html", name=current_user.full_name,parking_data=parking_data,summary=summary)
                
                    


        else:
            return render_template("dashboard_admin.html",name=current_user.full_name,parking_data="")
        
    else:
        
        return redirect(url_for("main.login"))




@main.route("/admin/addnewlot",methods=["GET","POST"])
@login_required
@role_required('admin')
def addnewlot():
    if current_user.is_admin == "Yes":

        
        que=User.query.filter(User.is_admin=="Yes").first()
        id=que.id
        if request.method=="GET":



                return render_template("new_parking_lot.html",success=True)



        elif request.method=="POST":

              
            lot_name = request.form.get('lot_name')
            lot_location = request.form.get('lot_location')
            lot_spot_count =int( request.form.get('lot_spot_count'))

            lot_price_per_hour = int(request.form.get('lot_price_per_hour'))
            existing = Parking_lot.query.filter_by(lot_name=lot_name).first()
            

            if existing:

                return render_template('new_parking_lot.html',success=False)

            else:


            
                new_lot= Parking_lot(
                                        owner_id=id,
                                        lot_name=lot_name,
                                        lot_address=lot_location,
                                        lot_spot_count=lot_spot_count,
                                        lot_price_per_hour=lot_price_per_hour
                                        
                                        
                            
                )

                

                db.session.add(new_lot)
                db.session.commit()

                lot_id= Parking_lot.query.filter_by(lot_name=lot_name).first().lot_id
                for x in range(lot_spot_count):

                    new_spot= Parking_spot(

                                    lot_id=lot_id,
                                    spot_number=x,
                                    is_available="Yes"


                    )
                    db.session.add(new_spot)
                db.session.commit()

                return redirect(url_for('main.admin_dashboard'))           

    else:
       
        return redirect(url_for("main.login"))





@main.route("/register",methods=["GET","POST"])
def register():

    if request.method=="GET":
      
        return render_template("registration.html")
    
    elif request.method=="POST":
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        vehicle_number=request.form.get('vehicle_number')
        is_admin=request.form.get('is_admin')
        email_reg = User.query.with_entities(User.email).all()
        email_list = [email[0] for email in email_reg]

        print(email_list)
        if email in email_list:

         
            return render_template("registration.html", success=False)
        
        else:

            if vehicle_number:
                
            

                    new_user = User(
                            email=email,
                            password=password,
                            full_name=full_name,
                            address=address,
                            pincode=pincode,
                            vehicle_number=vehicle_number)




            else:
                
                    new_user = User(
                            email=email,
                            password=password,
                            full_name=full_name,
                            address=address,
                            pincode=pincode)

            db.session.add(new_user)
            db.session.commit()

            
            return render_template("registration.html", success=True)


@main.route("/<parking_lot_name>/<parking_spot_id>",methods=["GET","POST"])
@login_required
@role_required('admin')
def edit_parking_spot(parking_lot_name,parking_spot_id):

        if request.method=="GET":


            lot = Parking_lot.query.filter_by(lot_name=parking_lot_name).first()
            if lot is None:
                
                parking_lot_id=None
                parking_lot_price=None
                parking_spot = None
                availability = None
                print(parking_spot)
                return render_template("parking_spot.html",parking_spot_id=parking_spot_id,parking_lot_name=parking_lot_name,parking_lot_price=parking_lot_price,success=True,availability=availability)
            
            else:

                 
                parking_lot_id=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_id
                parking_lot_price=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_price_per_hour
                parking_spot = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first()
                availability = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first().is_available
                print(parking_spot)
                return render_template("parking_spot.html",parking_spot_id=parking_spot_id,parking_lot_name=parking_lot_name,parking_lot_price=parking_lot_price,success=True,availability=availability)
            






        

        elif request.method=="POST":
            parking_lot_id=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_id
            availability = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first().is_available
            if availability=="Yes":
                spot = Parking_spot.query.filter_by(lot_id=parking_lot_id, id=parking_spot_id).first()
                db.session.delete(spot)
                db.session.commit()
                return redirect(url_for('main.admin_dashboard'))           
            

            else:

                parking_lot_id=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_id
                parking_lot_price=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_price_per_hour
                parking_spot = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first()
                availability = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first().is_available
                return render_template("parking_spot.html",parking_spot_id=parking_spot_id,parking_lot_name=parking_lot_name,parking_lot_price=parking_lot_price,success=False,availability=availability)
            




@main.route("/book_spot/<user_id>/<parking_lot_id>",methods=['GET','POST'])
@role_required('user')
@login_required
def book_spot(user_id,parking_lot_id):

    if request.method=="GET":


            check_availability= Parking_spot.query.filter_by(lot_id=parking_lot_id,is_available="Yes").count()

            if check_availability>0:
                
                parking_spot_id=Parking_spot.query.filter_by(lot_id=parking_lot_id,is_available="Yes").first().id
                parking_lot_price=Parking_lot.query.filter_by(lot_id=parking_lot_id).first().lot_price_per_hour
                parking_lot_name=Parking_lot.query.filter_by(lot_id=parking_lot_id).first().lot_name
                booking_spot_details={
                     
                                            "user_id":user_id,
                                            "parking_lot_id":parking_lot_id,
                                            "parking_spot_id":parking_spot_id,
                                            "parking_lot_price":parking_lot_price,
                                            "parking_lot_name": parking_lot_name
                }

                return render_template("book_spot.html",booking_spot_details=booking_spot_details)
            
            else:
                 flash("No parking spots are available at the moment.", "warning")
                 return redirect(url_for('main.user_dashboard',id=user_id))


    if request.method=="POST":
        
                parking_spot_id=Parking_spot.query.filter_by(lot_id=parking_lot_id,is_available="Yes").first().id
                spot=Parking_spot.query.filter_by(lot_id=parking_lot_id,spot_id=parking_spot_id).first()

                if spot:
                     spot.is_available = "Yes"
                     db.session.commit()
                     flash(f"Spot {spot.id} is now booked.", "success")


                return redirect(url_for("main.user_dashboard",id=user_id))


@main.route("/dashboard/user/<id>",methods=['GET','POST'])
@role_required('user')
@login_required
def user_dashboard(id):
    if request.method=="GET":
        user=User.query.filter(User.id==id).first()
        
         
         
        

        user_data={
                                "name": user.full_name,
                                "address": user.address,
                                "email": user.email,
                                "pincode": user.pincode,
                                "vehicle_number": user.vehicle_number,
                                "id": user.id

                }
        
        parking_locations=Parking_lot.query.all()
        parking_data={}
        for location in parking_locations:

                available_spots=Parking_spot.query.filter_by(lot_id=location.lot_id,is_available="Yes").count()
                parking_data[location.lot_id]={
                                            'lot_name':location.lot_name,
                                            'lot_address':location.lot_address,
                                            'available_spots': available_spots
                }


        print(parking_data)

        return render_template('dashboard_user.html',user_data=user_data, parking_data=parking_data)
    

    elif request.method=="POST":
        
            query=request.form.get('search_location')

            print(query)

            sql = text("""
                        SELECT pl.*
                        FROM parking_lot_search
                        JOIN parking_lot pl ON parking_lot_search.rowid = pl.lot_id
                        WHERE parking_lot_search MATCH :term
                    """)
            results = db.session.execute(sql, {'term': query}).fetchall()


            print("Results",results)

            location_ids=[]
            for x in results:
                location_ids.append(x[0])





            user=User.query.filter(User.id==id).first()
        
         
         
        

            user_data={
                                "name": user.full_name,
                                "address": user.address,
                                "email": user.email,
                                "pincode": user.pincode,
                                "vehicle_number": user.vehicle_number,
                                "id": user.id




                }
            


            parking_locations=Parking_lot.query.filter(Parking_lot.lot_id.in_(location_ids)).all()
            parking_data={}
            for location in parking_locations:

                available_spots=Parking_spot.query.filter_by(lot_id=location.lot_id,is_available="Yes").count()
                parking_data[location.lot_id]={
                                            'lot_name':location.lot_name,
                                            'lot_address':location.lot_address,
                                            'available_spots': available_spots
                }


            print(parking_data)



            return render_template('dashboard_user.html',user_data=user_data, parking_data=parking_data)






# @main.route("/users_dashboard",methods=["GET","POST"])
# @login_required
# def users():

#     if current_user.is_admin == "Yes":


#         if request.method=="GET":
            

#             user_data=User.query.all()
#             users={}
#             for user in user_data:

#                 users[user]={
#                                 "name": user.full_name,
#                                 "address": user.address,
#                                 "email": user.email,
#                                 "pincode": user.pincode,
#                                 "is_admin": user.is_admin


#                 }


#             print(users)
#             return render_template("dashboard_user.html",users=users)
        




