## Smart Plug NFC Demo (Simple App)

This is a **very small, easy-to-run demo app** for your project  
“Smart Home Energy Management System with Security Alert using NFC-Based Device Identification”.

It focuses only on:

- **A simple backend API** to manage:
  - homes (houses)
  - smart plugs
  - electrical devices
  - NFC tags linked to devices
- **A minimal web frontend** to:
  - create a home
  - add smart plugs and devices
  - link an NFC tag UID to a device
  - simulate “tapping” a tag on a plug to identify which device is connected

This matches the core idea in the project document but keeps the implementation **small and easy to understand**.

---

### 1. Backend service (Node + Express + SQLite)

Location: `backend/`

Tech stack:

- Node.js (ES modules)
- Express
- better-sqlite3 (single-file SQLite database)
- CORS

#### Install & run

From the project root:

```bash
cd backend
npm install
npm run start   # or: npm run dev
```

The backend will listen on `http://localhost:4000` and create `data.db` in the `backend` folder.

#### Main endpoints (all JSON)

- `GET /health`  
  Simple health check.

- `GET /api/houses`  
  List all homes.

- `POST /api/houses`  
  Create a home.

  Body:

  ```json
  { "house_name": "My Home" }
  ```

- `GET /api/houses/:houseId/plugs`  
  List smart plugs in a home.

- `POST /api/houses/:houseId/plugs`  
  Add a smart plug.

  Body:

  ```json
  { "plug_name": "Iron plug" }
  ```

- `POST /api/plugs/:plugId/toggle`  
  Toggle plug status (`on`/`off`). This is **simulated** (no MQTT/hardware).

- `GET /api/houses/:houseId/devices`  
  List devices in a home.

- `POST /api/houses/:houseId/devices`  
  Add an electrical device.

  Example body:

  ```json
  {
    "device_name": "Steam iron",
    "device_type": "iron",
    "rated_power_w": 2000,
    "risk_level": "high",
    "auto_off_minutes": 30
  }
  ```

- `POST /api/devices/:deviceId/nfc-tags`  
  Link an NFC tag UID to a device.

  Body:

  ```json
  { "uid": "04A1B2C3D4" }
  ```

- `GET /api/nfc-tags/:uid`  
  Look up which device is associated with a tag UID.

- `POST /api/mock/nfc-detected`  
  **Simple “NFC tap” simulation** for the frontend.

  Body:

  ```json
  {
    "plugId": "<smart_plug_id>",
    "uid": "04A1B2C3D4"
  }
  ```

  Response:

  ```json
  {
    "plug": { ... },
    "device": { ... }
  }
  ```

This is enough to demonstrate the **device identification with NFC + basic control context** without implementing the full microservice or MQTT architecture yet.

---

### 2. Frontend app (HTML + vanilla JS)

Location: `frontend/`

Tech stack:

- Plain `index.html`
- `app.js` with `fetch()` calls to the backend
- No build tools required

You can open `frontend/index.html` directly in a browser, or serve it with any static file server.

#### Usage flow

1. **Start the backend** on `http://localhost:4000`.
2. Open `frontend/index.html` in a browser.
3. In the “Backend URL” field, keep `http://localhost:4000` and click **Check**.
4. **Create a home**:
   - Enter a home name.
   - Click **Create home**.
5. **Add a smart plug**:
   - Select your home.
   - Enter a plug name (e.g. “Iron plug”).
   - Click **Add plug**.
6. **Register a device**:
   - Fill device name, type, power, risk level, and auto-off time.
   - Click **Save device**.
7. **Link an NFC tag**:
   - Choose a device in “Link NFC tag → device”.
   - Enter a fake NFC UID (e.g. `04A1B2C3D4`).
   - Click **Link tag**.
8. **Simulate a tap**:
   - Choose a plug.
   - Enter the same UID.
   - Click **Simulate tap** to see which device is identified.

All API calls and events are logged in the small “Activity” panel on the right.

---

### 3. How this matches your project document

- Uses a **backend service** with a relational-style schema:
  - `houses`, `smart_plugs`, `electrical_devices`, `nfc_tags`
- Supports **NFC-based device identification**:
  - Tag UID → Device profile (risk, auto-off minutes, etc.)
- Demonstrates **core user flows** from the document in a simplified way:
  - manage home, plugs, devices
  - register NFC tags
  - simulate plugging in / tapping a device

Next steps if you want to go further:

- Add **Authentication + multi-user / multi-household** the way the document describes.
- Split the backend into real **microservices** and introduce **MQTT** for communicating with your ESP32-based hardware.
- Replace the simple web frontend with a full **mobile app** (e.g. React Native or Flutter) using the same REST API.

