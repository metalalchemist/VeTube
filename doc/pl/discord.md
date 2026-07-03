# VeTube i Discord: przewodnik krok po kroku

VeTube może na żywo czytać wiadomości z kanału tekstowego na serwerze Discord. Oficjalna droga wymagana przez Discorda to użycie „bota": specjalnego konta, które sami tworzycie za darmo, tylko raz, w około 10 minut. Ten przewodnik opisuje cały proces i jest napisany z myślą o użytkownikach czytników ekranu (bez zrzutów ekranu, z dokładnymi nazwami wszystkich przycisków).

Uwaga: portal deweloperów Discorda wyświetla się w języku Twojego konta Discord, jeśli jest dostępny; w przeciwnym razie po angielsku. Nazwy przycisków poniżej podano po angielsku jako odniesienie; jeśli Twój portal jest przetłumaczony, pojawią się w Twoim języku.

## Czego potrzebujesz
- Konta Discord.
- Uprawnienia do zapraszania botów na serwer, który chcesz czytać (uprawnienie „Zarządzanie serwerem"). Jeśli go nie masz, na końcu kroku 4 możesz wysłać link z zaproszeniem administratorowi, aby otworzył go za Ciebie.

## Krok 1: utworzenie aplikacji
1. Otwórz https://discord.com/developers/applications i zaloguj się.
2. Naciśnij przycisk „New Application".
3. Wpisz nazwę (na przykład „VeTube"), zaakceptuj warunki i naciśnij „Create".

## Krok 2: pobranie tokenu bota
1. Na stronie swojej aplikacji przejdź do sekcji „Bot" w menu po lewej stronie.
2. Naciśnij przycisk „Reset Token" i potwierdź przyciskiem „Yes, do it!".
3. Discord poprosi Cię ponownie o hasło (lub klucz dostępu), aby sprawdzić, że to Ty: wpisz je i zatwierdź. Jeśli masz weryfikację dwuetapową, może też poprosić o kod.
4. Pojawi się nowy token z przyciskiem „Copy" do skopiowania go do schowka. Wklej go tymczasowo w bezpieczne miejsce, na przykład do Notatnika: ze względów bezpieczeństwa token jest pokazywany tylko raz, przy utworzeniu.

Ważne: token jest jak hasło Twojego bota. Nie udostępniaj go i nigdzie nie publikuj. Jeśli wycieknie, wróć na tę stronę i naciśnij „Reset Token", aby wygenerować nowy; stary przestanie działać.

## Krok 3: włączenie „Message Content Intent"
Bez tej opcji Discord nie pozwala botowi czytać treści wiadomości.
1. Wciąż w sekcji „Bot" zjedź w dół do „Privileged Gateway Intents".
2. Włącz przełącznik „Message Content Intent".
3. Naciśnij „Save Changes" na pasku, który się pojawi.

## Krok 4: zaproszenie bota na Twój serwer
1. Przejdź do sekcji „OAuth2" w menu po lewej stronie i znajdź „URL Generator".
2. Na liście „Scopes" zaznacz pole „bot".
3. W części „Bot Permissions", która pojawi się poniżej, zaznacz „View Channels" i „Read Message History".
4. Na dole strony, przy „Generated URL", naciśnij „Copy".
5. Otwórz ten adres w przeglądarce i wybierz swój serwer z listy rozwijanej „Dodaj do serwera". Wskazówka dla czytnika ekranu: dopóki nie wybierzesz serwera, dolny przycisk nazywa się „Nie wypełniono niektórych pól"; po wybraniu serwera zmienia się na „Autoryzuj". Naciśnij go. (Jeśli nie możesz zapraszać botów, wyślij ten adres administratorowi serwera.)

## Krok 5: skopiowanie linku do kanału
1. W Discordzie znajdź kanał tekstowy, który chcesz czytać.
2. Otwórz jego menu kontekstowe: prawy przycisk myszy albo klawisz Aplikacje lub Shift+F10 z czytnikiem ekranu.
3. Wybierz „Kopiuj link". Link wygląda tak: https://discord.com/channels/1234567890/0987654321

## Krok 6: wklejenie do VeTube
1. Otwórz VeTube, wklej link do kanału w głównym polu tekstowym i naciśnij „Dostęp" lub Enter.
2. Za pierwszym razem VeTube poprosi o token bota: wklej go i naciśnij „OK". Zostanie zapisany i nie będzie więcej wymagany.
3. Gotowe! Wiadomości z kanału zaczną napływać. Wiadomości właściciela serwera i osób mogących moderować pojawią się w kategorii „Moderatorzy"; reszta w kategorii „Ogólne".

## Rozwiązywanie problemów
- „Token jest nieprawidłowy": skopiuj cały token z portalu (krok 2). W razie wątpliwości wygeneruj nowy przez „Reset Token".
- Discord prosi o hasło przy generowaniu tokenu: to normalne, to kontrola bezpieczeństwa (krok 2).
- „Bot nie ma włączonej opcji Message Content Intent": powtórz krok 3 i zapisz zmiany.
- „Nie znaleziono kanału Discorda": sprawdź, czy bot został zaproszony na ten właśnie serwer (krok 4) i czy skopiowano link do właściwego kanału (krok 5).
- Czat się łączy, ale wiadomości nie przychodzą: upewnij się, że bot widzi ten kanał. W przypadku kanałów prywatnych trzeba dać mu dostęp albo rolę, która go ma.
