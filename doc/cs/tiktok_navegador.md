# Čtení chatu TikTok z prohlížeče: rozšíření pro lokální podepisování

Tento návod popisuje alternativní způsob čtení chatu živého vysílání TikTok ve VeTube, určený pro případ, že obvyklý způsob selže. Je vhodné číst ho od začátku do konce: nejprve k čemu slouží, pak proč vzniklo, jak ho nainstalovat a používat, a nakonec poznámky k bezpečnosti.

## K čemu slouží

Aby bylo možné číst chat vysílání, TikTok vyžaduje, aby požadavek na *websocket* chatu byl **podepsaný**. VeTube o tento podpis obvykle žádá externí službu (EulerStream). Když tato služba vypadne — což se děje často — VeTube nemůže obvyklým způsobem číst chat **žádného** vysílání TikTok.

Rozšíření řeší přesně tento problém: místo spoléhání na externí službu nechá **váš vlastní prohlížeč** — který má vysílání již otevřené a chat už přijímá přes podepsané, funkční spojení — předávat tyto zprávy do VeTube. Rozšíření žádný nový podpis nepočítá: pouze kopíruje zprávy, které váš prohlížeč už přijímá.

Jednou větou: *VeTube čte chat přes rameno vašeho prohlížeče, protože ten je skutečně připojen k TikToku.*

## Proč vzniklo

Neexistuje žádné oficiální API pro čtení chatu vysílání TikTok, takže VeTube (a jakýkoli podobný program) je závislý na externí službě, která vypočítá podpis vyžadovaný TikTokem. Tato služba, EulerStream:

- často vypadává (a dokud nefunguje, nikdo takto nemůže číst žádné vysílání TikTok),
- rozděluje omezenou kvótu mezi všechny své uživatele,
- je třetí strana nesouvisející s VeTube.

Protože se podpisu nelze vyhnout, rozšíření vzniklo, aby tento problém vyřešilo bez závislosti na této třetí straně: pokud váš prohlížeč už sleduje vysílání přes podepsané a funkční spojení, není třeba žádat o podpis nikoho jiného. Jde o alternativu, ne o trvalou náhradu — používá se, když obvyklá služba selže.

## Jak ho nainstalovat

Rozšíření **není v Chrome Web Store**: je součástí VeTube, ve složce `interceptor_extension`. Nainstalujte ho jednorázově:

1. Otevřete Chrome (nebo prohlížeč založený na Chromiu, například Edge nebo Brave) a přejděte na `chrome://extensions`.
2. Zapněte **„Režim pro vývojáře"** (přepínač vpravo nahoře).
3. Klikněte na **„Načíst rozbalené"** a vyberte složku `interceptor_extension` (je součástí VeTube).
4. Hotovo: v seznamu rozšíření se objeví **„VeTube – most chatu TikTok Live"**.

## Jak ho používat

Na domovské obrazovce VeTube, v rozbalovacím seznamu **„Zachytávat chat z:"**, jsou pro TikTok dvě možnosti: **„TikTok"** (obvyklá služba) a **„TikTok (prohlížeč, experimentální)"** (toto rozšíření). Pro přímé použití rozšíření:

1. Otevřete vysílání ve svém prohlížeči (s již nainstalovaným rozšířením). Chrome zobrazí lištu s textem *„… ladí tento prohlížeč"*: to je normální a znamená to, že rozšíření čte chat. Nezavírejte ji.
2. Ve VeTube napište **stejného uživatele** jako u vysílání (`@uživatel`, přesně tak, jak je uveden).
3. Vyberte **„TikTok (prohlížeč, experimentální)"** v „Zachytávat chat z:" a klikněte na **Připojit**.

Můžete také nechat VeTube, aby to nabídl automaticky: pokud zvolíte běžný „TikTok" a obvyklé připojení selže, VeTube se zeptá, jestli chcete přejít na čtení z prohlížeče (s vysíláním již otevřeným tam). Pokud souhlasíte, čtení pokračuje bez restartování čehokoli.

Požadavky: rozšíření musí být načteno **před** otevřením vysílání (pokud byla karta již otevřená, načtěte ji znovu) a na dané kartě nesmí být otevřené nástroje pro vývojáře (F12), protože používají stejný kanál jako rozšíření.

## Poznámky k bezpečnosti

- **Rozšíření pouze čte to, co váš prohlížeč už přijímá.** Neobchází žádnou ochranu TikToku: podpis stále počítá samotný TikTok v rámci vaší vlastní relace, jako obvykle.
- **Nikdy neodesílá váš cookie relace** (`sessionid`) ani žádné přihlašovací údaje účtu. Chat veřejného vysílání funguje stejně i bez přihlášení.
- **Vše zůstává ve vašem počítači.** Rozšíření komunikuje pouze s `127.0.0.1:8790` (VeTube, na vašem vlastním počítači); nic se neodesílá na žádný externí server ani třetí straně.
- **Nemění stránku TikToku** ani nezasahuje do její bezpečnosti: pouze sleduje provoz chatu, stejně jako by ho viděly nástroje pro vývojáře v prohlížeči.

Podrobnější technické informace (jak je rozšíření postavené, jaký protokol používá pro komunikaci s VeTube, a diagnostiku problémů) najdete v souborech `FIRMADOR_LOCAL.md` a `interceptor_extension/LEEME.md` ve zdrojovém kódu VeTube.
