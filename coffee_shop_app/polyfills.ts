// setImmediate is used by react-native-root-toast but doesn't exist in browsers.
if (typeof setImmediate === 'undefined') {
  (global as any).setImmediate = (fn: (...args: unknown[]) => void, ...args: unknown[]) =>
    setTimeout(fn, 0, ...args);
}
