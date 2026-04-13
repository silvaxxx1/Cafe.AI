# Coffee Shop App — React Native Frontend

Expo-based mobile app for the coffee shop chatbot. Runs in browser, Android, and iOS.

## Setup

```bash
npm install
cp .env_example.txt .env
# Edit .env — set EXPO_PUBLIC_RUNPOD_API_URL to your backend URL
```

Default `.env` points to `http://localhost:8000/chat` (the local Python server).  
Start the backend first — see `python_code/api/README.md`.

## Running

```bash
npm run web      # browser at http://localhost:8081
npm run android  # Android emulator or device via Expo Go
npm run ios      # iOS simulator (macOS only)
npm start        # shows QR code — scan with Expo Go on your phone
```

**Running on a physical phone:** Make sure the phone is on the same Wi-Fi as your computer. Replace `localhost` with your computer's local IP in `.env`:
```
EXPO_PUBLIC_RUNPOD_API_URL='http://192.168.x.x:8000/chat'
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `EXPO_PUBLIC_RUNPOD_API_URL` | Yes | Backend URL — `http://localhost:8000/chat` locally |
| `EXPO_PUBLIC_RUNPOD_API_KEY` | Yes | Any string locally (`local-dev`), RunPod token in production |
| `EXPO_PUBLIC_FIREBASE_*` | No | Firebase Realtime DB credentials — app renders without them (empty menu) |

## Screens

- **Home** — browse menu by category, add to cart (requires Firebase for product data)
- **Chat** — AI chatbot; completing an order auto-fills the cart
- **Order** — review cart, adjust quantities, checkout

## Key Notes

- Firebase is optional for local dev — the app renders with an empty menu without it
- The chat auto-fills the cart when the order agent returns `memory.order`
- Cart state is global via `components/CartContext.tsx`
- All API calls go through `services/chatBot.ts` → `config/runpodConfigs.ts`
