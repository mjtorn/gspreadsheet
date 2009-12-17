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

        table = Table(self)

        table.create(name, fields)

        return table

class Table(object):
    """Table object
    """

    def __init__(self, db_instance):
        """Create a Table instance for db, call create() to actually create it
        """

        self.db = db_instance

        # Set some shortcuts for ease
        self.client = self.db.client
        self.key = self.db.key

        # And this is to come
        self.worksheet = None
        self.worksheet_id = None

        # This must be populated by create, maybe in the future also by get
        self.fields = None

    def create(self, name, fields):
        """Create remote table
        """

        self.fields = fields

        ## Defaults
        row_count = 1
        col_count = len(fields)

        self.worksheet = self.client.ssclient.AddWorksheet(name, row_count, col_count, self.key)

        # Create our worksheet id
        id_parts = self.worksheet.id.text.split('/')
        self.worksheet_id = id_parts[-1]

        ## Apparently Google Spreadsheet sucks enough to use row 1 as titles
        i = 0
        for column in self.fields:
            i += 1
            self.client.ssclient.UpdateCell(1, i, column, self.key, self.worksheet_id)

    def insert_into(self, **kwargs):
        """Insert a new row
        """

        if not self.worksheet or not self.fields:
            raise AttributeError('Create a worksheet first!')

        row = Row(self)

        row.create(**kwargs)

        return row


class Row(object):
    """A spreadsheet row
    """

    def __init__(self, table):
        """Construct row with references to table
        """

        self.table = table
        self.db = table.db

        ## Lots of shortcutting
        # "Connection"
        self.client = self.db.client
        self.key = self.db.key

        # Table object
        self.worksheet = self.table.worksheet
        self.worksheet_id = self.table.worksheet_id

        # Addressing
        self.fields = self.table.fields

        ## And something to come later
        self.row = None
        self.data = {}

    def create(self, **kwargs):
        """Inesrt data appropriately into row
        """

        for k, v in kwargs.items():
            kwargs[k] = unicode(v)

        self.row = self.client.ssclient.InsertRow(kwargs, self.key, wksht_id=self.worksheet_id)

        self.data = kwargs

# EOF

