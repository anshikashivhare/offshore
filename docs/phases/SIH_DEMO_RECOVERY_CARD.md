# SIH DEMO RECOVERY CARD
**Project:** SIH 26059

*Keep this printed beside the operator.*

## Symptoms & Recovery

**1. "Map is blank / Not loading"**
- **Action:** Check Mapbox/Deck.gl API key in `.env`.
- **Action:** Hard refresh the browser (`Cmd+Shift+R`).

**2. "Route calculation spins endlessly"**
- **Symptom:** Backend may have crashed.
- **Action:** Open terminal where `start_demo.sh` is running. Press `Ctrl+C`. Run `./scripts/start_demo.sh` again.

**3. "Server returned 500 Error"**
- **Action:** Verify Python preflight passed. Ensure `seaice_xgb_v002.json` and `iceberg_lstm_v002.pt` exist in `ml/models/weights/`.

**4. "Safest route isn't generating"**
- **Action:** THIS IS INTENTIONAL. The DB is offline (`DEMO_MODE=True`). The backend blocks 'Safest' requests to protect against 0-risk hallucinations. Switch objective to 'Fastest' to bypass risk gating.

## Canonical Route Values (For Copy/Paste Backup)
- **Origin:** `-60.0, 50.0`
- **Destination:** `-60.0, 52.0`
- **Vessel:** `Research Icebreaker`
