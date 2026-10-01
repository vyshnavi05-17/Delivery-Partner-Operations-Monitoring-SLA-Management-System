from page_runtime import load_main_app

main_app = load_main_app()
load_data, quality = main_app.load_data, main_app.quality

cases, _, _ = load_data()
quality(cases)
