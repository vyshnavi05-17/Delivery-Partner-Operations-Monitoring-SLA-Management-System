from page_runtime import load_main_app

main_app = load_main_app()
case_management, load_data = main_app.case_management, main_app.load_data

cases, associates, _ = load_data()
case_management(cases, associates)
