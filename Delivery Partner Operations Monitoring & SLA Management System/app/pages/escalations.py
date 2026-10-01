from page_runtime import load_main_app

main_app = load_main_app()
escalations, load_data = main_app.escalations, main_app.load_data

cases, _, _ = load_data()
escalations(cases)
