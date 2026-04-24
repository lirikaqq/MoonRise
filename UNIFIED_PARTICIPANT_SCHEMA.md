# Unified Participant Data Schema

## Overview

This document describes the unified participant data schema implemented in the MoonRise project to resolve inconsistencies between manual CSV/TSV imports and registration form data. The schema ensures consistent participant information across all frontend components (participant cards, applications tab, teams tab, etc.).

## Problem Statement

Before unification, participant data came from two sources:
1. **Manual CSV/TSV import** (tournament #6) – data stored in `TournamentParticipant.application_data` JSON field
2. **Registration form submissions** – data also stored in `application_data` but with different field names and structures

This caused frontend components to display empty cards, missing tags, missing bios, and incorrect roles because they were looking for fields in different locations.

## Solution: Unified Schema

We introduced a unified data schema with the following components:

### 1. Pydantic Models (`backend/app/schemas/participant.py`)

- **`ParticipantCore`** – Core fields that every participant response should include
- **`ParticipantResponse`** – Wrapper for API responses containing a list of participants

### 2. Normalization Function (`normalize_participant_data`)

Extracts and normalizes participant data from `TournamentParticipant` and `User` objects with proper field priority:

```python
def normalize_participant_data(participant_obj, user_obj, battletag: Optional[str] = None) -> dict:
    # 1. Parse application_data JSON
    # 2. Apply field priority (application_data → user fields → fallbacks)
    # 3. Normalize role values ('sup' → 'support')
    # 4. Return unified dictionary
```

### 3. Field Priority and Fallbacks

| Field | Priority (highest to lowest) | Notes |
|-------|------------------------------|-------|
| `display_name` | 1. `application_data.display_name`<br>2. `user.display_name`<br>3. `user.username`<br>4. `application_data.battletag_name`<br>5. `application_data.discord_tag`<br>6. `'?'` | Used for participant display |
| `battle_tag` | 1. `application_data.battle_tag`<br>2. `application_data.battletag_value`<br>3. `battletag` parameter<br>4. `'?'` | BattleTag with #number |
| `discord_tag` | 1. `application_data.discord_tag`<br>2. `application_data.discord_handle`<br>3. `user.username`<br>4. `'?'` | Discord username |
| `primary_role` | 1. `application_data.primary_role`<br>2. `'flex'` | Normalized to: `'tank'`, `'dps'`, `'support'`, `'flex'` |
| `secondary_role` | 1. `application_data.secondary_role`<br>2. `'flex'` | Same normalization as primary |
| `bio` | 1. `application_data.bio`<br>2. `application_data.notes`<br>3. `user.bio`<br>4. `''` | Participant biography |
| `notes` | 1. `application_data.notes`<br>2. `application_data.admin_notes`<br>3. `''` | Administrative notes |
| `rank` | 1. `application_data.rank`<br>2. `''` | Player rank |

### 4. Role Normalization

Role values are normalized to match frontend expectations and backend constants:

- `'tank'` → `'tank'`
- `'dps'` → `'dps'`
- `'sup'`, `'support'`, `'heal'`, `'хил'`, `'сап'` → `'support'`
- Any other value → `'flex'`

## API Endpoints Updated

### 1. `GET /api/tournaments/{id}/participants` (P0 - Highest Priority)
- **File**: `backend/app/routers/tournaments.py`
- **Response model**: `ParticipantResponse`
- **Changes**: Uses `normalize_participant_data` to return unified participant objects
- **Fields returned**: All `ParticipantCore` fields plus `application_data` (original JSON for backward compatibility)

### 2. Other Endpoints (Future Updates)
- `GET /api/tournaments/{id}/applications` – Should be updated to use unified schema
- `GET /api/tournaments/{id}/teams` – Should be updated to use unified schema
- `GET /api/tournaments/{id}/free-players` – Should be updated to use unified schema

## Frontend Changes

### 1. ParticipantCard Component (`frontend/src/pages/TournamentDetail.jsx`)
- **Problem**: Cards showed "?" because data was in `application_data` but component looked at root level
- **Solution**: Added computed variables with fallbacks:
  ```javascript
  const displayName = player.display_name || player.user_display_name || '?'
  const battleTag = player.battle_tag || '?'
  const primaryRole = player.primary_role || 'flex'
  const bio = player.bio || player.notes || ''
  ```
- **Updated JSX**: Use computed variables instead of direct `player.*` access

### 2. ApplicationsTab.jsx
- **Status**: Already uses `parseApplicationData` function that extracts from `application_data`
- **Compatibility**: Works with both old and new data structures
- **Future improvement**: Update to also check root-level unified fields

### 3. TeamsTab.jsx
- **Status**: Already uses `normalizePlayer` function with fallbacks
- **Compatibility**: Works with both old and new data structures
- **Future improvement**: Update to also check root-level unified fields

## Import Script Updates

### `restore_tournament_6.py`
- **Role mapping**: Changed from `'sup'` to `'support'` to match unified schema
- **Added fields**: `display_name` to `application_data`
- **User display_name**: Set `user.display_name` to cleaned battletag name
- **Backward compatibility**: Maintains all existing `application_data` fields

## TypeScript Interface

Created `frontend/src/types/participant.ts` with `ParticipantData` interface matching `ParticipantCore`:

```typescript
export interface ParticipantData {
  id: number;
  user_id: number;
  display_name: string;
  discord_tag: string;
  battle_tag: string;
  primary_role: 'tank' | 'dps' | 'support' | 'flex';
  secondary_role: 'tank' | 'dps' | 'support' | 'flex';
  bio: string;
  notes: string;
  rank: string;
  avatar_url: string;
  is_captain: boolean;
  is_allowed: boolean;
  status: 'pending' | 'registered' | 'checkedin' | 'rejected';
  submitted_at: string;
  application_data: any; // Original JSON for backward compatibility
}
```

## Testing

### 1. Unit Test
- **File**: `backend/test_participant_schema.py`
- **Purpose**: Verify `normalize_participant_data` function with various input scenarios
- **Test cases**: 
  - Empty application_data
  - Partial fields
  - Role normalization
  - Field priority

### 2. Manual Testing
- Open tournament #6 participants tab – cards should show names, roles, battletags instead of "?"
- Verify applications tab displays D: and B: tags correctly
- Verify teams tab shows player names and roles

## Migration Steps for Future Imports

1. Ensure import scripts include `display_name`, `battle_tag`, `discord_tag`, `primary_role`, `secondary_role`, `bio`, `notes` in `application_data`
2. Use role values: `'tank'`, `'dps'`, `'support'`, `'flex'`
3. Set `user.display_name` when creating ghost users
4. The `normalize_participant_data` function will handle the rest

## Backward Compatibility

- All existing `application_data` remains unchanged
- Frontend components work with both old and new data structures
- API responses include original `application_data` alongside unified fields
- No database schema changes required

## Future Work

1. Update remaining API endpoints (`/applications`, `/teams`, `/free-players`) to use unified schema
2. Consider adding database columns for frequently accessed fields (denormalization)
3. Create migration script to populate `user.display_name` for existing participants
4. Update admin interfaces to edit unified fields directly

## Files Modified

### Backend
- `backend/app/schemas/participant.py` – New schema and normalization function
- `backend/app/routers/tournaments.py` – Updated `get_tournament_participants` endpoint
- `backend/restore_tournament_6.py` – Updated import script
- `backend/test_participant_schema.py` – Test script

### Frontend
- `frontend/src/pages/TournamentDetail.jsx` – Updated ParticipantCard component
- `frontend/src/types/participant.ts` – TypeScript interface

## Conclusion

The unified participant data schema resolves inconsistencies between data sources and ensures consistent participant information across all frontend components. The solution is backward-compatible, requires no database migrations, and can be incrementally extended to other parts of the application.