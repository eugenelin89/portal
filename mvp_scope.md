# MVP_SCOPE.md — BC Baseball Transfer Portal

This document defines the **strict scope** of the Minimum Viable Product (MVP).

The purpose of this document is to:
- Ensure the project is **finishable on time**
- Prevent feature creep
- Clarify what will and will not be built for the first release

**Target milestone:** MVP working demo

---

## 1. MVP Definition
The MVP demonstrates the **core value proposition**:

> *A league-governed, privacy-first transfer portal where teams can post tryouts and players can declare availability (“Open”) and be contacted in a controlled way.*

If a feature does not directly support this loop, it is **out of scope for the MVP**.

---

## 2. In-Scope Features (MVP)

### 2.1 Accounts & Roles
- User registration and login
- Role assignment:
  - Player / Parent
  - Coach / Manager
  - League / Association Admin
- Coach accounts require admin approval

---

### 2.2 Tryout Listings
- Coaches can:
  - Create tryout listings
  - Edit or cancel their own tryouts
- Tryout listing includes:
  - Team
  - Age group
  - Level (A / AA / AAA)
  - Date(s) and location
  - External registration link
- Players/families can:
  - Browse tryouts
  - Filter by age group, level, and date
  - View association info pages linked from tryouts, including upcoming tryouts
  - See association logos (URL) on info pages
  - Use a homepage dropdown to jump to associations
  - See a regional hero banner on the homepage

---

### 2.3 Player Profile (Core)
- Player profile with:
  - Name (or initials)
  - Birth year / age group
  - Positions
  - Bats / throws
- Profiles are **private by default**

---

### 2.4 Open Availability Status
- Player can toggle:
  - Open
  - Not Open
- Optional metadata:
  - Desired level(s)
  - Positions willing to play
- Open status is:
  - Opt-in
  - Not public
  - Visible only to permitted teams

---

### 2.5 Open Visibility Controls (MVP Simplified)
For MVP, **choose ONE visibility mechanism**:

**MVP Choice:** Allowed Teams
- Player explicitly selects which teams may view Open status
- No free browsing of Open players

(Allowed Regions can be added post-MVP.)

---

### 2.6 Contact Request Workflow
- Permitted teams can:
  - Send a contact request to an Open player
- Player can:
  - Accept the request (contact details shared)
  - Decline the request
- All requests are logged

---

### 2.7 Admin Tools (Minimal)
- Admin can:
  - Approve coach accounts
  - Create regions (BC only in MVP)
  - Create associations and teams
  - Maintain association info pages

---

## 3. Explicitly Out of Scope (MVP)

The following **will not** be built for the MVP:

### 3.1 Social Features
- Public feeds
- Following / likes
- Comments
- Direct messaging (beyond contact approval)

---

### 3.2 Rankings & Scouting
- Player rankings
- Leaderboards
- Performance comparisons

---

### 3.3 Verification System
- Coach/team/league verification of stats or clips
- Trust badges

---

### 3.4 Cross-Region Expansion
- Only **BC** is active
- Architecture supports expansion, but no ON/AB UI

---

### 3.5 Payments & Monetization
- No billing
- No subscriptions
- No payment processing

---

## 4. Nice-to-Have (Only If Time Remains)
- Team needs postings
- Auto-expiration for Open status
- Email notifications
- Basic audit log UI

If these features are not completed, the MVP is still considered **successful**.

---

## 5. Success Criteria for MVP
The MVP is successful if:
- A coach can post a tryout
- A player can browse tryouts
- A player can mark themselves Open
- A team can request contact
- A player can accept or decline

These steps can be demonstrated live.

---

## 6. Demo Scenario (Canonical)
1. Admin logs in and approves a coach
2. Coach creates a tryout
3. Player browses tryouts
4. Player sets Open = ON
5. Coach sends contact request
6. Player accepts request

---

## 7. Post-MVP Direction
After MVP:
- Add social features with privacy controls
- Add verification and trust indicators
- Expand to additional regions
- Introduce league/team monetization

---

## 8. Guiding Rule
> **If it does not improve the demo flow, it does not belong in the MVP.**

---

This document is intentionally strict.
It exists to ensure the project ships.
