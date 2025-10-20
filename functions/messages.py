from firebase_functions.https_fn import on_request, Request, Response
from firebase_functions.firestore_fn import on_document_created, Event, DocumentSnapshot
from google.cloud.firestore import Client
from firebase_admin import firestore

@on_request()
def addmessage(req: Request) -> Response:
    """Take the text parameter passed to this HTTP endpoint and insert it into
    a new document in the messages collection."""
    # Grab the text parameter.
    original = req.args.get("text")
    if original is None:
        return Response("No text parameter provided", status=400)

    firestore_client: Client = firestore.client()

    # Push the new message into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("messages").add({"original": original})

    # Send back a message that we've successfully written the message
    return Response(f"Message with ID {doc_ref.id} added.")

@on_document_created(document="messages/{pushId}")
def makeuppercase(event: Event[DocumentSnapshot | None]) -> None:
    """Listens for new documents to be added to /messages. If the document has
    an "original" field, creates an "uppercase" field containg the contents of
    "original" in upper case."""

    # Get the value of "original" if it exists.
    if event.data is None:
        return
    try:
        original = event.data.get("original")
    except KeyError:
        # No "original" field, so do nothing.
        return

    # Set the "uppercase" field.
    print(f"Uppercasing {event.params['pushId']}: {original}")
    upper = original.upper()
    event.data.reference.update({"uppercase": upper})