# VeTube et Discord : guide pas à pas

VeTube peut lire en temps réel les messages d'un canal texte d'un serveur Discord. Pour le faire par la voie officielle, Discord impose de passer par un « bot » : un compte spécial que vous créez vous-même gratuitement, une seule fois, en une dizaine de minutes. Ce guide explique toute la procédure et il est pensé pour les utilisateurs de lecteurs d'écran (pas de captures d'écran, les noms exacts de chaque bouton).

Remarque : le portail des développeurs Discord n'existe qu'en anglais, c'est pourquoi les noms de ses boutons sont donnés ici en anglais. L'application de chat Discord, elle, est bien traduite en français.

## Ce qu'il vous faut
- Un compte Discord.
- Le droit d'inviter des bots sur le serveur que vous voulez lire (permission « Gérer le serveur »). Si vous ne l'avez pas, à la fin de l'étape 4 vous pourrez envoyer le lien d'invitation à un administrateur pour qu'il l'ouvre à votre place.

## Étape 1 : créer l'application
1. Ouvrez https://discord.com/developers/applications et connectez-vous.
2. Activez le bouton « New Application ».
3. Saisissez un nom (par exemple « VeTube »), acceptez les conditions puis activez « Create ».

## Étape 2 : récupérer le token du bot
1. Sur la page de votre application, allez dans la section « Bot » du menu de gauche.
2. Activez le bouton « Reset Token » et confirmez avec « Yes, do it! ». Si vous avez la vérification en deux étapes, le code vous sera demandé.
3. Le nouveau token apparaît avec un bouton « Copy » pour le copier dans le presse-papiers. Collez-le temporairement dans un endroit sûr, par exemple le Bloc-notes.

Important : le token est comme le mot de passe de votre bot. Ne le partagez pas et ne le publiez nulle part. S'il fuite, revenez sur cette page et activez « Reset Token » pour en générer un autre ; l'ancien cesse de fonctionner.

## Étape 3 : activer « Message Content Intent »
Sans cette option, Discord n'autorise pas le bot à lire le contenu des messages.
1. Toujours dans la section « Bot », descendez jusqu'à « Privileged Gateway Intents ».
2. Activez l'interrupteur « Message Content Intent ».
3. Activez « Save Changes » dans la barre qui apparaît.

## Étape 4 : inviter le bot sur votre serveur
1. Allez dans la section « OAuth2 » du menu de gauche et repérez « URL Generator ».
2. Dans la liste « Scopes », cochez la case « bot ».
3. Dans « Bot Permissions », qui apparaît en dessous, cochez « View Channels » et « Read Message History ».
4. Tout en bas de la page, dans « Generated URL », activez « Copy ».
5. Ouvrez cette URL dans votre navigateur, choisissez le serveur dans la liste déroulante puis activez « Continuer » et « Autoriser ». (Si vous n'avez pas le droit d'inviter des bots, envoyez cette URL à un administrateur du serveur.)

## Étape 5 : copier le lien du canal
1. Dans Discord, repérez le canal texte que vous voulez lire.
2. Ouvrez son menu contextuel : clic droit, ou touche Applications ou Maj+F10 avec le lecteur d'écran.
3. Choisissez « Copier le lien ». Le lien a cette forme : https://discord.com/channels/1234567890/0987654321

## Étape 6 : coller dans VeTube
1. Ouvrez VeTube, collez le lien du canal dans la zone de texte principale et activez « Accéder » ou appuyez sur Entrée.
2. La première fois, VeTube vous demandera le token du bot : collez-le puis activez « Accepter ». Il sera enregistré et ne vous sera plus demandé.
3. C'est prêt ! Les messages du canal commencent à arriver. Les messages du propriétaire du serveur et des personnes pouvant modérer apparaissent dans la catégorie « Modérateurs » ; les autres dans « Général ».

## Dépannage
- « Le token n'est pas valide » : copiez le token en entier depuis le portail (étape 2). Dans le doute, générez-en un nouveau avec « Reset Token ».
- « Il manque au bot l'option Message Content Intent » : reprenez l'étape 3 et enregistrez les modifications.
- « Le canal Discord est introuvable » : vérifiez que le bot est invité sur ce serveur précis (étape 4) et que vous avez copié le lien du bon canal (étape 5).
- Le chat se connecte mais aucun message n'arrive : assurez-vous que le bot peut voir ce canal. Pour un canal privé, il faut lui en donner l'accès ou un rôle qui l'a.
