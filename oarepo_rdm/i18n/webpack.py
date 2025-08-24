from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    ".",
    default="semantic-ui",
    themes={
        "semantic-ui": {
            "entry": {},
            "dependencies": {},
            "devDependencies": {},
            "aliases": {
                "@translations/oarepo_rdm": "translations/oarepo_rdm/i18next.js"
            },
        }
    },
)
