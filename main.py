from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from flask_sqlalchemy import SQLAlchemy
import paho.mqtt.client as mqtt
import threading
import json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.secret_key = 'your_secret_key'  # Tambahkan secret key untuk session
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    password = db.Column(db.String)
    


# Simpan data terakhir dari MQTT
latest_data = {"message": "Belum ada data"}

# Fungsi dipanggil saat terhubung ke broker
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke broker dengan kode:", rc)
    client.subscribe("usk/iot/mqtt/contoh")

# Fungsi dipanggil saat pesan diterima
def on_message(client, userdata, msg):
    
    global latest_data
    print(f"Pesan diterima: {msg.payload.decode()} dari topik {msg.topic}")
    try:
        latest_data = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("❌ Gagal decode JSON! Isinya bukan JSON valid.")
        latest_data = {"message": msg.payload.decode()}  # fallback string biasa

# Setup MQTT client
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Sesuaikan dengan broker kamu (localhost, test.mosquitto.org, dll)
    client.connect("broker.hivemq.com", 1883, 60)
    client.loop_forever()

# Jalankan MQTT di thread terpisah
mqtt_thread = threading.Thread(target=start_mqtt)
mqtt_thread.daemon = True
mqtt_thread.start()

# Route
@app.route("/", methods=["GET","POST"])
def home():
    return render_template("form.html")

@app.route("/data")
def data():
    suhu = latest_data.get("temp")
    kelembaban = latest_data.get("humidity")
    return jsonify([{
        "lat": -6.2,
        "lng": 106.8,
        'temp': temp,
        'humidity': humidity
    }])
@app.route("/dashboard", methods=["POST"])
def dashboard():
    name = request.form['nama']
    password = request.form['password']
    user = Users.query.filter_by(name=name, password=password).first()
    if user:
        session['user_id'] = user.id 
        user_id = session.get('user_id')
        user = Users.query.get(user_id)
        return render_template("index.html",a=user,latest_data=latest_data)
    
    return redirect(url_for("home"))


@app.route("/register", methods=["GET","POST"])   
def register():
    if request.method=="POST":
        name = request.form['nama1']
        password = request.form['password1']
        new_user = Users(name=name, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("register.html")
    
@app.route("/ubahakun", methods=["POST","GET"])
def ubahakun():
    if request.method=="POST":
        user_id = session.get('user_id')
        user = Users.query.get(user_id)  # Ambil pengguna berdasarkan id
        if user:  # Pastikan pengguna ditemukan
            user.name = request.form["nama2"]
            user.password = request.form["password2"]
            db.session.commit()
        return redirect(url_for("home"))
    return render_template("ubahakun.html")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
