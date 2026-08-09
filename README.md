# 🐷 Papapig — Intelligence System

Le cerveau, la personnalité et les automatismes de Papapig, le compagnon IA de Joy.

**Ce repository contient :**
- `papapig_personality.py` — le cerveau : 2 personas (Chowder 🟣 / Papa Pig 🐷), lexique émotionnel thaï, moteur émotionnel (valence × activation, miroir 70%), tamagotchi, statuts maison/travail
- `INTELLIGENCE.md` — la spec d'intelligence en pseudo-code
- `index.html` — dashboard public temps réel (état du cœur, énergie, émotions 7 jours, automatismes)
- `data/state.json` — données anonymisées générées par `papapig_webpush.py`

**🔐 Confidentialité absolue :**
Toutes les conversations sont **chiffrées (AES-256)**. Personne ne peut les lire —
ni le public, ni le propriétaire du serveur. Ce site ne montre **que des métadonnées**
(émotion du jour, énergie, événements maison/travail) — **jamais le contenu des messages**.

**⚙️ Fonctionnement :**
- Tourne sur LM Studio local (gemma-4-e2b, MLX 4-bit) — aucun appel cloud
- Vision locale pour les photos
- 8 automatismes (crons) : news, journal, bonne nuit, réveil, stickers, émotions
- Sauvegardes chiffrées automatiques à vie (Drive + local)

## Pipeline
```
message → perception (langue, emojis, mots-clés thaï)
       → analyse émotionnelle (GoEmotions 27, valence, activation)
       → choix persona (mots-clés ou persona de la veille)
       → génération (Validation → Perspective → Question → Action)
       → style (2-4 lignes thaï, ครับ, humour sauf tristesse)
       → mémoire (journal + emotions.json + brain_state)
```

## Mise à jour du dashboard
```bash
python3 papapig_webpush.py   # génère state.json + push GitHub
```
(cron : toutes les 30 min, silencieux)

## Section Reminder (rappel générique, bidirectionnel)
- **Stockage** : table Supabase `events` (colonnes : `title`, `date`, `start_time`, `status` [todo/in_progress/done/pending], `priority` [low/normal/high], `is_private`, `created_via` [site/whatsapp], `profile`, `sync_id`).
- **Site → WhatsApp** : actions du site (créer / cocher Terminé) → `POST`/`PATCH` REST Supabase (policy anon limitée aux valeurs valides) → le cron `reminder_events.py` (15 min) relance J-1/H-3 via `hermes send`.
- **WhatsApp → Site** : `events_writer.py` (cron 2 min) scan le log, détecte RDV/rappels (`เตือน`, `rappelle-moi`… + heure), INSERT → le site (poll 60 s) affiche avec badge « Importé de WhatsApp ». Dédup par curseur d'octets ; `REMIND_WORDS` limite les faux positifs (les mots courants comme `กลับบ้าน` ne déclenchent rien).
- **Récap WhatsApp** : bouton du site → RPC `request_wa_summary()` (SECURITY DEFINER) → insert `reminder_commands` → cron `wa_summary_sender.py` (2 min) envoie le résumé du jour à Joy.
- **Environnement attendu (jamais dans index.html)** : `SUPABASE_URL`, clé service_role (server-side) `~/.hermes/profiles/papapig/supabase_svc.key`, `GITHUB_PAT` `~/.hermes/.github_pat`, envoi WhatsApp via `hermes -p penguinpig send`. Aucun secret n'est embarqué côté client (clé anon publique uniquement, RLS restreinte).
