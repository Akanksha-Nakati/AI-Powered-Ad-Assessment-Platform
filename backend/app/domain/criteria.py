"""The scoring rubric.

Previously these six criteria existed only as a comma-separated list inside a
prompt f-string, which meant the API contract, the UI labels and the model's
instructions could drift apart silently. They live here now, once.
"""

from enum import StrEnum


class Criterion(StrEnum):
    ATTENTION = "attention"
    CLARITY = "clarity"
    TARGETING = "targeting"
    CTA = "cta"
    BRANDING = "branding"
    VALUE = "value"


#: Shown to the model so a "7" means the same thing across runs and providers.
RUBRICS: dict[Criterion, str] = {
    Criterion.ATTENTION: (
        "Does the creative stop the scroll? Judge focal hierarchy, contrast, and "
        "whether a single element wins the eye in the first half-second."
    ),
    Criterion.CLARITY: (
        "Is the offer understandable without effort? Judge copy length, legibility "
        "against the background, and whether one idea dominates rather than three."
    ),
    Criterion.TARGETING: (
        "Does the creative speak to the stated industry and platform audience? "
        "Judge idiom, imagery, and format fit for the placement."
    ),
    Criterion.CTA: (
        "Is there one obvious next step? Judge verb strength, visual prominence, "
        "and whether the CTA competes with other elements."
    ),
    Criterion.BRANDING: (
        "Is the advertiser identifiable and consistent? Judge logo presence, "
        "palette discipline, and whether brand recall survives a one-second view."
    ),
    Criterion.VALUE: (
        "Is a concrete benefit or proof point present? Judge outcome-led messaging "
        "over feature lists, and the presence of social proof or risk reduction."
    ),
}
