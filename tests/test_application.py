from service.application_service import get_application_info_cached
import time

def test_get_application_info_cached():
    app_id = 'e27f0067-7cb1-498b-9fa4-c6d4d81655fb'
    i = 0
    while i < 30:
        app = get_application_info_cached(app_id)
        assert app is not None
        time.sleep(1)
        i+=1
    
# python -m pytest -v -s