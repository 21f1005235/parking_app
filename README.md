<form class="modal-form" action="{{ url_for('main.edit_parking_spot', parking_lot_name=parking_lot_name, parking_spot_id=parking_spot_id) }}" method="POST">


 summary={
                        "total_parking_spots": 0,
                        "available_spots" : 0,
                        "occupied_spots":0,
                        "total_revenue":0

            }

            for x in parking_data:

          
               summary["total_parking_spots"]+=parking_data[x]["total_count"]
               summary["occupied_spots"]+=parking_data[x]["occupied_count"]
               summary["total_revenue"]+=(parking_data[x]["occupied_count"]*parking_data[x]["lot_price_per_hour"])

            print(parking_data)