# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

import gdata.docs.service
import gdata.spreadsheet.service

class Client(object):
    """Unified client wraps around both docs and spreadsheet client
    """

    def __init__(self, email, password):
        """Authentication
        """

        self.ssclient = gdata.spreadsheet.service.SpreadsheetsService(email=email, password=password)
        self.docsclient = gdata.docs.service.DocsService(email=email, password=password)

        self.ssclient.ProgrammaticLogin()
        self.docsclient.ProgrammaticLogin()

class Database(object):
    """Spreadsheet-Database
    """

    def __init__(self, client):
        """Constructor, client is an external client we can reuse
        """

        self.client = client

        ## TODO: Maybe we could have the db name in the constructor
        ## and do a get_or_create kind of number on it?
        self.db = None

        ## This is an identifier for our spreadsheet, so tables can be added correctly
        # Dependant on db
        self.key = None

    def create(self, name, data=',,,'):
        """Create a new spreadsheet-database identified by name, containing data from file ob/string
        """

        if not name or not isinstance(name, basestring):
            raise ValueError('Require textual, non-zero-length name')

        if not isinstance(data, file):
            from cStringIO import StringIO

            data = StringIO(data)

        clen = len(data.read())
        data.seek(0)

        data_source = gdata.MediaSource(file_handle=data, content_type='text/csv', content_length=clen)

        db = self.client.docsclient.Upload(data_source, name, label='Spreadsheet')

        self.db = db
        
        ## Create also the key
        id_parts = self.db.id.text.split('/')
        self.key = id_parts[-1].replace('spreadsheet%3A', '')

    def create_table(self, name, fields):
        """Create a new worksheet-table with given fields
        """

        if not self.db:
            raise AttributeError('Create a database first!')

        ## Defaults
        row_count = 1
        col_count = len(fields)

        self.client.ssclient.AddWorksheet(name, row_count, col_count, self.key)

# EOF

