# Changelog: v1 → v2

**Account:** GreenLeaf Property Management
**Account ID:** greenleaf_6555c4

---

## `business_hours`

**Before:**
```
Monday to Friday, 8:00 AM to 6:00 PM MST. We're closed on weekends and federal holidays
```
**After:**
```
Monday to Friday, 8:00 AM to 7:00 PM MST. We extended by an hour because of high call volume in the evening
```

## `call_transfer_rules`

**Before:**
```
During office hours, transfer to the front desk at extension 100 first. If no answer, try the property manager on-call at extension 200
```
**After:**
```
During office hours, transfer to the front desk at extension 100 first. If no answer after 20 seconds, try extension 200. If still no answer, try the office manager at extension 150
```

## `emergency_definition`

**Before:**
```
Any situation involving flooding, fire, gas leaks, no heat in winter, no AC when temperatures exceed 100°F, or a security breach at a property
```
**After:**
```
Any situation involving flooding, fire, gas leaks, no heat in winter, no AC when temperatures exceed 95°F, security breaches, or elevator malfunctions. We lowered the AC threshold and added elevator issues
```

## `emergency_routing_rules`

**Before:**
```
Transfer to our on-call maintenance supervisor at extension 501. If they don't answer, try the backup number 303-555-0199
```
**After:**
```
Transfer to on-call maintenance supervisor at extension 501. If no answer, try backup number 303-555-0199, and now also try the property manager cell at 303-555-0250 as a third option
```

## `integration_constraints`

**Before:**
```
We use AppFolio for property management. No direct API integration is needed for now — just standard call handling
```
**After:**
```
We're now testing an AppFolio API integration for logging maintenance requests. Clara should still handle calls normally but note that automated ticket creation is being piloted
```

## `notes`

**Before:**
```
Tenants sometimes call about packages — we don't handle package tracking, so just let them know to contact their carrier directly.
```
**After:**
```
We hired a new assistant property manager, Janet, who handles tenant complaints directly. Her extension is 175. Also, we now have a Spanish-speaking staff member available at extension 160 for callers who prefer Spanish.
```

## `questions_or_unknowns`

**Before:**
```
- And what's your office address?
```
**After:**
```
- And what's your office address?
- Any changes to business hours?
- What about services?
- Sarah: Any update to the emergency definition?
- Sarah: What about emergency routing?
- Sarah: Any changes to the call transfer rules?
- Sarah: How about integration constraints?
- Sarah: Anything else?
```

## `services_supported`

**Before:**
```
- Maintenance requests
- rent inquiries
- lease questions
- lockout assistance
- general property information
```
**After:**
```
- Maintenance requests
- rent inquiries
- lease questions
- lockout assistance
- general property information
- HOA coordination
```
