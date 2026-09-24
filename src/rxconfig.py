import reflex as rx

config = rx.Config(
    app_name="FinalYearPro",
    app_module="src.ui.app:app",
    plugins=[
        rx.plugins.RadixThemesPlugin(),
    ],
)