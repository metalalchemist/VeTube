# VeTube a Discord: průvodce krok za krokem

VeTube umí v reálném čase číst zprávy z textového kanálu na serveru Discord. Oficiální cesta podle pravidel Discordu vyžaduje takzvaného „bota": zvláštní účet, který si sami zdarma vytvoříte, jen jednou, asi za 10 minut. Tento průvodce popisuje celý postup a je psán pro uživatele odečítačů obrazovky (žádné snímky obrazovky, přesné názvy všech tlačítek).

Poznámka: portál pro vývojáře Discordu se zobrazuje v jazyce vašeho účtu Discord, pokud je k dispozici; jinak v angličtině. Názvy tlačítek níže jsou uvedeny anglicky jako reference; pokud je váš portál přeložen, zobrazí se ve vašem jazyce.

## Co budete potřebovat
- Účet na Discordu.
- Oprávnění zvát boty na server, který chcete číst (oprávnění „Spravovat server"). Pokud ho nemáte, můžete na konci kroku 4 poslat zvací odkaz správci, aby ho otevřel za vás.

## Krok 1: vytvoření aplikace
1. Otevřete https://discord.com/developers/applications a přihlaste se.
2. Stiskněte tlačítko „New Application".
3. Zadejte název (například „VeTube"), potvrďte podmínky a stiskněte „Create".

## Krok 2: získání tokenu bota
1. Na stránce vaší aplikace přejděte do sekce „Bot" v levé nabídce.
2. Stiskněte tlačítko „Reset Token" a potvrďte volbou „Yes, do it!".
3. Discord vás poté znovu požádá o heslo (nebo přístupový klíč), aby ověřil, že jste to vy: zadejte ho a potvrďte. Máte-li dvoufázové ověření, může být vyžádán i kód.
4. Zobrazí se nový token s tlačítkem „Copy" pro zkopírování do schránky. Dočasně si ho vložte na bezpečné místo, například do Poznámkového bloku: z bezpečnostních důvodů se token zobrazí jen jednou, při vytvoření.

Důležité: token je jako heslo vašeho bota. Nikomu ho nedávejte a nikde ho nezveřejňujte. Pokud unikne, vraťte se na tuto stránku a stiskněte „Reset Token" pro vygenerování nového; starý přestane fungovat.

## Krok 3: zapnutí „Message Content Intent"
Bez této volby Discord botovi nedovolí číst obsah zpráv.
1. Stále v sekci „Bot" sjeďte dolů na „Privileged Gateway Intents".
2. Zapněte přepínač „Message Content Intent".
3. Stiskněte „Save Changes" na liště, která se objeví.

## Krok 4: pozvání bota na váš server
1. Přejděte do sekce „OAuth2" v levé nabídce a najděte „URL Generator".
2. V seznamu „Scopes" zaškrtněte políčko „bot".
3. V části „Bot Permissions", která se objeví níže, zaškrtněte „View Channels" a „Read Message History".
4. Na konci stránky u „Generated URL" stiskněte „Copy".
5. Otevřete tuto adresu v prohlížeči a v rozbalovacím seznamu „Přidat na server" vyberte svůj server. Tip pro odečítač obrazovky: dokud není vybrán žádný server, spodní tlačítko se jmenuje „Nevyplnili jste některá pole"; po výběru serveru se změní na „Autorizovat". Stiskněte ho. (Pokud nemůžete zvát boty, pošlete tuto adresu správci serveru.)

## Krok 5: zkopírování odkazu na kanál
1. V Discordu najděte textový kanál, který chcete číst.
2. Otevřete jeho místní nabídku: pravé tlačítko myši, nebo klávesa Aplikace či Shift+F10 s odečítačem.
3. Zvolte „Kopírovat odkaz". Odkaz vypadá takto: https://discord.com/channels/1234567890/0987654321

## Krok 6: vložení do VeTube
1. Otevřete VeTube, vložte odkaz na kanál do hlavního textového pole a stiskněte „Přístup" nebo Enter.
2. Napoprvé si VeTube vyžádá token bota: vložte ho a stiskněte „OK". Uloží se a už nebude znovu vyžadován.
3. Hotovo! Zprávy z kanálu začnou přicházet. Zprávy majitele serveru a lidí s právem moderovat se objeví v kategorii „Moderátoři"; ostatní v kategorii „Obecné".

## Řešení potíží
- „Token není platný": zkopírujte celý token z portálu (krok 2). V případě pochybností vygenerujte nový přes „Reset Token".
- Discord chce při generování tokenu moje heslo: to je normální, jde o bezpečnostní kontrolu (krok 2).
- „Bot nemá zapnutou volbu Message Content Intent": projděte znovu krok 3 a uložte změny.
- „Kanál na Discordu nebyl nalezen": zkontrolujte, že je bot pozván právě na tento server (krok 4) a že jste zkopírovali odkaz na správný kanál (krok 5).
- Chat se připojí, ale nechodí žádné zprávy: ověřte, že bot daný kanál vidí. U soukromých kanálů mu musíte dát přístup nebo roli, která ho má.
