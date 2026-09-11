# Membaca chat TikTok dari browser: ekstensi penanda tangan lokal

Panduan ini menjelaskan cara alternatif untuk membaca chat siaran langsung TikTok di VeTube, untuk digunakan saat cara biasa gagal. Panduan ini disusun untuk dibaca dari atas ke bawah: pertama untuk apa fungsinya, lalu mengapa dibuat, cara memasang dan menggunakannya, dan terakhir catatan keamanannya.

## Untuk apa fungsinya

Untuk membaca chat sebuah siaran langsung, TikTok mengharuskan permintaan ke *websocket* chat harus **ditandatangani**. VeTube biasanya meminta tanda tangan itu ke layanan eksternal (EulerStream). Ketika layanan itu mati — yang sering terjadi — VeTube tidak bisa membaca chat siaran langsung TikTok **mana pun** lewat jalur biasa.

Ekstensi ini menyelesaikan masalah itu: alih-alih bergantung pada layanan eksternal tersebut, ekstensi ini membiarkan **browser kamu sendiri** — yang sudah membuka siaran langsung itu dan sudah menerima chatnya lewat koneksi yang sudah ditandatangani dan berfungsi — meneruskan pesan-pesan itu ke VeTube. Ekstensi ini tidak menghitung tanda tangan baru: ia hanya menyalin pesan yang sudah diterima browser kamu.

Singkatnya: *VeTube membaca chat dengan "mengintip" dari browser kamu, karena browser itulah yang benar-benar terhubung ke TikTok.*

## Mengapa ekstensi ini dibuat

Tidak ada API resmi untuk membaca chat siaran langsung TikTok, jadi VeTube (dan program sejenis lainnya) bergantung pada layanan eksternal untuk menghitung tanda tangan yang diwajibkan TikTok. Layanan tersebut, EulerStream:

- sering mati (dan selama layanan itu mati, tidak ada yang bisa membaca siaran langsung TikTok dengan cara ini),
- membagi kuota terbatas di antara semua penggunanya,
- adalah pihak ketiga yang tidak terkait dengan VeTube.

Karena tanda tangan itu tidak bisa dihindari, ekstensi ini dibuat untuk mengatasi masalah tersebut tanpa bergantung pada pihak ketiga itu: jika browser kamu sudah menonton siaran langsung dengan koneksi yang sudah ditandatangani dan berfungsi, tidak perlu meminta tanda tangan ke pihak lain. Ini adalah alternatif, bukan pengganti tetap — digunakan saat layanan biasa gagal.

## Cara memasangnya

Ekstensi ini **tidak ada di Chrome Web Store**: ekstensi ini sudah disertakan bersama VeTube, di folder `interceptor_extension`. Untuk memasangnya, cukup sekali saja:

1. Buka Chrome (atau browser berbasis Chromium lainnya, seperti Edge atau Brave) dan buka `chrome://extensions`.
2. Aktifkan **"Mode pengembang"** (sakelar di kanan atas).
3. Klik **"Muat yang belum dipaketkan"** dan pilih folder `interceptor_extension` (yang disertakan bersama VeTube).
4. Selesai: **"VeTube – jembatan chat TikTok Live"** akan muncul di daftar ekstensi.

## Cara menggunakannya

Di layar utama VeTube, pada menu tarik-turun **"Tangkap chat dari:"**, ada dua pilihan untuk TikTok: **"TikTok"** (layanan biasa) dan **"TikTok (browser, eksperimental)"** (ekstensi ini). Untuk menggunakan ekstensi ini secara langsung:

1. Buka siaran langsungnya di browser kamu (dengan ekstensi yang sudah terpasang). Chrome akan menampilkan bilah bertuliskan *"… sedang men-debug browser ini"*: ini normal dan menjadi tanda bahwa ekstensi sedang membaca chat. Jangan tutup bilah itu.
2. Di VeTube, ketik **nama pengguna yang sama** dengan siaran langsungnya (`@pengguna`, persis seperti yang tertulis).
3. Pilih **"TikTok (browser, eksperimental)"** pada "Tangkap chat dari:" lalu klik **Akses**.

Kamu juga bisa membiarkan VeTube menawarkannya secara otomatis: jika kamu memilih "TikTok" biasa dan koneksi biasa gagal, VeTube akan bertanya apakah kamu ingin beralih membaca dari browser (dengan siaran langsung yang sudah dibuka di sana). Jika kamu setuju, chat tetap dibaca tanpa perlu memulai ulang apa pun.

Syarat: ekstensi harus sudah dimuat **sebelum** siaran langsungnya dibuka (jika tab-nya sudah terbuka lebih dulu, muat ulang tab tersebut), dan jangan membuka alat pengembang (F12) pada tab itu, karena alat itu menggunakan saluran yang sama dengan ekstensi.

## Catatan keamanan

- **Ekstensi ini hanya membaca apa yang sudah diterima browser kamu.** Ia tidak melewati perlindungan apa pun dari TikTok: tanda tangannya tetap dibuat oleh TikTok sendiri, dalam sesi kamu, seperti biasa.
- **Ekstensi ini tidak pernah mengirim cookie sesi kamu** (`sessionid`) atau kredensial akun apa pun. Chat siaran langsung publik tetap berfungsi sama tanpa perlu masuk akun.
- **Semuanya tetap berada di komputer kamu.** Ekstensi ini hanya berkomunikasi dengan `127.0.0.1:8790` (VeTube, di mesin kamu sendiri); tidak ada yang dikirim ke server eksternal atau pihak ketiga mana pun.
- **Ekstensi ini tidak mengubah halaman TikTok** atau mengganggu keamanannya: ia hanya mengamati lalu lintas chat, sama seperti yang akan terlihat oleh alat pengembang browser.

Detail teknis lebih lanjut (bagaimana ekstensi ini dibuat, protokol yang digunakan untuk berkomunikasi dengan VeTube, dan cara mendiagnosis masalah) ada di `FIRMADOR_LOCAL.md` dan `interceptor_extension/LEEME.md`, di dalam kode sumber VeTube.
