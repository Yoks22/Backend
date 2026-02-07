def manual_sync(client):
    try:
        res = client.sync_all()
        return True, "Sync completed", res
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e), None
