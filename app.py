import re

from flask import Flask, abort, redirect, request, url_for
from markupsafe import escape

app = Flask(__name__)

# Data User dan Armada
USERS = {
    "admin_rental": {"nama": "Rina Wijaya", "peran": "Admin", "bergabung": "Januari 2023"},
    "member_dewi": {"nama": "Dewi Anggraini", "peran": "Member", "bergabung": "Maret 2024"},
    "pelanggan_budi": {"nama": "Budi Santoso", "peran": "Pelanggan", "bergabung": "Agustus 2025"},
}

ARMADA = [
    {"id": 1, "nama": "Toyota Avanza", "kursi": 7, "harga": 350000},
    {"id": 2, "nama": "Toyota Avanza Veloz", "kursi": 7, "harga": 400000},
    {"id": 3, "nama": "Honda Brio Satya", "kursi": 5, "harga": 280000},
    {"id": 4, "nama": "Toyota Kijang Innova", "kursi": 7, "harga": 550000},
    {"id": 5, "nama": "Toyota Fortuner", "kursi": 7, "harga": 900000},
]

# validasi
USERNAME_RE = re.compile(r"[a-z0-9_]{4,15}")
RESERVED = {"admin", "owner", "root", "system"}
ATURAN = "4 sampai 15 karakter; hanya huruf kecil, angka, dan garis bawah (_)."


def periksa_username(username):
    """Kembalikan (status, pesan)."""
    if len(username) < 4:
        return "tidak_valid", "Terlalu pendek. Minimal 4 karakter."
    if len(username) > 15:
        return "tidak_valid", "Terlalu panjang. Maksimal 15 karakter."
    if not USERNAME_RE.fullmatch(username):
        return "tidak_valid", "Hanya boleh huruf kecil, angka, dan garis bawah (_)."
    if username in RESERVED:
        return "dicadangkan", "Nama ini dicadangkan oleh sistem dan tidak bisa dipakai."
    if username in USERS:
        return "terdaftar", "Username sudah dipakai."
    return "tersedia", "Username ini masih tersedia."


def rupiah(nilai):
    return "Rp" + f"{nilai:,}".replace(",", ".")


# Pembuat halaman
def halaman(judul, isi):
    """Membungkus isi dengan navbar dan footer. Fase 2 menggantinya dengan base.html."""
    menu = [("beranda", "Beranda"), ("tentang", "Tentang"), ("produk", "Armada"),
            ("kontak", "Kontak"), ("cek_form", "Cek username")]
    navbar = " | ".join(f'<a href="{url_for(ep)}">{label}</a>' for ep, label in menu)
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{judul} | Millena Car</title></head>
<body style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; padding: 16px; line-height: 1.5">
<nav style="border-bottom: 1px solid #ccc; padding-bottom: 8px; margin-bottom: 24px">{navbar}</nav>
{isi}
<footer style="margin-top: 40px; color: #777; font-size: 14px">Millena Car</footer>
</body></html>"""


def form_cek(nilai=""):
    return f"""<form action="{url_for('cek_form')}" method="get">
<input name="username" value="{escape(nilai)}" placeholder="contoh: member_dewi" required>
<button type="submit">Cek username</button>
<br><small>{ATURAN}</small></form>"""


# Route statis
@app.route("/")
def beranda():
    return halaman("Beranda", f"""<h1>Millena Car</h1>
<p>Sewa mobil harian. Cek dulu username akunmu:</p>{form_cek()}""")


@app.route("/tentang")
def tentang():
    return halaman("Tentang", """<h1>Tentang</h1>
<p>Millena Car menyewakan mobil harian dengan atau tanpa sopir.
Akun ada tiga jenis: pelanggan, member, dan admin.</p>""")


@app.route("/produk")
def produk():
    baris = "".join(
        f'<li><a href="{url_for("produk_detail", id=m["id"])}">{m["nama"]}</a>'
        f' - {rupiah(m["harga"])}/hari</li>' for m in ARMADA)
    return halaman("Armada", f"<h1>Armada</h1><ul>{baris}</ul>")


@app.route("/kontak")
def kontak():
    return halaman("Kontak", """<h1>Kontak</h1>
<p>WhatsApp: 0812-0000-0000<br>Email: halo@millenacar.example</p>""")


# Route converter int
@app.route("/produk/<int:id>")
def produk_detail(id):
    mobil = next((m for m in ARMADA if m["id"] == id), None)
    if mobil is None:
        abort(404)
    return halaman(mobil["nama"], f"""<h1>{mobil['nama']}</h1>
<p>Kapasitas: {mobil['kursi']} kursi<br>Harga: {rupiah(mobil['harga'])} per hari</p>
<p><a href="{url_for('produk')}">Kembali ke armada</a></p>""")


# Route dinamis
@app.route("/cek")
def cek_form():
    q = request.args.get("username", "").strip().lower()
    if not q:
        return halaman("Cek username", f"<h1>Cek username</h1>{form_cek()}")
    if USERNAME_RE.fullmatch(q):
        return redirect(url_for("cek", username=q))
    status, pesan = periksa_username(q)
    return halaman("Cek username", f"<h1>Cek username</h1>{form_cek(q)}<p>{pesan}</p>"), 400


@app.route("/cek/<username>")
def cek(username):
    kanonik = username.lower()
    if kanonik != username:
        return redirect(url_for("cek", username=kanonik), code=301)

    status, pesan = periksa_username(username)
    kode = 400 if status in ("tidak_valid", "dicadangkan") else 200
    tautan = ""
    if status == "terdaftar":
        tautan = f'<p><a href="{url_for("user_profile", username=username)}">Lihat profil</a></p>'
    return halaman("Cek username", f"""<h1>Cek username</h1>{form_cek(username)}
<h2>{escape(username)}</h2><p>{pesan}</p>{tautan}"""), kode


@app.route("/user/<username>")
def user_profile(username):
    nama = username.lower()
    if not USERNAME_RE.fullmatch(nama):
        return redirect(url_for("cek", username=nama))
    data = USERS.get(nama)
    if data is None:
        abort(404)
    return halaman(f"Profil {nama}", f"""<h1>{data['nama']}</h1>
<p>Username: {nama}<br>Peran: {data['peran']}<br>Bergabung: {data['bergabung']}</p>""")


# Halaman 404
@app.errorhandler(404)
def halaman_tidak_ditemukan(error):
    return halaman("Tidak ditemukan", f"""<h1>404: Halaman tidak ditemukan</h1>
<p><a href="{url_for('beranda')}">Kembali ke beranda</a></p>"""), 404


if __name__ == "__main__":
    app.run(debug=True)
