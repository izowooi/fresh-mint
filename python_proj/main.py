import functions_framework
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime


def update_server_access(server_name: str):
    cred = credentials.Certificate("fresh-mint.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://fresh-mint.firebaseio.com/'
        # Firebase Realtime Database URL
    })

    ref = db.reference(f'servers/{server_name}')  # 특정 서버 이름의 경로를 참조
    print(f"Reference obtained for server: {server_name}")

    data = ref.get()  # 서버 데이터를 가져옴
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 현재 시간
    if data:
        print(f"Existing server data: {data}")
        if "access_date" in data:
            data["access_date"].append(current_time)
        else:
            data["access_date"] = [current_time]
        ref.update(data)
    else:
        print(f"No data for server: {server_name}. Initializing default data.")
        default_data = {
            "access_date": [current_time],
            "description": f"This is {server_name}",
            "name": server_name
        }
        ref.set(default_data)
    print(f"Updated data for {server_name}")



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

#add_server_log('server2')
update_server_access("server1")  # 기존 서버 업데이트
