# Import library yang dibutuhkan
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Konfigurasi koneksi database dan pengaturan lainnya
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/flask-db'  # Ganti sesuai konfigurasi database kamu
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Digunakan untuk keamanan flash messages

# Inisialisasi objek SQLAlchemy
db = SQLAlchemy(app)

# Filter custom untuk memformat harga (misal: Rp 10.000,00)
@app.template_filter('format_price')
def format_price(value):
    if value is None:
        return ''
    return f"Rp {value:,.2f}"

# Definisi model Baju (representasi tabel di database)
class Baju(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    ukuran = db.Column(db.String(10), nullable=False)
    harga = db.Column(db.Float, nullable=False)
    stok = db.Column(db.Integer, nullable=False)

# Membuat semua tabel jika belum ada (hanya saat pertama kali)
with app.app_context():
    db.create_all()

# Route utama untuk menampilkan daftar baju
@app.route('/')
def index():
    baju_list = Baju.query.all()
    return render_template('index.html', baju_list=baju_list)

# Route untuk menambahkan baju baru (dari form HTML)
@app.route('/tambah', methods=['POST'])
def tambah_baju():
    try:
        nama = request.form['nama']
        ukuran = request.form['ukuran']
        harga = float(request.form['harga'])
        stok = int(request.form['stok'])
        # Validasi harga dan stok
        if harga <= 0 or stok < 0:
            flash("Harga harus positif dan stok tidak boleh negatif", "danger")
            return redirect(url_for('index'))
        # Menambahkan baju ke database
        baju = Baju(nama=nama, ukuran=ukuran, harga=harga, stok=stok)
        db.session.add(baju)
        db.session.commit()
        flash("Baju berhasil ditambahkan", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('index'))

# Route untuk memperbarui data baju
@app.route('/update/<int:id>', methods=['POST'])
def update_baju(id):
    baju = Baju.query.get_or_404(id)
    try:
        baju.nama = request.form['nama']
        baju.ukuran = request.form['ukuran']
        baju.harga = float(request.form['harga'])
        baju.stok = int(request.form['stok'])
        # Validasi harga dan stok
        if baju.harga <= 0 or baju.stok < 0:
            flash("Harga harus positif dan stok tidak boleh negatif", "danger")
            return redirect(url_for('index'))
        db.session.commit()
        flash("Baju berhasil diperbarui", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('index'))

# Route untuk menghapus data baju
@app.route('/delete/<int:id>', methods=['GET'])
def delete_baju(id):
    baju = Baju.query.get_or_404(id)
    try:
        db.session.delete(baju)
        db.session.commit()
        flash("Baju berhasil dihapus", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('index'))

# API endpoint untuk mendapatkan semua data baju dalam format JSON
@app.route('/api/baju', methods=['GET'])
def api_get_all():
    baju_list = Baju.query.all()
    return jsonify([
        {
            'id': b.id,
            'nama': b.nama,
            'ukuran': b.ukuran,
            'harga': b.harga,
            'stok': b.stok
        } for b in baju_list
    ])
    
# API endpoint untuk mendapatkan semua data baju dalam format JSON dari id
@app.route('/api/baju/<int:id>', methods=['GET'])
def api_get_by_id(id):
    baju = Baju.query.get_or_404(id)
    return jsonify({
        'id': baju.id,
        'nama': baju.nama,
        'ukuran': baju.ukuran,
        'harga': baju.harga,
        'stok': baju.stok
    })


# API endpoint untuk menambahkan data baju via JSON (misal dari aplikasi lain)
@app.route('/api/baju', methods=['POST'])
def api_create():
    data = request.get_json()
    try:
        baju = Baju(
            nama=data['nama'],
            ukuran=data['ukuran'],
            harga=float(data['harga']),
            stok=int(data['stok'])
        )
        db.session.add(baju)
        db.session.commit()
        return jsonify({'message': 'Baju berhasil ditambahkan'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# API endpoint untuk memperbarui data baju berdasarkan ID
@app.route('/api/baju/<int:id>', methods=['PUT'])
def api_update(id):
    baju = Baju.query.get_or_404(id)
    data = request.get_json()
    try:
        baju.nama = data['nama']
        baju.ukuran = data['ukuran']
        baju.harga = float(data['harga'])
        baju.stok = int(data['stok'])
        db.session.commit()
        return jsonify({'message': 'Baju berhasil diperbarui'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# API endpoint untuk menghapus data baju berdasarkan ID
@app.route('/api/baju/<int:id>', methods=['DELETE'])
def api_delete(id):
    baju = Baju.query.get_or_404(id)
    try:
        db.session.delete(baju)
        db.session.commit()
        return jsonify({'message': 'Baju berhasil dihapus'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Error handler untuk menangani HTTPException dan menampilkan flash message
@app.errorhandler(HTTPException)
def handle_error(e):
    flash(f"Error: {e.description}", "danger")
    return redirect(url_for('index'))

# Menjalankan aplikasi jika file ini dijalankan langsung
if __name__ == '__main__':
    app.run(debug=True)
