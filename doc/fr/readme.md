# VeTube
Lisez et gérez de manière accessible le chat de vos propres directs ou de ceux de vos créateurs favoris.
## Sites pris en charge
- YouTube (premières, directs en cours et passés)
- Twitch.tv (directs en cours et passés)
- TikTok (directs en cours)
- Kick (directs en cours)
- Le Salon (le chat des différentes tables)
## Caractéristiques
- Mode automatique : lit les messages du chat en temps réel à l'aide de la voix SAPI5.
- Interface invisible : gérez les chats depuis n'importe quelle fenêtre à l'aide de simples raccourcis clavier. Un lecteur d'écran actif est nécessaire.
- Lecteurs d'écran pris en charge :
  - NVDA
  - JAWS
  - Window-Eyes
  - SuperNova
  - System Access
  - PC Talker
  - ZDSR
- Possibilité de configurer le programme selon les besoins de l'utilisateur :
  - activer ou désactiver les sons du programme.
  - activer ou désactiver la lecture automatique.
  - configurer la liste des messages dans l'interface invisible.
  - configurer les préférences de la voix SAPI.
  - personnaliser les raccourcis clavier globaux.
- conserver plusieurs captures de chats à la fois.
- changer facilement de mode de lecture des chats : choisissez de lire tous les chats, ou seulement ceux d'une catégorie précise.
- enregistrez vos directs dans une section favoris : rejouez le chat autant de fois que vous le souhaitez, sans avoir à rechercher le lien à nouveau.
- archiver un message : utile pour garder des rappels.
- traduisez le chat d'un direct dans la langue de votre choix.

## Raccourcis clavier
### Avec l'interface invisible
| Action | Combinaison de touches |
| --- | --- |
| Mettre en sourdine la voix SAPI | Ctrl+P |
| Démarrer / annuler la capture d'un autre direct | Alt+Maj+H |
| Aller au direct précédent | Ctrl+Alt+Maj+Flèche gauche |
| Aller au direct suivant | Ctrl+Alt+Maj+Flèche droite |
| Tampon précédent | Alt+Maj+Flèche gauche |
| Tampon suivant | Alt+Maj+Flèche droite |
| Élément précédent | Alt+Maj+Flèche haut |
| Élément suivant | Alt+Maj+Flèche bas |
| Premier élément | Alt+Maj+Début |
| Dernier élément | Alt+Maj+Fin |
| Archiver un message | Alt+Maj+A |
| Copier le message actuel | Alt+Maj+C |
| Effacer un tampon créé précédemment | Alt+Maj+D |
| Ajouter le message au tampon des favoris | Alt+Maj+F |
| Activer ou désactiver la lecture automatique | Alt+Maj+R |
| Désactiver les sons du programme | Alt+Maj+P |
| Rechercher un mot parmi les messages | Alt+Maj+B |
| Afficher le message actuel dans une zone de texte | Alt+Maj+V |
| Ouvrir l'éditeur de combinaisons de clavier de VeTube | Alt+Maj+K |
| Mettre en pause ou reprendre la lecture d'un direct | Ctrl+Maj+P |
| Avancer la lecture du direct | Ctrl+Maj+Flèche droite |
| Reculer la lecture du direct | Ctrl+Maj+Flèche gauche |
| Augmenter le volume | Ctrl+Maj+Flèche haut |
| Baisser le volume | Ctrl+Maj+Flèche bas |
| Arrêter et libérer le lecteur | Ctrl+Maj+S |

### Dans l'historique du chat
| Action | Combinaison de touches |
| --- | --- |
| Lire le message sélectionné | Espace |

### Dans la section des favoris
| Action | Combinaison de touches |
| --- | --- |
| Accéder au lien sélectionné | Espace |

## Futures mises à jour
Voici ce que j'ai prévu pour les prochaines mises à jour :
- Possibilité d'afficher, depuis l'interface invisible, les informations de la personne qui écrit dans le chat :
  - le nom de la chaîne de l'utilisateur ;
  - et bien d'autres choses encore.

## Contribuer à la traduction
Si vous souhaitez aider à traduire VeTube dans votre langue, vous devrez installer les outils d'internationalisation.

1.  **Installer Babel :**
    ```bash
    pip install Babel
    ```
    *Remarque : veillez à bien installer le paquet `Babel` (et non un paquet incorrect de taille minuscule).*

2.  **Extraire les textes pour mettre à jour le modèle (.pot) :**
    Si de nouvelles chaînes ont été ajoutées au code, mettez à jour le fichier modèle :
    ```bash
    pybabel extract -F babel.cfg -o vetube.pot .
    ```

3.  **Démarrer une nouvelle traduction :**
    Si vous traduisez vers une nouvelle langue (par exemple `it` pour l'italien) :
    ```bash
    pybabel init -i vetube.pot -d locales -l it -D vetube
    ```

4.  **Mettre à jour les traductions existantes :**
    Si la langue existe déjà et que vous avez mis à jour le `.pot`, synchronisez les fichiers `.po` :
    ```bash
    pybabel update -i vetube.pot -d locales -D vetube
    ```

5.  **Compiler les traductions :**
    Pour que le programme prenne en compte les changements, compilez les fichiers `.po` en `.mo` :
    ```bash
    pybabel compile -d locales -D vetube
    ```

# Remerciements
Je remercie :

[4everzyanya](https://www.youtube.com/c/4everzyanya/),

testeur principal du projet.

[Johan G](https://github.com/JohanAnim),

qui a aidé à créer l'interface graphique du projet et à corriger certains bugs mineurs.

Je sais que, grâce à vous, cette application continuera de s'améliorer, et que chacune de vos idées et collaborations sera la bienvenue dans ce projet que nous construirons tous ensemble.

Pour vos idées, bugs et suggestions, vous pouvez m'écrire à
cesar.verastegui17@gmail.com
## Liens de téléchargement
Avec votre soutien, vous contribuez à la croissance de ce programme.

[Vous joignez-vous à notre cause ?](https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U)

[télécharger le programme pour 64 bits](https://github.com/metalalchemist/VeTube/releases/latest/download/VeTube-x64.zip)
[télécharger le programme pour 32 bits](https://github.com/metalalchemist/VeTube/releases/download/v3.7/VeTube-x86.zip)
