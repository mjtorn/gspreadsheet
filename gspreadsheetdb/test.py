#!/usr/bin/python
# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

### XXX: This could be made into a "real" test, like doctest, some day

import sys

import objects

def dec_traceback(func):
    def wrap(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except Exception, e:
            import sys, traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            for formatted in traceback.format_exception(exc_type, exc_value, exc_traceback):
                print formatted,

            # Cease execution on failed test
            print
            print 'Test threw unhandled exception, exiting!'
            sys.exit(1)

        return ret

    return wrap

### Tests that expect certain failure
@dec_traceback
def test_fail_create_database(db, db_name):
    try:
        db.create(db_name)
        print 'FAILED - did not die on ValueError'
        sys.exit(1)
    except ValueError, msg:
        print 'PASS - failed wih "%s"' % msg

@dec_traceback
def test_fail_create_table(db, name, fields):
    try:
        db.create_table(name, fields)
        print 'FAILED - did not die on AttributeError'
        sys.exit(1)
    except AttributeError, msg:
        print 'PASS - failed with "%s"' % msg

### Tests that expect success
@dec_traceback
def test_create_database(db, db_name):
    db.create(db_name)
    print 'PASS - created db'

@dec_traceback
def test_create_table(db, name, fields):
    table = db.create_table(name, fields)
    print 'PASS - created table'
    return table

@dec_traceback
def test_insert_into(table, **kwargs):
    row = table.insert_into(**kwargs)
    print 'PASS - inserted row'
    return row


if __name__ == '__main__':
    ### TODO: Read credentials from user maybe?
    
    if len(sys.argv) < 3:
        print 'USAGE: %s EMAIL PASSWORD' % sys.argv[0]
        sys.exit(1)

    email, password = sys.argv[1:]

    ### Begin testing

    ## Set things up
    client = objects.Client(email, password)
    db = objects.Database(client)

    ## We'll be creating a simple user database
    fields = ('uid', 'username', 'password')

    ## Can not create table before db
    test_fail_create_table(db, 'user', fields)

    ## So we create a database, fail
    test_fail_create_database(db, '')

    ## And we succeed
    test_create_database(db, 'Test Application')

    ## And we succeed in creating a table
    table = test_create_table(db, 'user', fields)

    ## And we insert into it
    row = test_insert_into(table, uid=1, username='user1', password='pass1')

    ## Access something
    assert row.data['uid'] == u'1', 'uid should be 1, as unicode'

# EOF

