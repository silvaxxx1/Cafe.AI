# Coffee Shop App — React Native Frontend

Expo-based app for the Fero Cafe chatbot. Runs in browser, Android, and iOS.

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

**Physical phone:** Make sure the phone is on the same Wi-Fi. Replace `localhost` with your computer's local IP in `.env`:
```
EXPO_PUBLIC_RUNPOD_API_URL='http://192.168.x.x:8000/chat'
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `EXPO_PUBLIC_RUNPOD_API_URL` | Yes | Backend URL — `http://localhost:8000/chat` locally |
| `EXPO_PUBLIC_FIREBASE_*` | No | Firebase Realtime DB credentials — app renders without them (empty menu) |

## Screens

- **Splash** (`index.tsx`) — landing screen, entry point
- **Home** (`(tabs)/home.tsx`) — browse menu by category, add to cart
- **Chat** (`(tabs)/chatRoom.tsx`) — AI barista; completing an order auto-fills the cart
- **Order** (`(tabs)/order.tsx`) — review cart, adjust quantities, checkout
- **Details** (`details.tsx`) — product detail view
- **Thank You** (`thankyou.tsx`) — order confirmation

## Design System

- **Theme** — `constants/theme.ts` — full light/dark token set (follows system preference)
- **Accent** — terracotta `#C67C4E`, warm cream/dark-roast surfaces
- **Typography** — Sora (Regular, Medium, SemiBold, Bold, ExtraBold)
- **Responsive** — 2/3/4-column grid adapts to screen width; web runs in a max-width frame

## Key Notes

- Firebase is optional — chat and ordering work without it (empty menu on Home tab)
- Chat auto-fills the cart when the order agent returns `memory.order`
- Cart state is global via `components/CartContext.tsx`
- `polyfills.ts` shims `setImmediate` for web compatibility
- All API calls go through `services/chatBot.ts`
