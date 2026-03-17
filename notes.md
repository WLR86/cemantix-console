# Fonctionnement

Le projet est une interface cli pour le jeu en ligne Cémantix.

Il est question de proposer des mots pour deviner le mot du jour, le serveur répond alors avec un score permettant de connaître la proximité entre le mot à trouver et le mot secret.

pour cela la variable word contient le mot à proposer, et le tout est POSTé à l'adresse :

<https://cemantix.certitudes.org/score?n=1475>

(ici n=1475 correspondant à la partie du jour, chaque jour il y a un nouveau mot à deviner)

le serveur répond alors avec un JSON contenant, par exemple :

{"p":982,"s":0.4546,"v":31017}

où :

- p (percentile, présent si le mot proposé est dans le top 1000, absent sinon) est la position dans le top 1000 étant le mot à deviner
- s est le score qui exprime une température : par exemple s=0.4546 vaut par exemple 45,46°C, s vaut 1 pour le mot à deviner, soit 100°C
- v est le nombre de joueur ayant à cet instant trouvé la solution

Voici un extrait de l'aide présentée sur le site, expliquant le principe du jeu :

Le but du jeu est de trouver le mot secret en essayant de s’en approcher le plus possible contextuellement. Chaque mot se voit attribuer une température dont des valeurs intéressantes sont données en légende à gauche. Si votre mot se trouve dans les 1000 mots les plus proches, un indice de progression gradué de 1 à 1000 ‰ apparaîtra.

La proximité d’un mot n’est pas orthographique (comme cet autre jeu) mais sémantique ou contextuelle. Elle est évaluée non pas à l’aide d’un dictionnaire, mais d’une base de données de textes de plus d’un milliard de mots à partir de laquelle on a calculé une “distance” relative entre chaque mot. Deux mots proches dans un tel champ lexical ne sont pas nécessairement synonymes. Par exemple, il se peut qu’un adjectif et son contraire soient considérés comme proches car ils peuvent qualifier la même chose.

La langue française ayant beaucoup de redondances orthographiques du fait des verbes conjugués et des variantes féminines ou plurielles des mots, celles-ci ont été eliminées : vous cherchez donc un nom singulier ou un adjectif masculin singulier. Les accents comptent, mais les majuscules sont ignorées et les noms propres ne sont généralement pas admis.

Il vous faudra plus de 6 essais ; sans doute des dizaines. Le classement qui vous est donné en fin de partie est votre place dans la liste des joueurs qui ont trouvé le mot du jour, il est indépendant du nombre d’essais.

Ma version CLI du jeu, codée en python donne pour jouer un environnement texte interactif listant les mots jusque là testés (limité en nombre de lignes par la taille de la fenêtre disponible), en indiquant les informations sous une forme tabulaire :

|                    vente   8.24°C  🥶    0  Solvers:              30800 | Time 163.4ms

|   31                coût  45.46°C  🥵  982 ◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼     1/57 |
|   32            financer   38.9°C  🥵  918 ◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼      2/57 |
|   34             dépense  35.28°C  😎  837 ◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼        3/57 |
|   30              budget  31.81°C  😎  702 ◼◼◼◼◼◼◼◼◼◼◼◼◼◼          4/57 |
|   44             évaluer  25.68°C  😎  269 ◼◼◼◼◼                   5/57 |
|   51             estimer  24.04°C  😎   78 ◼                       6/57 |
|   13               santé  23.31°C  🥶    0                         7/57 |
|   54       amortissement  21.57°C  🥶    0                         8/57 |
|   43          évaluation  21.45°C  🥶    0                         9/57 |
|   55             amortir  21.17°C  🥶    0                        10/57 |
|   52        prévisionnel  20.98°C  🥶    0                        11/57 |
|   14           politique  20.19°C  🥶    0                        12/57 |
|   50          estimation  20.09°C  🥶    0                        13/57 |
|   16             médical  19.97°C  🥶    0                        14/57 |
|   29           ministère  19.44°C  🥶    0                        15/57 |
|   21             hôpital  19.36°C  🥶    0                        16/57 |
|   18                soin  18.58°C  🥶    0                        17/57 |
Cémantix>

le prompt, situé en bas, permet de saisir les mots à tester, mais aussi des commandes (qui doivent alors être précédées d'un "/". ces commandes peuvent être par exemple /help, /cls, /nearby (liste des mots du top 1000, accessible lorsque le mot a été trouvé)

j'utilise le module python cmd pour créer l'environnement CLI

Lorsque le mot n'existe pas, le json retourné est de cette forme :

```JSON
{"e":"Je ne connais pas le mot <i>xxxxxxxx</i>."}
```
