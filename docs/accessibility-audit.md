# Accessibility record — www.clwydianacademy.co.uk (preview build, showcase on)

Checked 24 November 2026, by machine and by scripted keyboard. **No person using assistive
technology has tested this yet**; that is still to do before opening, and nothing below replaces it.

## 1. axe-core 4 (WCAG 2.0/2.1/2.2 A and AA, plus best practice)

All 69 pages of the preview build, at 1280px and 390px: 138 page loads.

**Result: 0 violations.** Found and fixed on the way:

| Rule | Where | Fix |
|---|---|---|
| heading-order | the footer's column titles (h4 straight after h2), every page | they are `h2` while the showcase is on |
| label-content-name-mismatch | the brand link in the header and footer | its accessible name now contains the words it shows |
| heading-order | CPD courses, Guides, Train your team, Privacy (EN and CY): h1 straight to h3 | the section gains a screen-reader `h2` (showcase on only) |
| region | the preview ribbon | it is a labelled `aside` |

With the showcase switch OFF the live site still has the three older faults above; they are fixed
only in the showcase build, so that the deployed folder stays identical to main until Mark says.

## 2. Keyboard only

Not walked by script on this host: its pages are documents and links, with one enquiry form that
existing checks cover (`scripts/check_forms.py`: every control labelled). The three hero paths,
the gallery filter links, the before-and-after slider (an ordinary range input) and the lightbox
(a native dialog, closed with Escape) are all standard keyboard-operable elements; the slider and
lightbox are covered by `scripts/test_showcase.py`.

## 3. 200% zoom

A 1280 x 800 window at 200% lays out as 640 x 400 CSS pixels. Checked for sideways scrolling,
clipped text and text pushed off the edge.

10 pages of this host among 19 views across both. **Result: 0 problems.** Also: no horizontal
scroll on 7 pages at 8 widths from 320px to 1920px.

## 4. Already held by tests or measurement

- Lighthouse accessibility 100 on `/`, `/cy/`, `/work/` and `/salon/prices/` (local preview).
- Every image has width, height and alt text; stock photographs are described, never claimed.
- Scroll reveals are visible by default and off under reduced motion.

## 5. Not checked

- A screen reader run-through by a person (NVDA, VoiceOver, TalkBack).
- Voice control, switch access, and a magnifier.
- Colour-blindness simulation beyond the rule that a selection is never shown by colour alone.
