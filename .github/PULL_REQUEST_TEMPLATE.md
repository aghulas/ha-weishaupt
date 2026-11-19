## What and why

## How it was tested

- [ ] `scripts/test.sh` passes (and `npm test` / `npm run build` in `frontend/` if the panel changed; the built file is committed)
- [ ] `scripts/vendor_metadata.py --check` passes (translations and icons are generated, never edited by hand)
- [ ] Nothing site-specific: no address, host name, person or building name, serial number

## Writes

- [ ] This change does not add a write path, or it goes through the writer and its guard (`writer.py`)
