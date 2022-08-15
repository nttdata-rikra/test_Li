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
            
            # 音声と認識結果保存
            try:
                if patient_information["data_type"] == "patient_free":
                    record_tmp = T_WardSound(
                        recording_id      = now_time_number + "PATIENT_FREE" + user_id,
                        text_conv_state   = "変換中",
                        text_conv_res     = "",
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
                        text_conv_res     = "",
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
            upload_file_path = os.path.join(BASE_DIR, "..\\media\\ward\\sound\\soap_data\\complete_analyzing", "sd" + record_tmp.recording_id + ".wav")
            
            # 音声データの取得
            blob = request.FILES.get("data").read()
            
            # 音声ファイルを音声ファイル格納フォルダに保存
            output_file = open(upload_file_path, "wb")
            output_file.write(blob)
            output_file.close()

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
