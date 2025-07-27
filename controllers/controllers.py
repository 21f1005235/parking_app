from flask import Flask, request,flash,redirect, url_for,jsonify
from flask import render_template
from flask_login import current_user
from functools import wraps
from flask import Blueprint, render_template, request
from models.models import User,Parking_lot,Parking_spot,ParkingLotSearch,Bookings,ReleaseHistory
from database import db
from flask_login import login_user, logout_user, login_required
from sqlalchemy import text
from flask import sessions

from collections import defaultdict
from datetime import datetime, timedelta


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











#Setting up admin dashboard
@main.route('/admin_dashboard',methods=['GET','POST'])
@login_required
@role_required('admin')
def admin_dashboard():
    if current_user.is_admin == "Yes":


        print("Current user Id",current_user.id)
        parking_lot_list=[lot.lot_name for lot in Parking_lot.query.with_entities(Parking_lot.lot_name).all()]
        print("Parking LOt List", parking_lot_list)
        
        if parking_lot_list:
                
            
            
            parking_data={}
            for lot_name in parking_lot_list:

                
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
                                                "spot_ids":spot_ids,
                                                "lot_id":lot_id
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
                    
                    summary["total_parking_spots"] += total
                    summary["occupied_spots"] += occupied
                    summary["available_spots"] += total - occupied
            
            charges=ReleaseHistory.query.all()
            total_sum=0
            for record in charges:
                 if record.charge_paid:
                    total_sum=total_sum+record.charge_paid

            summary["total_revenue"]=round(total_sum,2)

           
            return render_template("dashboard_admin.html", name=current_user.full_name,parking_data=parking_data,summary=summary,id=current_user.id)
                
                    


        else:
            return render_template("dashboard_admin.html",name=current_user.full_name,parking_data={},summary={},id=current_user.id)
        
    else:
        
        return redirect(url_for("main.login"))





@main.route('/admin/dashboard/users',methods=['GET'])
@login_required
@role_required('admin')
def admin_dashboard_users():
     


    registered_users=User.query.all()
    user_list_data={}
    
    if len(registered_users)>0:
        for user in registered_users:
            
            if user.is_admin=='user':

                user_list_data[user.id]={
                                            "full_name":user.full_name,
                                            "email":user.email,
                                            "address":user.address,
                                            "pincode":user.pincode,
                                            "vehicle_number":user.vehicle_number

                }
            else:
                 admin_name=user.full_name

    return render_template('dashboard_admin_users.html',user_list_data=user_list_data,admin_name=admin_name,name=current_user.full_name,id=current_user.id)











# To add a new parking lot by admin
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

            lot_price_per_hour = float(request.form.get('lot_price_per_hour'))
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









# To register a new user
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

        # bookings_by_user=Bookings.query.filter_by(user_id=id,current_status='active').all()
        # booking_data={}
        # for booking in bookings_by_user:
             
        #      lot_charge=Parking_lot.query.filter_by(lot_id=booking.lot_id).first().lot_price_per_hour
        #      lot_name=Parking_lot.query.filter_by(lot_id=booking.lot_id).first().lot_name
        #      booking_data[booking.booking_id]={
        #                                             "spot_id": booking.spot_id,
        #                                             "lot_id":  booking.lot_id,
        #                                             "user_id": booking.user_id,
        #                                             "vehicle_number": booking.vehicle_number,
        #                                             "start_time": booking.start_time,
        #                                             "current_status":booking.current_status,
        #                                             "lot_name":lot_name,
        #                                             "lot_charge":lot_charge,
        #                                             "total_charges": calculate_charges(datetime.datetime.now(),datetime.datetime.strptime(booking.start_time, "%Y-%m-%d %H:%M:%S.%f"),lot_charge)
        #                                          }
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




@main.route("/<parking_lot_name>/<parking_spot_id>/details",methods=["GET"])
@login_required
@role_required('admin')
def parking_spot_details_occupied(parking_lot_name,parking_spot_id):

    
    if request.method=="GET":
            
            print(parking_lot_name,parking_spot_id)

            lot = Parking_lot.query.filter_by(lot_name=parking_lot_name).first()
        

            
            parking_lot_id=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_id
            parking_spot = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first()

            lot_charge = Parking_lot.query.filter_by(lot_id=parking_lot_id).first().lot_price_per_hour

            booking_query=Bookings.query.filter_by(lot_id=parking_lot_id,spot_id=parking_spot_id,current_status='active').first()
            customer_id= booking_query.user_id
            vehicle_number=booking_query.vehicle_number
            start_time=booking_query.start_time
            
                
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
            
            total_charges = calculate_charges(datetime.now(), start_time, lot_charge)
            
            


            spot_details={
                            'customer_id':customer_id,
                            'vehicle_number':vehicle_number,
                            'start_time':start_time,
                            'total_charges':total_charges,
                            'parking_lot_id':parking_lot_id,
                            'parking_spot_id':parking_spot_id,
                            'parking_lot_name':parking_lot_name,
                            'spot_id':parking_spot_id,
                            
                        
            }




            
            return render_template('parking_spot_details_occupied.html',spot_details=spot_details)

                



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
              
                return render_template("parking_spot.html",parking_spot_id=parking_spot_id,parking_lot_name=parking_lot_name,parking_lot_price=parking_lot_price,success=True,availability=availability)
            
            else:

                 
                parking_lot_id=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_id
                parking_lot_price=Parking_lot.query.filter_by(lot_name=parking_lot_name).first().lot_price_per_hour
                parking_spot = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first()
                availability = Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first().is_available
               
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
                spot=Parking_spot.query.filter_by(lot_id=parking_lot_id,id=parking_spot_id).first()
                
                if spot:
                     spot.is_available = "No"
                     db.session.commit()
                     flash(f"Spot {spot.id} is now booked.", "success")
                     vehicle_number=request.form.get("vehicle_number")

                     new_booking= Bookings(
                          
                                                spot_id=parking_spot_id,
                                                lot_id=parking_lot_id,
                                                user_id=user_id,
                                                vehicle_number=vehicle_number,
                                                start_time=datetime.now(),
                                                current_status="active"
                     )
                     db.session.add(new_booking)
                     db.session.commit()
                return redirect(url_for("main.user_dashboard",id=user_id))







@main.route("/parking_lot/delete/<parking_lot_id>",methods=['GET'])
@role_required('admin')
@login_required
def delete_parking_lot(parking_lot_id):
     

    try: 
         
         check_booking=Bookings.query.filter_by(lot_id=parking_lot_id,current_status='active').count()

         if check_booking>0:
              
              flash('Cannot delete parking lot. Currently occupied','danger')
              return redirect(url_for('main.admin_dashboard'))
        
         else:
              
            lot=Parking_lot.query.filter_by(lot_id=parking_lot_id).first()

            if lot:
                 db.session.delete(lot)
                 db.session.commit()
                 return redirect(url_for('main.admin_dashboard')) 

    except Exception as e:
        db.session.rollback()
        flash(f"Error occurred: {e}", "danger")
        return redirect(url_for('main.admin_dashboard'))
                


#Milestone-VP- Cost Calculation
# Milestone-VP Search-Implemented




@main.route("/parking_lot/edit/<parking_lot_id>",methods=['GET','POST'])
@role_required('admin')
@login_required
def edit_parking_lot(parking_lot_id):

    try:
        parking_lot = Parking_lot.query.filter_by(lot_id=parking_lot_id).first()
        current_occupied_spot_count=Parking_spot.query.filter_by(lot_id=parking_lot_id,is_available="No").count()
            
        if not parking_lot:
            flash("Parking lot not found.", "danger")
            return redirect(url_for('main.admin_dashboard'))

        if request.method == "GET":
            lot_details = {
                "lot_name": parking_lot.lot_name,
                "lot_address": parking_lot.lot_address,
                "lot_spot_count": parking_lot.lot_spot_count,
                "lot_price_per_hour": parking_lot.lot_price_per_hour,
                "lot_id":parking_lot.lot_id
            }
            return render_template('edit_parking_lot.html', lot_details=lot_details)

        elif request.method == "POST":
            # Get form data
            new_lot_name = request.form.get("lot_name")
            new_lot_address = request.form.get("lot_address")
            new_lot_spot_count = int(request.form.get("lot_spot_count"))
            new_lot_price_per_hour = request.form.get("lot_price_per_hour")



            print("New_lot_name",new_lot_name)
            print("New Spot Count",new_lot_spot_count)
            print("New Spot price",new_lot_price_per_hour)


            if new_lot_spot_count<current_occupied_spot_count:
                  flash(f'Cannot reduce spot count to {new_lot_spot_count}. Currently {current_occupied_spot_count} spots are occupied.', 'warning')
                  print(f"Debug: new_count={new_lot_spot_count}, occupied={current_occupied_spot_count}")  # Debug line
                  return redirect(url_for('main.edit_parking_lot', parking_lot_id=parking_lot_id))
            
            # Optional: Type casting with error handling

            try:
                parking_lot.lot_spot_count = int(new_lot_spot_count)
                parking_lot.lot_price_per_hour = float(new_lot_price_per_hour)


            except ValueError:
                flash("Invalid input for spot count or price per hour.", "danger")
                return redirect(request.url)

            # Update fields
            parking_lot.lot_name = new_lot_name
            parking_lot.lot_address = new_lot_address

            db.session.commit()

            #Function to create additional spots or deletion of spots
            parking_lot_check(parking_lot_id=parking_lot_id)

            flash("Parking lot details updated successfully.", "success")
            return redirect(url_for('main.admin_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error occurred: {e}", "danger")
        return redirect(url_for('main.admin_dashboard'))




# @main.route("/release_spot/<user_id>/<parking_lot_id>/<spot_id>",methods=["GET","POST"])
# @login_required
# @role_required('user')
# def release_spot(user_id,parking_lot_id,spot_id):

#     if request.method=="GET":
          


          
#           vehicle_number= Bookings.query.filter_by(spot_id=spot_id,lot_id=parking_lot_id,user_id=user_id).first().vehicle_number
#           start_time=Bookings.query.filter_by(spot_id=spot_id,lot_id=parking_lot_id,user_id=user_id).first().start_time
#           lot_name=Parking_lot.query.filter_by(lot_id=parking_lot_id).first().lot_name
#           lot_charge=Parking_lot.query.filter_by(lot_id=parking_lot_id).first().lot_price_per_hour
#           release_spot_details={
              
#                                     "user_id":user_id,
#                                     "parking_lot_id":parking_lot_id,
#                                     "spot_id": spot_id,
#                                     "vehicle_number":vehicle_number,
#                                     "lot_name":lot_name,
#                                     "start_time":start_time,
#                                     "total_charges":calculate_charges(datetime.datetime.now(),datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f"),lot_charge)
#          }  
        
#           return render_template("release_spot.html",release_spot_details=release_spot_details)
    
#     if request.method=="POST":
         
#         release_time=datetime.datetime.now()
#         lot_charge=Parking_lot.query.filter_by(lot_id=parking_lot_id).first().lot_price_per_hour
#         vehicle_number= Bookings.query.filter_by(spot_id=spot_id,lot_id=parking_lot_id,user_id=user_id).first().vehicle_number
#         start_time=Bookings.query.filter_by(spot_id=spot_id,lot_id=parking_lot_id,user_id=user_id).first().start_time
#         charges=calculate_charges(release_time,datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f"),lot_charge)

#         new_release_record=ReleaseHistory(
              

#                                 spot_id=spot_id,
#                                 vehicle_number=vehicle_number,
#                                 lot_id=parking_lot_id,
#                                 released_by_user_id=user_id,
#                                 release_time=release_time,
#                                 charge_paid=charges

#          )
#         print(new_release_record)
#         db.session.add(new_release_record)
#         db.session.commit()

#         try:
#             booking_record = Bookings.query.filter_by(user_id=user_id, spot_id=spot_id, lot_id=parking_lot_id).first()

#             if booking_record:
#                 booking_record.current_status = "inactive"
#                 booking_record.end_time=datetime.datetime.now()
#                 db.session.commit()
            
   
#         except Exception as e:
#             db.session.rollback()
#             print(f"Error updating booking: {e}")

#         try:
#             parking_spot_record = Parking_spot.query.filter_by( id=spot_id, lot_id=parking_lot_id).first()

#             if parking_spot_record:
#                 parking_spot_record.is_available = "Yes"
                
#                 db.session.commit()
            
   
#         except Exception as e:
#             db.session.rollback()
#             print(f"Error updating booking: {e}")












#         return redirect(url_for('main.user_dashboard',id=user_id))


@main.route("/release_spot/<user_id>/<parking_lot_id>/<spot_id>", methods=["GET", "POST"])
@login_required
@role_required('user')
def release_spot(user_id, parking_lot_id, spot_id):
    try:
        booking = Bookings.query.filter_by(spot_id=spot_id, lot_id=parking_lot_id, user_id=user_id, current_status='active').first()
        parking_lot = Parking_lot.query.filter_by(lot_id=parking_lot_id).first()
        parking_spot = Parking_spot.query.filter_by(id=spot_id, lot_id=parking_lot_id).first()

        if not booking or not parking_lot or not parking_spot:
            flash("Invalid booking or parking details.", "danger")
            return redirect(url_for('main.user_dashboard', id=user_id))

        start_time = booking.start_time
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
        lot_charge = parking_lot.lot_price_per_hour

        if request.method == "GET":
            total_charges = calculate_charges(datetime.now(), start_time, lot_charge)
            release_spot_details = {
                "user_id": user_id,
                "parking_lot_id": parking_lot_id,
                "spot_id": spot_id,
                "vehicle_number": booking.vehicle_number,
                "lot_name": parking_lot.lot_name,
                "start_time": start_time,
                "total_charges": total_charges
            }
            return render_template("release_spot.html", release_spot_details=release_spot_details)

        elif request.method == "POST":
            release_time = datetime.now()
            charges = calculate_charges(release_time, start_time, lot_charge)
            print("Charges",charges)
            # Add to ReleaseHistory
            new_release_record = ReleaseHistory(
                spot_id=spot_id,
                vehicle_number=booking.vehicle_number,
                lot_id=parking_lot_id,
                released_by_user_id=user_id,
                release_time=release_time,
                charge_paid=charges
            )
            db.session.add(new_release_record)

            # Update Bookings
            booking.current_status = "inactive"
            booking.end_time = release_time

            # Update Parking_spot availability
            parking_spot.is_available = "Yes"  # Or True if Boolean

            db.session.commit()

            flash("Parking spot released successfully.", "success")
            return redirect(url_for('main.user_dashboard', id=user_id))

    except Exception as e:
        db.session.rollback()
        print(f"Error in releasing spot: {e}")
        flash("An error occurred while releasing the parking spot.", "danger")
        return redirect(url_for('main.user_dashboard', id=user_id))
















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
        
        bookings_by_user=Bookings.query.filter_by(user_id=id,current_status='active').all()
        booking_data={}
        for booking in bookings_by_user:
             
             lot_charge=Parking_lot.query.filter_by(lot_id=booking.lot_id).first().lot_price_per_hour
             lot_name=Parking_lot.query.filter_by(lot_id=booking.lot_id).first().lot_name
             start_time=booking.start_time
             
             if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
             booking_data[booking.booking_id]={
                                                    "spot_id": booking.spot_id,
                                                    "lot_id":  booking.lot_id,
                                                    "user_id": booking.user_id,
                                                    "vehicle_number": booking.vehicle_number,
                                                    "start_time": booking.start_time,
                                                    "current_status":booking.current_status,
                                                    "lot_name":lot_name,
                                                    "lot_charge":lot_charge,
                                                    "total_charges": calculate_charges(datetime.now(),start_time,lot_charge)
                                                 }
             
        print("booking_data",booking_data)
        parking_locations=Parking_lot.query.all()
        parking_data={}
        for location in parking_locations:

                available_spots=Parking_spot.query.filter_by(lot_id=location.lot_id,is_available="Yes").count()
                parking_data[location.lot_id]={
                                            'lot_name':location.lot_name,
                                            'lot_address':location.lot_address,
                                            'available_spots': available_spots,
                                            'lot_charge': location.lot_price_per_hour
                }


        print(parking_data)

        return render_template('dashboard_user.html',user_data=user_data, parking_data=parking_data,booking_data=booking_data,id=current_user.id,name=current_user.full_name)
    

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
                                            'available_spots': available_spots,
                                            'lot_charge': location.lot_price_per_hour
                }

            print("Parking Data Check",parking_data)
            

            bookings_by_user=Bookings.query.filter_by(user_id=id,current_status='active').all()
            booking_data={}
            for booking in bookings_by_user:
             
                lot_charge=Parking_lot.query.filter_by(lot_id=booking.lot_id).first().lot_price_per_hour
                lot_name=Parking_lot.query.filter_by(lot_id=booking.lot_id).first().lot_name
                start_time = booking.start_time
                if isinstance(start_time, str):
                    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
                booking_data[booking.booking_id]={
                                                        "spot_id": booking.spot_id,
                                                        "lot_id":  booking.lot_id,
                                                        "user_id": booking.user_id,
                                                        "vehicle_number": booking.vehicle_number,
                                                        "start_time": start_time,
                                                        "current_status":booking.current_status,
                                                        "lot_name":lot_name,
                                                        "lot_charge":lot_charge,
                                                        "total_charges": calculate_charges(datetime.now(),start_time,lot_charge)
                                                    }

            return render_template('dashboard_user.html',user_data=user_data, parking_data=parking_data,booking_data=booking_data, id=current_user.id,name=current_user.full_name)




@main.route("/admin/dashboard/search", methods=["GET", "POST"])
@login_required
@role_required('admin')
def search_admin():
    if request.method == 'POST':
        search_by = request.form.get('search_by')
        search_string = request.form.get('search_string')

        print("Search by:", search_by)
        print("Search string:", search_string)

        parking_data = {}
        sr_parking_lot_id = []

        if search_by == "user_id":
            booking_results = Bookings.query.filter_by(user_id=int(search_string), current_status="active").all()
            print("Booking results:", booking_results)
            sr_parking_lot_id = [booking.lot_id for booking in booking_results]

        elif search_by == "location":
            results = Parking_lot.query.filter(Parking_lot.lot_address.ilike(f"%{search_string}%")).all()
            print("Booking results for user:", results)
            sr_parking_lot_id = [lot.lot_id for lot in results]

        elif search_by == "user_name":
            user = User.query.filter(User.full_name.ilike(f"%{search_string}%")).first()
            print("Matching users:", user)
            if user:
                results = Bookings.query.filter_by(user_id=user.id, current_status="active").all()
                print("Booking results for user name:", results)
                sr_parking_lot_id = [booking.lot_id for booking in results]
            else:
                sr_parking_lot_id = []

        elif search_by == "vehicle_number":
            search_string = search_string.upper().strip()
            results = Bookings.query.filter_by(vehicle_number=search_string, current_status="active").all()
            print("Booking results for vehicle_number:", results)
            sr_parking_lot_id = [booking.lot_id for booking in results]

        for lot_id in set(sr_parking_lot_id):  # avoid duplicates
            lot = Parking_lot.query.filter_by(lot_id=lot_id).first()
            if lot:
                lot_name = lot.lot_name
                occupied_spots = [spot.id for spot in Parking_spot.query.filter_by(lot_id=lot_id, is_available="No").all()]
                occupied_count = len(occupied_spots)
                total_count = Parking_spot.query.filter_by(lot_id=lot_id).count()
                spot_ids = [spot.id for spot in Parking_spot.query.filter_by(lot_id=lot_id).all()]
                parking_data[lot_name] = {
                    "occupied_spots": occupied_spots,
                    "occupied_count": occupied_count,
                    "total_count": total_count,
                    "lot_price_per_hour": lot.lot_price_per_hour,
                    "spot_ids": spot_ids,
                    "lot_id": lot_id
                }
        print("sr_parking_lot_id:", sr_parking_lot_id)
        print(parking_data)
        return render_template("search_admin.html", parking_data=parking_data, search_string=search_string,search_by=search_by,name=current_user.full_name,id=current_user.id)

    return render_template("search_admin.html",parking_data={}, search_string="", search_by="", name=current_user.full_name,id=current_user.id)












def calculate_charges(end_time,start_time,lot_charges):
     

        charges= ((end_time-start_time).total_seconds()/3600)*lot_charges
     
        return round(charges,2)

#Comment to  for role based access
#comment for milestone- VP admin dashboard management
#Commnet Milestone-VP User-Dashboard-Management
def parking_lot_check(parking_lot_id):
     
    try: 
            print("Calling here")
            if not parking_lot_id:

                flash('Invalid parking lot ID','error')
                return redirect(url_for('main.admin_dashboard'))
        


           

            parking_lot=Parking_lot.query.filter_by(lot_id=parking_lot_id).first()

            if not parking_lot:
                 flash("Parking lot not found",'errror')
                 return redirect(url_for('main.admin_dashboard'))
            


            target_spot_count=Parking_lot.query.filter_by(lot_id=parking_lot_id).first().lot_spot_count

            current_spot_count=Parking_spot.query.filter_by(lot_id=parking_lot_id).count()

            if target_spot_count>current_spot_count:
                 
                
                success = _add_parking_spots(parking_lot_id, target_spot_count, current_spot_count)
                
                
                if success:
                    flash(f'Added {target_spot_count - current_spot_count} parking spots', 'success')
                else:
                    flash('Error adding parking spots', 'error')

            elif target_spot_count < current_spot_count:
            # Remove excess spots
                success = _remove_parking_spots(parking_lot_id, current_spot_count, target_spot_count)
                if success:
                    flash(f'Removed {current_spot_count - target_spot_count} parking spots', 'success')
                else:
                    flash('Error removing parking spots', 'error')
            else:
                    flash('Parking lot is already synchronized', 'info')
        
            return redirect(url_for('main.admin_dashboard'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('main.admin_dashboard'))

     
            
            
            




def _add_parking_spots(parking_lot_id, target_count, current_count):
    """Helper function to add parking spots"""
    
    print(f"DEBUG: Adding spots for lot_id={parking_lot_id}")
    print(f"DEBUG: target_count={target_count}, current_count={current_count}")
    try:
        # Get the highest existing spot number
        last_spot = Parking_spot.query.filter_by(lot_id=parking_lot_id)\
                                     .order_by(Parking_spot.spot_number.desc())\
                                     .first()
        
        next_spot_number = (last_spot.spot_number + 1) if last_spot else 1
        spots_to_add = target_count - current_count
        
        # Bulk create spots
        new_spots = []
        for i in range(spots_to_add):
            new_spot = Parking_spot(
                lot_id=parking_lot_id,  # Fixed: use correct variable
                spot_number=next_spot_number + i,  # Fixed: sequential numbering
                is_available="Yes"  # Fixed: use boolean instead of string
            )
            new_spots.append(new_spot)
        
        # Bulk insert
        db.session.add_all(new_spots)
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding spots: {e}")
        return False


def _remove_parking_spots(parking_lot_id, current_count, target_count):
    """Helper function to remove parking spots"""
    try:
        spots_to_remove = current_count - target_count
        
        # Check for active bookings before removal
        active_bookings = Bookings.query.filter_by(
            lot_id=parking_lot_id, 
            current_status='active'
        ).count()
        
        if active_bookings > target_count:
            raise ValueError(f"Cannot remove spots: {active_bookings} active bookings exceed target capacity")
        
        # Get spots to remove (highest numbered first)
        spots_to_delete = Parking_spot.query.filter_by(lot_id=parking_lot_id)\
                                           .filter(Parking_spot.is_available == "Yes")\
                                           .order_by(Parking_spot.spot_number.desc())\
                                           .limit(spots_to_remove)\
                                           .all()
        
        if len(spots_to_delete) < spots_to_remove:
            raise ValueError("Not enough available spots to remove")
        
        # Bulk delete
        for spot in spots_to_delete:
            db.session.delete(spot)
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error removing spots: {e}")
        return False












# Edit profile and update profile
    
@main.route('/edit-profile/<int:user_id>', methods=['GET'])
@login_required
def edit_profile(user_id):
    user = User.query.filter_by(id=user_id).first()
    is_admin= user.is_admin 
    user_data= {
                    "id": user_id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "address": user.address,
                    "pincode": user.pincode,
                    "vehicle_number": user.vehicle_number,
                    "is_admin": is_admin
    }

    if not user:
        return "User not found", 404
    return render_template('edit_profile.html', user_data=user_data)


@main.route('/edit-profile/<int:user_id>', methods=['POST'])
@login_required
def update_profile(user_id):
    full_name = request.form.get('full_name')
    address= request.form.get('address')
    pincode = request.form.get('pincode')
    vehicle_number = request.form.get('vehicle_number')
    
    print ("Full_name",full_name)
    print ("Address",address)
    print("Pincode",pincode)
    print("Vehicle_number",vehicle_number)
    # Update the DB
    query= User.query.filter_by(id=user_id).first()
    if not query:
        flash("User not found.", "danger")
        return redirect(url_for('main.login'))
    query.full_name = full_name
    query.address = address
    query.pincode = pincode
    query.vehicle_number = vehicle_number  # Keep existing if not provided
    db.session.commit()


    if current_user.is_admin == "Yes":
        flash("Profile updated successfully.", "success")
        return redirect (url_for('main.admin_dashboard'))
    else:
         flash("Profile updated successfully.", "success")
         return redirect( url_for('main.user_dashboard', id=user_id))




def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


@main.route('/admin/summary', methods=['GET'])
@login_required
@role_required('admin')
def admin_summary():
    



    # --- Weekly Revenue (filtered by parking lot) ---
   




    earliest_record = ReleaseHistory.query.order_by(ReleaseHistory.release_time.asc()).first()
    weekly_revenue = []

    if earliest_record and earliest_record.release_time:
        today = datetime.today().date()

        release_dt = parse_datetime(earliest_record.release_time)
        start_date = release_dt.date()
        start_of_week = start_date - timedelta(days=start_date.weekday())
        end_of_week = today - timedelta(days=today.weekday())

        revenue_data = defaultdict(float)

        records = ReleaseHistory.query.filter(ReleaseHistory.release_time >= start_of_week).all()
        for rec in records:
            if rec.release_time:
                release_dt = parse_datetime(rec.release_time)
                week_start = release_dt.date() - timedelta(days=release_dt.weekday())
                revenue_data[week_start] += rec.charge_paid or 0

    #     all_weeks = sorted(revenue_data.keys(), reverse=True)[:10]
    #     weekly_revenue = [
    #         {
    #             "date": week.strftime("%Y-%m-%d"),
    #             "revenue": round(revenue_data[week], 2)
    #         } for week in reversed(all_weeks)
    #     ]
        week = start_of_week 
        weekly_revenue = []
        while (week <= end_of_week):
            weekly_revenue.append({
                "date": week.strftime("%Y-%m-%d"),
                "revenue": round(revenue_data[week], 2)
            })
            week += timedelta(days=7)
    print("Weekly Revenue Data:", weekly_revenue)
        





    # --- Occupancy trend ---
    # booking_data = defaultdict(int)
    # bookings = Bookings.query.filter(Bookings.start_time >= week_start).all()

    # for b in bookings:
        
    #     # Convert start_time to datetime if it's a string

    #     start_time = b.start_time
    #     if isinstance(start_time, str):
    #                 start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")

                    
    #     booking_data[start_time.date()] += 1


    # occupancy_trend = [{"date": d.strftime("%Y-%m-%d"), "active": booking_data[d]} for d in sorted(booking_data)]
    today = datetime.today().date()
    start_date = today - timedelta(days=9)  # Last 10 days including today
    date_range = [start_date + timedelta(days=i) for i in range(10)]

    booking_data = defaultdict(int)
    for d in date_range:
        booking_data[d] = 0

    # Query bookings with start_time in the date range (>= start_date and <= today)
    bookings = Bookings.query.filter(
        Bookings.start_time >= datetime.combine(start_date, datetime.min.time()),
        Bookings.start_time <= datetime.combine(today, datetime.max.time())
    ).all()

    for b in bookings:
        start_time = b.start_time
        if isinstance(start_time, str):
            try:
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        booking_date = start_time.date()
        if booking_date in booking_data:
            booking_data[booking_date] += 1

    # Prepare occupancy trend for last 10 days
    occupancy_trend = [
        {"date": d.strftime("%Y-%m-%d"), "active": booking_data[d]}
        for d in date_range
    ]
















    # --- Pie Chart: Total occupancy ---
    total_spots = Parking_spot.query.count()
    occupied = Parking_spot.query.filter_by(is_available="No").count()
    available = total_spots - occupied

    # --- Top Users ---
    top_users = db.session.query(User.full_name, db.func.count(Bookings.booking_id).label("booking_count"))\
                .join(Bookings, Bookings.user_id == User.id)\
                .group_by(User.full_name).order_by(db.desc("booking_count")).limit(5).all()

    return render_template(
        'admin_summary.html',
        name=current_user.full_name,
        weekly_revenue=weekly_revenue,
        occupancy_trend=occupancy_trend,
        occupancy_pie={"occupied": occupied, "available": available},
        top_users=top_users,
        id= current_user.id
    )




@main.route('/usersummary/<int:user_id>', methods=['GET'])
@login_required
@role_required('user')
def user_summary(user_id):

    

    releases = ReleaseHistory.query.filter_by(released_by_user_id=user_id).all()

    weekly_usage = defaultdict(lambda: {'duration': 0.0, 'count': 0})

    for release in releases:
        # Find the corresponding booking record
        booking = Bookings.query.filter_by(
            user_id=release.released_by_user_id,
            lot_id=release.lot_id,
            spot_id=release.spot_id
        ).order_by(Bookings.start_time.desc()).first()

        if not booking or not booking.start_time or not release.release_time:
            continue  # Skip if data is incomplete

        # Convert strings to datetime if needed
        start_time = booking.start_time
        release_time = release.release_time

        if isinstance(start_time, str):
            try:
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

        if isinstance(release_time, str):
            try:
                release_time = datetime.strptime(release_time, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                release_time = datetime.strptime(release_time, "%Y-%m-%d %H:%M:%S")

        # Calculate duration in hours
        duration_seconds = (release_time - start_time).total_seconds()
        duration_hours = round(duration_seconds / 3600, 2)

        # Calculate week start date
        week_start = release_time.date() - timedelta(days=release_time.weekday())

        # Update the dictionary
        weekly_usage[week_start]['duration'] += duration_hours
        weekly_usage[week_start]['count'] += 1

    # Sort and limit to last 10 weeks
    sorted_weeks = sorted(weekly_usage.keys(), reverse=True)[:10]
    user_weekly_data = [
        {
            "week": week.strftime("%Y-%m-%d"),
            "duration": abs(round(weekly_usage[week]['duration'], 2)),
            "count": weekly_usage[week]['count']
        }
        for week in reversed(sorted_weeks)
    ]
    
    print("User Weekly Data:", user_weekly_data)
    return render_template("user_summary.html", user_weekly_data=user_weekly_data, name=current_user.full_name,id= current_user.id)



@main.route('/api/users', methods=['POST'])
def add_user_api():
    data = request.get_json()
    
    required_fields = ['full_name', 'email', 'password','address','pincode', 'vehicle_number']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 409

   
    if data['pincode'] and not data['pincode'].isdigit():
        return jsonify({'error': 'Pincode must be numeric'}), 400
    

    if data['email'] and '@' not in data['email']:
        return jsonify({'error': 'Invalid email format'}), 400
    


    new_user = User(
        full_name=data['full_name'],
        email=data['email'],
        password=data['password'],  # Assuming password is hashed before sending
        address=data['address'],
        pincode=data['pincode'],
        vehicle_number=data['vehicle_number'],

    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully', 'user_id': new_user.id}), 201