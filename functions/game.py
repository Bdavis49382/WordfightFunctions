from firebase_functions.https_fn import on_request, Request, Response
from firebase_functions.firestore_fn import on_document_created, Event, DocumentSnapshot
from google.cloud.firestore import Client, SERVER_TIMESTAMP
from firebase_admin import firestore
from random import shuffle, choice

@on_request()
def create_game(req: Request) -> Response:
    """Create a new game for this user and their opponent saved to the database"""
    # Grab the text parameter.
    user = req.args.get("user")
    opponent = req.args.get("opponent")
    if user is None or opponent is None:
        return Response("Players not provided", status=400)

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
    _, doc_ref = firestore_client.collection("messages").add(game)
    game['id'] = doc_ref
    # Send back the created game
    return Response(game.__str__())

def build_grid()  -> list[dict[str]]:
    base_dice = ["AAEEGN","ELRTTY","AOOTTW","ABBJOO","EHRTVW","CIMOTU","DISTTY","EIOSST","DELRVY","ACHOPS","HIMNQU","EEINSU","EEGHNW","AFFKPS","HLNNRZ","DEILRX","AAEEGN","ACHOPS","AFFKPS","DEILRX","DELRVY","EEGHNW","EIOSST","HIMNQU","HLNNRZ",
        ]
    shuffle(base_dice)
    return [
        {
            "letter":choice(die),
            "index":i,
            "allegiance":'none',
            "clicked":'false'
        }
        for i,die in enumerate(base_dice)]
