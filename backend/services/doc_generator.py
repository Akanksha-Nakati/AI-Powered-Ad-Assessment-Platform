from pathlib import Path
from textwrap import dedent


def ensure_marketing_docs(doc_dir: Path) -> None:
    """
    Create core marketing markdown docs on first run.
    """
    doc_dir.mkdir(parents=True, exist_ok=True)

    docs = {
        "AIDA.md": dedent(
            """
            # AIDA Framework for Ads

            ## Attention
            - Lead with a bold visual focal point and a 3-7 word hook.
            - Contrast foreground vs. background; avoid clutter that competes for focus.
            - Platform fit: vertical for stories/reels, square for feeds, horizontal for banners.

            ## Interest
            - Highlight 1-2 key benefits aligned to audience pain points.
            - Use scannable structure: short lines, subheads, or badges (e.g., “New”, “Save 30%”).
            - Reinforce with supporting imagery that shows the product in use.

            ## Desire
            - Show proof: testimonials, ratings, social proof, or certifications.
            - Emphasize outcomes over features (e.g., “sleep better” vs “memory foam”).
            - Reduce friction: free trials, easy returns, fast shipping.

            ## Action
            - Single, clear CTA with imperative verbs (e.g., “Shop now”, “Book a demo”).
            - Place CTA high contrast, near focal content, and repeat once if space allows.
            - Add urgency or scarcity only when authentic (“Ends Sunday”, “Spots limited”).
            """
        ).strip(),
        "Color_Psychology.md": dedent(
            """
            # Color Psychology for Advertising

            ## Core Principles
            - Use a limited palette (1-2 primaries + 1 accent) to avoid visual noise.
            - Maintain contrast for readability: WCAG AA contrast on text/background.
            - Harmonize palette with brand identity to improve recall.

            ## Color Associations
            - Red: urgency, excitement, appetite. Great for sales; use sparingly to avoid fatigue.
            - Blue: trust, calm, reliability. Ideal for finance, tech, healthcare.
            - Green: growth, wellness, sustainability. Good for eco or health offers.
            - Yellow/Orange: optimism, friendliness, approachability; balance with neutrals.
            - Black/White/Neutrals: premium, minimal, focus on product.

            ## Application
            - CTA buttons: high-contrast accent distinct from background and other elements.
            - Backgrounds: neutral or soft tones to let product/CTA pop.
            - Text on images: use overlays or strokes when backgrounds are busy.
            """
        ).strip(),
        "CTA_Best_Practices.md": dedent(
            """
            # CTA Best Practices

            ## Clarity
            - Use explicit verbs: “Get quote”, “Book demo”, “Download guide”.
            - Match promise to landing experience; avoid bait-and-switch.

            ## Visibility
            - Size: large enough to notice, small enough to avoid overpowering the hero.
            - Placement: near product/value text and above the fold when possible.
            - Contrast: distinct color, whitespace buffer, minimal competing elements.

            ## Friction Reduction
            - Set expectations: “2-min form”, “No credit card”, “Free shipping”.
            - Use microcopy to address objections: “Cancel anytime”, “No spam”.

            ## Variations by Platform
            - Stories/Reels: vertical-safe zones, CTA within thumb reach.
            - Feed: square/vertical, test secondary CTA in caption.
            - Banners: concise copy, CTA right-aligned or near focal element.
            """
        ).strip(),
    }

    for filename, content in docs.items():
        path = doc_dir / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")

