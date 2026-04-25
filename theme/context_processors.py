VALID_THEMES = {"light", "dracula"}
LEGACY_DARK_THEMES = {"dark", "synthwave", "graphite"}


def cooplink_theme(request):
    theme = request.COOKIES.get("cooplink-theme", "")

    if theme in LEGACY_DARK_THEMES:
        theme = "dracula"
    elif theme not in VALID_THEMES:
        theme = ""

    return {
        "cooplink_theme": theme,
        "cooplink_theme_is_dracula": theme == "dracula",
    }
