# Instructions Hackathon:

Pour run, après uv sync, fais uv run vibe

# Changelog des modifications

## Résumé

Ajout d'un **mode apprentissage** (`/learn`) qui, lorsqu'il est activé, génère automatiquement une question pédagogique liée aux modifications effectuées par l'agent et l'écrit dans un fichier `questions.md`.

---

## Fichiers modifiés

### `vibe/core/agent_loop.py` — Classe `AgentLoop`

**Rôle de la classe :** `AgentLoop` est le cœur du système. Elle orchestre la boucle de conversation : elle envoie les messages au modèle LLM, reçoit les réponses en streaming, gère les appels d'outils, et émet des événements (`AssistantEvent`, `ToolCallEvent`, etc.) que l'interface graphique consomme pour afficher les messages.

**Modifications :**

- **`__init__`** : Ajout de l'attribut `self.learn_mode = False`. Ce booléen détermine si le mode apprentissage est actif pour la session en cours.
- **`act(msg)`** : Méthode principale appelée à chaque message utilisateur. Après la fin de la boucle de conversation (`_conversation_loop`), un appel conditionnel à `_write_question_to_file()` a été ajouté — il ne s'exécute que si `self.learn_mode` est `True`.
- **`_write_question_to_file()`** *(nouvelle méthode)* : Après chaque tour de conversation, si le mode apprentissage est activé, cette méthode :

  1. Reconstruit un résumé textuel des derniers messages de la conversation (jusqu'à 10 messages).
  2. Effectue un appel LLM séparé et indépendant (sans modifier l'historique `self.messages`) pour demander au modèle de générer une question pédagogique et sa réponse, en lien avec les modifications effectuées.
  3. Écrit le résultat dans `questions.md` dans le répertoire courant, en ajoutant à la suite du fichier s'il existe déjà.
  4. Le format attendu est : `<Question> ... <Answer> ...`
  5. Les erreurs sont silencieusement ignorées pour ne pas interrompre le flux principal.

---

### `vibe/cli/commands.py` — Classe `CommandRegistry`

**Rôle de la classe :** `CommandRegistry` maintient le registre de toutes les commandes slash (`/help`, `/clear`, `/compact`, etc.). Elle associe chaque alias (ex. `/learn`) à un nom de commande et à la méthode handler correspondante dans `VibeApp`.

**Modification :**

- Ajout de la commande `"learn"` dans le dictionnaire `self.commands` :
  - Alias : `/learn`
  - Description : `"Toggle learn mode (writes Q&A to questions.md after each turn)"`
  - Handler : `"_toggle_learn_mode"` (méthode dans `VibeApp`)

---

### `vibe/cli/textual_ui/app.py` — Classe `VibeApp`

**Rôle de la classe :** `VibeApp` est l'application Textual principale (interface terminal). Elle gère les entrées utilisateur, dispatche les commandes slash, les skills, et les messages vers l'`AgentLoop`. Elle contient tous les handlers des commandes built-in.

**Modification :**

- **`_toggle_learn_mode()`** *(nouvelle méthode)* : Handler appelé lorsque l'utilisateur tape `/learn`. Il bascule le booléen `self.agent_loop.learn_mode` (on → off → on…) et affiche un message de confirmation dans le chat indiquant l'état courant du mode.

---

## Comportement final

| Action utilisateur                    | Résultat                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------ |
| `/learn` (mode désactivé)         | Active le mode, affiche "Learn mode**enabled**…"                        |
| `/learn` (mode activé)             | Désactive le mode, affiche "Learn mode**disabled**"                     |
| Message quelconque (mode activé)     | L'agent répond normalement**ET** génère une Q&A dans `questions.md` |
| Message quelconque (mode désactivé) | L'agent répond normalement, rien n'est écrit                                 |
