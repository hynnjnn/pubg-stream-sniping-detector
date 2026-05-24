from config import base_url, headers
from json_handler import save_json, load_json
import json
import requests

def get_player_by_name(player_name):
    """
    플레이어 이름으로 플레이어 정보를 조회하는 함수
    """
    # 플레이어 검색 URL
    search_url = f"{base_url}/players"
    
    # 쿼리 파라미터
    params = {"filter[playerNames]": player_name}
    
    print(f"플레이어 '{player_name}' 검색 중...")
    print(f"URL: {search_url}")
    print(f"파라미터: {params}")
    
    try:
        # API 요청
        response = requests.get(search_url, headers=headers, params=params)
        
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 플레이어 데이터 확인
            if data.get('data') and len(data['data']) > 0:
                player = data['data'][0]
                print(f"✅ 성공! 플레이어를 찾았습니다.")
                print(f"플레이어 ID: {player['id']}")
                print(f"플레이어 이름: {player['attributes']['name']}")
                
                # 전체 응답 데이터도 출력
                # print("\n전체 응답 데이터:")
                # print(json.dumps(data, indent=2, ensure_ascii=False))
                
                return player
            else:
                print(f"❌ 플레이어 '{player_name}'를 찾을 수 없습니다.")
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


def get_player_stats(player_id):
    """
    플레이어 통계 정보를 가져오는 함수
    """
    stats_url = f"{base_url}/players/{player_id}/seasons/lifetime"
    
    try:
        response = requests.get(stats_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("\n플레이어 통계:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"통계 조회 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"통계 조회 네트워크 오류: {e}")
        return None


if __name__ == "__main__":
    
    print("\n" + "="*50)
    player_name = "50091"
    folder_name = "StopStreamSniping\player_data"
    
    print(f"플레이어 '{player_name}' 정보를 조회합니다...")
    player = get_player_by_name(player_name)

    save_json(player, player_name+'_data.json', folder_name)

    # player = load_json(player_name+'_data.json', folder_name)

    # matches = player['relationships']['matches']['data']

    print("완료")