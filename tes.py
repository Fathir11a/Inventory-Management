import sqlite3
from flask import render_template, session, redirect, url_for

@app.route('/stok-masuk')
def stok_masuk():
    # Pastikan user sudah login dan memiliki role 'admin'
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    try:
        # Langsung koneksi ke database
        conn = sqlite3.connect('nama_database.db')  # Ganti dengan nama file database kamu
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT sm.id, b.nama AS nama_barang, sm.jumlah, sm.tanggal 
            FROM stok_masuk sm
            JOIN barang b ON sm.barang_id = b.id
            ORDER BY sm.tanggal DESC
        ''')
        data = cursor.fetchall()

        # Debug: print isi data ke terminal
        print("=== DEBUG: Isi data stok masuk ===")
        for row in data:
            print(dict(row))

        conn.close()

    except sqlite3.Error as e:
        return f"Database error: {e}"

    # Kirim data ke template HTML
    return render_template('stok_masuk.html', data=data)
