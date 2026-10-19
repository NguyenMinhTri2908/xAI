import reflex as rx

config = rx.Config(
    app_name="ui",
    app_module_import="src.ui.app",
    reload_paths=["src"],
    plugins=[
        rx.plugins.RadixThemesPlugin(),
        rx.plugins.SitemapPlugin(),
    ],
)