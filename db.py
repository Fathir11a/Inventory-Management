import sqlite3

# Koneksi ke database
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Hapus tabel lama jika ada
c.execute("DROP TABLE IF EXISTS report;")

# Buat tabel baru
c.execute('''
    CREATE TABLE report (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        issue TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending'
    );
''')

# Commit perubahan
conn.commit()
conn.close()

print("Tabel 'report' berhasil dibuat.")