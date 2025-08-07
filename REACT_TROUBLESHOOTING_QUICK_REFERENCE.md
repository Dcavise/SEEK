# React Troubleshooting Quick Reference Card

**📅 Last Updated**: August 7, 2025  
**🎯 Purpose**: Quick reference for React infinite loop issues  
**✅ Status**: All known issues resolved - app production ready

## 🔥 EMERGENCY: If App Won't Start

```bash
# 1. Stop everything
Ctrl+C (kill dev server)

# 2. Clear cache
rm -rf seek-property-platform/node_modules/.vite

# 3. Restart
cd seek-property-platform && npm run dev

# 4. Check console for errors
# Should be completely clean on startup
```

## 🚨 If "Maximum Update Depth Exceeded" Returns

### Immediate Diagnosis:
```bash
# Check these patterns that cause infinite loops:
grep -r "|| \[\]" src/                    # New arrays
grep -r "|| {}" src/                      # New objects  
grep -r "useEffect.*\[\]" src/            # Empty dependency arrays
grep -r "set[A-Z].*useEffect" src/       # setState in useEffect
```

### Root Causes to Look For:

1. **New Array Creation**: `data?.items || []` → Use stable `EMPTY_ARRAY`
2. **Unchecked State Updates**: `setState(value)` → Check if `value` changed first
3. **Unstable useEffect**: Dependencies that change every render
4. **Context State Cascades**: Context updates triggering child updates infinitely

## ✅ Prevention Patterns

### Safe Empty Values:
```typescript
// ❌ WRONG
properties: data?.properties || []

// ✅ CORRECT  
const EMPTY_PROPERTIES = [];
properties: data?.properties || EMPTY_PROPERTIES
```

### Safe State Updates:
```typescript
// ❌ WRONG
setProperties(newProps);

// ✅ CORRECT
if (!areEqual(currentProps, newProps)) {
  setProperties(newProps);
}
```

### Safe useEffect:
```typescript
// ❌ WRONG
useEffect(() => {
  updateState(value);
}, [value, updateState]); // updateState changes every render

// ✅ CORRECT
const prevValueRef = useRef(value);
useEffect(() => {
  if (prevValueRef.current !== value) {
    prevValueRef.current = value;
    updateState(value);
  }
}, [value]);
```

## 📋 Files Most Likely to Cause Issues

1. **Context Providers** (`src/contexts/`)
2. **Custom Hooks** (`src/hooks/`)  
3. **Page Components** (`src/pages/`)
4. **Complex State Components** (forms, filters, tables)

## 🎯 Fixed Files Reference

These files contain the permanent solutions:

- `src/contexts/PropertyContext.tsx` - Property equality checking
- `src/pages/Index.tsx` - Previous property tracking
- `src/hooks/usePropertySearch.ts` - Stable empty references

## 📖 Full Documentation

For complete technical details: `REACT_INFINITE_LOOP_SOLUTION.md`

---

**🚀 Remember**: The fix is about **stable references** and **preventing unnecessary updates**. Always check if values actually changed before updating state!