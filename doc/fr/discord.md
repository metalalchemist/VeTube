# VeTube et Discord : guide pas à pas

VeTube peut lire en temps réel les messages d'un canal texte d'un serveur Discord. Pour le faire par la voie officielle, Discord impose de passer par un « bot » : un compte spécial que vous créez vous-même gratuitement, une seule fois, en une dizaine de minutes. Ce guide explique toute la procédure et il est pensé pour les utilisateurs de lecteurs d'écran (pas de captures d'écran, les noms exacts de chaque bouton).

Remarque : le portail des développeurs Discord s'affiche dans la langue de votre compte Discord. Les noms de boutons ci-dessous sont ceux de la version française, vérifiés avec NVDA ; si votre portail s'affiche en anglais, l'équivalent anglais est donné entre parenthèses.

## Ce qu'il vous faut
- Un compte Discord.
- Le droit d'inviter des bots sur le serveur que vous voulez lire (permission « Gérer le serveur »). Si vous ne l'avez pas, à la fin de l'étape 4 vous pourrez envoyer le lien d'invitation à un administrateur pour qu'il l'ouvre à votre place.

## Étape 1 : créer l'application
1. Ouvrez https://discord.com/developers/applications et connectez-vous.
2. Activez le bouton « Nouvelle application » (« New Application »).
3. Dans la boîte de dialogue, saisissez un nom (par exemple « VeTube ») dans le champ « Nom », cochez la case d'acceptation des conditions, puis activez « Créer » (« Create »).

## Étape 2 : récupérer le token du bot
1. Sur la page de votre application, allez dans la section « Bot » du menu de navigation.
2. Activez le bouton « Réinitialiser le token » (« Reset Token ») et confirmez avec « Oui, faites-le ! » (« Yes, do it! »).
3. Discord vous redemande alors votre mot de passe (ou votre clé d'accès) pour vérifier que c'est bien vous : saisissez-le et validez. Si vous avez la vérification en deux étapes, le code peut aussi vous être demandé.
4. Le nouveau token s'affiche avec un bouton « Copier » (« Copy ») pour le mettre dans le presse-papiers. Collez-le temporairement dans un endroit sûr, par exemple le Bloc-notes — pour des raisons de sécurité, le token n'est montré qu'une seule fois, à sa création.

Important : le token est comme le mot de passe de votre bot. Ne le partagez pas et ne le publiez nulle part. S'il fuite, revenez sur cette page et activez « Réinitialiser le token » pour en générer un autre ; l'ancien cesse de fonctionner.

## Étape 3 : activer l'« Intention du contenu du message »
Sans cette option, Discord n'autorise pas le bot à lire le contenu des messages.
1. Toujours dans la section « Bot », descendez jusqu'à « Intentions de passerelle privilégiée » (« Privileged Gateway Intents »).
2. Activez l'interrupteur « Intention du contenu du message » (« Message Content Intent »). Astuce NVDA : depuis le haut de la page, la touche X (case à cocher suivante) l'atteint en cinq appuis ; il s'annonce « Requis pour que ton bot reçoive le contenu du message dans la plupart des messages ». Appuyez sur Espace pour l'activer.
3. Une barre apparaît en bas de la page : activez « Enregistrer les modifications » (« Save Changes »).

## Étape 4 : inviter le bot sur votre serveur
1. Allez dans la section « OAuth2 » du menu de navigation et repérez le générateur d'URL (« URL Generator »).
2. Dans la liste « Scopes », cochez la case « bot ».
3. Dans les permissions du bot, qui apparaissent en dessous, cochez « Voir les salons » (« View Channels ») et « Voir les anciens messages » (« Read Message History »).
4. Tout en bas de la page, copiez l'URL générée avec son bouton « Copier » (« Copy »).
5. Ouvrez cette URL dans votre navigateur. Sur la page « Chat Bot veut accéder à ton compte Discord » : choisissez votre serveur dans la liste déroulante « Ajouter au serveur : », puis activez le bouton d'autorisation en bas. À savoir avec un lecteur d'écran : tant qu'aucun serveur n'est choisi, ce bouton s'appelle « Tu n'as pas rempli certains champs » ; il devient « Autoriser » une fois le serveur sélectionné. (Si vous n'avez pas le droit d'inviter des bots, envoyez cette URL à un administrateur du serveur.)

## Étape 5 : copier le lien du canal
1. Dans Discord, repérez le canal texte que vous voulez lire.
2. Ouvrez son menu contextuel : clic droit, ou touche Applications ou Maj+F10 avec le lecteur d'écran.
3. Choisissez « Copier le lien ». Le lien a cette forme : https://discord.com/channels/1234567890/0987654321

## Étape 6 : coller dans VeTube
1. Ouvrez VeTube, collez le lien du canal dans la zone de texte principale et activez « Accéder » ou appuyez sur Entrée.
2. La première fois, VeTube vous demandera le token du bot : collez-le puis activez « OK ». Il sera enregistré et ne vous sera plus demandé.
3. C'est prêt ! VeTube annonce « Chargement » puis « Entrée dans le chat », et les messages du canal commencent à arriver. Les messages du propriétaire du serveur et des personnes pouvant modérer apparaissent dans la catégorie « Modérateurs » si elle est activée dans vos réglages ; sinon, comme tous les autres messages, dans « Général ».

## Dépannage
- « Le token n'est pas valide » : copiez le token en entier depuis le portail (étape 2). Dans le doute, générez-en un nouveau avec « Réinitialiser le token ».
- Discord me redemande mon mot de passe quand je génère le token : c'est normal, c'est une vérification de sécurité (étape 2).
- « Il manque au bot l'option Message Content Intent » : reprenez l'étape 3 et enregistrez les modifications.
- « Le canal Discord est introuvable » : vérifiez que le bot est invité sur ce serveur précis (étape 4) et que vous avez copié le lien du bon canal (étape 5).
- Le chat se connecte mais aucun message n'arrive : assurez-vous que le bot peut voir ce canal. Pour un canal privé, il faut lui en donner l'accès ou un rôle qui l'a.
