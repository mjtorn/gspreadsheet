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

    def __init__(self, client, key=None):
        """Constructor, client is an external client we can reuse
        """

        self.client = client

        ## Emtpy tables; set SpreadsheetsWorksheetsFeed
        self.tables = None

        if key is None:
            ## Set by create() or open()
            self.db = None

            ## This is an identifier for our spreadsheet, so tables can be added correctly
            # Dependant on db
            self.key = None
        else:
            self.open(key)

    def refresh_tables(self):
        """Method that updates the db's tables (SpreadsheetsWorksheetsFeed)
        """

        if self.key is None:
            raise AttributeError('Can not refresh tables on uninitialised db')

        self.tables = self.client.ssclient.GetWorksheetsFeed(self.key)

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

        ## Make sure internal book-keeping is ok
        self.refresh_tables()

    def open(self, key):
        """Open an existing spreadsheet
        """

        ## Set our key
        self.key = key

        base_uri = r'/feeds/documents/private/full/spredsheet%%3A%s' % self.key

        ## Set also the "db"
        self.db = self.client.docsclient.GetDocumentListEntry(base_uri)

        ## Make sure internal book-keeping is ok
        self.refresh_tables()

    def create_table(self, name, fields):
        """Create a new worksheet-table with given fields
        """

        if not self.db:
            raise AttributeError('Create a database first!')

        table = Table(self)

        table.create(name, fields)

        ## Make sure internal book-keeping is ok
        self.refresh_tables()

        return table

    def open_table(self, name):
        """Retrieve table
        """

        try:
            worksheet = [t for t in self.tables.entry if t.title.text == name][0]

            ## Fake us a Table instance from that
            table = Table(self)

            table.worksheet = worksheet

            # Create its worksheet id
            id_parts = table.worksheet.id.text.split('/')
            table.worksheet_id = id_parts[-1]

            ### TODO: Figure out how to get fields from empty (fields-only) table
            ## Cheat the fields
            #row = table.get_row(1)
            
            ## The return is a dictionary, with titles and gdata.spreadsheet.Custom instances
            #table.fields = row.row.custom.keys()

            ## Make sure this does not remain dangling anywhere
            #del row

            return table
        except IndexError:
            raise AttributeError('Table "%s" not found' % name)


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
        Give the data as keyword arguments, eg insert_into(uid=1, username='foo')
        """

        if not self.worksheet:
            raise AttributeError('Create a worksheet first!')

        ## TODO: Figure out how to get fields out of an empty table!
        #for key in kwargs.keys():
        #    if not key in self.fields:
        #        raise KeyError('Table does not accept key "%s"' % key)

        row = Row(self)

        row.create(**kwargs)

        return row

    def get_row(self, row_num):
        """Get a row by number; 1-indexed
        """

        qry = gdata.spreadsheet.service.ListQuery()
        qry.start_index = unicode(row_num)
        qry.max_results = '1'

        res = self.client.ssclient.GetListFeed(self.key, wksht_id=self.worksheet_id, query=qry)

        if len(res.entry):
            row = Row(self)

            ## Set the real data as if we were just created
            row.row = res.entry[0]

            ## Populate the data dictionary too
            for label, bob in row.row.custom.items():
                row.data[label] = bob.text

            return row

        raise ValueError('No such row')


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

