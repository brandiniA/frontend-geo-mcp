# Parser Component Validation

This document explains how the parser validates and filters component names during indexing.

## Overview

The parser uses intelligent pattern matching to distinguish between:
- ✅ **React Components** (PascalCase) → Indexed
- ❌ **Constants** (SCREAMING_SNAKE_CASE) → Rejected
- ❌ **Variables/Functions** (camelCase, etc.) → Rejected
- ❌ **Configuration** (suffixes like _DEFAULT, _CONFIG) → Rejected
- ❌ **Factory Functions** (functions returning objects) → Rejected
- ❌ **Instances** (results of function calls) → Rejected

## Validation Rules

The `_is_valid_component_name()` method in `src/utils/parser.py` applies 8 validation criteria in order:

### 1. Must Start with UPPERCASE (PascalCase)
- ✅ `Button`, `UserProfile`, `MyComponent`
- ❌ `button`, `userProfile`, `myComponent`

**Why:** React convention - components always use PascalCase

### 2. Cannot Start with NUMBER
- ❌ `2Button`, `3rdComponent`

**Why:** Invalid JavaScript syntax

### 3. Cannot Start with UNDERSCORE
- ❌ `_private`, `__internal`

**Why:** Convention for private/protected variables

### 4. Cannot be SCREAMING_SNAKE_CASE
- ❌ `API_URL`, `MAX_RETRIES`, `CONFIG_NAME`
- Pattern: Contains `_` AND all uppercase

**Why:** Universal convention for constants

### 5. Cannot Have Environment Variable Prefixes
- ❌ `REACT_APP_KEY`, `VITE_SECRET`, `NODE_ENV`, `npm_CONFIG`

**Why:** These are build tool configuration, not components

### 6. Cannot Match Function/Variable Patterns
Common prefixes indicate functions or variables, not components:
- ❌ `isActive`, `hasError`, `canDelete`
- ❌ `getValue`, `setValue`, `getUser`
- ❌ `makeRequest`, `createUser`, `fetchData`
- ❌ `parseJSON`, `validateEmail`, `formatDate`

Detected patterns: `is*`, `has*`, `can*`, `should*`, `get*`, `set*`, `make*`, `create*`, `add*`, `remove*`, `delete*`, `update*`, `fetch*`, `load*`, `save*`, `parse*`, `format*`, `validate*`, `check*`, `compute*`, `calculate*`

**Why:** These are utility functions or state values, not UI components

### 7. Cannot Have Constant Suffixes
- ❌ `Config_DEFAULT`, `Theme_DARK`, `Theme_LIGHT`
- ❌ `SIZE_MAX`, `API_KEYS`, `PORT_TIMEOUT`

Detected suffixes: `_DEFAULT`, `_CONFIG`, `_SETTINGS`, `_OPTIONS`, `_DARK`, `_LIGHT`, `_THEME`, `_KEYS`, `_TYPES`, `_MAX`, `_MIN`, `_WIDTH`, `_HEIGHT`, `_SIZE`, `_URL`, `_API`, `_HOST`, `_PORT`, `_TIMEOUT`

**Why:** These suffix patterns indicate configuration/constants

### 8. Cannot be Reserved Words
- ❌ `Component`, `React`, `Fragment`, `Suspense`
- ❌ `Error`, `Promise`, `Object`, `Array`

Full list includes JavaScript built-ins and React internals.

**Why:** These are reserved words or core APIs

## Factory Functions & Instances Detection

After passing basic validation, the parser also rejects factory functions and instances using `_is_factory_or_instance()`.

### What Gets Rejected

#### 1. Factory Functions
Pattern: A function that returns an object (not JSX)
```javascript
// ❌ REJECTED - Returns { generateToken, ... }, not JSX
function OpenPay() {
  const generateToken = async (cardData) => { ... };
  return { generateToken };
}
```

#### 2. Instances of Factories
Pattern: Variable assigned result of calling a function
```javascript
// ❌ REJECTED - Result of OpenPay() call
const openPay = OpenPay();

// ❌ REJECTED - Result of DatabaseClient() call
const db = DatabaseClient();
```

#### 3. Utility Functions
Pattern: Plain functions without JSX in body
```javascript
// ❌ REJECTED - Utility function, no JSX
function helperFunction() {
  return someValue;
}

// ❌ REJECTED - Even if exported
export function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

### Detection Strategy

The parser checks:
1. **Has `return { ... }`?** → Factory function
2. **Assigned from `Name()` call?** → Instance of factory  
3. **Function body without JSX?** → Utility function

### Real-World Example

```javascript
// ❌ REJECTED (Factory pattern)
function OpenPay() {
  const generateToken = async (cardData) => {
    // ... implementation
    return new Promise((resolve, reject) => {
      window.OpenPay.token.create(
        cardData,
        (res) => resolve(res.data.id),
        (error) => reject(error)
      );
    });
  };
  return { generateToken };
}

// ❌ REJECTED (Instance)
const openPay = OpenPay();

// ❌ REJECTED (Export of instance)
export default openPay;
```

### ✅ What Still Gets Indexed

```javascript
// ✅ ACCEPTED - Returns JSX (actual React component)
export const PaymentForm = ({ onSubmit }) => (
  <form onSubmit={onSubmit}>
    {/* JSX content */}
  </form>
);
```

## Examples

### ✅ ACCEPTED - Valid Components

```javascript
// Standard components
export const Button = () => <button />;
export const UserProfile = ({ id }) => <div>...</div>;
export const LoginForm = () => <form>...</form>;

// With numbers (after first character)
export const Form2FA = () => <div>...</div>;

// With acronyms
export const APIClient = () => <div>...</div>;
export const HTTPStatus = () => <div>...</div>;
```

### ❌ REJECTED - Not Components

```javascript
// Constants - SCREAMING_SNAKE_CASE
export const API_URL = "https://api.example.com";
export const MAX_RETRIES = 3;
export const DB_HOST = "localhost";
export const THEME_COLORS = {...};

// Variables - camelCase
export const userData = { name: "John" };
export const isEnabled = true;
export const count = 0;

// Functions - common patterns
export const isActive = (user) => user.active;
export const hasError = (error) => !!error;
export const getValue = (obj) => obj.value;
export const fetchData = async () => {...};

// Configuration - special suffixes
export const Theme_DARK = {...};
export const Theme_LIGHT = {...};
export const Color_DEFAULT = "#fff";
export const API_KEYS = ["key1", "key2"];

// Private/protected
export const _private = () => {...};
export const __internal = "value";

// Factory functions & instances
function OpenPay() { return { ... }; }
const openPay = OpenPay();
```

## Directory Structure for Clean Code

Following conventions prevents parser confusion:

```
src/
├── components/           # 📦 COMPONENTS (PascalCase)
│   ├── Button.tsx
│   ├── UserProfile.tsx
│   └── LoginForm.tsx
│
├── constants/            # ⚙️ CONSTANTS (SCREAMING_SNAKE_CASE)
│   ├── api.ts           # API_URL, API_TIMEOUT, etc.
│   ├── themes.ts        # THEME_DARK, THEME_LIGHT, etc.
│   └── config.ts        # Configuration variables
│
├── utils/               # 🔧 UTILITIES (camelCase)
│   ├── helpers.ts       # Helper functions
│   ├── api.ts           # fetchData, makeRequest, etc.
│   └── validators.ts    # isEmail, isValid, etc.
│
└── hooks/               # 🪝 CUSTOM HOOKS (use + PascalCase)
    ├── useUserData.ts
    ├── useAuth.ts
    └── useLocalStorage.ts
```

## How to Check If Something Is a Component

Before exporting from a component file, ask:

1. **Does it return JSX?** → YES = Component ✅
2. **Is it configuration/constants?** → Move to `constants/` 📝
3. **Is it a utility function?** → Move to `utils/` 🔧
4. **Is it a custom hook?** → Use `use` prefix in `hooks/` 🪝
5. **Is it a factory function?** → Move to `utils/` (or use differently) ❌

## Best Practices

### ✅ DO

```javascript
// ✅ Keep only components in component files
export const UserCard = ({ user }) => (
  <div className={`card ${getCardClass(user)}`}>
    {user.name}
  </div>
);

// Put utilities elsewhere
// src/utils/card.ts
export const getCardClass = (user) => user.active ? "active" : "inactive";
```

### ❌ DON'T

```javascript
// ❌ Don't mix everything in component files
export const UserCard = ({ user }) => (...);

// ❌ This will be rejected by parser
export const API_USER_ENDPOINT = "https://api.example.com/users";
export const getUserClass = (user) => (...);
export const isUserActive = (user) => (...);
export const UserCard_DEFAULT = (...);

// ❌ Factory functions
function ProvideUser() { return { getUser() { ... } }; }
const userProvider = ProvideUser();
```

## Performance Impact

The validation is applied during parsing and happens once per sync. It ensures:

- ✅ Clean indexed data (only actual components)
- ✅ Accurate search results
- ✅ No false positives in component discovery
- ✅ Better IDE integration in Cursor

## Modifying Validation Rules

To adjust validation rules, edit the following methods in:
```
src/utils/parser.py
- _is_valid_component_name() (lines 95-187)      # Basic naming rules
- _is_factory_or_instance() (lines 189-220)       # Factory & instance detection
```

Rules are organized as:

1. **_is_valid_component_name():**
   - Basic validation (type checking)
   - Naming pattern checks (lowercase, digits, underscores)
   - Convention checks (SCREAMING_SNAKE_CASE, env vars)
   - Pattern checks (function prefixes like `is*`, `get*`)
   - Suffix checks (configuration suffixes)
   - Reserved word checks

2. **_is_factory_or_instance():**
   - Factory pattern detection (returns object)
   - Instance pattern detection (assigned from function call)
   - Utility function detection (no JSX in body)

---

**Last Updated:** October 2025  
**Version:** 1.1  
**Applies to:** Frontend GPS MCP v1.0+ (with factory function detection)
