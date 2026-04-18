# Frontend — React Native / Expo Deep Dive

**Location:** `coffee_shop_customer_service_chatbot/coffee_shop_app/`

---

## Stack

| Layer | Technology |
|---|---|
| Framework | React Native 0.81.5 + Expo 54 |
| Routing | Expo Router 6 (file-based, like Next.js App Router) |
| Styling | NativeWind 2 (Tailwind via `className`) + `StyleSheet.create` for dynamic themed values |
| Theme | `constants/theme.ts` — full light/dark token set, `useTheme()` hook |
| Responsive | `constants/responsive.ts` — `useGridColumns()`, `webPointer`, `webSelectText` |
| State | React Context (CartContext, memoized) + local useState |
| Fonts | Expo Font (Sora: Regular, Medium, SemiBold, Bold, ExtraBold) |
| HTTP | axios 1.7 |
| DB | Firebase Realtime Database (optional) |
| Icons | @expo/vector-icons (Feather, AntDesign, Ionicons, MaterialIcons, FontAwesome5/6) |

---

## File-Based Routing Structure

```
app/
├── index.tsx                  → splash/landing screen
├── _layout.tsx                → root layout: CartProvider + RootSiblingParent + Stack
├── details.tsx                → product detail page (receives params from home)
├── thankyou.tsx               → post-order confirmation
└── (tabs)/
    ├── _layout.tsx            → bottom tab bar (Home, Chat Bot, Cart)
    ├── home.tsx               → menu browse + category filter
    ├── chatRoom.tsx           → chat interface
    └── order.tsx              → cart review + checkout
```

Expo Router maps this directly to URL paths:
- `/` → `index.tsx`
- `/(tabs)/home` → `home.tsx`
- `/(tabs)/chatRoom` → `chatRoom.tsx`
- `/(tabs)/order` → `order.tsx`
- `/details` → `details.tsx`
- `/thankyou` → `thankyou.tsx`

---

## Root Layout (`app/_layout.tsx`)

Wraps the entire app in three providers, in this order:

```tsx
<CartProvider>                    // global cart state
  <RootSiblingParent>             // enables Toast notifications anywhere
    <Stack>                       // Expo Router navigation stack
      <Stack.Screen name="index"   options={{ headerShown: false }} />
      <Stack.Screen name="details" options={{ headerShown: true }} />
      <Stack.Screen name="thankyou" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)"  options={{ headerShown: false }} />
    </Stack>
  </RootSiblingParent>
</CartProvider>
```

Also loads Sora fonts via `useFonts` — returns `undefined` (blank screen) until fonts are ready. `NativeWindStyleSheet.setOutput({ default: "native" })` activates NativeWind for native targets.

On **web**, wraps the navigator in a max-width frame (480px) centered on the viewport, mimicking a phone shell. Imports `polyfills.ts` as the first line to shim `setImmediate` for browser compatibility (`react-native-root-toast` uses it internally).

---

## Tab Layout (`app/(tabs)/_layout.tsx`)

Three tabs, all using `@expo/vector-icons`:

| Tab | Icon | Header | Tab bar visible |
|---|---|---|---|
| Home | `Entypo home` | hidden | yes |
| Chat Bot | `FontAwesome6 robot` | shown (via Stack.Screen) | **hidden** |
| Cart | `Entypo shopping-cart` | shown | **hidden** |

Active tint: `#C67C4E` (brand orange).

Chat and Cart tabs hide the bottom tab bar (`tabBarStyle: { display: 'none' }`), giving a full-screen focused experience.

---

## Screens

### index.tsx — Splash

Static screen with `ImageBackground` (`assets/images/index_bg_image.png`).
Single CTA: "Get Started" → `router.push("/(tabs)/home")`.
No logic, no state.

### home.tsx — Menu Browse

**State:**
- `products: Product[]` — full list from Firebase
- `shownProducts: Product[]` — filtered by selected category
- `productCategories: ProductCategory[]` — `[{ id: string, selected: bool }]`
- `selectedCategory: string` — initially `'All'`

**Two `useEffect` hooks:**
1. On mount: `fetchProducts()` → build category list → set both `products` and `shownProducts`
2. On `selectedCategory` change: filter `products` → update `shownProducts` and category `selected` flags

**Layout:** `FlatList` with dynamic `numColumns` (2 on mobile, 3 at 600px+, 4 at 900px+) via `useGridColumns()`. Uses `key={numColumns}` to force remount on column change (React Native requirement). `ListHeaderComponent` contains:
- `SearchArea` (decorative — no search logic implemented)
- `Banner` (static promo image)
- Horizontal category pill filter

Each product card shows image, name, category, price, and an `+` button.

Navigation to details: `router.push({ pathname: '/details', params: { ...product } })` — all product fields passed as route params.

**Add to cart from home:** calls `addToCart(item.name, 1)` + shows a Toast notification.

### chatRoom.tsx — Chat Interface

**State:**
- `messages: MessageInterface[]` — full conversation history (never trimmed)
- `isTyping: boolean` — controls TypingIndicator visibility

**refs:**
- `textRef` — holds current input value without re-rendering on every keystroke
- `inputRef` — programmatically clears the `TextInput` after sending

**`handleSendMessage` flow:**
1. Trim input; skip if empty
2. Append user message to history
3. Clear input field
4. `setIsTyping(true)`
5. `await callChatBotAPI(allMessages)`
6. `setIsTyping(false)`
7. Append response to messages
8. If `response.memory.order` exists: `emptyCart()` then re-add each item

**Why `emptyCart()` before re-adding:** The LLM returns the **complete current order** every time, not a delta. So the cart must be wiped and rebuilt from the full order on each turn.

**Layout:**
- `PageHeader` at top (title "Chat Bot")
- `MessageList` (scrollable, auto-scrolls to bottom)
- Input bar at bottom with `TextInput` + send button (`Feather send` icon)

### order.tsx — Cart

**State:**
- `products: Product[]` — fetched from Firebase (for prices and images)
- `totalPrice: number` — computed reactively

**Total calculation:**
```typescript
products.reduce((total, product) => {
    const quantity = cartItems[product.name] || 0;
    return total + product.price * quantity;
}, 0);
```

Only products with `quantity > 0` (from cartItems) are shown in the list.

**Checkout:** `orderNow()` empties cart, shows Toast, navigates to `/thankyou`. No actual payment or API call.

**Price display in footer:** `$ {totalPrice + 1}` — the `+1` is a hardcoded delivery fee. Not dynamic.

### details.tsx — Product Detail

Reads all data from route params (no second Firebase call):
```typescript
const { name, image_url, type, description, price, rating } = useLocalSearchParams()
```

Components used: `DetailsHeader`, `DescriptionSection`, `SizesSection` (static, no real size logic).

"Buy Now" = `addToCart(name, 1)` + Toast + `router.back()`.

---

## Components

### MessageList + MessageItem

`MessageList` renders a `ScrollView` with `useEffect` to scroll to bottom whenever `messages` changes.

`MessageItem` branches on `message.role`:
- `'user'` → right-aligned, white bubble, neutral border
- anything else (assistant) → left-aligned, indigo bubble (`bg-indigo-100`)

### TypingIndicator

Animates "Typing..." with cycling dots using `setInterval(500ms)`. Shown inside the same indigo bubble style as assistant messages.

### CartContext

```typescript
type CartItems = { [productName: string]: number }
```

Three methods:
- `addToCart(name, qty)` — accumulates
- `SetQuantityCart(name, delta)` — increments/decrements, min 0
- `emptyCart()` — resets to `{}`

Context throws if used outside `CartProvider`. The `useCart()` hook enforces this.

### Banner

Fully static component — hardcoded "Buy one get one FREE" promo text with `assets/images/banner.png`. No dynamic content.

### SearchArea

Renders a search bar UI. **No search logic implemented.** It's a visual placeholder.

---

## Services

### `services/chatBot.ts`

```typescript
async function callChatBotAPI(messages: MessageInterface[]): Promise<MessageInterface>
```

- Posts to `API_URL` with full message history
- Auth header: `Bearer ${API_KEY}` (can be `'local-dev'` locally)
- Reads `response.data["output"]` as the returned message
- Throws on network or HTTP error (caught in `chatRoom.tsx` with Alert)

### `services/productService.ts`

```typescript
async function fetchProducts(): Promise<Product[]>
```

- Returns `[]` if `fireBaseDB` is null (Firebase not configured)
- Reads `ref(fireBaseDB, 'products')` snapshot
- Iterates `snapshot.val()` object (Firebase stores arrays as objects keyed by push-ID)
- **Module-level cache** — result stored after first fetch; subsequent calls return cache immediately. Concurrent calls share one in-flight promise to prevent duplicate Firebase reads.

---

## Configuration

### `config/runpodConfigs.ts`

```typescript
const API_URL = process.env.EXPO_PUBLIC_RUNPOD_API_URL as string;
const API_KEY = process.env.EXPO_PUBLIC_RUNPOD_API_KEY as string;
```

### `config/firebaseConfig.ts`

Only initializes Firebase if `EXPO_PUBLIC_FIREBASE_DATABASE_URL` is set. Exports `fireBaseDB: Database | null`.

Note: `EXPO_PUBLIC_FIREBASE_PROHECT_Id` — the env var name has a typo ("PROHECT" instead of "PROJECT"). Both the env example and the config use this same typo, so they match. Do not fix one without fixing the other.

---

## TypeScript Types (`types/types.ts`)

```typescript
interface Product {
    id: string;
    category: string;
    description: string;
    image_url: string;
    name: string;
    price: number;
    rating: number;
}

interface ProductCategory {
    id: string;
    selected: boolean;
}

interface MessageInterface {
    role: string;          // "user" | "assistant" — no literal union enforced
    content: string;
    memory?: any;          // untyped — carries agent-specific state
}
```

`memory` is typed as `any`. This is the main typing gap — the structure varies per agent and is only documented in code comments and prompts.

---

## NativeWind Styling

`tailwind.config.js` extends with:
```js
theme: {
    extend: {
        colors: {
            app_orange_color: '#C67C4E'  // primary brand color
        }
    }
}
```

Used throughout as `className='bg-app_orange_color'` or `text-app_orange_color`.

`NativeWindStyleSheet.setOutput({ default: "native" })` in root layout ensures styles compile to React Native StyleSheet objects, not web CSS.

---

## Path Alias

`tsconfig.json`:
```json
"paths": { "@/*": ["./*"] }
```

`@/components/...`, `@/services/...`, `@/types/...`, `@/config/...` all resolve from the app root. Used consistently across all screens and components.
