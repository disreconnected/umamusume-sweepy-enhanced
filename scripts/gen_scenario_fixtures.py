"""Generate structural scenario fixtures for the manual-play adapters.

These fixtures document the assumed protocol shapes (chara_info, home_info,
race_start_info, free_data_set, plus the scenario containers) and drive the
adapter replay/recommendation tests and the UMA_TEST_MODE fixture transport.
They are structural stand-ins: the authoritative path is
`python -m career_bot.capture sanitize <raw.jsonl> --scenario <slug>` from a
live capture. IDs are capture-derived (see scenario-manifest.json).

Usage: python scripts/gen_scenario_fixtures.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures" / "scenarios"


def chara(**overrides):
    base = {
        "turn": 12,
        "playing_state": 1,
        "card_id": 100101,
        "scenario_id": 4,
        "speed": 120,
        "stamina": 110,
        "power": 130,
        "guts": 90,
        "wiz": 100,
        "vital": 80,
        "max_vital": 100,
        "motivation": 4,
        "skill_point": 320,
        "fans": 500,
        "chara_effect_id_array": [],
        "evaluation_info_array": [],
        "skill_array": [],
        "skill_tips_array": [],
    }
    base.update(overrides)
    return base


def command(cmd_type, cmd_id, group_id=0, select_id=0, enable=1, failure_rate=0,
            params=None, partners=None, tips=None):
    return {
        "command_type": cmd_type,
        "command_id": cmd_id,
        "command_group_id": group_id,
        "select_id": select_id,
        "is_enable": enable,
        "failure_rate": failure_rate,
        "params_inc_dec_info_array": params or [],
        "training_partner_array": partners or [],
        "tips_event_partner_array": tips or [],
    }


def stat(target_type, value):
    return {"target_type": target_type, "value": value}


def home(commands, continue_num=0, free_continue_num=0):
    return {
        "command_info_array": commands,
        "available_continue_num": continue_num,
        "available_free_continue_num": free_continue_num,
    }


def tips(*rows):
    return list(rows)


def tip(group_id, rarity, level=1):
    return {"group_id": group_id, "rarity": rarity, "level": level}


def event(event_id, story_id, choices, chara_id=100101):
    return {
        "event_id": event_id,
        "chara_id": chara_id,
        "story_id": story_id,
        "event_contents_info": {"choice_array": choices},
    }


def choice(select_index, reward=None):
    return {"select_index": select_index, "reward_array": reward or []}


def fixture(name, endpoint, data, scenario, payload=None):
    return {
        "name": name,
        "scenario": scenario,
        "request": {"endpoint": endpoint, "payload": payload or {}},
        "response": {
            "data": data,
            "data_headers": {"result_code": 1, "viewer_id": f"f{scenario}_viewer"},
        },
    }


def write(scenario, files):
    directory = OUT / scenario
    directory.mkdir(parents=True, exist_ok=True)
    for name, record in files:
        path = directory / f"{name}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{scenario}: {len(files)} fixtures")


def build_trackblazer():
    files = []
    # 001 home with commands + shop + rival race + skill tips
    c = chara(
        evaluation_info_array=[
            {"target_id": 1, "evaluation": 75, "is_outing": 0, "story_step": 2},
            {"target_id": 2, "evaluation": 40, "is_outing": 0, "story_step": 1},
        ],
        skill_tips_array=tips(tip(20001, 1, 2), tip(20008, 1, 2)),
    )
    data = {
        "chara_info": c,
        "home_info": home([
            command(1, 101, partners=[1, 2], failure_rate=20, params=[stat(1, 25), stat(3, 10), stat(10, -10)]),
            command(1, 103, partners=[], failure_rate=10, params=[stat(3, 12)]),
            command(7, 701, params=[stat(10, 25)]),
            command(3, 390, params=[stat(10, 15)]),
            command(8, 801, params=[stat(10, 40)]),
        ]),
        "free_data_set": {
            "coin_num": 120,
            "pick_up_item_info_array": [
                {"shop_item_id": 11, "item_id": 2001, "coin_num": 35, "original_coin_num": 35, "item_buy_num": 0, "limit_buy_count": 3, "limit_turn": 0},
                {"shop_item_id": 12, "item_id": 3001, "coin_num": 10, "original_coin_num": 10, "item_buy_num": 0, "limit_buy_count": 1, "limit_turn": 0},
            ],
            "user_item_info_array": [
                {"item_id": 2001, "num": 2},
                {"item_id": 10001, "num": 1},
            ],
            "rival_race_info_array": [{"program_id": 10101, "chara_id": 100202}],
            "item_effect_array": [],
        },
        "race_condition_array": [],
    }
    files.append(("001_load_career", fixture("001_load_career", "single_mode_free/load", data, "trackblazer")))

    # 002 after a speed train
    c2 = chara(turn=13, speed=145, skill_point=340, vital=70,
               evaluation_info_array=[{"target_id": 1, "evaluation": 78, "is_outing": 0, "story_step": 2}],
               skill_tips_array=tips(tip(20001, 1, 2)))
    data2 = {"chara_info": c2, "home_info": home([
        command(1, 101, partners=[1], failure_rate=18, params=[stat(1, 22), stat(10, -10)]),
        command(1, 103, partners=[], failure_rate=8, params=[stat(3, 10)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 120, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("002_train_speed", fixture("002_train_speed", "single_mode_free/exec_command", data2, "trackblazer", {"command_type": 1, "command_id": 101})))

    # 003 multi-choice event
    data3 = {"chara_info": chara(skill_tips_array=tips(tip(20001, 1, 2))), "unchecked_event_array": [event(501, "500001", [choice(1), choice(2)])], "home_info": home([])}
    files.append(("003_event_multi", fixture("003_event_multi", "single_mode_free/load", data3, "trackblazer")))

    # 004 event resolved -> home
    data4 = {"chara_info": chara(turn=13, motivation=5, skill_tips_array=tips(tip(20001, 1, 2))), "home_info": home([
        command(1, 101, partners=[1], failure_rate=15, params=[stat(1, 20), stat(10, -10)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 120, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("004_event_choice", fixture("004_event_choice", "single_mode_free/check_event", data4, "trackblazer", {"event_id": 501, "choice_number": 1})))

    # 005 race select (race command enabled, condition array)
    c5 = chara(turn=24, fans=1200, skill_tips_array=tips(tip(20001, 1, 2)))
    data5 = {"chara_info": c5, "home_info": home([
        command(1, 101, partners=[1], failure_rate=15, params=[stat(1, 20), stat(10, -10)]),
        command(4, 401, enable=1),
    ]), "race_condition_array": [{"program_id": 10101, "turn": 24}], "free_data_set": {"coin_num": 120, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("005_race_select", fixture("005_race_select", "single_mode_free/load", data5, "trackblazer")))

    # 006 race entry response (playing_state 2, race_start_info, no continue)
    c6 = chara(turn=24, playing_state=2, vital=70)
    data6 = {"chara_info": c6, "race_start_info": {
        "program_id": 10101, "race_instance_id": "10101", "is_short": 1,
        "race_horse_data": [{"viewer_id": f"f{'_trackblazer'}_viewer", "frame_order": 3}],
    }, "home_info": home([], continue_num=0, free_continue_num=0)}
    files.append(("006_race_entry", fixture("006_race_entry", "single_mode_free/race_entry", data6, "trackblazer", {"program_id": 10101})))

    # 007 race_start (no continue offered)
    c7 = chara(turn=24, playing_state=2, vital=70)
    data7 = {"chara_info": c7, "race_start_info": {
        "program_id": 10101, "race_instance_id": "10101", "is_short": 1,
        "race_horse_data": [{"viewer_id": f"f{'_trackblazer'}_viewer", "frame_order": 3}],
    }, "home_info": home([], continue_num=0, free_continue_num=0)}
    files.append(("007_race_start", fixture("007_race_start", "single_mode_free/race_start", data7, "trackblazer", {"is_short": 1})))

    # 008 race_end -> home
    c8 = chara(turn=24, playing_state=1, vital=60, fans=1600)
    data8 = {"chara_info": c8, "home_info": home([
        command(1, 101, partners=[1], failure_rate=12, params=[stat(1, 20), stat(10, -10)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 130, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("008_race_end", fixture("008_race_end", "single_mode_free/race_end", data8, "trackblazer")))

    # 009 race_out -> home (same shape)
    files.append(("009_race_out", fixture("009_race_out", "single_mode_free/race_out", data8, "trackblazer")))

    # 010 race_continue offered (rank unparsable -> 99, continue offered)
    c10 = chara(turn=36, playing_state=2, vital=55)
    data10 = {"chara_info": c10, "race_start_info": {
        "program_id": 10101, "race_instance_id": "10101", "is_short": 1,
        "continue_num": 0,
        "race_horse_data": [{"viewer_id": f"f{'_trackblazer'}_viewer", "frame_order": 4}],
    }, "home_info": home([], continue_num=2, free_continue_num=1)}
    files.append(("010_race_continue", fixture("010_race_continue", "single_mode_free/race_start", data10, "trackblazer", {"is_short": 1})))

    # 011 shop with coin budget
    c11 = chara(turn=40, vital=50)
    data11 = {"chara_info": c11, "home_info": home([
        command(1, 101, partners=[1], failure_rate=20, params=[stat(1, 22), stat(10, -10)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {
        "coin_num": 200,
        "pick_up_item_info_array": [
            {"shop_item_id": 21, "item_id": 2001, "coin_num": 35, "original_coin_num": 35, "item_buy_num": 0, "limit_buy_count": 3, "limit_turn": 0},
            {"shop_item_id": 22, "item_id": 10001, "coin_num": 40, "original_coin_num": 40, "item_buy_num": 0, "limit_buy_count": 1, "limit_turn": 0},
            {"shop_item_id": 23, "item_id": 3001, "coin_num": 10, "original_coin_num": 10, "item_buy_num": 1, "limit_buy_count": 1, "limit_turn": 0},
        ],
        "user_item_info_array": [{"item_id": 2001, "num": 1}, {"item_id": 10001, "num": 1}],
        "rival_race_info_array": [], "item_effect_array": [],
    }}
    files.append(("011_shop", fixture("011_shop", "single_mode_free/load", data11, "trackblazer")))

    # 012 skills (one affordable, one not)
    c12 = chara(skill_point=200, skill_tips_array=tips(tip(20001, 1, 2), tip(20008, 1, 2)))
    data12 = {"chara_info": c12, "home_info": home([
        command(1, 101, partners=[1], failure_rate=15, params=[stat(1, 20), stat(10, -10)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("012_skills", fixture("012_skills", "single_mode_free/load", data12, "trackblazer")))

    # 013 finish screen
    c13 = chara(turn=77, state=3)
    data13 = {"chara_info": c13, "single_mode_finish_common": {"result_code": 1}}
    files.append(("013_finish", fixture("013_finish", "single_mode_free/load", data13, "trackblazer")))

    # 014 climax ready
    c14 = chara(turn=74, vital=60)
    data14 = {"chara_info": c14, "trackblazer_info": {"climax_ready": True, "climax_program_id": 10901},
              "home_info": home([command(4, 401, enable=1)]), "race_condition_array": [{"program_id": 10901, "turn": 74}],
              "free_data_set": {"coin_num": 90, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("014_climax", fixture("014_climax", "single_mode_free/load", data14, "trackblazer")))

    # 015 forced (single-choice) event for drain tests
    data15 = {"chara_info": chara(turn=13), "unchecked_event_array": [event(502, "400004002", [choice(1)])], "home_info": home([])}
    files.append(("015_event_forced", fixture("015_event_forced", "single_mode_free/load", data15, "trackblazer")))

    # 016 low energy -> rest recommendation
    c16 = chara(turn=20, vital=15, motivation=3)
    data16 = {"chara_info": c16, "home_info": home([
        command(1, 101, partners=[1], failure_rate=45, params=[stat(1, 25), stat(10, -15)]),
        command(7, 701, params=[stat(10, 25)]),
        command(3, 390, params=[stat(10, 15)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("016_low_energy", fixture("016_low_energy", "single_mode_free/load", data16, "trackblazer")))

    # 017 friendship training beats plain training
    c17 = chara(turn=20, vital=80,
                evaluation_info_array=[{"target_id": 1, "evaluation": 75, "is_outing": 0, "story_step": 2}])
    data17 = {"chara_info": c17, "home_info": home([
        command(1, 101, partners=[1], failure_rate=10, params=[stat(1, 22), stat(10, -10)]),
        command(1, 102, partners=[], failure_rate=5, params=[stat(3, 20)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("017_friendship", fixture("017_friendship", "single_mode_free/load", data17, "trackblazer")))

    write("trackblazer", files)


def build_ura():
    files = []
    goals = [
        {"program_id": 10101, "turn": 12, "goal_title": "Hoppful Stakes", "cleared": False, "required_fans": 350},
        {"program_id": 10102, "turn": 24, "goal_title": "Classic Satsuki Sho", "cleared": False, "required_fans": 1500},
    ]
    c = chara(scenario_id=1, turn=12, fans=100,
              evaluation_info_array=[{"target_id": 1, "evaluation": 80, "is_outing": 0, "story_step": 3}],
              skill_tips_array=tips(tip(20001, 1, 2)))
    data = {"chara_info": c, "ura_goal_array": goals, "ura_final_info": {"is_final": False},
            "home_info": home([
                command(1, 101, partners=[1], failure_rate=15, params=[stat(1, 22), stat(10, -10)]),
                command(4, 401, enable=1),
                command(7, 701, params=[stat(10, 25)]),
            ]), "race_condition_array": [{"program_id": 10101, "turn": 12}],
            "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("001_load_career", fixture("001_load_career", "single_mode_free/load", data, "ura")))

    cleared_goals = [
        {"program_id": 10101, "turn": 12, "goal_title": "Hoppful Stakes", "cleared": True, "required_fans": 350},
        {"program_id": 10102, "turn": 24, "goal_title": "Classic Satsuki Sho", "cleared": False, "required_fans": 1500},
    ]
    c2 = chara(scenario_id=1, turn=12, playing_state=2, vital=70)
    data2 = {"chara_info": c2, "race_start_info": {
        "program_id": 10101, "race_instance_id": "10101", "is_short": 1, "continue_num": 0,
        "race_horse_data": [{"viewer_id": "fura_viewer", "frame_order": 3}],
    }, "home_info": home([], continue_num=0, free_continue_num=0)}
    files.append(("002_race_entry", fixture("002_race_entry", "single_mode_free/race_entry", data2, "ura", {"program_id": 10101})))

    files.append(("003_race_start", fixture("003_race_start", "single_mode_free/race_start", data2, "ura", {"is_short": 1})))

    c4 = chara(scenario_id=1, turn=12, playing_state=1, vital=60)
    data4 = {"chara_info": c4, "home_info": home([
        command(1, 101, partners=[1], failure_rate=12, params=[stat(1, 20), stat(10, -10)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("004_race_end", fixture("004_race_end", "single_mode_free/race_end", data4, "ura")))

    c5 = chara(scenario_id=1, turn=13, fans=600, skill_tips_array=tips(tip(20001, 1, 2)))
    data5 = {"chara_info": c5, "ura_goal_array": cleared_goals, "ura_final_info": {"is_final": False}, "home_info": home([
        command(1, 101, partners=[1], failure_rate=12, params=[stat(1, 20), stat(10, -10)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("005_race_out", fixture("005_race_out", "single_mode_free/race_out", data5, "ura")))

    c6 = chara(scenario_id=1, turn=20, fans=900)
    data6 = {"chara_info": c6, "unchecked_event_array": [event(601, "600001", [choice(1), choice(2)])], "home_info": home([])}
    files.append(("006_event_multi", fixture("006_event_multi", "single_mode_free/load", data6, "ura")))

    data6b = {"chara_info": chara(scenario_id=1, turn=20, fans=950), "home_info": home([
        command(1, 101, partners=[], failure_rate=10, params=[stat(1, 18)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("007_event_choice", fixture("007_event_choice", "single_mode_free/check_event", data6b, "ura", {"event_id": 601, "choice_number": 1})))

    c8 = chara(scenario_id=1, turn=30, vital=70,
               evaluation_info_array=[{"target_id": 3, "evaluation": 70, "is_outing": 0, "story_step": 1}],
               skill_tips_array=tips(tip(20001, 1, 2)))
    data8 = {"chara_info": c8, "ura_goal_array": [], "ura_final_info": {"is_final": False}, "home_info": home([
        command(1, 101, partners=[3], failure_rate=10, params=[stat(1, 24), stat(10, -10)]),
        command(1, 105, partners=[], failure_rate=5, params=[stat(2, 16)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("008_friendship_train", fixture("008_friendship_train", "single_mode_free/load", data8, "ura")))

    c9 = chara(scenario_id=1, turn=36, playing_state=2, vital=50)
    data9 = {"chara_info": c9, "race_start_info": {
        "program_id": 10102, "race_instance_id": "10102", "is_short": 1, "continue_num": 0,
        "race_horse_data": [{"viewer_id": "fura_viewer", "frame_order": 5}],
    }, "home_info": home([], continue_num=1, free_continue_num=0)}
    files.append(("009_race_continue", fixture("009_race_continue", "single_mode_free/race_start", data9, "ura", {"is_short": 1})))

    c10 = chara(scenario_id=1, turn=50, skill_point=150, skill_tips_array=tips(tip(20001, 1, 3)))
    data10 = {"chara_info": c10, "ura_goal_array": [], "ura_final_info": {"is_final": False}, "home_info": home([
        command(1, 101, partners=[], failure_rate=10, params=[stat(1, 18)]),
        command(7, 701, params=[stat(10, 25)]),
    ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("010_skills", fixture("010_skills", "single_mode_free/load", data10, "ura")))

    c11 = chara(scenario_id=1, turn=72, fans=90000, state=3)
    data11 = {"chara_info": c11, "ura_final_info": {"is_final": True, "final_program_id": 10999, "result": 0}, "single_mode_finish_common": {"result_code": 1}}
    files.append(("011_final_finish", fixture("011_final_finish", "single_mode_free/load", data11, "ura")))

    write("ura", files)


def build_unity():
    files = []
    members = [
        {"trained_chara_id": 100001, "card_id": 100101, "name": "Team A", "position": 1, "rank": 15},
        {"trained_chara_id": 100002, "card_id": 100202, "name": "Team B", "position": 2, "rank": 12},
        {"trained_chara_id": 100003, "card_id": 100303, "name": "Team C", "position": 3, "rank": 9},
    ]
    c = chara(scenario_id=2, turn=24, vital=80,
              evaluation_info_array=[{"target_id": 1, "evaluation": 80, "is_outing": 0, "story_step": 2}],
              skill_tips_array=tips(tip(20001, 1, 2)))
    data = {"chara_info": c,
            "unity_team_info": {"team_member_array": members, "team_rank": 5, "roster_slot_array": [], "roster_decision_required": False},
            "unity_cup_info": {"round": 1, "phase": "qualifying", "opponent_program_id": 0, "category": "", "result": 0, "is_final": False, "opponent_decision_required": False},
            "unity_spirit_info": {"gauge_array": [{"category": "short", "value": 80}, {"category": "mile", "value": 30}], "burst_array": [], "burst_ready": False},
            "home_info": home([
                command(1, 101, partners=[1, 100001], failure_rate=12, params=[stat(1, 22), stat(10, -10)]),
                command(7, 701, params=[stat(10, 25)]),
            ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("001_load_career", fixture("001_load_career", "single_mode_free/load", data, "unity")))

    data2 = {"chara_info": chara(scenario_id=2, turn=25, vital=75),
             "unity_team_info": {"team_member_array": members, "team_rank": 5,
                                 "roster_slot_array": [{"slot": 1, "category": "short", "filled": False}, {"slot": 2, "category": "mile", "filled": False}],
                                 "roster_decision_required": True},
             "unity_cup_info": {"round": 1, "phase": "qualifying", "opponent_program_id": 0, "category": "", "result": 0, "is_final": False, "opponent_decision_required": False},
             "unity_spirit_info": {"gauge_array": [], "burst_array": [], "burst_ready": False},
             "home_info": home([]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("002_roster_decision", fixture("002_roster_decision", "single_mode_free/load", data2, "unity")))

    data3 = {"chara_info": chara(scenario_id=2, turn=26, vital=70),
             "unity_team_info": {"team_member_array": members, "team_rank": 5,
                                 "roster_slot_array": [{"slot": 1, "category": "short", "filled": True}, {"slot": 2, "category": "mile", "filled": True}],
                                 "roster_decision_required": False},
             "unity_cup_info": {"round": 1, "phase": "opponent", "opponent_program_id": 0, "category": "", "result": 0, "is_final": False, "opponent_decision_required": True},
             "unity_spirit_info": {"gauge_array": [], "burst_array": [], "burst_ready": False},
             "unity_opponent_array": [
                 {"program_id": 20101, "category": "short"},
                 {"program_id": 20102, "category": "long"},
             ],
             "home_info": home([]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("003_opponent_decision", fixture("003_opponent_decision", "single_mode_free/load", data3, "unity")))

    c4 = chara(scenario_id=2, turn=30, vital=85,
               evaluation_info_array=[{"target_id": 1, "evaluation": 82, "is_outing": 0, "story_step": 2}],
               skill_tips_array=tips(tip(20001, 1, 2)))
    data4 = {"chara_info": c4,
             "unity_team_info": {"team_member_array": members, "team_rank": 6, "roster_slot_array": [], "roster_decision_required": False},
             "unity_cup_info": {"round": 1, "phase": "qualifying", "opponent_program_id": 0, "category": "", "result": 0, "is_final": False, "opponent_decision_required": False},
             "unity_spirit_info": {"gauge_array": [{"category": "mile", "value": 100}], "burst_array": ["mile"], "burst_ready": True},
             "home_info": home([
                 command(1, 101, partners=[1, 100001], failure_rate=10, params=[stat(1, 25), stat(10, -10)]),
                 command(1, 105, partners=[], failure_rate=5, params=[stat(2, 14)]),
                 command(7, 701, params=[stat(10, 25)]),
             ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("004_spirit_burst", fixture("004_spirit_burst", "single_mode_free/load", data4, "unity")))

    data5 = {"chara_info": chara(scenario_id=2, turn=40), "unchecked_event_array": [event(701, "700001", [choice(1), choice(2), choice(3)])], "home_info": home([])}
    files.append(("005_event_multi", fixture("005_event_multi", "single_mode_free/load", data5, "unity")))

    c6 = chara(scenario_id=2, turn=73, state=3)
    data6 = {"chara_info": c6, "single_mode_finish_common": {"result_code": 1}}
    files.append(("006_finish", fixture("006_finish", "single_mode_free/load", data6, "unity")))

    write("unity", files)


def build_grand_concert():
    files = []
    c = chara(scenario_id=3, turn=12, vital=60,
              evaluation_info_array=[{"target_id": 1, "evaluation": 78, "is_outing": 0, "story_step": 2}],
              skill_tips_array=tips(tip(20001, 1, 2)))
    data = {"chara_info": c,
            "concert_info": {
                "performance_point_array": [{"key": "speed", "value": 30}, {"key": "stamina", "value": 20}, {"key": "power", "value": 25}, {"key": "guts", "value": 10}, {"key": "wit", "value": 15}],
                "hype": 12,
                "learned_song_count": 2,
                "songs_this_half": 2,
                "technique_array": [
                    {"technique_id": 1, "name": "Recovery Chorus", "cost": 20, "energy_recovery": 40, "owned": False, "deck_relevant": False},
                    {"technique_id": 2, "name": "Speed Encore", "cost": 30, "energy_recovery": 0, "owned": False, "deck_relevant": True},
                ],
                "song_array": [
                    {"song_id": 1, "name": "Friendship Song", "cost": 15, "skill_point_priority": True, "friendship_priority": True},
                    {"song_id": 2, "name": "Ballad", "cost": 10, "skill_point_priority": False, "friendship_priority": False},
                ],
                "promo_program_id": 30101,
                "promo_ready": False,
                "promo_done": False,
                "grand_concert_ready": False,
            },
            "home_info": home([
                command(1, 101, partners=[1], failure_rate=12, params=[stat(1, 22), stat(10, -10)]),
                command(7, 701, params=[stat(10, 25)]),
            ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("001_load_career", fixture("001_load_career", "single_mode_free/load", data, "grand_concert")))

    c2 = chara(scenario_id=3, turn=16, vital=20)
    data2 = {"chara_info": c2,
             "concert_info": {
                 "performance_point_array": [{"key": "speed", "value": 40}],
                 "hype": 12, "learned_song_count": 3, "songs_this_half": 3,
                 "technique_array": [
                     {"technique_id": 1, "name": "Recovery Chorus", "cost": 20, "energy_recovery": 40, "owned": False, "deck_relevant": False},
                     {"technique_id": 3, "name": "Power Ballad", "cost": 25, "energy_recovery": 0, "owned": False, "deck_relevant": False},
                 ],
                 "song_array": [],
                 "promo_program_id": 30101, "promo_ready": False, "promo_done": False, "grand_concert_ready": False,
             },
             "home_info": home([
                 command(1, 101, partners=[], failure_rate=40, params=[stat(1, 20), stat(10, -15)]),
                 command(7, 701, params=[stat(10, 25)]),
             ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("002_technique_offer", fixture("002_technique_offer", "single_mode_free/load", data2, "grand_concert")))

    c3 = chara(scenario_id=3, turn=20, vital=70)
    data3 = {"chara_info": c3,
             "concert_info": {
                 "performance_point_array": [{"key": "speed", "value": 60}],
                 "hype": 20, "learned_song_count": 3, "songs_this_half": 3,
                 "technique_array": [],
                 "song_array": [
                     {"song_id": 2, "name": "Ballad", "cost": 10, "skill_point_priority": False, "friendship_priority": False},
                 ],
                 "promo_program_id": 30101, "promo_ready": False, "promo_done": False, "grand_concert_ready": False,
             },
             "home_info": home([
                 command(1, 101, partners=[], failure_rate=10, params=[stat(1, 20)]),
                 command(7, 701, params=[stat(10, 25)]),
             ]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("003_song_pacing", fixture("003_song_pacing", "single_mode_free/load", data3, "grand_concert")))

    c4 = chara(scenario_id=3, turn=30, vital=80)
    data4 = {"chara_info": c4,
             "concert_info": {
                 "performance_point_array": [{"key": "speed", "value": 90}],
                 "hype": 40, "learned_song_count": 5, "songs_this_half": 0,
                 "technique_array": [],
                 "song_array": [],
                 "promo_program_id": 30101, "promo_ready": True, "promo_done": False, "grand_concert_ready": False,
             },
             "home_info": home([command(4, 401, enable=1)]), "race_condition_array": [{"program_id": 30101, "turn": 30}],
             "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("004_promo_ready", fixture("004_promo_ready", "single_mode_free/load", data4, "grand_concert")))

    c5 = chara(scenario_id=3, turn=71, vital=70)
    data5 = {"chara_info": c5,
             "concert_info": {
                 "performance_point_array": [{"key": "speed", "value": 200}],
                 "hype": 90, "learned_song_count": 15, "songs_this_half": 4,
                 "technique_array": [], "song_array": [],
                 "promo_program_id": 30101, "promo_ready": False, "promo_done": True, "grand_concert_ready": True,
             },
             "home_info": home([]), "free_data_set": {"coin_num": 0, "pick_up_item_info_array": [], "user_item_info_array": [], "rival_race_info_array": [], "item_effect_array": []}}
    files.append(("005_grand_ready", fixture("005_grand_ready", "single_mode_free/load", data5, "grand_concert")))

    data6 = {"chara_info": chara(scenario_id=3, turn=40), "unchecked_event_array": [event(801, "800001", [choice(1), choice(2)])], "home_info": home([])}
    files.append(("006_event_multi", fixture("006_event_multi", "single_mode_free/load", data6, "grand_concert")))

    c7 = chara(scenario_id=3, turn=73, state=3)
    data7 = {"chara_info": c7, "single_mode_finish_common": {"result_code": 1}}
    files.append(("007_finish", fixture("007_finish", "single_mode_free/load", data7, "grand_concert")))

    write("grand_concert", files)


def main():
    build_trackblazer()
    build_ura()
    build_unity()
    build_grand_concert()
    print("done")


if __name__ == "__main__":
    sys.exit(main())
