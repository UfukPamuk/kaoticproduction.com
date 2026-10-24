"""Site constants: the ONLY place to change links, e-mail and the trailer.

After editing, rebuild the HTML:
    python tools/build.py
then commit and push. (Images, fonts and the press-kit zip are made by
tools/make_assets.py and only need rebuilding when the source art changes.)
"""

SITE_URL = "https://kaoticproduction.com"   # no trailing slash

# Public support / contact address (home, game page, privacy, support).
CONTACT_EMAIL = "destek@kaoticproduction.com"
# General and press contact (press kit, "press or business" line on home).
PRESS_EMAIL = "info@kaoticproduction.com"

# Store links. Leave "" while a store page is not live: the button then
# shows "Coming soon" and is not a link. Paste the real URL to switch it on.
STEAM_URL = ""          # e.g. "https://store.steampowered.com/app/1234560/Reverdo/"
APP_STORE_URL = ""      # e.g. "https://apps.apple.com/app/id0000000000"
GOOGLE_PLAY_URL = ""    # e.g. "https://play.google.com/store/apps/details?id=com.reverdo.game"

# YouTube video id of the full trailer (the part after "watch?v=").
# "" shows the poster with "Trailer coming soon on YouTube".
YOUTUBE_ID_EN = "QZI_pq7fEjc"
YOUTUBE_ID_TR = "VDeJZjBKnSk"      # Turkish trailer; falls back to the English one if ""

STEAM_PRICE = "6,99 USD"          # shown as-is (TR uses the same string)
STEAM_PRICE_EN = "US$6.99"
