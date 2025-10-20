from firebase_functions.https_fn import on_call, CallableRequest, HttpsError, FunctionsErrorCode
from firebase_functions.firestore_fn import Event, DocumentSnapshot
from google.cloud.firestore import Client, SERVER_TIMESTAMP
from firebase_admin import firestore
from random import shuffle, choice

@on_call()
def create_game(req: CallableRequest) -> dict:
    """Create a new game for this user and their opponent saved to the database"""
    # Grab the text parameter.
    user = req.data['user']
    opponent = req.data['opponent']
    if user is None or opponent is None:
        raise HttpsError(message="Players not provided", code=FunctionsErrorCode.INVALID_ARGUMENT)
    
    firestore_client: Client = firestore.client()

    game = {
        "blocks": build_grid(),
        "turn": user,
        "players": [user, opponent],
        "usedWords":[],
        "blueScore":0,
        "redScore":0,
        "lastMove": SERVER_TIMESTAMP
    }

    # Push the new message into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("games").add(game)
    game['id'] = doc_ref.id
    # Can't serialize the timestamp sentinel
    del game['lastMove']
    # Send back the created game
    return game

def build_grid()  -> list[dict[str]]:
    base_dice = ["AAEEGN","ELRTTY","AOOTTW","ABBJOO","EHRTVW","CIMOTU","DISTTY","EIOSST","DELRVY","ACHOPS","HIMNQU","EEINSU","EEGHNW","AFFKPS","HLNNRZ","DEILRX","AAEEGN","ACHOPS","AFFKPS","DEILRX","DELRVY","EEGHNW","EIOSST","HIMNQU","HLNNRZ",
        ]
    shuffle(base_dice)
    return [
        {
            "letter":choice(die),
            "index":i,
            "allegiance":'none',
            "clicked":False
        }
        for i,die in enumerate(base_dice)]
