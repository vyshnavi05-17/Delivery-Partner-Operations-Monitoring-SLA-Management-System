from page_runtime import load_main_app

main_app = load_main_app()
dashboard, load_data = main_app.dashboard, main_app.load_data

cases, associates, _ = load_data()
dashboard(cases, associates)
