# VeTube

Kelola dan baca chat dari siaran langsung milikmu atau dari kreator favoritmu dengan mudah.
[Demonstrasi fungsi program ini](https://youtu.be/4XawJoBymPs)

## Platform yang Didukung:

- YouTube (tayangan perdana, siaran langsung, dan yang sudah selesai)
- Twitch.tv (siaran langsung dan yang sudah selesai)
- TikTok (siaran langsung)
- Kick (siaran langsung)
- QuentinC's playroom (chat dari berbagai meja permainan)

## Fitur

- Mode otomatis: Membaca pesan chat secara real-time menggunakan suara sapi5, atau melalui pembaca layar yang digunakan.
- Antarmuka tidak terlihat: Kelola chat dari jendela mana pun menggunakan pintasan keyboard sederhana. Diperlukan pembaca layar yang aktif.
- Pembaca layar yang didukung:
  - NVDA
  - JAWS
  - Window-Eyes
  - SuperNova
  - System Access
  - PC Talker
  - ZDSR
- Dapat disesuaikan dengan kebutuhan pengguna:
  - Aktifkan atau nonaktifkan suara aplikasi.
  - Aktifkan atau nonaktifkan mode baca otomatis.
  - Konfigurasikan daftar pesan dalam antarmuka tak terlihat.
  - Atur preferensi suara sapi.
  - Personalisasi pintasan keyboard global.
- simpan beberapa obrolan yang dimonitor.
- Mudah mengubah mode pembacaan chat: baca semua chat atau hanya kategori tertentu.
- Simpan siaran langsung favoritmu. Putar ulang chat sebanyak yang diinginkan tanpa perlu mencari ulang tautan.
- simpan pesan Anda di bagian favorit. Ulangi chat tersebut sebanyak yang Anda mau tanpa harus mencari link lagi.
- Arsipkan pesan untuk pengingat penting.
- Terjemahkan chat dalam siaran langsung ke dalam bahasa yang diinginkan.

## Pintasan Keyboard

### Menggunakan Antarmuka Tidak Terlihat:

| Aksi                                | Pintasan Keyboard         |
| ----------------------------------- | ------------------------- |
| Nonaktifkan suara sapi              | Control + P               |
| mulai/batalkan penangkapan obrolan siaran langsung lain              | Alt + Shift + h               |
| pergi ke siaran langsung sebelumnya                   | control + Alt + Shift + panah kiri  |
| pergi ke siaran langsung berikutnya                   | control + Alt + Shift + panah kanan |
| Buffer sebelumnya                   | Alt + Shift + panah kiri  |
| Buffer berikutnya                   | Alt + Shift + panah kanan |
| Elemen sebelumnya                   | Alt + Shift + panah atas  |
| Elemen berikutnya                   | Alt + Shift + panah bawah |
| Elemen awal                         | Alt + Shift + Home        |
| Elemen akhir                        | Alt + Shift + End         |
| Arsipkan pesan                      | Alt + Shift + A           |
| Salin pesan saat ini                | Alt + Shift + C           |
| Hapus buffer yang dibuat sebelumnya | Alt + Shift + D           |
| Tambahkan pesan ke favorit          | Alt + Shift + F           |
| Aktifkan/nonaktifkan mode otomatis  | Alt + Shift + R           |
| Nonaktifkan suara aplikasi          | Alt + Shift + P           |
| Cari kata dalam pesan               | Alt + Shift + S           |
| Tampilkan pesan dalam kotak teks    | Alt + Shift + V           |
| Buka editor keyboard VeTube         | Alt + Shift + K           |
| jeda atau lanjutkan pemutaran langsung      | control shift p           |
| maju cepat pemutaran langsung      | control shift panah kanan           |
| mundur cepat pemutaran langsung      | control shift panah kiri           |
| volume naik      | control shift panah atas           |
| volume turun      | control shift panah bawah           |
| Hentikan dan lepaskan pemutar      | control shift s           |

### Dalam Riwayat Chat:

| Aksi                     | Pintasan Keyboard |
| ------------------------ | ----------------- |
| Putar pesan yang dipilih | Spasi             |

### Dalam Favorit:

| Aksi                     | Pintasan Keyboard |
| ------------------------ | ----------------- |
| Buka tautan yang dipilih | Spasi             |

## Rencana Pembaruan Mendatang:

Pembaruan yang akan datang mencakup:

- Menampilkan informasi pengguna yang sedang chatting dari antarmuka tidak terlihat:
  - Nama channel pengguna
  - Dan fitur tambahan lainnya

## Berkolaborasi dalam terjemahan
Jika Anda ingin berkontribusi menerjemahkan VeTube ke bahasa Anda, Anda perlu menginstal alat internasionalisasi.
1.  **Instal Babel:**
    ```bash
    pip install Babel
    ```
    *Catatan: Pastikan Anda menginstal paket `Babel` (huruf besar B direkomendasikan di PyPI, meskipun pip tidak peka huruf besar-kecil), hindari paket berukuran kecil yang salah.*

2.  **Ekstrak teks untuk memperbarui template (.pot):**
    Jika string baru telah ditambahkan ke kode, perbarui file template dengan perintah ini:
    ```bash
    pybabel extract -F babel.cfg -o VeTube.pot .
    ```

3.  **Mulai terjemahan baru:**
    Apabila Anda ingin menerjemahkan ke bahasa baru (contoh `it` untuk bahasa Italia), bisa gunakan perintah ini, perhatikan ada huruf local it nya:
    ```bash
    pybabel init -i vetube.pot -d locales -l it -D vetube
    ```

4.  **Memperbaharui terjemahan yang ada:**
    Jika bahasa sudah ada dan Anda telah mengextrak `.pot`, sinkronkan file `.po`:
    ```bash
    pybabel update -i VeTube.pot -d locales -D VeTube
    ```

5.  **Kompilasi terjemahan:**
    Agar program mengenali perubahan tersebut, kompilasi file `.po` menjadi `.mo`:
    ```bash
    pybabel compile -d locales -D VeTube
    ```


## Ucapan Terima Kasih:

Terima kasih kepada:

[4everzyanya](https://www.youtube.com/c/4everzyanya/),

Tester utama proyek ini.

[Johan G](https://github.com/JohanAnim),

Yang membantu membuat antarmuka grafis serta memperbaiki beberapa bug kecil.

Dengan dukungan kalian, aplikasi ini akan terus berkembang. Setiap ide dan kolaborasi kalian sangat dihargai dalam membangun proyek ini bersama-sama.

Untuk ide, laporan bug, dan saran, silakan hubungi:
cesar.verastegui17@gmail.com

## Tautan Unduhan

Dengan dukunganmu, program ini akan terus berkembang.

[Bergabunglah dengan kami](https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U)

[Unduh program untuk 64-bit](https://github.com/metalalchemist/VeTube/releases/download/v3.6/VeTube-x64.zip)  
[Unduh program untuk 32-bit](https://github.com/metalalchemist/VeTube/releases/download/v3.6/VeTube-x86.zip)
