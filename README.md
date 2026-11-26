# Hermes Telegram relay (GitHub Actions, no card)

Free, no VPS, no card. A public GitHub repo runs this workflow every 5 minutes:
it polls Telegram with `getUpdates`, and any text message from the allowed user
is written into the Kaggle notebook's `TASK` line and pushed to Kaggle. The
Kaggle notebook does the real Hermes inference on 2x T4 and sends the final
reply + files to Telegram itself.

## Setup

1. Create a **public** repository from these files (public = unlimited free Actions minutes).
2. Repo → Settings → Secrets and variables → Actions → New repository secret:
   - `TELEGRAM_BOT_TOKEN`
   - `KAGGLE_API_TOKEN`
3. Make sure the workflow has `contents: write` (already in the YAML) so `state.json`
   can be committed. This also keeps the 60-day scheduled-workflow auto-disable away.
4. Send any text to @Nayeemclawbot. Within ~5 minutes (sometimes delayed 5–30 min
   by GitHub), the task is submitted to Kaggle; the final result comes from the notebook.

## Notes

- `state.json` stores the Telegram `update_id` offset. On the first run all old
  updates are skipped, so nothing is replayed.
- Only user `6729267449` can trigger runs.
- Kaggle still has its 12h session and ~30 GPU-hours/week limits.
- GitHub may delay or drop scheduled runs under load; this is not real-time.

Trigger workflow discovery.
