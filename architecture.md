# ARCHITECTURE.md — BC Baseball Transfer Portal

## 0. Overview
This document describes the technical architecture for **transferportal.ca**, with regional instances such as **`bc.transferportal.ca`**.

Design goals:
- One shared codebase and deployment.
- Region-scoped governance for associations/teams.
- Global player identity that can be reused across regions.
- Privacy-first visibility controls, especially for “Open” status.
- Mobile-friendly web UI now; clean path to a dedicated mobile app later.

---

## 1. High-Level Architecture
**Django monolith (MVP)**
- Server-rendered pages for core flows.
- Optional APIs (Django REST Framework) added incrementally.

**Core concept:** multi-tenant-by-subdomain.
- Subdomain determines the **current region tenant** (e.g., `bc`).
- Region-scoped data is automatically filtered to the current region.
- Global player identity is shared across all regions.

---

## 2. Regional Tenancy Model (Subdomain = Region)
### 2.1 Hostname Parsing
- Requests arrive on hostnames like `bc.transferportal.ca`.
- Middleware derives `request.region` from the hostname.

**Rules**
- `transferportal.ca` (root) can be marketing/landing.
- `bc.transferportal.ca` maps to region code `bc`.
- Future regions: `on`, `ab`, etc.

### 2.2 Django Settings
- `ALLOWED_HOSTS` supports subdomains: `.transferportal.ca`.
- DNS/ingress supports wildcard: `*.transferportal.ca` → same server.

### 2.3 Implementation Pattern
**Middleware** (conceptual)
- Parse host
- Set `request.region`
- Attach `request.tenant` object (Region/Tenant model) if used

**Template context**
- Region branding can use `request.region`.

---

## 3. Data Partitioning Strategy
### 3.1 Global vs Region-Scoped Data
**Global (shared across regions)**
- User account
- PlayerProfile
- Showcase links (PBR/YouTube)
- Player privacy settings (including allowed regions/teams)

**Region-scoped**
- Association
- Team
- TryoutEvent
- TeamNeed
- ContactRequest (initiated by a region team)
- Admin roles/permissions

### 3.2 Region Field / Tenant FK
For region-scoped models, include one of:
- `region = CharField(choices=REGIONS)`
- or `region = ForeignKey(Region)`

Recommendation: **ForeignKey to Region** for extensibility (names, rules, settings).

### 3.3 Default Filtering
All reads for region-scoped objects default to `region=request.region`.

Mitigations to avoid cross-region leakage:
- Shared query helpers / custom model managers (e.g., `Team.objects.in_region(request.region)`)
- Tests that ensure list/detail views cannot access out-of-region objects
- Admin restrictions: region admins only see their region’s objects

---

## 4. Privacy & Visibility Model
Privacy is **default-deny**.

### 4.1 Profile Visibility (MVP)
The MVP uses a single profile visibility setting for the entire profile.

Future (post-MVP):
- Per-section visibility for profile info, achievements, and highlights
- Additional audience types beyond allow-listed associations

### 4.2 “Open” Status Visibility
“Open” status is especially sensitive and must be private by default.

**Controls**
- MVP: Allowed Teams (allow-list of teams that may view Open status)
- Post-MVP: Allowed Regions (list of regions that may view Open status)

**Effective rule**
A team can view a player’s Open status only if:
- Team is in an allowed region AND
- (optional) team is explicitly allow-listed (if enabled)

### 4.3 Contact Requests
- Only teams that can view Open status can send ContactRequests.
- ContactRequests are auditable and rate-limited.
- Messaging/contact exchange occurs only after player approval.

---

## 5. Core Domain Model (Conceptual)
Entities (from requirements):
- Region
- User
- Role / Membership (region-scoped)
- Association (region-scoped)
- Team (region-scoped)
- PlayerProfile (global)
- AvailabilityStatus (global, but evaluated against region/team)
- TryoutEvent (region-scoped)
- TeamNeed (region-scoped)
- ContactRequest (region-scoped)
- AuditLogEntry (region-scoped, append-only)

Key relationships (high-level):
- Region 1—* Association
- Association 1—* Team
- User 1—1 PlayerProfile (optional)
- Team *—* User (coach memberships)
- PlayerProfile 1—* AvailabilityStatus (latest = current)
- Team 1—* TryoutEvent
- Team 1—* TeamNeed
- Team 1—* ContactRequest —* PlayerProfile

---

## 6. Authorization Model
### 6.1 Role-Based Access Control (RBAC)
Roles:
- Player/Parent
- Coach/Manager
- Region Admin

Region-scoped permissions:
- Region Admin manages only their region.
- Coaches can post only for teams they’re assigned to.
- Players manage only their own profiles and visibility.

### 6.2 Guardrails
- “Open” is opt-in
- Contact requests require visibility permission
- Rate limits for coaches
- Audit logs for sensitive actions

---

## 7. Tryout & Placement Flows (System View)
### 7.1 Tryout Listings
- Coach creates TryoutEvent in region
- Families browse region tryouts (mobile-friendly)
- Registration link points outward

### 7.2 Post-Tryout Availability
- Player sets status Open
- Visibility is controlled via allowed regions/teams

### 7.3 Roster Completion
- Team posts TeamNeed
- Team filters Open players
- Team sends ContactRequest
- Player accepts/declines
- If accepted and committed, player toggles Committed, removing from Open searches

---

## 8. Verification (Optional / Future)
The system can support “verification badges” without becoming a ranking system.

Examples:
- Coach/team/league verifies a stat line or achievement entry
- Verification attaches:
  - verifier identity
  - timestamp
  - object reference

Verification indicates authenticity only.

---

## 9. Mobile-Friendly Web and Mobile App Path
### 9.1 MVP Web
- Responsive templates (Bootstrap/Tailwind)
- Phone-first flows: browse tryouts, toggle Open, handle requests
- Association info pages with public contact details
- Association logos via URL (recommended square, 200–800px)
- Regional homepage association dropdown

### 9.2 APIs for Mobile
- Add DRF endpoints for:
  - Tryout search
  - Availability status
  - Contact requests
  - Notifications

### 9.3 Notifications
- Email in MVP
- Push notifications in mobile app (future)

---

## 10. Deployment Notes (MVP)
- Single deployment serving all regions
- Wildcard DNS for `*.transferportal.ca`
- HTTPS certificates cover subdomains (wildcard cert or managed service)

---

## 11. Testing Strategy (Important)
- Unit tests for middleware region parsing
- Permission tests for:
  - region scoping
  - Open visibility
  - contact request permissions
- Regression tests to prevent cross-region data leaks

---

## 12. Future Extensions
- Additional regions (subdomains)
- Team/league integrations (imports)
- Richer social features with privacy-scoped audiences
- Dedicated mobile apps
