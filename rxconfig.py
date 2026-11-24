import reflex as rx

config = rx.Config(
    app_name="src",
    app_module_import="src.app",
    plugins=[
        rx.plugins.RadixThemesPlugin(),
        rx.plugins.SitemapPlugin(),
    ],
)