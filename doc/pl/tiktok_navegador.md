# Odczyt czatu TikTok z przeglądarki: rozszerzenie lokalnego podpisywania

Ten poradnik opisuje alternatywny sposób odczytu czatu transmisji na żywo TikTok w VeTube, przeznaczony na wypadek, gdy zwykła metoda zawiedzie. Warto przeczytać go od początku do końca: najpierw do czego służy, potem dlaczego powstał, jak go zainstalować i używać, a na końcu uwagi dotyczące bezpieczeństwa.

## Do czego służy

Aby odczytać czat transmisji, TikTok wymaga, żeby żądanie do *websocketu* czatu było **podpisane**. VeTube zwykle prosi o ten podpis zewnętrzną usługę (EulerStream). Gdy ta usługa przestaje działać — co zdarza się często — VeTube nie może odczytać czatu **żadnej** transmisji TikTok zwykłą drogą.

Rozszerzenie rozwiązuje dokładnie ten problem: zamiast polegać na tej zewnętrznej usłudze, pozwala **twojej własnej przeglądarce** — która ma już otwartą transmisję i już odbiera czat przez podpisane, działające połączenie — przekazywać te wiadomości do VeTube. Rozszerzenie nie oblicza żadnego nowego podpisu: po prostu kopiuje wiadomości, które twoja przeglądarka już odbiera.

W jednym zdaniu: *VeTube czyta czat, zaglądając przez ramię twojej przeglądarki, która jest tym, co naprawdę jest połączone z TikTokiem.*

## Dlaczego powstało

Nie istnieje oficjalne API do odczytu czatu transmisji TikTok, więc VeTube (i każdy podobny program) zależy od zewnętrznej usługi obliczającej podpis wymagany przez TikTok. Ta usługa, EulerStream:

- często przestaje działać (a gdy nie działa, nikt nie może w ten sposób odczytać żadnej transmisji TikTok),
- dzieli ograniczony limit między wszystkich swoich użytkowników,
- jest podmiotem zewnętrznym, niezwiązanym z VeTube.

Ponieważ podpisu nie da się pominąć, rozszerzenie powstało, aby rozwiązać ten problem bez zależności od tego zewnętrznego podmiotu: skoro przeglądarka już ogląda transmisję przez podpisane, działające połączenie, nie trzeba prosić nikogo innego o podpis. To alternatywa, a nie stałe zastępstwo — służy na wypadek, gdy zwykła usługa zawiedzie.

## Jak go zainstalować

Rozszerzenia **nie ma w Chrome Web Store**: jest dołączone do VeTube, w folderze `interceptor_extension`. Aby je zainstalować, jednorazowo:

1. Otwórz Chrome (lub przeglądarkę opartą na Chromium, np. Edge lub Brave) i przejdź do `chrome://extensions`.
2. Włącz **„Tryb dewelopera”** (przełącznik w prawym górnym rogu).
3. Kliknij **„Wczytaj rozpakowane”** i wybierz folder `interceptor_extension` (dołączony do VeTube).
4. Gotowe: na liście rozszerzeń pojawi się **„VeTube – most czatu TikTok Live”**.

## Jak go używać

Na ekranie głównym VeTube, w rozwijanej liście **„Przechwytuj czat z:”**, są dwie opcje dla TikToka: **„TikTok”** (zwykła usługa) i **„TikTok (przeglądarka, eksperymentalne)”** (to rozszerzenie). Aby użyć rozszerzenia bezpośrednio:

1. Otwórz transmisję w przeglądarce (z już zainstalowanym rozszerzeniem). Chrome pokaże pasek z napisem *„… debuguje tę przeglądarkę”*: to normalne i oznacza, że rozszerzenie odczytuje czat. Nie zamykaj go.
2. W VeTube wpisz **tego samego użytkownika**, co w transmisji (`@użytkownik`, dokładnie tak, jak jest zapisany).
3. Wybierz **„TikTok (przeglądarka, eksperymentalne)”** w „Przechwytuj czat z:” i kliknij **Połącz**.

Możesz też pozwolić, żeby VeTube zaproponował to samo automatycznie: jeśli wybierzesz zwykły „TikTok”, a zwykłe połączenie zawiedzie, VeTube zapyta, czy chcesz przejść na odczyt z przeglądarki (przy już otwartej tam transmisji). Jeśli się zgodzisz, odczyt jest kontynuowany bez ponownego uruchamiania.

Wymagania: rozszerzenie musi być wczytane **przed** otwarciem transmisji (jeśli karta była już otwarta, odśwież ją), a na tej karcie nie mogą być otwarte narzędzia deweloperskie (F12), ponieważ korzystają z tego samego kanału co rozszerzenie.

## Uwagi dotyczące bezpieczeństwa

- **Rozszerzenie tylko odczytuje to, co twoja przeglądarka już odbiera.** Nie omija żadnego zabezpieczenia TikToka: podpis nadal oblicza sam TikTok, w ramach twojej własnej sesji, tak jak zawsze.
- **Nigdy nie wysyła twojego ciasteczka sesji** (`sessionid`) ani żadnych danych uwierzytelniających konta. Czat publicznej transmisji działa tak samo bez zalogowania.
- **Wszystko pozostaje na twoim komputerze.** Rozszerzenie komunikuje się wyłącznie z `127.0.0.1:8790` (VeTube, na twojej własnej maszynie); nic nie jest wysyłane do żadnego zewnętrznego serwera ani podmiotu trzeciego.
- **Nie modyfikuje strony TikToka** ani nie ingeruje w jej bezpieczeństwo: obserwuje jedynie ruch czatu, tak samo jak zobaczyłyby to narzędzia deweloperskie przeglądarki.

Więcej szczegółów technicznych (jak zbudowane jest rozszerzenie, protokół komunikacji z VeTube i diagnostyka problemów) znajduje się w plikach `FIRMADOR_LOCAL.md` i `interceptor_extension/LEEME.md` w kodzie źródłowym VeTube.
