# Lire TikTok depuis le navigateur : l'extension du signataire local

Ce guide explique une manière alternative de lire le chat d'un direct TikTok dans VeTube, prévue pour les cas où la méthode habituelle échoue. Il est pensé pour être lu du début à la fin : d'abord à quoi ça sert, puis pourquoi ça existe, comment l'installer et l'utiliser, et enfin les notes de sécurité.

## À quoi ça sert

Pour lire le chat d'un direct, TikTok exige que la requête vers le *websocket* du chat soit **signée**. VeTube demande normalement cette signature à un service externe (EulerStream). Quand ce service tombe en panne — ce qui arrive souvent — VeTube ne peut plus lire le chat d'**aucun** direct TikTok par la voie habituelle.

L'extension résout exactement ce problème : au lieu de dépendre de ce service externe, elle laisse **votre propre navigateur** — qui a déjà le direct ouvert et reçoit déjà le chat via une connexion signée et fonctionnelle — transmettre ces messages à VeTube. L'extension ne calcule aucune nouvelle signature : elle copie simplement les messages que votre navigateur reçoit déjà.

En une phrase : *VeTube lit par-dessus l'épaule de votre navigateur, qui est celui réellement connecté à TikTok.*

## Pourquoi elle a été créée

Il n'existe pas d'API officielle pour lire le chat d'un direct TikTok, donc VeTube (et tout programme similaire) dépend d'un service externe pour calculer la signature exigée par TikTok. Ce service, EulerStream :

- tombe souvent en panne (et tant qu'il est en panne, personne ne peut lire de direct TikTok de cette façon),
- répartit un quota limité entre tous ses utilisateurs,
- est un tiers extérieur à VeTube.

Comme il est impossible d'éviter la signature, l'extension a été créée pour résoudre ce problème sans dépendre de ce tiers : si votre navigateur regarde déjà le direct avec une connexion signée et fonctionnelle, il n'est pas nécessaire de demander une signature à qui que ce soit d'autre. C'est une alternative, pas un remplacement définitif : elle sert quand le service habituel échoue.

## Comment l'installer

L'extension n'est **pas sur le Chrome Web Store** : elle est fournie avec VeTube, dans le dossier `interceptor_extension`. Pour l'installer, une seule fois :

1. Ouvrez Chrome (ou un navigateur basé sur Chromium, comme Edge ou Brave) et allez sur `chrome://extensions`.
2. Activez le **« Mode développeur »** (interrupteur en haut à droite).
3. Cliquez sur **« Charger l'extension non empaquetée »** et choisissez le dossier `interceptor_extension` (fourni avec VeTube).
4. C'est fait : **« VeTube – pont du chat TikTok Live »** apparaît dans la liste des extensions.

## Comment l'utiliser

Sur l'écran d'accueil de VeTube, dans le menu déroulant **« Capturer le chat de : »**, il y a deux options pour TikTok : **« TikTok »** (le service habituel) et **« TikTok (navigateur, expérimental) »** (cette extension). Pour utiliser directement l'extension :

1. Ouvrez le direct dans votre navigateur (avec l'extension déjà installée). Chrome affichera une barre indiquant *« … est en train de déboguer ce navigateur »* : c'est normal, c'est le signe que l'extension lit le chat. Ne la fermez pas.
2. Dans VeTube, saisissez le **même utilisateur** que celui du direct (le `@utilisateur`, tel qu'il apparaît).
3. Choisissez **« TikTok (navigateur, expérimental) »** dans « Capturer le chat de : » et cliquez sur **Accéder**.

Vous pouvez aussi laisser VeTube vous le proposer automatiquement : si vous choisissez « TikTok » normal et que la connexion habituelle échoue, VeTube vous demande si vous voulez passer à la lecture depuis le navigateur (le direct étant déjà ouvert). Si vous acceptez, la lecture continue sans rien redémarrer.

Prérequis : l'extension doit être chargée **avant** d'ouvrir le direct (si l'onglet était déjà ouvert, rechargez-le), et les outils de développement (F12) ne doivent pas être ouverts sur cet onglet, car ils utilisent le même canal que l'extension.

## Notes de sécurité

- **L'extension ne fait que lire ce que votre navigateur reçoit déjà.** Elle ne contourne aucune protection de TikTok : la signature reste calculée par TikTok, sur votre propre session, comme d'habitude.
- **Elle n'envoie jamais votre cookie de session** (`sessionid`) ni aucun identifiant de votre compte. Le chat d'un direct public fonctionne de la même façon sans être connecté.
- **Tout reste sur votre ordinateur.** L'extension ne communique qu'avec `127.0.0.1:8790` (VeTube, sur votre propre machine) ; rien n'est envoyé à un serveur externe ni à un tiers.
- **Elle ne modifie pas la page TikTok** et n'interfère pas avec sa sécurité : elle observe uniquement le trafic du chat, de la même façon que le feraient les outils de développement du navigateur.

Plus de détails techniques (comment l'extension est construite, le protocole utilisé pour communiquer avec VeTube, et le dépannage) se trouvent dans `FIRMADOR_LOCAL.md` et `interceptor_extension/LEEME.md`, dans le code source de VeTube.
