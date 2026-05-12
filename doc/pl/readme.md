# vetube
Czytaj i zarządzaj w sposób dostępny czatem swoich własnych transmisji na żywo lub swoich ulubionych twórców.
[demonstracja działania produktu](https://youtu.be/4XawJoBymPs)
## obsługiwane witryny:
- youtube (premiery oraz transmisje na żywo trwające i przeszłe)
- twitch.tv (transmisje na żywo trwające i przeszłe)
- tiktok (transmisje na żywo trwające)
- kick (transmisje na żywo trwające)
- playroom (czat różnych stołów)
## Funkcje
- Tryb automatyczny: Czyta wiadomości czatu w czasie rzeczywistym za pomocą głosu SAPI5.
- Niewidzialny interfejs: Zarządzaj czatami z dowolnego okna za pomocą prostych poleceń klawiaturowych. Wymagany jest aktywny czytnik ekranu.
- Obsługiwane czytniki:
  - NVDA
  - JAWS
  - Window-Eyes
  - SuperNova
  - System Access
  - PC Talker
  - ZDSR
- Możliwość konfiguracji zgodnie z potrzebami użytkownika.
  - włączanie lub wyłączanie dźwięków programu.
  - włączanie lub wyłączanie automatycznego czytania.
  - konfigurowanie listy wiadomości w niewidzialnym interfejsie.
  - konfigurowanie preferencji głosu SAPI.
  - personalizowanie globalnych skrótów klawiszowych.
- utrzymywanie wielu przechwyconych czatów.
- łatwa zmiana trybu czytania czatów: zdecyduj, czy chcesz czytać wszystkie czaty, czy tylko te z konkretnej kategorii.
- zapisywanie transmisji w sekcji ulubionych. powtarzaj czat tyle razy, ile chcesz, bez konieczności ponownego szukania linku.
- archiwizowanie wiadomości: przydatne do przypomnień.
- tłumacz czat ze streamingu na dowolny język.

## Skróty klawiszowe.
### Korzystanie z niewidzialnego interfejsu.
| akcja                    | kombinacja klawiszy |
| ------------------------- | ----------- |
| Wycisz głos SAPI      | control+p           |
| rozpocznij/anuluj przechwytywanie nowej transmisji      | alt shift h            |
| przejdź do poprzedniej transmisji      | control alt shift strzałka w lewo            |
| przejdź do następnej transmisji     | control alt shift strzałka w prawo            |
| poprzedni bufor      | alt shift strzałka w lewo            |
| następny bufor      | alt shift strzałka w prawo            |
| Poprzedni element      | alt shift strzałka w górę           |
| Następny element      | alt shift strzałka w dół           |
| Pierwszy element      | alt shift home           |
| Ostatni element      | alt shift end           |
| archiwizuj wiadomość      | alt shift a           |
| Kopiuj aktualną wiadomość      | alt shift c           |
| Usuń wcześniej utworzony bufor      | alt shift d           |
| dodaj wiadomość do bufora ulubionych      | alt shift f           |
| Włącz lub wyłącz automatyczne czytanie      | alt shift r           |
| wyłącz dźwięki programu      | alt shift p           |
| szukaj słowa wśród wiadomości      | alt shift b           |
| pokaż aktualną wiadomość w polu tekstowym      | alt shift v           |
| wywołaj edytor klawiatury vetube      | alt shift k           |
| wstrzymaj lub wznów odtwarzanie transmisji      | control shift p           |
| przewiń transmisję do przodu      | control shift strzałka w prawo           |
| przewiń transmisję do tyłu      | control shift strzałka w lewo           |
| zwiększ głośność      | control shift strzałka w górę           |
| zmniejsz głośność      | control shift strzałka w dół           |
| zatrzymaj i zwolnij odtwarzacz      | control shift s           |

### W historii czatu:
| akcja                    | kombinacja klawiszy |
| ------------------------- | ----------- |
| Odtwórz wybraną wiadomość      | spacja           |

### W sekcji ulubionych:
| akcja                    | kombinacja klawiszy |
| ------------------------- | ----------- |
| przejdź do wybranego linku      | spacja           |

## przyszłe aktualizacje:
Dodałem do nadchodzących przyszłych aktualizacji:
- Możliwość wyświetlania informacji o osobie czatującej z niewidzialnego interfejsu:
  - Nazwa kanału użytkownika
  - I wiele więcej.

## Współpraca przy tłumaczeniu
Jeśli chcesz pomóc w tłumaczeniu VeTube na swój język, musisz zainstalować narzędzia do internacjonalizacji.

1.  **Zainstaluj Babel:**
    ```bash
    pip install Babel
    ```
    *Uwaga: Upewnij się, że instalujesz pakiet `Babel` (zalecane duże B w PyPI, choć pip nie rozróżnia wielkości liter), unikaj nieprawidłowych pakietów o bardzo małym rozmiarze.*

2.  **Wyodrębnij teksty, aby zaktualizować szablon (.pot):**
    Jeśli do kodu dodano nowe ciągi znaków, zaktualizuj plik szablonu:
    ```bash
    pybabel extract -F babel.cfg -o vetube.pot .
    ```

3.  **Rozpocznij nowe tłumaczenie:**
    Jeśli zamierzasz tłumaczyć na nowy język (przykład `it` para włoskiego):
    ```bash
    pybabel init -i vetube.pot -d locales -l it -D vetube
    ```

4.  **Aktualizuj istniejące tłumaczenia:**
    Jeśli język już istnieje i zaktualizowałeś plik `.pot`, zsynchronizuj pliki `.po`:
    ```bash
    pybabel update -i vetube.pot -d locales -D vetube
    ```

5.  **Kompiluj tłumaczenia:**
    Aby program rozpoznał zmiany, skompiluj pliki `.po` do `.mo`:
    ```bash
    pybabel compile -d locales -D vetube
    ```

# podziękowania:
Dziękuję:

[4everzyanya](https://www.youtube.com/c/4everzyanya/),

Główny tester projektu.

[Johan G](https://github.com/JohanAnim),

Który pomógł stworzyć interfejs graficzny projektu i naprawić niektóre drobne błędy.

Wiem, że dzięki wam ta aplikacja będzie się nadal rozwijać, a każdy z waszych pomysłów i współpracy będzie mile widziany w tym projekcie, który budujemy razem.

W sprawie pomysłów, błędów i sugestii możesz do mnie pisać na:
cesar.verastegui17@gmail.com
## Linki do pobrania.
Swoim wsparciem przyczyniasz się do dalszego rozwoju tego programu.

[Dołączysz do naszej sprawy?](https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U)

[pobierz program dla 64 bitów](https://github.com/metalalchemist/VeTube/releases/download/v3.7/VeTube-x64.zip)
[pobierz program dla 32 bitów](https://github.com/metalalchemist/VeTube/releases/download/v3.7/VeTube-x86.zip)
