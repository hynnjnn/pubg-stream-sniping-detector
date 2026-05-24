import json
import os

def save_json(data, filename, folder_path="."):
    full_path = os.path.join(folder_path, filename)

    os.makedirs(folder_path, exist_ok=True)

    if data is None:
        print("🚨 데이터가 없습니다. 함수를 종료합니다.")
        return
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ 데이터가 '{full_path}' 파일에 성공적으로 저장되었습니다.")
    except IOError as e:
        print(f"❌ 파일 저장 중 오류가 발생했습니다: {e}")


def load_json(filename, folder_path="."):
    full_path = os.path.join(folder_path, filename)

    if not os.path.exists(full_path):
        print(f"⚠️ 경고: 파일 '{full_path}'을(를) 찾을 수 없습니다.")
        return None  # 파일을 찾지 못하면 None을 반환

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            player_data = json.load(f)
        print(f"✅ '{full_path}' 파일에서 데이터를 성공적으로 로드했습니다.")
        return player_data
    except FileNotFoundError:
        print(f"❌ 오류: '{full_path}' 파일을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 오류: '{full_path}' 파일의 JSON 형식이 올바르지 않습니다. {e}")
        return None
    except Exception as e:
        print(f"❌ 알 수 없는 오류가 발생했습니다: {e}")
        return None