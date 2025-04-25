from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = ''  # untuk session

from flask import g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_user_from_db(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_from_db(username)
        if user and user[2] == password:
            session['username'] = username
            session['role'] = user[3]  

            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))

    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    if 'username' in session and session.get('role') == 'admin':
        conn = get_db()
        cursor = conn.cursor()
        query = '''
            SELECT
                b.id,
                b.barang,
                b.jumlah,
                COALESCE(SUM(sm.jumlah), 0) AS stok_masuk,
                COALESCE(SUM(sk.jumlah), 0) AS stok_keluar
            FROM
                stock b
            LEFT JOIN stok_masuk sm ON b.id = sm.barang_id
            LEFT JOIN stok_keluar sk ON b.id = sk.barang_id
            GROUP BY
                b.id;
        '''
        cursor.execute(query)
        laporan = cursor.fetchall()
        conn.close()

        return render_template('admin.html', username=session['username'], laporan=laporan)

    return "Akses ditolak! Hanya admin yang bisa melihat halaman ini."


@app.route('/tambah-barang', methods=['GET', 'POST'])
def tambah_barang():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        if all(key in request.form for key in ('barang', 'jumlah', 'harga')):
            barang = request.form['barang']
            jumlah = request.form['jumlah']
            harga = request.form['harga']

            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO stock (barang, jumlah, harga) VALUES (?, ?, ?)", 
                      (barang, jumlah, harga))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_dashboard'))
        else:
            return "Data tidak lengkap!"

    return render_template('tambah_barang.html')


@app.route('/lihat-barang')
def lihat_barang():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM stock")
    data_barang = c.fetchall()
    conn.close()

     # Debug: Cek data yang dikembalikan
    print("=== DATA BARANG USER ===")
    print(data_barang)

    return render_template('lihat_barang.html', barang=data_barang)

@app.route('/edit-barang/<int:id>', methods=['GET', 'POST'])
def edit_barang(id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        barang = request.form['barang']
        jumlah = request.form['jumlah']
        harga = request.form['harga']
        c.execute("UPDATE stock SET barang=?, jumlah=?, harga=? WHERE id=?", 
                  (barang, jumlah, harga, id))
        conn.commit()
        conn.close()
        return redirect(url_for('lihat_barang'))

    c.execute("SELECT * FROM stock WHERE id=?", (id,))
    barang = c.fetchone()
    conn.close()
    return render_template('edit_barang.html', stock=barang)

@app.route('/hapus-barang/<int:id>')
def hapus_barang(id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM stock WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('lihat_barang'))


@app.route('/stok-masuk')
def stok_masuk():
    # Pastikan user sudah login dan memiliki role 'admin'
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))  # Arahkan ke halaman login jika tidak memenuhi syarat
    db = get_db()
    try:
        cursor = db.execute('''
            SELECT sm.id, b.barang AS nama_barang, sm.jumlah, sm.tanggal 
            FROM stok_masuk sm
            JOIN stock b ON sm.barang_id = b.id
            ORDER BY sm.tanggal DESC
        ''')

        data = cursor.fetchall()

        
        print("=== DATA STOK MASUK ===")
        print(data)  # Debug: Cek data yang dikembalikan

    except sqlite3.Error as e:
        # Tangani jika ada error koneksi database
        return f"Database error: {e}"

    # Render template dengan data yang diambil dari query
    return render_template('stok_masuk.html', data=data)

@app.route('/stok-keluar')
def stok_keluar():
    # Pastikan user sudah login dan memiliki role 'admin'
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    try:
        cursor = db.execute('''
            SELECT sk.id, b.barang AS nama_barang, sk.jumlah, sk.tanggal 
            FROM stok_keluar sk
            JOIN stock b ON sk.barang_id = b.id
            ORDER BY sk.tanggal DESC
        ''')
        data = cursor.fetchall()

        print("=== DATA STOK MASUK ===")
        print(data)  # Debug: Cek data yang dikembalikan

    except sqlite3.Error as e:
        return f"Database error: {e}"

    return render_template('stok_keluar.html', data=data)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

# Tampilkan daftar pengguna (admin only)
@app.route('/pengguna')
def pengguna():
    if session.get('role') != 'admin':
        flash("Akses ditolak")
        return redirect(url_for('index'))  # Redirect ke halaman utama atau login
    
    conn = get_db()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('pengguna.html', users=users)


@app.route('/edit-pengguna/<int:id>', methods=['GET', 'POST'])
def edit_pengguna(id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        new_password = request.form['new_password']
        new_role = request.form['new_role']

        # Update password jika diisi
        if new_password:
            c.execute("UPDATE users SET password=? WHERE id=?", (new_password, id))

        # Update role jika diisi
        if new_role:
            c.execute("UPDATE users SET role=? WHERE id=?", (new_role, id))

        conn.commit()
        conn.close()
        return redirect(url_for('pengguna'))  # Redirect ke halaman daftar pengguna

    c.execute("SELECT * FROM users WHERE id=?", (id,))
    user = c.fetchone()
    conn.close()
    return render_template('edit_pengguna.html', user=user)


# Hapus pengguna (admin only)
@app.route('/hapus-pengguna/<int:id>')
def hapus_pengguna(id):
    if session.get('role') != 'admin':
        flash("Akses ditolak")
        return redirect(url_for('index'))

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Pengguna berhasil dihapus.")
    return redirect(url_for('pengguna'))


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Memeriksa peran pengguna
    user_role = session.get('role')  

    if user_role not in ['admin', 'user']:
        return "Access Denied", 403  

    db = get_db()
    cur = db.execute('SELECT id, barang, jumlah FROM stock')
    barang = cur.fetchall()

    return render_template('dashboard.html', username=session['username'], barang=barang, user_role=user_role)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import sqlite3

@app.route('/input-stok', methods=['GET', 'POST'])
def input_stok():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Ambil daftar barang
    c.execute("SELECT id, barang FROM stock")
    barang_list = c.fetchall()

    # Ambil user_id dari username
    c.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
    user = c.fetchone()
    user_id = user[0] if user else None

    if request.method == 'POST':
        barang_id = request.form['barang_id']
        jumlah = int(request.form['jumlah'])
        tanggal = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tipe = request.form['tipe']  # Menentukan stok masuk atau keluar

        if user_id is None:
            conn.close()
            return "User tidak ditemukan."

        if tipe == 'masuk':
            # Masukkan stok masuk ke database
            c.execute("INSERT INTO stok_masuk (barang_id, jumlah, tanggal, user_id) VALUES (?, ?, ?, ?)", 
                      (barang_id, jumlah, tanggal, user_id))
            # Update stok
            c.execute("UPDATE stock SET jumlah = jumlah + ? WHERE id = ?", (jumlah, barang_id))
            flash('Stok berhasil dimasukkan!', 'success')

        elif tipe == 'keluar':
            # Masukkan stok keluar ke database
            c.execute("INSERT INTO stok_keluar (barang_id, jumlah, tanggal, user_id) VALUES (?, ?, ?, ?)", 
                      (barang_id, jumlah, tanggal, user_id))
            # Update stok
            c.execute("UPDATE stock SET jumlah = jumlah - ? WHERE id = ?", (jumlah, barang_id))
            flash('Stok berhasil dikeluarkan!', 'success')

        conn.commit()
        conn.close()
        return redirect(url_for('input_stok'))

    conn.close()
    return render_template('input_stok.html', barang_list=barang_list)



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, 'user'))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username sudah digunakan, coba yang lain."
        
        conn.close()
        return redirect(url_for('login'))

    return render_template('register.html')

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        issue = request.form.get('issue')

        conn = get_db()
        conn.execute(
        'INSERT INTO report (user_id, issue, status) VALUES (?, ?, ?)',
        (user_id, issue, 'pending')
        )

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('report.html') 

@app.route('/admin/reports')
def admin_report():
    conn = get_db()
    reports = conn.execute('SELECT * FROM report ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('admin_report.html', reports=reports)


@app.route('/admin/update_status', methods=['POST'])
def update_report_status():
    report_id = request.form['report_id']
    new_status = request.form['status']
    
    conn = get_db()
    conn.execute('UPDATE report SET status = ? WHERE id = ?', (new_status, report_id))
    conn.commit()
    print(f"[DEBUG] Updating Report ID {report_id} -> Status: {new_status}")

    conn.close()

    return redirect('/admin/reports') 



if __name__ == '__main__':
    app.run(debug=True)