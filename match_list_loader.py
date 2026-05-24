from config import base_url, headers
from json_handler import save_json
import json
import os
import requests

def get_match_by_id(match_id):
    """
    매치 정보를 조회 함수
    """
    # 매치 검색 URL
    search_url = f"{base_url}/matches/{match_id}"
    
    print(f"매치 '{match_id}' 검색 중...")
    print(f"URL: {search_url}")
    
    try:
        # API 요청
        response = requests.get(search_url, headers=headers)
        
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 매치 데이터 확인
            if data.get('data'):
                match = data['data']
                print(f"✅ 성공! 매치를 찾았습니다.")
                print(f"매치 ID: {match['id']}")
                print(f"매치 타입: {match['type']}")
                
                # 매치 기본 정보 출력
                attributes = match.get('attributes', {})
                print(f"맵: {attributes.get('mapName', 'N/A')}")
                print(f"게임 모드: {attributes.get('gameMode', 'N/A')}")
                
                # print("\n전체 응답 데이터:")
                # print(json.dumps(data, indent=2, ensure_ascii=False))
                
                return data
            else:
                print(f"❌ 매치 '{match_id}'를 찾을 수 없습니다.")
                return None
                
        else:
            print(f"❌ API 요청 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return None

def get_multiple_matches(match_ids):
    """
    여러 매치 정보 조회
    """
    matches = []
    
    for i, match_id in enumerate(match_ids):
        print(f"\n--- 매치 {i+1}/{len(match_ids)} 조회 중 ---")
        match = get_match_by_id(match_id)
        if match:
            matches.append(match)
    
    return matches

def extract_match_participants(match_data):
    """
    매치 데이터에서 참가자 리스트를 추출하는 함수
    
    Args:
        match_data (dict): 매치 API 응답 데이터
    
    Returns:
        list: 참가자 정보 리스트 (name, playerId 포함)
    """
    participants = []
    
    try:
        # included 섹션에서 participant 타입의 데이터들을 찾기
        if 'included' in match_data:
            for item in match_data['included']:
                if item.get('type') == 'participant':
                    attributes = item.get('attributes', {})
                    stats = attributes.get('stats', {})
                    
                    if stats.get('name', 'Unknown'):
                        participants.append(stats.get('name', 'Unknown'))
        
        print(f"✅ 총 {len(participants)}명의 참가자를 찾았습니다.")
        return participants
        
    except Exception as e:
        print(f"❌ 참가자 정보 추출 중 오류 발생: {e}")
        return []


def count_participants(participants, target_user):
    result = {}

    for match_id, users in participants.items():
        if target_user not in users:
            continue

        for user in users:
            # if user == target_user:
            #     continue  # 타겟 유저 자신은 제외

            if user in result:
                result[user]['count'] += 1
                result[user]['match_ids'].append(match_id)
            else:
                result[user] = {
                    'count': 1,
                    'match_ids': [match_id]
                }

    return result


def get_matches_from_user(target_user):
    match_ids = []
    folder_name = "StopStreamSniping\player_data"
    full_path = os.path.join(folder_name, target_user+'_data.json')

    if not os.path.exists(full_path):
        print(f"⚠️ 경고: 파일 '{full_path}'을(를) 찾을 수 없습니다.")
        return None  # 파일을 찾지 못하면 None을 반환

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            player_data = json.load(f)
        
        for match in player_data['relationships']['matches']['data'][:30]:
            match_ids.append(match['id'])
        return match_ids
        
    except FileNotFoundError:
        print(target_user+"_data.json 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")




if __name__ == "__main__":
    # 최종 매치 테스트
    target_user = "50091"
    result_folder = "StopStreamSniping\matches"
    total_participants = {}

    # player_data.json에서 매치 ID들 추출
    match_ids = get_matches_from_user(target_user)

    for match_id in match_ids:
        match_data = get_match_by_id(match_id)

        if match_data:
            # 참가자 리스트 추출
            participants = extract_match_participants(match_data)
            
            if participants:
                total_participants[match_id] = participants
            else:
                print(f"❌ {match_id}의 참가자 정보를 추출할 수 없습니다.")

    result = count_participants(total_participants, target_user)

    sorted_result = sorted(result.items(), key=lambda x: x[1]['count'], reverse=True)
    
    save_json(sorted_result, target_user+"_result.json", result_folder)

    print(f'{len(match_ids)}개의 매치 결과입니다.')