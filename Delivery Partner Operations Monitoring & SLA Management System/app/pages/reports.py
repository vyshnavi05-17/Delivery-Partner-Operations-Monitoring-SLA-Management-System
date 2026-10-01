from page_runtime import load_main_app

main_app = load_main_app()
load_data, reports = main_app.load_data, main_app.reports

cases, associates, _ = load_data()
reports(cases, associates)
