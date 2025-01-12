import functions_framework
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

CREDENTIALS_PATH = "fresh-mint.json"  # Firebase 인증 파일 경로
DATABASE_URL = "https://fresh-mint.firebaseio.com/"  # Firebase 실시간 DB URL
SERVERS_PATH = "servers"  # 서버 정보가 저장되는 RTDB 루트 경로


def initialize_firebase(credentials_file: str = CREDENTIALS_PATH, database_url: str = DATABASE_URL) -> None:
    if not firebase_admin._apps:
        cred = credentials.Certificate(credentials_file)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
    print("Firebase initialized")

def append_access_date(ref, data: dict, current_time: str) -> dict:
    if "access_date" in data:
        data["access_date"].append(current_time)
    else:
        data["access_date"] = [current_time]
    return data

def create_new_server_data(server_name: str, current_time: str) -> dict:
    return {
        "access_date": [current_time],
        "description": f"This is {server_name}",
        "name": server_name
    }

def update_server_access(server_name: str) -> str:
    try:
        ref = db.reference(f"{SERVERS_PATH}/{server_name}")
        print(f"Reference obtained for server: {server_name}")

        existing_data = ref.get()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if existing_data and isinstance(existing_data, dict):
            print(f"Existing server data: {existing_data}")
            updated_data = append_access_date(ref, existing_data, current_time)
            ref.update(updated_data)
            return f"[SUCCESS] '{server_name}' updated with access_date {current_time}"
        else:
            print(f"No data for server: {server_name}. Creating new data.")
            new_data = create_new_server_data(server_name, current_time)
            ref.set(new_data)
            return f"[SUCCESS] New data created for '{server_name}' with initial access_date {current_time}"
    except Exception as e:
        error_msg = f"[ERROR] Failed to update server '{server_name}': {e}"
        print(error_msg)
        return error_msg

def test_update_server_access(server_name: str) -> None:
    initialize_firebase()
    print(update_server_access(server_name))

@functions_framework.http
def update_server_access_http(request):
    initialize_firebase()

    request_json = request.get_json(silent=True)
    request_args = request.args

    if (not request_json or 'server_name' not in request_json) and \
       (not request_args or 'server_name' not in request_args):
        return "[ERROR] Missing 'server_name' parameter", 400

    if request_json and 'server_name' in request_json:
        server_name = request_json['server_name']
    else:
        server_name = request_args['server_name']

    result_message = update_server_access(server_name)
    return result_message

#test_update_server_access("server1")  # 기존 서버 업데이트
