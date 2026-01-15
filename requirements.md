# BC Baseball Transfer Portal — Requirements

## 1. Purpose
Build a league-friendly **BC Baseball Transfer Portal** that reduces chaos during tryout season by:
- Centralizing **tryout dates + registration links** across British Columbia.
- Allowing players/families to self-declare **availability (“Open”)** (similar to entering a transfer portal), without stigma.
- Helping associations/teams **complete rosters** efficiently through a controlled, auditable matching flow.

> Note: The term *Transfer Portal* is used intentionally to mirror the college model. The BC Baseball Transfer Portal is opt-in, league-governed, and designed specifically for youth baseball within British Columbia.

---

## 2. Goals
- One place for families to find nearby tryouts and registration links.
- A safe, opt-in way for players to be discoverable if they are still looking.
- A structured way for teams short on players to request contact.
- Minimize poaching accusations via permissions, time windows, and audit logs.

---

## 3. Non-Goals
- **Not a fully public, open-by-default social network in the MVP.**
- **Not a rankings or leaderboard system.**
- Not automated acceptance or roster decisions.
- Not forcing associations to label players as “cut.”

### 3.1 Future Direction (Social Network With Privacy)
- Private-by-default profiles with granular visibility.
- Per-post / per-section audience control.
- Verified roles (coach, team, league).
- Opt-in messaging only.

---

## 4. User Roles
### 4.1 Player / Parent
- Manage player profile and privacy.
- Browse tryouts.
- Toggle Open status.
- Approve or decline contact requests.

### 4.2 Coach / Manager
- Post tryouts for assigned teams.
- Post team needs.
- View Open players (if permitted).
- Send contact requests.

### 4.3 Association / League Admin
- Verify coaches and teams.
- Configure tryout windows and rules.
- View audit logs.
- Maintain association info pages.

---

## 5. Core Features (Functional Requirements)

### 5.1 Authentication & Accounts
- Users can register and log in.
- Accounts are role-based.
- Coaches require admin approval.
- Coach signup requires email verification; domain-matched emails can be auto-approved.

### 5.2 Tryout Listings
- Teams can post tryout dates, locations, and registration links.
- Families can browse and filter tryouts.
- Tryout edits are logged.

### 5.2A Association Info Pages
- Each association has a public information page.
- Admins can maintain association details (description, contact info, website).
- Admins can upload a square logo (200–800px).

### 5.3 Player Profile
- Name (or initials)
- Birth year / age group
- Positions
- Bats / throws
- Optional home association

#### 5.3.1 Achievement & Highlight Showcase (Optional)
- Player may showcase achievements and milestones.
- Player may link to third-party profiles (e.g. PBR).
- Player may link to external highlight videos (e.g. YouTube).

#### 5.3.2 Optional Verification
- Stats or achievements may be verified by a coach, team, or league (post-MVP).
- Verification indicates authenticity only.

#### 5.3.3 Privacy & Recruiting Visibility
- Profiles are private by default.
- MVP uses a single profile visibility setting.
- Per-section visibility is a post-MVP enhancement.

##### 5.3.3.1 Open Visibility Controls
- MVP: Allowed Teams (explicit allow-list).
- Post-MVP: Allowed Regions.
- Open status is never public.

### 5.4 Open Availability Status
- Player may toggle Open / Not Open.
- Optional metadata: levels, positions, timing.
- Auto-expiration supported.

### 5.5 Team Needs (Post-MVP)
- Teams can post roster needs.
- Teams can browse Open players.

### 5.6 Contact Requests
- Teams send contact requests.
- Players accept or decline.
- All actions are logged.

### 5.7 Commitment
- Player marks Committed when joining a team.
- Committed players are hidden from Open search.

---

## 6. Rules & Guardrails

### 6.1 Cross-Region Identity Model
- Players have a single global profile.
- Associations and teams are region-scoped.
- Cross-region visibility is opt-in.

---

## 7. Data Entities
- User
- PlayerProfile
- Region
- Association
- Team
- TryoutEvent
- TeamNeed
- AvailabilityStatus
- ContactRequest
- AuditLogEntry

---

## 8. Non-Functional Requirements
- Built with **Django**.
- Mobile-friendly, responsive UI.
- Privacy by default.
- Secure access control.
- Reliable during peak tryout weeks.

---

## 9. Success Metrics
- Reduced parent panic after tryouts.
- Faster roster completion.
- Adoption by at least one BC association.

---

## 10. Post-MVP Enhancements
- Team needs postings and browsing.
- Per-section profile visibility controls.
- Allowed regions visibility.
- Verification system for achievements and stats.

---

## 11. References
- See **ARCHITECTURE.md** for technical design and subdomain-based regional architecture.
