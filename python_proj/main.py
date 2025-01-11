import functions_framework
import firebase_admin
from firebase_admin import credentials, db

def add_server_log(server_name: str):
    print('begin')
    try:
        cred = credentials.Certificate("fresh-mint.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://fresh-mint.firebaseio.com/'
            # Firebase Realtime Database URL
        })

        # As an admin, the app has access to read and write all data, regradless of Security Rules
        ref = db.reference('servers/server1')

        print('Reference obtained')
        data = ref.get()
        print('Data retrieved:', data)
    except Exception as e:
        print('Error:', e)
    print('end')



@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'name' in request_json:
        name = request_json['name']
    elif request_args and 'name' in request_args:
        name = request_args['name']
    else:
        name = 'World'

    return 'Hello {}!'.format(name)

add_server_log('server1')