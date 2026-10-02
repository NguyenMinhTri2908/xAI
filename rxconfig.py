import reflex as rx

config = rx.Config(
    app_name="ui",
    reload_paths=["src"],
    plugins=[
        rx.plugins.RadixThemesPlugin(),
        rx.plugins.SitemapPlugin(),
    ],
)