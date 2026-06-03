# Design Specification: Library Split-Right Search & Filters

Implementation of real-time search and filter capabilities for the library panel stacks on the right side of the dashboard web interface in the Sweepy dashboard.

## Purpose & Scope
Allow users to easily manage, search, and select Decks, Trainees, Friend Supports, Parents, Friend Parents (Borrow), and Owned Cards. This is particularly crucial for the race-heavy Make A New Track (MANT) scenario where finding specific support cards and high-star parents (e.g., Speed 9★) is necessary.

---

## 1. UI Components Design
We will place an embedded, responsive toolbar block within the collapsible body of each section, directly above its list/grid container:

### A. Decks Section
* **Input Field**: Text search input `deck-search-input`.
* **Behavior**: Real-time filtering matching substring on the Deck Name.

### B. Trainees Section
* **Input Field**: Text search input `trainee-search-input`.
* **Behavior**: Substring matching on the Trainee Character Name.

### C. Friend Supports & Owned Cards Sections
* **Search Input**: `support-search-input` (for Owned Cards) and `friend-search-input` (for Friends). Matches card name or trainer name (for friends).
* **Card Type Dropdown**: Dropdown list to filter by attributes (Speed, Stamina, Power, Guts, Wisdom, Group, Friend).
* **Rarity Chip Buttons**: Clickable badges to filter by rarity (`SSR`, `SR`, `R`).
* **Limit Break Buttons** (Friends only): Chip buttons to filter by limit break levels (All, LB0, LB1, LB2, LB3, LB4).

### D. Parents & Friend Parents (Borrow) Sections
An advanced collapsible **Spark Filters** drawer modeled after the latest `uma.moe` filtering layout:
* **Quick Search Field**: A text input to quick-search by character name.
* **Rank Dropdown Filter**: Filter by rank (All, UG or higher, SS or higher, S or higher, etc.).
* **Spark Filters Drawer**:
  * Separated by categories: **Blue Factors (Stats)**, **Pink Factors (Aptitudes)**, **Green Factors (Unique)**, and **White Factors (Skills/Races)**.
  * For each category, users can click `+ Add [Category] Factor` to add a new row of criteria.
  * Each criteria row consists of:
    1. A search-select dropdown listing factor names present in the data.
    2. A star target slider or button row (1★ to 9★ for Blue/Pink/White; 1★ to 3★ for Green).
    3. A delete button (red cross icon) to remove that row.

---

## 2. Technical Architecture & Filter Logic

### A. In-Memory Filter State
We will maintain a global filter state object inside `state.filters`:
```javascript
state.filters = {
    decks: { query: '' },
    trainees: { query: '' },
    friends: {
        query: '',
        type: 'all',
        rarity: { SSR: true, SR: true, R: true },
        limitBreak: 'all'
    },
    ownedCards: {
        query: '',
        type: 'all',
        rarity: { SSR: true, SR: true, R: true }
    },
    parents: {
        query: '',
        rank: 'all',
        criteria: [] // { category: 'blue'|'pink'|'green'|'white', name: '', minStars: 1 }
    },
    friendVets: {
        query: '',
        rank: 'all',
        criteria: [] // { category: 'blue'|'pink'|'green'|'white', name: '', minStars: 1 }
    }
};
```

### B. Filter Rules & Matching Algorithms
1. **Friends allowed rule**: The existing logic in `friendAllowed(friend)` will run *first* to exclude cards already in the deck or matching the trainee. The custom filters will run on the resulting allowed list.
2. **Owned Parents Spark Summing**:
   * For owned parents, we check the pedigree tree (`tree.self`, `tree.p1`, `tree.p2`).
   * For each active filter criteria, we match the factor name and sum up the star count (`.stars`) across all three generation nodes.
   * If `sum(stars) >= criteria.minStars`, it matches.
3. **Borrowed Friends Spark Summing**:
   * For friend parents, we check the flat list of `factors` inside the veteran object.
   * We sum up the `.stars` of all factors with the matching factor name.
   * If `sum(stars) >= criteria.minStars`, it matches.
4. **Boolean AND operation**: If multiple criteria rows are added, a parent card must satisfy **ALL** criteria (AND logic) to remain visible.

---

## 3. UI Styling & Theme Integration
* All input boxes, select boxes, and sliders will match the user's active theme (pink/blue) and follow the glassmorphic dark design in `public/styles.css`.
* Checkbox chips/badges will toggle state by adding/removing an `.active` class (styled with primary accents).

---

## 4. Verification & Testing Plan
* **Manual Verification**:
  1. Open the UI, check that search inputs appear and filter items in real-time.
  2. Verify that type, rarity, and limit break buttons filter Support Cards & Friends correctly.
  3. Verify adding multiple factor rows under "Spark Filters" and confirming that parents are correctly filtered based on combined star counts.
  4. Ensure selecting cards/items updates the active deck selection properly.
