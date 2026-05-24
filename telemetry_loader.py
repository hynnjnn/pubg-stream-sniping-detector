from config import base_url, headers
from json_handler import save_json, load_json
from match_list_loader import get_match_by_id
import json
import requests


def get_telemetry_data(url):
    response = requests.get(url)
    return response.json()


# def get_player_attacks_by_name(player_name):
#     log_player_attack = []
#     telemetry_data = load_json("telemetry_data.json")
    
#     for item in telemetry_data:
#         if item['_T'] == 'LogPlayerAttack' or item['_T'] == 'LogPlayerTakeDamage':
#             if item["attacker"] and item["attacker"]["name"] == player_name:
#                 log_data = {
#                     "timestamp": item['_D'],
#                     "attacker_name": item["attacker"]["name"],
#                     "attacker_position": {
#                         "x": item["attacker"]["location"]["x"],
#                         "y": item["attacker"]["location"]["y"],
#                         "z": item["attacker"]["location"]["z"]
#                     }
#                 }
#                 if item.get('victim', []):
#                     log_data["victim_name"] = item["victim"]["name"]
#                     log_data["victim_position"] = {
#                         "x": item["victim"]["location"]["x"],
#                         "y": item["victim"]["location"]["y"],
#                         "z": item["victim"]["location"]["z"]
#                     }
#                     log_data["damage_dealt"] = int(item["damage"])
#                 print(item["attacker"]["name"])
#                 log_player_attack.append(log_data)
#     return log_player_attack


def get_match_ids_by_key(data_list, target_key):
    for item in data_list:
        key = item[0]
        value_dict = item[1]

        if key == target_key:
            return value_dict.get("match_ids", [])  # 'match_ids'가 없으면 빈 리스트 반환
    return []


if __name__ == "__main__":
    target_user = "50091"

    match_data_path = "StopStreamSniping\matches"
    telemetry_data_path = rf"StopStreamSniping\telemetry_data\{target_user}"

    matches = load_json(target_user+"_result.json", match_data_path)


    match_ids = get_match_ids_by_key(matches, target_user)
    # match_ids = ['827b6a3c-a9fa-49dc-8947-2953edc9cca7']

    # print(match_ids)

    for match_id in match_ids:
        match_data = get_match_by_id(match_id)

        # 텔레메트리 데이터 가져오기
        for item in match_data.get('included', []):
            if item.get('type') == 'asset':
                url = item.get('attributes').get('URL')
                data = get_telemetry_data(url)
                if data:
                    save_json(data, match_id+".json", telemetry_data_path)
                    print(f"✅ 텔레메트리 데이터가 '{telemetry_data_path}\{match_id}.json' 파일에 성공적으로 저장되었습니다.")
                else:
                    print(f"❌ 텔레메트리 데이터를 찾을 수 없습니다.")
