



def test_delete_record():
    pass

def test_update_record_not_redcap_not_db():
    pass

def test_update_record_not_redcap_in_db():
    pass

def test_update_record_in_redcap_not_db():
    pass

def test_update_record_in_redcap_in_db():
    pass



def test_configs():

    avail_configs = ['a', 'b']

    for config in avail_configs:

        test_delete_record()
        test_update_record_not_redcap_not_db()
        test_update_record_not_redcap_in_db()
        test_update_record_in_redcap_not_db()
        test_update_record_in_redcap_in_db()

