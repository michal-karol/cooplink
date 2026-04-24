VALID_THEMES = {"light", "graphite"}
LEGACY_DARK_THEMES = {"dark", "synthwave"}


def cooplink_theme(request):
    theme = request.COOKIES.get("cooplink-theme", "")

    if theme in LEGACY_DARK_THEMES:
        theme = "graphite"
    elif theme not in VALID_THEMES:
        theme = ""

    return {
        "cooplink_theme": theme,
        "cooplink_theme_is_graphite": theme == "graphite",
    }
