import Alamofire
import Network

 //音声送信処理
func recordingSave(wavData: Data, patientInformation: [String: Any], recordStartTime: Date, text: String) -> (result: Bool, messageId: String) {
    
   //  患者情報をjsonに
    var patientInformationJson: Data
    do {
        patientInformationJson = try JSONSerialization.data(withJSONObject: patientInformation)
    }
    catch {
        return (false, "common.error.system")
    }
    
     //録音開始日時をstringにしてからData型に
    let dateFormatter = DateFormatter()
    dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
    guard let recordStartTimeData: Data = dateFormatter.string(from: recordStartTime).data(using: .utf8) else {return (false, "common.error.system")}
    guard let textData: Data = text.data(using: .utf8) else {return (false, "common.error.system")}
    
     //認識結果テキストをData型に
    guard let textData: Data = text.data(using: .utf8) else {return (false, "common.error.system")}
    
    let url = Consts.URL_BASE + "ward/recording/send_sound_and_text"
    
    var retryCount = 0 //リトライ回数カウンタ
    
    func sendData() -> (result: Bool, messageId: String) {
        var result = false
        var messageId = ""
        //録音データ送信リトライ回数に達した場合は処理を中止
        if(retryCount >= Consts.RECORDING_SEND_RETRY_MAX) {
            return (false, "error.SC_10_03.00002")
        }
        AF.upload(multipartFormData: { (multipartFormData) in
            multipartFormData.append(patientInformationJson, withName: "patient_information", mimeType: "text/plain")
            multipartFormData.append(recordStartTimeData, withName: "record_start_time", mimeType: "text/plain")
            multipartFormData.append(wavData, withName: "data", fileName: "sound.wav", mimeType: "audio/x-wav")
            multipartFormData.append(textData, withName: "text", mimeType: "text/plain")
        }, to: url, method: .post, requestModifier: { $0.timeoutInterval = 5.0 }).validate().response {(response) -> () in
            switch (response.result) {
            case .success:
                var sessionCheckResult = ""
                if let unwrapped = response.data {
                    do {
                        let json = try JSONSerialization.jsonObject(with: unwrapped)
                        let d = json as! [String: String]
                        guard let sessionCheckResultTmp = d["result"] else {return}
                        sessionCheckResult = sessionCheckResultTmp
                    } catch {
                    }
                }
                if(sessionCheckResult == "NG") {  //セッションチェックエラー時
                    (result, messageId) = (false, "warn.common.session")
                } else {  //送信成功時
                    (result, messageId) =  (true, "")
                }
            //送信失敗時処理
            case .failure(let error):
                //タイムアウトが発生した場合
                if error.isSessionTaskError {
                    retryCount += 1
                    //送信を再実行（録音データ送信リトライ待機時間後）
                    // 録音データ送信リトライ待機時間は、タイムアウトとなるまでに要する時間を控除する。
                    Thread.sleep(forTimeInterval: Consts.RECORDING_SEND_RETRY_WAIT_TIME - Consts.RECORDING_SEND_TIMEOUT_TIME)
                    (result, messageId) = sendData()
                    //               //その他システムエラーの場合
                } else {
                    (result, messageId) =  (false, "warn.common.system_error")
                }
            }
        }
        return (result, messageId)
    }

    //ネットワークチェック
    if Network.shared.isOnline() {
        return sendData()
    } else {
        return (false, "warn.common.network")
        
    }
}
