def test_pipeline_is_working():
    assert 1 + 1 == 2

def test_auth_imports_correctly():
    try:
        import features.auth
        import_successful = True
    except Exception as e:
        print(f"Import failed: {e}")
        import_successful = False
        
    assert import_successful == True