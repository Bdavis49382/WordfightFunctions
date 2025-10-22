from firebase_functions.https_fn import on_call, CallableRequest, HttpsError, FunctionsErrorCode
from firebase_functions.firestore_fn import Event, DocumentSnapshot, DocumentReference
from google.cloud.firestore import Client, SERVER_TIMESTAMP
from firebase_admin import firestore
from google.cloud.firestore_v1 import ArrayUnion
import requests


@on_call()
def submit_word(req: CallableRequest) -> dict:
    """Submits a given word made up of blocks"""
    # Grab the text parameter.
    word = req.data['word']
    game_id = req.data['gameId']
    return submit(word, game_id)

def submit(word, game_id) -> dict:
    """Submits a given word made up of blocks"""

    string_word = ''.join([block['letter'] for block in word])
    verified, message = verify_word(string_word, game_id)
    if not verified:
        raise HttpsError(message=message,code=FunctionsErrorCode.INVALID_ARGUMENT)
    
    game_ref = firestore.client().collection("games").document(game_id)

    game_ref.update({'usedWords':ArrayUnion([string_word])})
    update_colors(word, game_ref)
    return game_ref.get().to_dict()

def update_colors(word: list[dict], game_ref: DocumentReference):
    doc = game_ref.get()
    game = doc.to_dict()
    if 'blocks' not in game:
        raise HttpsError(code=500,message="game was not correctly loaded, and does not have blocks.")
    
    blocks: list[dict] = game['blocks']

    for block in word:
        changing_block = blocks[block['index']]
        # every block in word that's not surrounded should switch allegiance to the current player
        if not changing_block['surrounded']:
            changing_block['allegiance'] = game['turn']
    
    # return a boolean representing whether the given block should be solidified because all its neighbors are the same color
    def should_solidify(block, blocks):
        if block['allegiance'] == 'none':
            return False
        row = block['index'] % 5
        col = block['index'] // 5
        neighborIndices = []
        if row < 4:
            neighborIndices.append(row + 1 + col * 5) 
        if row > 0:
            neighborIndices.append(row - 1 + col * 5) 
        if col < 4:
            neighborIndices.append(row + (col + 1) * 5)
        if col > 0:
            neighborIndices.append(row + (col - 1) * 5)
        for i in neighborIndices:
            if i >= 0 and i <= 24:
                if blocks[i]['allegiance'] != block['allegiance']:
                    return False
        return True

    # solidify any surrounded blocks
    for block in blocks:
        if should_solidify(block, blocks):
            block['surrounded'] = True
            # regardless of whether the value changed, update the score because it is solid now
            if block['allegiance'] == game['players'][0]:
                game['scores'][0] += 1
            else:
                game['scores'][1] += 1
        else:
            block['surrounded'] = False
    
    game_ref.update({
        'blocks':blocks,
        'scores':game['scores'],
        'finished':max(game['scores']) >= 10,
        'turn':game['players'][1] if game['turn'] == game['players'][0] else game['players'][0],
        'lastMove':SERVER_TIMESTAMP
        })


def verify_word(word: str, game_id: str,) -> tuple[bool, str]:
    url = f'https://freedictionaryapi.com/api/v1/entries/en/{word.lower()}?translations=false&pretty=false'
    res: requests.Response = requests.get(url)

    if not res.ok:
        return False, "Verification against dictionary failed."
    
    doc = firestore.client().collection('games').document(game_id).get()

    if not doc.exists:
        return False, "Game not found."

    game = doc.to_dict()


    if word in game['usedWords']:
        return False, f"{word} has already been used in this game."
    
    data = res.json()
    if 'entries' in data and len(data['entries']) > 0:
        return True, "Verified."
    else:
        return False, f"{word} does not appear in the dictionary."