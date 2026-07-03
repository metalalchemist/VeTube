# VeTube dan Discord: panduan langkah demi langkah

VeTube dapat membaca pesan dari kanal teks di server Discord secara real-time. Untuk melakukannya lewat jalur resmi, Discord mewajibkan penggunaan "bot": akun khusus yang Anda buat sendiri secara gratis, cukup sekali, dalam sekitar 10 menit. Panduan ini menjelaskan seluruh prosesnya dan ditulis untuk pengguna pembaca layar (tanpa tangkapan layar, dengan nama persis setiap tombol).

Catatan: portal pengembang Discord hanya tersedia dalam bahasa Inggris, karena itu nama tombolnya ditulis di sini dalam bahasa Inggris. Aplikasi obrolan Discord sendiri sudah diterjemahkan.

## Yang Anda perlukan
- Akun Discord.
- Izin untuk mengundang bot ke server yang ingin Anda baca (izin "Kelola Server"). Jika tidak punya, di akhir langkah 4 Anda bisa mengirim tautan undangan ke administrator agar dibukakan untuk Anda.

## Langkah 1: membuat aplikasi
1. Buka https://discord.com/developers/applications lalu masuk.
2. Tekan tombol "New Application".
3. Ketik nama (misalnya "VeTube"), setujui ketentuannya, lalu tekan "Create".

## Langkah 2: mendapatkan token bot
1. Di halaman aplikasi Anda, buka bagian "Bot" pada menu di sebelah kiri.
2. Tekan tombol "Reset Token" dan konfirmasi dengan "Yes, do it!". Jika Anda memakai verifikasi dua langkah, kode akan diminta.
3. Token baru muncul dengan tombol "Copy" untuk menyalinnya ke papan klip. Tempelkan sementara di tempat aman, misalnya Notepad.

Penting: token itu seperti kata sandi bot Anda. Jangan dibagikan atau dipublikasikan. Jika bocor, kembali ke halaman ini dan tekan "Reset Token" untuk membuat yang baru; token lama berhenti berfungsi.

## Langkah 3: mengaktifkan "Message Content Intent"
Tanpa opsi ini, Discord tidak mengizinkan bot membaca isi pesan.
1. Masih di bagian "Bot", gulir ke bawah sampai "Privileged Gateway Intents".
2. Nyalakan sakelar "Message Content Intent".
3. Tekan "Save Changes" pada bilah yang muncul.

## Langkah 4: mengundang bot ke server Anda
1. Buka bagian "OAuth2" pada menu di sebelah kiri dan cari "URL Generator".
2. Pada daftar "Scopes", centang kotak "bot".
3. Pada "Bot Permissions" yang muncul di bawahnya, centang "View Channels" dan "Read Message History".
4. Di bagian bawah halaman, pada "Generated URL", tekan "Copy".
5. Buka URL itu di peramban, pilih server pada kotak kombo, lalu tekan "Lanjutkan" kemudian "Otorisasi". (Jika Anda tidak boleh mengundang bot, kirim URL itu ke administrator server.)

## Langkah 5: menyalin tautan kanal
1. Di Discord, temukan kanal teks yang ingin Anda baca.
2. Buka menu konteksnya: klik kanan, atau tombol Aplikasi atau Shift+F10 dengan pembaca layar.
3. Pilih "Salin Tautan". Tautannya berbentuk seperti ini: https://discord.com/channels/1234567890/0987654321

## Langkah 6: menempel di VeTube
1. Buka VeTube, tempelkan tautan kanal di kotak teks utama, lalu tekan "Akses" atau Enter.
2. Pada kali pertama, VeTube akan meminta token bot: tempelkan lalu tekan "OK". Token akan disimpan dan tidak diminta lagi.
3. Selesai! Pesan dari kanal mulai berdatangan. Pesan pemilik server dan orang yang bisa memoderasi muncul di kategori "Moderator"; sisanya di "Umum".

## Pemecahan masalah
- "Token tidak valid": salin token secara lengkap dari portal (langkah 2). Jika ragu, buat yang baru dengan "Reset Token".
- "Bot belum mengaktifkan opsi Message Content Intent": ulangi langkah 3 dan simpan perubahannya.
- "Kanal Discord tidak ditemukan": pastikan bot diundang ke server yang sama (langkah 4) dan tautan kanal yang disalin benar (langkah 5).
- Obrolan tersambung tetapi tidak ada pesan masuk: pastikan bot dapat melihat kanal itu. Untuk kanal privat, beri bot akses atau peran yang memilikinya.
