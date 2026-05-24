import os
import numpy as np
import pandas as pd
from maps import maps
from json_handler import load_json, save_json


def mask_player_name(name, streamer_name="50091kg"):
    """
    유저 닉네임의 뒤쪽 절반을 마스킹 처리

    스트리머 이름은 마스킹하지 않고 그대로 유지
    """
    if not name or name == streamer_name:
        return name

    name_str = str(name)
    length = len(name_str)

    mask_length = length // 2

    visible_length = length - mask_length
    return name_str[:visible_length] + ("*" * mask_length)


def append_player_positions_to_csv(
    telemetry_data, csv_filename, match_id, streamer_name="50091kg"
):
    """
    배틀그라운드 텔레메트리 데이터에서 플레이어 위치 정보('LogPlayerPosition')를 추출
    
    유저별 타임스탬프와 가장 가까운 스트리머의 좌표를 추적하여 거리 계산
    """
    player_positions = []

    # 맵 이름 및 최대 좌표
    map_code = next(
        (item["mapName"] for item in telemetry_data if "mapName" in item), None
    )
    map_info = maps.get(map_code, {})
    map_name = map_info.get("map_name", map_code)
    max_coord = map_info.get("max_coord", 816000)

    # 플레이어 위치 이벤트 추출
    for item in telemetry_data:
        if item.get("_T") == "LogPlayerPosition":
            common = item.get("common", {})

            # 대기실 / 비행기기 데이터 제외
            is_game_val = common.get("isGame", 0)
            if is_game_val < 0.5:
                continue

            character = item.get("character", {})
            location = character.get("location", {})

            # 플레ㅇ이어 이름 마스킹 처리
            raw_name = character.get("name")
            masked_name = mask_player_name(raw_name, streamer_name)

            player_data = {
                "match_id": match_id,
                "timestamp": item.get("_D"),
                "player_name": masked_name,
                "x": location.get("x"),
                "y": location.get("y"),
                "cal_y": (
                    max_coord - location.get("y")
                    if location.get("y") is not None
                    else None
                ),
                "is_game": is_game_val,
                "map_name": map_name,
            }
            player_positions.append(player_data)

    if not player_positions:
        print(
            f"⚠️ 경고: '{match_id}' 매치에 조건(is_game >= 0.5)을 만족하는 데이터가 없습니다."
        )
        return

    # DataFrame 변환 및 시계열 정렬
    df = pd.DataFrame(player_positions)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # 스트리머 데이터 분리 및 유효성 검사
    streamer_df = df[df["player_name"] == streamer_name].copy()

    # 스트리머 로그 없는 매치 무시시
    if streamer_df.empty:
        print(
            f"❌ 제외됨: [{match_id}] 매치 내에 스트리머('{streamer_name}') 로그가 없어 기록하지 않고 패스합니다."
        )
        return

    # 스트리머 사망 이후 데이터 제거
    last_streamer_timestamp = streamer_df["timestamp"].max()
    df = df[df["timestamp"] <= last_streamer_timestamp].copy()

    streamer_df = df[df["player_name"] == streamer_name].copy()

    # merge를 위한 스트리머 좌표 테이블
    streamer_coords = (
        streamer_df[["timestamp", "x", "y"]]
        .rename(columns={"x": "streamer_x", "y": "streamer_y"})
        .sort_values(by="timestamp")
    )

    # pd.merge_asof (허용 오차 12초)
    df = pd.merge_asof(
        df,
        streamer_coords,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(seconds=12),
    )

    # 허용 오차 12초 초과 데이터 존재 여부 확인
    missing_streamer_count = df["streamer_x"].isna().sum()
    if missing_streamer_count > 0:
        print(
            f"⚠️ 경고: [{match_id}] 매치 내 {missing_streamer_count}개의 유저 로그가 스트리머와 시간 오차 12초를 초과 (거리 계산 제외)"
        )

    # 거리 계산
    valid_rows = df["streamer_x"].notna() & df["streamer_y"].notna()
    df["distance_meters"] = np.nan
    df.loc[valid_rows, 'distance_meters'] = (
        np.sqrt(
            (df.loc[valid_rows, "x"] - df.loc[valid_rows, "streamer_x"]) ** 2
            + (df.loc[valid_rows, "y"] - df.loc[valid_rows, "streamer_y"]) ** 2
        )
        / 100
    )

    # 임시 결합했던 스트리머 좌표 컬럼 제거
    df = df.drop(columns=["streamer_x", "streamer_y"])

    if df.empty:
        print(f"⚠️ 알림: [{match_id}] 필터링 후 남은 데이터가 없습니다.")
        return

    # 정렬 및 저장
    df = df.sort_values(by=["player_name", "timestamp"]).reset_index(drop=True)
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    file_exists = os.path.exists(csv_filename)
    df.to_csv(
        csv_filename,
        mode="a",
        index=False,
        header=not file_exists,
        encoding="utf-8-sig",
    )

    print(
        f"✅ [{match_id}] 근접 시간 보정 거리 계산 및 유저 마스킹 완료! 데이터 저장 완료."
    )

    return None


if __name__ == "__main__":
    target_user = "50091kg"
    telemetry_data_path = r"StopStreamSniping\telemetry_data\\" + target_user

    output_dir = r"StopStreamSniping\position_data\\" + target_user
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_csv_path = os.path.join(output_dir, "result_positions_combined_tmp.csv")

    if os.path.exists(output_csv_path):
        os.remove(output_csv_path)
        print(f"🧹 기존 통합 CSV 파일 삭제 완료: {output_csv_path}")

    if os.path.exists(telemetry_data_path):
        file_names = [
            f
            for f in os.listdir(telemetry_data_path)
            if os.path.isfile(os.path.join(telemetry_data_path, f))
        ]
        print(f"처리할 파일 개수: {len(file_names)}")

        for file_name in file_names:
            tele_data = load_json(file_name, telemetry_data_path)
            match_id_from_file = file_name[:-5]

            append_player_positions_to_csv(
                tele_data,
                output_csv_path,
                match_id_from_file,
                streamer_name=target_user,
            )

        print(
            f"\n🎉 모든 매치 데이터 마스킹 결합 및 거리 계산이 완료되었습니다!\n📍 경로: {output_csv_path}"
        )
    else:
        print(f"경로가 존재하지 않습니다: {telemetry_data_path}")