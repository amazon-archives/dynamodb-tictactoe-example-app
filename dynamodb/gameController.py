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
from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from boto.dynamodb2.exceptions import ItemNotFound
from boto.dynamodb2.exceptions import ValidationException
from boto.dynamodb2.items   import Item
from boto.dynamodb2.table   import Table
from datetime               import datetime

class GameController:
    """
    This GameController class basically acts as a singleton providing the necessary
    DynamoDB API calls.
    """
    def __init__(self, connectionManager):
        self.cm = connectionManager
        self.ResourceNotFound = 'com.amazonaws.dynamodb.v20120810#ResourceNotFoundException'

    def createNewGame(self, gameId, creator, invitee):
        """
        Using the High-Level API, an Item is created and saved to the table.
        All the primary keys for either the schema or an index (GameId,
        HostId, StatusDate, and OpponentId) as well as extra attributes needed to maintain
        game state are given a value.
        Returns True/False depending on the success of the save.
        """

        now = str(datetime.now())
        statusDate = "PENDING_" + now
        item = Item(self.cm.getGamesTable(), data= {
                            "GameId"     : gameId,
                            "HostId"     : creator,
                            "StatusDate" : statusDate,
                            "OUser"      : creator,
                            "Turn"       : invitee,
                            "OpponentId" : invitee
                        })

        return item.save()

    def checkIfTableIsActive(self):
        description = self.cm.db.describe_table("Games")
        status = description['Table']['TableStatus']

        return status == "ACTIVE"

    def getGame(self, gameId):
        """
        Basic get_item call on the Games Table, where we specify the primary key
        GameId to be the parameter gameId.
        Returns None on an ItemNotFound Exception.
        """
        try:
            item = self.cm.getGamesTable().get_item(GameId=gameId)
        except ItemNotFound as inf:
            return None
        except JSONResponseError as jre:
            return None

        return item

    def acceptGameInvite(self, game):
        date = str(datetime.now())
        status = "IN_PROGRESS_"
        statusDate = status + date
        key = {
                "GameId" : { "S" : game["GameId"] }
            }

        attributeUpdates = {
                        "StatusDate" : {
                            "Action" : "PUT",
                            "Value"  : { "S" : statusDate }
                            }
                        }

        expectations = {"StatusDate" : {
                            "AttributeValueList": [{"S" : "PENDING_"}],
                            "ComparisonOperator": "BEGINS_WITH"}
                    }

        try:
            self.cm.db.update_item("Games", key=key,
                        attribute_updates=attributeUpdates,
                        expected=expectations)
        except ConditionalCheckFailedException as ccfe:
            return False

        return True

    def rejectGameInvite(self, game):
        """
        Reject the game invite, by deleting the Item from the table.
        Conditional on the fact the game is still in the PENDING status.
        Returns True/False depending on success of delete.
        """

        key = {
                "GameId": { "S" : game["GameId"] }
            }
        expectation = {"StatusDate" : {
                            "AttributeValueList": [{"S" : "PENDING_"}],
                            "ComparisonOperator": "BEGINS_WITH" }
                    }

        try:
            self.cm.db.delete_item("Games", key, expected=expectation)
        except Exception as e:
            return False

        return True

    def getGameInvites(self,user):
        """
        Performs a query on the "OpponentId-StatusDate-index" in order to get the
        10 most recent games you were invited to.
        Returns a list of Game objects.
        """
        invites = []
        if user == None:
            return invites

        gameInvitesIndex = self.cm.getGamesTable().query(OpponentId__eq=user,
                                            StatusDate__beginswith="PENDING_",
                                            index="OpponentId-StatusDate-index",
                                            limit=10)


        for i in range(10):
            try:
                gameInvite = next(gameInvitesIndex)
            except StopIteration as si:
                break
            except ValidationException as ve:
                break
            except JSONResponseError as jre:
                if jre.body.get(u'__type', None) == self.ResourceNotFound:
                    return None
                else:
                    raise jre

            invites.append(gameInvite)

        return invites

    def updateBoardAndTurn(self, item, position, current_player):
        """
        Using the Low Level API, we execute a conditional write on the Item.
        We are able to specify the particular item by passing in the keys param, in
        this case it's just a GameId.
        In expectations, we expect
            the StatusDate to be IN_PROGRESS_<date of the game>,
            the Turn to be the player who is currently logged in,
            the "Space" to not exist as an attribute because it hasn't been written to yet.
        If this succeeds we update the Turn to the next player, as well.
        Returns True/False depending on the success of the these operations.
        """
        player_one = item["HostId"]
        player_two = item["OpponentId"]
        gameId     = item["GameId"]
        statusDate = item["StatusDate"]
        date = statusDate.split("_")[1]

        representation = "X"
        if item["OUser"] == current_player:
            representation = "O"

        if current_player == player_one:
            next_player = player_two
        else:
            next_player = player_one

        key = {
                "GameId" : { "S" : gameId }
            }

        attributeUpdates = {
                        position : {
                            "Action" : "PUT",
                            "Value"  : { "S" : representation }
                            },
                        "Turn" : {
                            "Action" : "PUT",
                            "Value" : { "S" : next_player }
                            }
                        }


        expectations = {"StatusDate" : {"AttributeValueList": [{"S" : "IN_PROGRESS_"}],
                                        "ComparisonOperator": "BEGINS_WITH"},
                        "Turn"       : {"Value" : {"S" : current_player}},
                        position     : {"Exists" : False}}

        # LOW LEVEL API
        try:
            self.cm.db.update_item("Games", key=key,
                        attribute_updates=attributeUpdates,
                        expected=expectations)
        except ConditionalCheckFailedException as ccfe:
            return False

        return True


    def getBoardState(self, item):
        """
        Puts the state of the board into a list, putting a blank space for
        spaces that are not occupied.
        """
        squares = ["TopLeft", "TopMiddle", "TopRight", "MiddleLeft", "MiddleMiddle", "MiddleRight", \
                    "BottomLeft", "BottomMiddle", "BottomRight"]
        state = []
        for square in squares:
            value = item[square]
            if value == None:
                state.append(" ")
            else:
                state.append(value)

        return state

    def checkForGameResult(self, board, item, current_player):
        """
        Check the board to see if you've won,lost tied or in progress.
        Returns "Win", "Loss", "Tie" or None (for in-progress)
        """
        yourMarker = "X"
        theirMarker = "O"
        if current_player == item["OUser"]:
            yourMarker = "O"
            theirMakrer = "X"

        winConditions = [[0,3,6],[0,1,2],[0,4,8],
                        [1,4,7],[2,5,8],[2,4,6],
                        [3,4,5],[6,7,8]]

        for winCondition in winConditions:
            b_zero = board[winCondition[0]]
            b_one  = board[winCondition[1]]
            b_two  = board[winCondition[2]]
            if b_zero == b_one and \
                b_one == b_two and \
                b_two == yourMarker:
                    return "Win"

            if b_zero == b_one and \
                b_one == b_two and \
                b_two == theirMarker:
                    return "Lose"

        if self.checkForTie(board):
            return "Tie"

        return None

    def checkForTie(self, board):
        """
        Checks the boardState to see if there are any empty spaces which would
        signify that the game hasn't come to a stalemate yet.
        """
        for cell in board:
            if cell == " ":
                return False
        return True

    def changeGameToFinishedState(self, item, result, current_user):
        """
        This game verifies whether a game has an outcome already and if not
        sets the StatusDate to FINISHED_<date> and fills the Result attribute
        with the name of the winning player.
        Returns True/False depending on the success of the operation.
        """

        #Happens if you're visiting a game that already has a winner
        if item["Result"] != None:
            return True

        date = str(datetime.now())
        status = "FINISHED"
        item["StatusDate"] = status + "_" + date
        item["Turn"] = "N/A"

        if result == "Tie":
            item["Result"] = result
        elif result == "Win":
            item["Result"] = current_user
        else:
            if item["HostId"] == current_user:
                item["Result"] = item["OpponentId"]
            else:
                item["Result"] = item["HostId"]

        return item.save()

    def mergeQueries(self, host, opp, limit=10):
        """
        Taking the two iterators of games you've played in (either host or opponent)
        you sort through the elements taking the top 10 recent games into a list.
        Returns a list of Game objects.
        """
        games = []
        game_one = None
        game_two = None
        while len(games) <= limit:
            if game_one == None:
                try:
                    game_one = next(host)
                except StopIteration as si:
                    if game_two != None:
                        games.append(game_two)

                    for rest in opp:
                        if len(games) == limit:
                            break
                        else:
                            games.append(rest)
                    return games

            if game_two == None:
                try:
                    game_two = next(opp)
                except StopIteration as si:
                    if game_one != None:
                        games.append(game_one)

                    for rest in host:
                        if len(games) == limit:
                            break
                        else:
                            games.append(rest)
                    return games

            if game_one > game_two:
                games.append(game_one)
                game_one = None
            else:
                games.append(game_two)
                game_two = None

        return games

    def getGamesWithStatus(self, user, status):
        """
        Query for all games that a user appears in and have a certain status.
        Sorts/merges the results of the two queries for top 10 most recent games.
        Return a list of Game objects.
        """

        if user == None:
            return []

        hostGamesInProgress = self.cm.getGamesTable().query(HostId__eq=user,
                                            StatusDate__beginswith=status,
                                            index="HostId-StatusDate-index",
                                            limit=10)

        oppGamesInProgress = self.cm.getGamesTable().query(OpponentId__eq=user,
                                            StatusDate__beginswith=status,
                                            index="OpponentId-StatusDate-index",
                                            limit=10)

        games = self.mergeQueries(hostGamesInProgress,
                                oppGamesInProgress)
        return games
