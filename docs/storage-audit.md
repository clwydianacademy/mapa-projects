# Cookie and storage audit — www.clwydianacademy.co.uk

Audited 22 November 2026 against the built site (`site/`) and the preview build with the salon
and the showcase on. Regulation 6 of PECR covers cookies **and** anything else stored on, or read
from, a visitor's device — `localStorage`, `sessionStorage`, IndexedDB, and fingerprinting.

| What | Found | Needs consent? |
|---|---|---|
| Cookies set by the site | **None.** No `Set-Cookie` from any page or from `/api/enquiry`; no `document.cookie` in any script. | — |
| `localStorage` / `sessionStorage` / IndexedDB | **None.** No script reads or writes them. | — |
| Analytics, tag managers, pixels | **None.** | — |
| Embedded third parties (maps, video, social) | **None.** The Find us block is text, not an embedded map. | — |
| Fonts | Switch OFF (today's live site): requested from Google Fonts — no cookie, but the visitor's IP address goes to Google. Showcase ON: served from our own origin, no third-party request at all. | No (nothing stored), but self-hosting removes the disclosure. |
| Enquiry form | Posts name, email, phone (optional) and message to `/api/enquiry`. Nothing is stored on the device. | No |

**Conclusion: no consent banner is needed on this host, and none should be added.** A banner is
required only for storage that is not strictly necessary; there is none. If analytics, a map
embed or a video is ever added, this audit must be redone **before** it ships, and anything
non-essential must wait for an opt-in.

The check is mechanised in `scripts/test_showcase.py` (no third-party font request on any preview
page) and by `grep -rn "localStorage\|sessionStorage\|document.cookie" site/assets/js` returning
nothing. The booking host has its own audit in the `salon-booking` repository.
