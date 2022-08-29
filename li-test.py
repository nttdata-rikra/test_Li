from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.views.generic import View
from django.conf import settings
from django.core import serializers
from datetime import date, datetime, time, timedelta
from math import floor

import sys
import logging
import os
import shutil
import json

from common.models import M_User
from ward  .models import T_WardSound
from common.util import PS_common_101, PS_common_201, PS_common_204, PS_common_303
from common.his import PS_common_302
from .ward_common import jsonAdditionalConverter
from .const import WARD_SHIHT_KBN_START_TIME

# ロガー設定
logger = logging.getLogger("ward")

# 病棟_患者選択画面内 担当患者取得処理
class GetPatient(View):
    def post(self, request, *args, **kwargs):
        process_name = "担当患者取得処理"
        """
        患者をリスト取得する。
        
        Arguments:
        
        Returns:
            [] -- 患者リストを返却する
        """
        try:
            user_id = None
            
            # セッションチェックは行わない（画面初期表示直後にのみ実行する処理のため）
            
            # セッションパラメータ・リクエストパラメータの取得
            user_id = request.session["user_id"]
            
            # 開始ログ出力（共通処理のメッセージ取得処理）（info.common.start）
            output_message, _ = PS_common_204("info.common.start")
            logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
            
            # 担当患者情報の取得
            # 現在日時の取得
            now_datetime = datetime.now()
            # 勤務区分開始時刻を時系列順にソート
            ward_shift_kbn_start_time_sorted = sorted(WARD_SHIHT_KBN_START_TIME.items(), key=lambda x:x[1])
            # 現在勤務日を算出
            # ※最初の勤務区分の開始時刻を超えた瞬間にその勤務日が始まる
            now_shift_date = (now_datetime - ward_shift_kbn_start_time_sorted[0][1]).date()
            # 現在勤務区分を算出
            # ※「次の勤務区分」が現在時刻を超える最初の勤務区分が現在の勤務区分
            for now_shift_kbn_index in range(len(ward_shift_kbn_start_time_sorted)):
                if now_shift_kbn_index == len(ward_shift_kbn_start_time_sorted) - 1 or now_datetime < datetime.combine(now_shift_date, time()) + ward_shift_kbn_start_time_sorted[now_shift_kbn_index + 1][1]:
                    break
            # 現在、前、次の[勤務日, 勤務区分]を検索条件配列に設定
            previous_1_shift_date_difference = floor((now_shift_kbn_index - 1)/3)
            previous_1_shift_kbn_index = (now_shift_kbn_index - 1) % 3
            next_1_shift_date_difference = floor((now_shift_kbn_index + 1)/3)
            next_1_shift_kbn_index = (now_shift_kbn_index + 1) % 3
            conditions = [
                [now_shift_date + timedelta(days=previous_1_shift_date_difference), ward_shift_kbn_start_time_sorted[previous_1_shift_kbn_index][0]],
                [now_shift_date                                                   , ward_shift_kbn_start_time_sorted[now_shift_kbn_index       ][0]],
                [now_shift_date + timedelta(days=next_1_shift_date_difference    ), ward_shift_kbn_start_time_sorted[next_1_shift_kbn_index    ][0]],
            ]
            
            result, patient_id_list, output_message = PS_common_303(user_id, conditions)
            
            if result != True:
                # システムエラーログ出力（共通処理のメッセージ取得処理）
                logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
                
                # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
                output_message, _ = PS_common_204("info.common.end")
                logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))

                sys.exit()
            
            # 患者情報の年齢算出に使用する本日日付
            today = date.today()
            
            # 患者情報の取得
            patient_information_list = []
            for patient_id in patient_id_list:
                result, _, patient_name, patient_kana_name, gen_cd, birth_date, output_message = PS_common_302(patient_id)
                
                if result != True:
                    # システムエラーログ出力（共通処理のメッセージ取得処理）
                    logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
                    
                    # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
                    output_message, _ = PS_common_204("info.common.end")
                    logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
                    sys.exit()
                
                patient_information_list.append({
                    "data_type"         : "his",
                    "patient_id"        : patient_id,
                    "patient_kana_name" : patient_kana_name,
                    "patient_name"      : patient_name,
                    "birth_date"        : date(int(birth_date/10000), int(birth_date/100)%100, birth_date%100),
                    "gen_cd"            : gen_cd,
                    "age"               : int(((today.year*10000 + today.month*100 + today.day) - birth_date)/10000),
                })
            
            # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
            output_message, _ = PS_common_204("info.common.end")
            logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
            
            return JsonResponse({
                "data" : json.dumps(patient_information_list, default = jsonAdditionalConverter)
            }, safe=False)
            
        except Exception as e:
            # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
            output_message, _ = PS_common_204("error.common.system")
            logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message), exc_info = True)
            
            # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
            output_message, _ = PS_common_204("info.common.end")
            logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
            sys.exit()

# # 病棟_患者選択画面内 担当患者追加処理
# class AddPatient(View):
#     def post(self, request, *args, **kwargs):
#         process_name = "担当患者追加処理"
#         """
#         DBに患者氏名画像を保存する。
#         
#         Arguments:
#         
#         Returns:
#             [] -- 保存成功の信号を返却する
#         """
#         try:
#             user_id = None
#             
#             # セッションチェック
#             session_check = PS_common_101(request, "ward", False)
#             
#             # セッションが存在しないまたは有効期限切れの場合はログイン画面にリダイレクト
#             if session_check[0] == "NG":
#                 return JsonResponse({
#                    "result" : session_check[0],
#                    "url"    : session_check[1],
#                }, safe=False)
#             
#             # セッションパラメータ・リクエストパラメータの取得
#             user_id = request.session["user_id"]
#             
#             # 開始ログ出力（共通処理のメッセージ取得処理）（info.common.start）
#             output_message, _ = PS_common_204("info.common.start")
#             logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#             
#             # DBに設定する現在時刻の取得
#             now_time = PS_common_201()
#             
#             # DBに登録（仮）
#             try:
#                 record_tmp = T_WardPatient(
#                     patient_id      = "TMP"+ datetime.now().strftime("%Y%m%d%H%M%S%f")[:17],
#                     user_id         = user_id,
#                     create_time     = now_time,
#                     update_time     = now_time
#                 )
#                 record_tmp.save()
#             
#             # その他データベースアクセスエラー
#             except Exception as e:
#                 # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
#                 output_message, _ = PS_common_204("error.common.db", ["T_WardPatient"])
#                 logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message), exc_info = True)
#                 
#                 # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#                 output_message, _ = PS_common_204("info.common.end")
#                 logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#                 sys.exit()
#             
#             # DBを更新（患者IDの採番）
#             record_tmp.patient_id = "AIH" + str(record_tmp.id).zfill(17)
#             try:
#                 record_tmp.save()
#             
#             # その他データベースアクセスエラー
#             except Exception as e:
#                 # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
#                 output_message, _ = PS_common_204("error.common.db", ["T_WardPatient"])
#                 logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message), exc_info = True)
#                 
#                 # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#                 output_message, _ = PS_common_204("info.common.end")
#                 logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#                 sys.exit()
#             
#             # 画像ファイル格納パス設定
#             BASE_DIR = getattr(settings, "BASE_DIR")
#             upload_file_path = os.path.join(BASE_DIR, "..\\media\\ward\\image\\patient_name", "pn" + record_tmp.patient_id + ".jpg")
# 
#             # 画像データの取得
#             blob = request.FILES.get("data").read()
#             
#             # 画像ファイルを画像ファイル格納フォルダに保存
#             outfile = open(upload_file_path, "wb")
#             outfile.write(blob)
#             outfile.close()
# 
#             # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#             output_message, _ = PS_common_204("info.common.end")
#             logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#             
#             return HttpResponse("success")
#             
#         except Exception as e:
#             # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
#             output_message, _ = PS_common_204("error.common.system")
#             logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message), exc_info = True)
#             
#             # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#             output_message, _ = PS_common_204("info.common.end")
#             logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#             sys.exit()
# 
# 
# # 病棟_患者選択画面内 担当患者個別削除処理
# class DeletePatient(View):
#     def post(self, request, *args, **kwargs):
#         process_name = "担当患者個別削除処理"
#         """
#         担当患者を個別に削除する。
#         
#         Arguments:
#         
#         Returns:
#             [] -- 削除成功の信号を返却する
#         """
#         try:
#             user_id = None
#             
#             # セッションチェック
#             session_check = PS_common_101(request, "ward", False)
#             
#             # セッションが存在しないまたは有効期限切れの場合はログイン画面にリダイレクト
#             if session_check[0] == "NG":
#                 return JsonResponse({
#                    "result" : session_check[0],
#                    "url"    : session_check[1],
#                }, safe=False)
#             
#             # セッションパラメータ・リクエストパラメータの取得
#             user_id    = request.session["user_id"]
#             patient_id = request.POST.get("patient_id")
#             
#             # 開始ログ出力（共通処理のメッセージ取得処理）（info.common.start）
#             output_message, _ = PS_common_204("info.common.start")
#             logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, メッセージ:{3}".format(process_name, user_id, patient_id, output_message))
#             
#             # 担当患者情報の削除
#             try:
#                 T_WardPatient.objects.get(
#                     user_id = user_id,
#                     patient_id = patient_id,
#                 ).delete()
#             
#             # その他データベースアクセスエラー
#             except Exception as e:
#                 # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
#                 output_message, _ = PS_common_204("error.common.db", ["T_WardPatient"])
#                 logger.error("処理名:{0}, ユーザID:{1}, 患者ID:{2}, メッセージ:{3}".format(process_name, user_id, patient_id, output_message), exc_info = True)
#                 
#                 # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#                 output_message, _ = PS_common_204("info.common.end")
#                 logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, メッセージ:{3}".format(process_name, user_id, patient_id, output_message))
#                 sys.exit()
#             
#             # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#             output_message, _ = PS_common_204("info.common.end")
#             logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, メッセージ:{3}".format(process_name, user_id, patient_id, output_message))
#             
#             return HttpResponse("success")
#             
#         except Exception as e:
#             # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
#             output_message, _ = PS_common_204("error.common.system")
#             logger.error("処理名:{0}, ユーザID:{1}, 患者ID:{2}, メッセージ:{3}".format(process_name, user_id, patient_id, output_message), exc_info = True)
#             
#             # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#             output_message, _ = PS_common_204("info.common.end")
#             logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, メッセージ:{3}".format(process_name, user_id, patient_id, output_message))
#             sys.exit()
# 
# 
# # 病棟_患者選択画面内 担当患者全削除処理
# class ClearPatient(View):
#     def post(self, request, *args, **kwargs):
#         process_name = "担当患者全削除処理"
#         """
#         担当患者を全て削除する。
#         
#         Arguments:
#         
#         Returns:
#             [] -- 削除成功の信号を返却する
#         """
#         try:
#             user_id = None
#             
#             # セッションチェック
#             session_check = PS_common_101(request, "ward", False)
#             
#             # セッションが存在しないまたは有効期限切れの場合はログイン画面にリダイレクト
#             if session_check[0] == "NG":
#                 return JsonResponse({
#                    "result" : session_check[0],
#                    "url"    : session_check[1],
#                }, safe=False)
#             
#             # セッションパラメータ・リクエストパラメータの取得
#             user_id    = request.session["user_id"]
#             
#             # 開始ログ出力（共通処理のメッセージ取得処理）（info.common.start）
#             output_message, _ = PS_common_204("info.common.start")
#             logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#             
#             # 担当患者情報の削除
#             try:
#                 T_WardPatient.objects.filter(
#                     user_id = user_id
#                 ).delete()
#             
#             # その他データベースアクセスエラー
#             except Exception as e:
#                 # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
#                 output_message, _ = PS_common_204("error.common.db", ["T_WardPatient"])
#                 logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message), exc_info = True)
#                 
#                 # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#                 output_message, _ = PS_common_204("info.common.end")
#                 logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#                 sys.exit()
#             
#             # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#             output_message, _ = PS_common_204("info.common.end")
#             logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#             
#             return HttpResponse("success")
#             
#         except Exception as e:
#             # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
#             output_message, _ = PS_common_204("error.common.system")
#             logger.error("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message), exc_info = True)
#             
#             # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
#             output_message, _ = PS_common_204("info.common.end")
#             logger.info("処理名:{0}, ユーザID:{1}, メッセージ:{2}".format(process_name, user_id, output_message))
#             sys.exit()

# 病棟_音声入力画面内 音声ファイル送信処理
class SendSound(View):
    def post(self, request, *args, **kwargs):
        process_name = "音声ファイル送信処理"
        """
        録音した音声をDBに保存する。
        
        Arguments:
        音声入力対象患者ID
        
        Returns:
            [] -- 削除成功の信号を返却する
        """
        try:
            user_id = None
            patient_information = {"patient_id" : None}
            record_start_time = None
            
            # セッションチェック
            session_check = PS_common_101(request, "ward", False)
            
            # セッションが存在しないまたは有効期限切れの場合はログイン画面にリダイレクト
            if session_check[0] == "NG":
                return JsonResponse({
                    "result" : session_check[0],
                    "url"    : session_check[1],
                }, safe=False)
            
            # セッションパラメータ・リクエストパラメータの取得
            user_id             = request.session["user_id"]
            patient_information = json.loads(request.POST.get("patient_information"))
            record_start_time    = request.POST.get("record_start_time")
            
            # 開始ログ出力（共通処理のメッセージ取得処理）（info.common.start）
            output_message, _ = PS_common_204("info.common.start")
            logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
            
            # DBに設定する現在時刻の取得
            now_time = PS_common_201()
            
            # 録音IDに使用する現在時刻の取得
            # 作成日時と同一の時刻を使用するが、時刻表記中の記号や空白を除去する。
            now_time_number = datetime.strptime(record_start_time, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S')
            
            # 音声保存
            try:
                if patient_information["data_type"] == "patient_free":
                    record_tmp = T_WardSound(
                        recording_id      = now_time_number + "PATIENT_FREE" + user_id,
                        text_conv_state   = "変換中",
                        patient_id        = "PATIENT_FREE",
                        patient_kana_name = "",
                        patient_name      = "",
                        gen_cd            = "",
                        age               = 0,
                        birth_date        = datetime.strptime(record_start_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),
                        user_id           = user_id,
                        record_start_time = record_start_time,
                        create_time       = now_time,
                        update_time       = now_time
                    )
                else:
                    record_tmp = T_WardSound(
                        recording_id      = now_time_number + patient_information["patient_id"] + user_id,
                        text_conv_state   = "変換中",
                        patient_id        = patient_information["patient_id"],
                        patient_kana_name = patient_information["patient_kana_name"],
                        patient_name      = patient_information["patient_name"],
                        gen_cd            = patient_information["gen_cd"],
                        age               = patient_information["age"],
                        birth_date        = patient_information["birth_date"],
                        user_id           = user_id,
                        record_start_time = record_start_time,
                        create_time       = now_time,
                        update_time       = now_time
                    )
                    
                record_tmp.save()
            
            # その他データベースアクセスエラー
            except Exception as e:
                # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
                output_message, _ = PS_common_204("error.common.db", ["T_WardSound"])
                logger.error("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message), exc_info = True)
                
                # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
                output_message, _ = PS_common_204("info.common.end")
                logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
                sys.exit()
            

            # 音声ファイル格納パス設定
            BASE_DIR = getattr(settings, "BASE_DIR")
            upload_file_path = os.path.join(BASE_DIR, "..\\media\\ward\\sound\\soap_data\\voice_temp", "sd" + record_tmp.recording_id + ".wav")

            # 音声データの取得
            blob = request.FILES.get("data").read()
            
            # 音声ファイルを音声ファイル格納フォルダに保存
            output_file = open(upload_file_path, "wb")
            output_file.write(blob)
            output_file.close()
            
            # 音声ファイル移動先パス設定
            move_file_path = os.path.join(BASE_DIR, "..\\media\\ward\\sound\\soap_data\\target_analyzing", "sd" + record_tmp.recording_id + ".wav")
            
            # 音声ファイルを解析対象ファイル格納フォルダに移動
            shutil.move(upload_file_path, move_file_path)
            
            # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
            output_message, _ = PS_common_204("info.common.end")
            logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
            
            return HttpResponse("success")
            
        except Exception as e:
            # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
            output_message, _ = PS_common_204("error.common.system")
            logger.error("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message), exc_info = True)
            
            # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
            output_message, _ = PS_common_204("info.common.end")
            logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
            sys.exit()


class SendSoundAndText(View):
    def post(self, request, *args, **kwargs):
        process_name = "音声ファイ・認識結果送信処理"
        """
        録音した音声と認識結果をDBに保存する。
        
        Arguments:
        音声入力対象患者ID
        
        Returns:
            [] -- 削除成功の信号を返却する
        """
        try:
            user_id = None
            patient_information = {"patient_id" : None}
            record_start_time = None
            text = None
            
            # セッションチェック
            session_check = PS_common_101(request, "ward", False)
            
            # セッションが存在しないまたは有効期限切れの場合はログイン画面にリダイレクト
            if session_check[0] == "NG":
                return JsonResponse({
                    "result" : session_check[0],
                    "url"    : session_check[1],
                }, safe=False)

            # セッションパラメータ・リクエストパラメータの取得
            user_id             = request.session["user_id"]
            patient_information = json.loads(request.POST.get("patient_information"))
            record_start_time    = request.POST.get("record_start_time")
            text = request.POST.get("text")
            
            # 開始ログ出力（共通処理のメッセージ取得処理）（info.common.start）
            output_message, _ = PS_common_204("info.common.start")
            logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
            
            # DBに設定する現在時刻の取得
            now_time = PS_common_201()

            # 録音IDに使用する現在時刻の取得
            # 作成日時と同一の時刻を使用するが、時刻表記中の記号や空白を除去する。
            now_time_number = datetime.strptime(record_start_time, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S')

            # 音声と認識結果保存
            try:
                if patient_information["data_type"] == "patient_free":
                    record_tmp = T_WardSound(
                        recording_id      = now_time_number + "PATIENT_FREE" + user_id,
                        text_conv_state   = "変換済み",
                        conv_str          = text,
                        patient_id        = "PATIENT_FREE",
                        patient_kana_name = "",
                        patient_name      = "",
                        gen_cd            = "",
                        age               = 0,
                        birth_date        = datetime.strptime(record_start_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),
                        user_id           = user_id,
                        record_start_time = record_start_time,
                        create_time       = now_time,
                        update_time       = now_time
                    )
                else:
                    record_tmp = T_WardSound(
                        recording_id      = now_time_number + patient_information["patient_id"] + user_id,
                        text_conv_state   = "変換済み",
                        tconv_str         = text,
                        patient_id        = patient_information["patient_id"],
                        patient_kana_name = patient_information["patient_kana_name"],
                        patient_name      = patient_information["patient_name"],
                        gen_cd            = patient_information["gen_cd"],
                        age               = patient_information["age"],
                        birth_date        = patient_information["birth_date"],
                        user_id           = user_id,
                        record_start_time = record_start_time,
                        create_time       = now_time,
                        update_time       = now_time
                    )
                    

            # その他データベースアクセスエラー
            except Exception as e:
                # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
                output_message, _ = PS_common_204("error.common.db", ["T_WardSound"])
                logger.error("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message), exc_info = True)
                
                # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
                output_message, _ = PS_common_204("info.common.end")
                logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
                sys.exit()

            try:

                # 音声ファイル格納パス設定
                BASE_DIR = getattr(settings, "BASE_DIR")
                upload_file_path = os.path.join(BASE_DIR, "..\\media\\ward\\sound\\soap_data\\complete_analyzing", "sd" + record_tmp.recording_id + ".wav")
                
                # 音声データの取得
                blob = request.FILES.get("data").read()
                
                # 音声ファイルを音声ファイル格納フォルダに保存
                output_file = open(upload_file_path, "wb")
                output_file.write(blob)
                output_file.close()

                # DB更新を確定
                record_tmp.save()

            # ファイル保存エラー
            except Exception as e:
                # システムエラーログ出力（共通処理のメッセージ取得処理）
                output_message, _ = PS_common_204("error.C10.00004")
                logger.error("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message), exc_info = True)
                
                # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
                output_message, _ = PS_common_204("info.common.end")
                logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
                sys.exit()

            # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
            output_message, _ = PS_common_204("info.common.end")
            logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
            
            return HttpResponse("success")
            
        except Exception as e:
            # システムエラーログ出力（共通処理のメッセージ取得処理）（error.common.system）
            output_message, _ = PS_common_204("error.common.system")
            logger.error("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message), exc_info = True)
            
            # 終了ログ出力（共通処理のメッセージ取得処理）（info.common.end）
            output_message, _ = PS_common_204("info.common.end")
            logger.info("処理名:{0}, ユーザID:{1}, 患者ID:{2}, 録音開始日時:{3}, メッセージ:{4}".format(process_name, user_id, ("PATIENT_FREE" if patient_information["data_type"] == "patient_free" else patient_information["patient_id"]), record_start_time, output_message))
            sys.exit()
            
            
