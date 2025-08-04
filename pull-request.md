# Pull Request: UI Improvements

**Branch:** `ui-improvement` → `main`

**Title:** UI: Improve playground selector components and toast styling

## Summary

- Fix consistent alignment and layout issues across playground selector components
- Improve toast notification styling for better theme consistency
- Enhance user experience with better spacing and visual hierarchy

## Changes

### Playground Selectors
- **Agent Selector**: Align dropdown content to the right for consistent positioning
- **App Selector**:
  - Improve popover width handling with better min/max constraints
  - Add proper margins and shrink behavior for checkmarks
- **Function Selector**:
  - Enhanced popover sizing with responsive width constraints
  - Improved item layout with better gap spacing
  - Removed unnecessary tooltip wrapper for cleaner rendering
  - Fixed checkmark positioning with proper flex properties
- **Linked Account Selector**:
  - Add validation to prevent invalid selections
  - Align dropdown content consistently
  - Handle edge cases where selected value may not exist in options

### Toast Notifications
- Enhanced error toast styling with proper background, text, and border colors
- Added CSS custom properties for better theme integration
- Improved visual consistency with the application's design system

## Files Changed

- `frontend/src/app/layout.tsx` - Toast styling improvements
- `frontend/src/app/playground/setting-agent-selector.tsx` - Dropdown alignment
- `frontend/src/app/playground/setting-app-selector.tsx` - Popover sizing and checkmark layout
- `frontend/src/app/playground/setting-function-selector.tsx` - Layout improvements and tooltip cleanup
- `frontend/src/app/playground/setting-linked-account-owner-id-selector.tsx` - Validation and alignment fixes
- `frontend/src/components/ui/sonner.tsx` - CSS custom properties for theming

## Commits

- `c9281a9` fix sooner bg color
- `d114ac9` improve ui for agent playground selection

## Test Plan

- [ ] Verify all playground selectors display correctly in both light and dark themes
- [ ] Test dropdown alignment and positioning across different screen sizes
- [ ] Confirm toast notifications appear with proper styling
- [ ] Validate that selector state handling works correctly with edge cases
- [ ] Check responsive behavior of popover components

---

🤖 Generated with [Claude Code](https://claude.ai/code)
