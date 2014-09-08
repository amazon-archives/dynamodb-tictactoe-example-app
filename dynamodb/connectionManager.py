from setupDynamoDB          import getDynamoDBConnection, createGamesTable 
from boto.dynamodb2.table   import Table
from uuid                   import uuid4

class ConnectionManager:

    def __init__(self, mode=None, config=None, endpoint=None, port=None):
        self.db = None
        self.gamesTable = None
        
        if mode == "local":
            if config is not None:
                raise Exception('Cannot specify config when in local mode')
            if endpoint is None:
                endpoint = 'localhost'
            if port is None:
                port = 8000
            self.db = getDynamoDBConnection(endpoint=endpoint, port=port, local=True)
        elif mode == "service":
            self.db = getDynamoDBConnection(config=config, endpoint=endpoint)
        else:
            raise Exception("Invalid arguments, please refer to usage.");

        self.setupGamesTable()

    def setupGamesTable(self):
        try:
            self.gamesTable = Table("Games", connection=self.db)
        except Exception, e:
            raise e, "There was an issue trying to retrieve the Games table."

    def getGamesTable(self):
        if self.gamesTable == None:
            self.setupGamesTable()
        return self.gamesTable

    def createGamesTable(self):
        self.gamesTable = createGamesTable(self.db)
