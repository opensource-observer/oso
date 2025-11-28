// fake-import.js
// THIS IS A TEST TO SEE WHAT DYNAMIC IMPORTS DO ON VERCEL.
export function then(resolve) {
  console.log("then() called");
  resolve("Module loaded successfully");
}
