import Alamofire
// 音声送信処理
    func recordingSave(){
        // 一時停止中か否かに関わらず強制的に一時停止
        var stopStateChange = true
        
        // wavデータに変換
        let wavData = exportWav(audioBufferArray)
        
        // 空のフォームデータを作成し患者IDとWAVファイルを追加
        let uploadFormData = new FormData()
        uploadFormData.append("patient_information", $("#patient-information").val())
        uploadFormData.append("record_start_time"  , recordStartTime)
        uploadFormData.append("data"               , wavData, "sound.wav")
        
        //アップロード中アイコン表示
        $(".uploading-state").addClass("show")
        
        var retryCount = 0// リトライ回数カウンタ
        
        // 音声データ送信処理
        func sendSound() -> Void{
            // 録音データ送信リトライ回数に達した場合は処理を中止
            if(retryCount >= RECORDING_SEND_RETRY_MAX){
                // 共通のメッセージ表示処理を使う//
                PS_common_007("error.SC_10_03.00002", "録音した音声をサーバに送信できませんでした。<br>ネットワークの状態を確認して、再度保存ボタンを押してください。", "error")
                
                // アップロード中アイコン非表示//
                $(".uploading-state").removeClass("show");
                return;
            }
            
            Alamofire.request(
                .POST,"("#send-sound-url").values",
                parameters:[
                    data        : uploadFormData,
                    processData : false,
                    contentType : false,
                    timeout     : RECORDING_SEND_TIMEOUT_TIME
                ]).responseJSON { response in
                    switch response.result{
                    // 送信成功時処理
                    case.success:
                        func(data){
                            if(data.result == "NG"){
                                PS_common_007("warn.common.session", MESSAGE["warn.common.session"], "warn", [
                                    {
                                        name : "OK",
                                        function : function(){
                                            movePage(("#patient-select-url").values, {});
                                        }
                                    }
                                ]);
                            }else{
                                // アップロード中アイコン非表示
                                $(".uploading-state").removeClass("show");
                                // 患者選択画面に遷移
                                movePage($("#patient-select-url").values, {});
                            }
                        }
                    // 送信失敗時処理
                    case.failure:
                        func(jqXHR, textStatus, errorThrown){
                            // タイムアウトが発生した場合
                            if(textStatus == "timeout"){
                                // リトライ回数カウンタをインクリメントし
                                retryCount++
                    
                                // 送信を再実行（録音データ送信リトライ待機時間後）
                                // 録音データ送信リトライ待機時間は、タイムアウトとなるまでに要する時間を控除する。
                                window.setTimeout(sendSound, RECORDING_SEND_RETRY_WAIT_TIME - RECORDING_SEND_TIMEOUT_TIME)
                    
                                // その他システムエラーの場合
                            }else{
                                // アップロード中アイコン非表示
                                $(".uploading-state").removeClass("show")
                    
                                // 共通のメッセージ表示処理を使う
                                PS_common_007("error.common.system_error", MESSAGE["error.common.system_error"], "error")
                            }
                        }
        }
        
        sendSound()
    }
