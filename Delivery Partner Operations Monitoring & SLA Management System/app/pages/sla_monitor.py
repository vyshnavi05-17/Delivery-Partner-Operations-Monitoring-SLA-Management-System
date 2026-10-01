from page_runtime import load_main_app

main_app = load_main_app()
load_data, sla_monitor = main_app.load_data, main_app.sla_monitor

cases, _, _ = load_data()
sla_monitor(cases)
