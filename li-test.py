import Alamofire
import Network
// ログイン処理
func login(userId, password) {
    // 送信処理
    let url = "/login/ward-native"
    let paramaters = [
        "user_id":userId,
        "password":password
    ]
    Alamofire.request(url,method: .post,paramaters:paramaters).responseJSON {
        response in
        switch response.result {
        case .success(let data):
            if data.result { // 認証が通った場合  
                return (true, "");
            } else { // 認証が通らなかった場合
                return (false, "error.SC_A10_01.00001");
            }
        case .failure():
            if textStatus ==  Consts.LOGIN_TIMEOUT_TIME { // タイムアウトが発生した場合
                return (false, "error.common.timeout");
            } else { // その他システムエラーの場合
                return (false, "error.common.system_error");
            }
        }
    })
}

//ネットワークチェック
monitor.pathUpdateHandler = { path in
        if path.status == .satisfied {
            login()
        }else{
            //ダイアログ表示(error.common.network)
        }
    }
monitor.start(queue:queue)





import Alamofire
import Network

// 音声送信処理
func recordingSave(wavData, patientInfromation, recordStartTime, text){
    
    // 空のフォームデータを作成し患者IDとWAVファイルを追加
    let url = "/ward/recording/send_sound_and_text"
    let monitor = NWPathMonitor()
    let queue =DispatchQueue(label:url)
                 
    var retryCount = 0// リトライ回数カウンタ
                
    func sendData() {
    // 録音データ送信リトライ回数に達した場合は処理を中止
        if(retryCount >= Consts.RECORDING_SEND_RETRY_MAX){
            // 共通のメッセージ表示処理を使う
            //PS_common_007("error.SC_10_03.00002", "録音した音声をサーバに送信できませんでした。<br>ネットワークの状態を確認して、再度保存ボタンを押してください。", "error")
            return(false,"error.SC_10_03.00002");
        }
                      
        Alamofire.upload(multipartFormData: { (multipartFormData) in
            multipartFormData.append(patient_information, withName: "patient_information", mimeType: "text/plain")
            multipartFormData.append(record_start_time, withName: "record_start_time", mimeType: "text/plain")
            multipartFormData.append(wavData, withName: "data", fileName: "sound.wav", mimeType: "audio/x-wav")
            multipartFormData.append(text, withName: "text", mimeType: "text/plain")
        },to: url,encodingCompletion:{ (encodingResult) in
            switch encodingResult {
            case .success():
                upload.responseJSON { response in
                    if(response.result == "NG"){ // セッションチェックエラー時
//                        PS_common_007("warn.common.session", MESSAGE["warn.common.session"], "warn", [
//                            {
//                                name : "OK",
//                                function : function(){
//                                    movePage($("#patient-select-url").val(), {})
//                                }
//                            }
//                        ])
                        return (false,"warn.common.session");
                        
                    }else{ // 送信成功時
                        return (true,"");
                    }
                }
                // 送信失敗時処理
            case .failure():
                // タイムアウトが発生した場合
                if(textStatus == Consts.RECORDING_SEND_TIMEOUT_TIME){
                    retryCount+=1
                    
                    // 送信を再実行（録音データ送信リトライ待機時間後）
                    // 録音データ送信リトライ待機時間は、タイムアウトとなるまでに要する時間を控除する。
                    window.setTimeout(sendSound, Consts.RECORDING_SEND_RETRY_WAIT_TIME - Consts.RECORDING_SEND_TIMEOUT_TIME)
                    
                    // その他システムエラーの場合
                }else{
                    // アップロード中アイコン非表示
                    
                    // 共通のメッセージ表示処理を使う
                    //PS_common_007("error.common.system_error", MESSAGE["error.common.system_error"], "error")
                    return (false,"error.common.system_error");
                }
            }
        }
    }

    monitor.pathUpdateHandler = { path in
            if path.status == .satisfied {
                return sendData();
            }else{
                return (false,"error.common.network");
            }
        }
    monitor.start(queue:queue)
}
