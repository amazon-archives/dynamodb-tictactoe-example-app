# Copyright 2014. Amazon Web Services, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from boto.exception         import JSONResponseError
from boto.dynamodb2.fields  import KeysOnlyIndex
from boto.dynamodb2.fields  import GlobalAllIndex
from boto.dynamodb2.fields  import HashKey
from boto.dynamodb2.fields  import RangeKey
from boto.dynamodb2.layer1  import DynamoDBConnection
from boto.dynamodb2.table   import Table

def getDynamoDBConnection(config=None, endpoint=None, port=None, local=False):
    if local:
        
        db = DynamoDBConnection(   
            host=endpoint,
            port=port,
            aws_secret_access_key='ticTacToeSampleApp', 
            aws_access_key_id='ticTacToeSampleApp',   
            is_secure=False)
    else:
        if config is not None:
            params = {
                'region': config.get('dynamodb', 'region'),
                'host': config.get('dynamodb', 'endpoint'),
                'is_secure': True
                }
            if endpoint is not None:
                params['host'] = endpoint
                del params['region']
            if config.has_option('dynamodb', 'aws_access_key_id'):
                params['aws_access_key_id'] = config.get('dynamodb', 'aws_access_key_id')
                params['aws_secret_access_key'] = config.get('dynamodb', 'aws_secret_access_key')

            db = DynamoDBConnection(**params)
        else:
            if endpoint:
                db = DynamoDBConnection(host=endpoint)
            else:
                db = DynamoDBConnection()
    return db

def createGamesTable(db):

    try:
        hostStatusDate = GlobalAllIndex("hostStatusDate", parts=[HashKey("HostId"),
                                                                RangeKey("StatusDate")])
        opponentStatusDate  = GlobalAllIndex("opponentStatusDate", parts=[HashKey("OpponentId"),
                                                                RangeKey("StatusDate")]) 

        #global secondary indexes
        GSI = [hostStatusDate, opponentStatusDate]

        gamesTable = Table.create("Games",
                    schema=[HashKey("GameId")],
                    throughput={
                        'read':1,
                        'write':1
                    },
                    global_indexes=GSI,
                    connection=db)

    except JSONResponseError, jre:
        try:
            gamesTable = Table("Games", connection=db)
        except Exception, e:
            print "Games Table doesn't exist."
    finally:
        return gamesTable 

#parse command line args for credentials and such
#for now just assume local is when args are empty
