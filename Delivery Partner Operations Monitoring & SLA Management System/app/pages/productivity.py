from page_runtime import load_main_app

main_app = load_main_app()
load_data, productivity = main_app.load_data, main_app.productivity

cases, associates, _ = load_data()
productivity(cases, associates)
