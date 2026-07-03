# VeTube i Discord: przewodnik krok po kroku

VeTube może na żywo czytać wiadomości z kanału tekstowego na serwerze Discord. Oficjalna droga wymagana przez Discorda to użycie „bota": specjalnego konta, które sami tworzycie za darmo, tylko raz, w około 10 minut. Ten przewodnik opisuje cały proces i jest napisany z myślą o użytkownikach czytników ekranu (bez zrzutów ekranu, z dokładnymi nazwami wszystkich przycisków).

Uwaga: portal deweloperów Discorda jest dostępny wyłącznie po angielsku, dlatego nazwy jego przycisków podano tu po angielsku. Sama aplikacja czatu Discord jest przetłumaczona.

## Czego potrzebujesz
- Konta Discord.
- Uprawnienia do zapraszania botów na serwer, który chcesz czytać (uprawnienie „Zarządzanie serwerem"). Jeśli go nie masz, na końcu kroku 4 możesz wysłać link z zaproszeniem administratorowi, aby otworzył go za Ciebie.

## Krok 1: utworzenie aplikacji
1. Otwórz https://discord.com/developers/applications i zaloguj się.
2. Naciśnij przycisk „New Application".
3. Wpisz nazwę (na przykład „VeTube"), zaakceptuj warunki i naciśnij „Create".

## Krok 2: pobranie tokenu bota
1. Na stronie swojej aplikacji przejdź do sekcji „Bot" w menu po lewej stronie.
2. Naciśnij przycisk „Reset Token" i potwierdź przyciskiem „Yes, do it!". Jeśli masz weryfikację dwuetapową, zostaniesz poproszony o kod.
3. Pojawi się nowy token z przyciskiem „Copy" do skopiowania go do schowka. Wklej go tymczasowo w bezpieczne miejsce, na przykład do Notatnika.

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
5. Otwórz ten adres w przeglądarce, wybierz serwer z listy rozwijanej i naciśnij „Kontynuuj", a potem „Autoryzuj". (Jeśli nie możesz zapraszać botów, wyślij ten adres administratorowi serwera.)

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
- „Bot nie ma włączonej opcji Message Content Intent": powtórz krok 3 i zapisz zmiany.
- „Nie znaleziono kanału Discorda": sprawdź, czy bot został zaproszony na ten właśnie serwer (krok 4) i czy skopiowano link do właściwego kanału (krok 5).
- Czat się łączy, ale wiadomości nie przychodzą: upewnij się, że bot widzi ten kanał. W przypadku kanałów prywatnych trzeba dać mu dostęp albo rolę, która go ma.
