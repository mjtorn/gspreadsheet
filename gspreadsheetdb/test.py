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

@dec_traceback
def test_fail_open_table(db, table_name):
    try:
        db.open_table(table_name)
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
def test_open_table(db, table_name):
    table = db.open_table(table_name)
    print 'PASS - opened table'
    return table

@dec_traceback
def test_insert_into(table, **kwargs):
    row = table.insert_into(**kwargs)
    print 'PASS - inserted row'
    return row

@dec_traceback
def test_open_empty_table(db, other_db, table_name):
    table = db.create_table(table_name, ('foo', 'bar', 'baz'))
    other_db.refresh_tables()
    return other_db.open_table(table_name)

@dec_traceback
def test_insert_and_get_row(table):
    table.insert_into(foo='This row is required')
    r = table.get_row(1)
    return r

@dec_traceback
def test_user_manipulation(table):
    table.insert_into(uid=2, username='user2', password='pass1')
    print 'PASS - inserted user'
    table.insert_into(uid=3, username='user3', password='pass3')
    print 'PASS - inserted user'

    users = table.filter()
    assert len(users) == 3, '%d users, not 3?' % len(users)
    print 'PASS - Has 3 users'

    users = table.filter(reverse=True, orderby='uid', password='pass1')
    assert len(users) == 2, '2 users should have pass1, not %d' % len(users)
    print 'PASS - Retrieved 2 users'

    specific_user = table.filter(uid=2)[0]

    other_instance_user = users[0]

    # Succeed update
    specific_user.update(username='lol', password='pass2')
    print 'PASS - First instance updated user'

    # Race and fail
    try:
        other_instance_user.update(username='user2', password='pass2')
        print 'FAILED should have failed'
        sys.exit(1)
    except objects.RequestError, e:
        assert e.message['status'] == 409, 'Bad status %s' % e.message['status']
        print 'PASS - Failed racy update'

    # Correct username here
    specific_user.update(username='user2')
    print 'PASS - Updated user'

@dec_traceback
def test_ok_users(table):
    users = table.filter(orderby='uid')

    for i in xrange(len(users)):
        n = i + 1
        n = str(n)
        user = users[i]
        assert user.data['uid'] == n
        assert user.data['username'] == 'user%s' % n
        assert user.data['password'] == 'pass%s' % n

        print 'PASS - user%s ok' % n

@dec_traceback
def test_random_user(table):
    user = table.get_random()

    print 'PASS - got user %s' % user

if __name__ == '__main__':
    ### TODO: Read credentials from user maybe?
    
    if len(sys.argv) < 3:
        print 'USAGE: %s EMAIL PASSWORD' % sys.argv[0]
        sys.exit(1)

    email, password = sys.argv[1:]

    ### Begin testing

    ## Set things up
    db = objects.Database(email, password)

    ## We'll be creating a simple user database
    fields = ('uid', 'username', 'password')

    ## Can not create table before db
    test_fail_create_table(db, 'user', fields)

    ## So we create a database, fail
    test_fail_create_database(db, '')

    ## And we succeed
    test_create_database(db, 'Test Application')

    print 'Database key %s' % db.key

    ## And we succeed in creating a table
    table = test_create_table(db, 'user', fields)

    ## And we insert into it
    row = test_insert_into(table, uid=1, username='user1', password='pass1')

    ## Access something
    assert row.data['uid'] == u'1', 'uid should be 1, as unicode'

    ## Open a second connection
    # Reuse the db key from the previous instance
    other_db = objects.Database(email, password, key=db.key)

    ## Table opening
    # First test a fail
    test_fail_open_table(other_db, 'test_does_not_exist')
    # Then a success
    table = test_open_table(other_db, 'user')

    ## Harder-core test
    t = test_open_empty_table(db, other_db, 'test')
    r = test_insert_and_get_row(t)

    ## Test adding some users
    test_user_manipulation(table)

    ## Assert stuff
    test_ok_users(table)

    ## Random?
    test_random_user(table)

# EOF

